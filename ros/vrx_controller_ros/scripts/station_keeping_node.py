#!/usr/bin/env python2
"""Melodic-native conservative station-keeping baseline for the stock T WAM-V."""

import math
import json
import os
import threading

import rospy
from geographic_msgs.msg import GeoPoseStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import NavSatFix
from std_msgs.msg import Float32, Float32MultiArray


def wrap_angle(value):
    return (value + math.pi) % (2.0 * math.pi) - math.pi


def quaternion_to_yaw(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))


def wgs84_to_enu(latitude, longitude, datum_latitude, datum_longitude):
    semi_major = 6378137.0
    flattening = 1.0 / 298.257223563
    eccentricity_sq = 2.0 * flattening - flattening * flattening

    def ecef(lat_deg, lon_deg):
        lat, lon = math.radians(lat_deg), math.radians(lon_deg)
        normal = semi_major / math.sqrt(1.0 - eccentricity_sq * math.sin(lat) ** 2)
        return (normal * math.cos(lat) * math.cos(lon),
                normal * math.cos(lat) * math.sin(lon),
                normal * (1.0 - eccentricity_sq) * math.sin(lat))

    origin, point = ecef(datum_latitude, datum_longitude), ecef(latitude, longitude)
    dx, dy, dz = [point[i] - origin[i] for i in range(3)]
    lat, lon = math.radians(datum_latitude), math.radians(datum_longitude)
    east = -math.sin(lon) * dx + math.cos(lon) * dy
    north = (-math.sin(lat) * math.cos(lon) * dx - math.sin(lat) * math.sin(lon) * dy
             + math.cos(lat) * dz)
    return east, north


def command_to_force(command):
    command = max(-1.0, min(1.0, float(command)))
    if command > 0.01:
        return min(0.01 + (59.82 - 0.01) / (0.56 + math.exp(-5.0 * (command - 0.28))) ** (1.0 / 0.38), 250.0)
    if command == 0.0:
        return 0.0
    return max(-199.13 + (-0.09 + 199.13) / (0.99 + math.exp(-8.84 * (command + 0.57))) ** (1.0 / 5.34), -100.0)


def force_to_command(force):
    force = max(-100.0, min(240.0, float(force)))
    if abs(force) < 0.1:
        return 0.0
    low, high = ((0.010000001, 1.0) if force > 0.0 else (-1.0, -0.010000001))
    for _ in range(60):
        middle = 0.5 * (low + high)
        if command_to_force(middle) < force:
            low = middle
        else:
            high = middle
    return 0.5 * (low + high)


class StationKeepingNode(object):
    def __init__(self):
        self.datum_latitude = float(rospy.get_param("/controller/datum_latitude_deg", 21.30996))
        self.datum_longitude = float(rospy.get_param("/controller/datum_longitude_deg", -157.8901))
        experiment = json.loads(os.environ.get("VRX_CONTROLLER_PARAMETERS_JSON", "{}"))
        self.kp = experiment.get("kp", rospy.get_param("/controller/pid/kp", [12.0, 12.0, 60.0]))
        self.kd = experiment.get("kd", rospy.get_param("/controller/pid/kd", [50.0, 50.0, 100.0]))
        self.output_min = experiment.get("output_min", [-100.0, -100.0, -160.0])
        self.output_max = experiment.get("output_max", [150.0, 150.0, 160.0])
        # Hybrid guidance is opt-in so the frozen fast-PD baseline remains
        # exactly reproducible.  Transit uses a bounded velocity reference
        # and bearing alignment, then hands off to the existing goal-heading
        # PD loop inside transit_radius_m.
        self.guidance_mode = str(experiment.get("guidance_mode", "pd"))
        self.transit_radius_m = max(0.1, float(experiment.get("transit_radius_m", 8.0)))
        self.transit_speed_mps = max(0.1, float(experiment.get("transit_speed_mps", 2.5)))
        self.transit_speed_gain = max(0.0, float(experiment.get("transit_speed_gain", 0.35)))
        self.transit_position_clip_m = max(0.1, float(experiment.get("transit_position_clip_m", 4.0)))
        self.transit_kp_position = max(0.0, float(experiment.get("transit_kp_position", 20.0)))
        self.transit_kd_velocity = max(0.0, float(experiment.get("transit_kd_velocity", 180.0)))
        self.transit_heading_kp = max(0.0, float(experiment.get("transit_heading_kp", self.kp[2])))
        self.transit_heading_kd = max(0.0, float(experiment.get("transit_heading_kd", self.kd[2])))
        self.hold_ki = [max(0.0, float(value)) for value in experiment.get("hold_ki", [0.0, 0.0, 0.0])]
        self.hold_integral_limit = [max(0.0, float(value)) for value in experiment.get("hold_integral_limit", [0.0, 0.0, 0.0])]
        if len(self.hold_ki) != 3 or len(self.hold_integral_limit) != 3:
            raise ValueError("hold_ki and hold_integral_limit must contain three values")
        self.hold_integral = [0.0, 0.0, 0.0]
        self.observer_bandwidth_hz = max(0.0, float(experiment.get("disturbance_observer_bandwidth_hz", 0.0)))
        self.observer_mass = [float(value) for value in experiment.get("disturbance_observer_mass", [320.0, 320.0, 446.0])]
        self.observer_damping = [float(value) for value in experiment.get("disturbance_observer_damping", [51.3, 40.0, 400.0])]
        if len(self.observer_mass) != 3 or len(self.observer_damping) != 3:
            raise ValueError("disturbance observer mass and damping must contain three values")
        if any(value <= 0.0 for value in self.observer_mass) or any(value < 0.0 for value in self.observer_damping):
            raise ValueError("disturbance observer mass must be positive and damping non-negative")
        self.observer_estimate = [0.0, 0.0, 0.0]
        self.previous_velocity = None
        self.previous_applied_wrench = [0.0, 0.0, 0.0]
        self.lock = threading.Lock()
        self.state = None
        self.target = None
        self.gps_xy = None
        self.namespace = rospy.get_param("~namespace", "wamv").strip("/")
        self.position_source_topic = rospy.get_param("~position_source", "/wamv/sensors/gps/gps/fix")
        self.goal_topic = rospy.get_param("~goal_topic", "/vrx/station_keeping/goal")
        self.diagnostics_topic = rospy.get_param("~diagnostics_topic", "/vrx_controller/diagnostics")
        names = ["left", "right", "lateral"]
        self.thrust = [rospy.Publisher("/{}/thrusters/{}_thrust_cmd".format(self.namespace, n), Float32, queue_size=1) for n in names]
        self.angle = [rospy.Publisher("/{}/thrusters/{}_thrust_angle".format(self.namespace, n), Float32, queue_size=1) for n in names]
        self.diagnostics = rospy.Publisher(self.diagnostics_topic, Float32MultiArray, queue_size=10)
        rospy.Subscriber(rospy.get_param("~localization_topic", "/wamv/robot_localization/odometry/filtered"), Odometry, self.on_odometry, queue_size=1)
        rospy.Subscriber(self.position_source_topic, NavSatFix, self.on_gps, queue_size=1)
        rospy.Subscriber(self.goal_topic, GeoPoseStamped, self.on_goal, queue_size=1)
        rospy.Timer(rospy.Duration(0.1), self.on_timer)
        rospy.on_shutdown(self.stop)

    def on_goal(self, message):
        x, y = wgs84_to_enu(message.pose.position.latitude, message.pose.position.longitude,
                            self.datum_latitude, self.datum_longitude)
        with self.lock:
            self.target = (x, y, quaternion_to_yaw(message.pose.orientation))
        rospy.loginfo("Received station-keeping goal ENU=(%.3f, %.3f)", x, y)

    def on_odometry(self, message):
        p, v = message.pose.pose, message.twist.twist
        with self.lock:
            self.state = (p.position.x, p.position.y, quaternion_to_yaw(p.orientation),
                          v.linear.x, v.linear.y, v.angular.z)

    def on_gps(self, message):
        if not any(math.isnan(v) or math.isinf(v) for v in (message.latitude, message.longitude)):
            with self.lock:
                self.gps_xy = wgs84_to_enu(message.latitude, message.longitude,
                                           self.datum_latitude, self.datum_longitude)

    def on_timer(self, _event):
        with self.lock:
            state, target, gps_xy = self.state, self.target, self.gps_xy
        if state is None or target is None or gps_xy is None:
            self.stop()
            return
        _odom_x, _odom_y, yaw, surge, sway, yaw_rate = state
        x, y = gps_xy
        dx, dy = target[0] - x, target[1] - y
        c, s = math.cos(yaw), math.sin(yaw)
        body_dx, body_dy = c * dx + s * dy, -s * dx + c * dy
        velocities = (surge, sway, yaw_rate)
        # Estimate slowly varying external body wrench.  The estimate is
        # intentionally disabled by default and is only applied in hold mode;
        # transit remains governed by the bounded velocity reference.
        if self.observer_bandwidth_hz > 0.0 and self.previous_velocity is not None:
            velocity = [surge, sway, yaw_rate]
            acceleration = [(velocity[i] - self.previous_velocity[i]) / 0.1 for i in range(3)]
            residual = [
                self.observer_mass[i] * acceleration[i]
                + self.observer_damping[i] * velocity[i]
                - self.previous_applied_wrench[i]
                for i in range(3)
            ]
            alpha = 1.0 - math.exp(-2.0 * math.pi * self.observer_bandwidth_hz * 0.1)
            self.observer_estimate = [
                self.observer_estimate[i] + alpha * (residual[i] - self.observer_estimate[i])
                for i in range(3)
            ]
        self.previous_velocity = [surge, sway, yaw_rate]
        distance = math.hypot(dx, dy)
        if self.guidance_mode == "hybrid" and distance > self.transit_radius_m:
            # Transit objective: close range quickly without asking the
            # allocator for an unbounded force proportional to a 100--200 m
            # initial error.  The position term is clipped for braking and
            # the velocity term tracks a bounded, range-proportional speed.
            bearing = math.atan2(dy, dx)
            desired_speed = min(self.transit_speed_mps, self.transit_speed_gain * distance)
            desired_world_x, desired_world_y = desired_speed * math.cos(bearing), desired_speed * math.sin(bearing)
            desired_body_x = c * desired_world_x + s * desired_world_y
            desired_body_y = -s * desired_world_x + c * desired_world_y
            clipped_dx = max(-self.transit_position_clip_m, min(self.transit_position_clip_m, body_dx))
            clipped_dy = max(-self.transit_position_clip_m, min(self.transit_position_clip_m, body_dy))
            heading_error = wrap_angle(bearing - yaw)
            wrench = [
                self.transit_kp_position * clipped_dx + self.transit_kd_velocity * (desired_body_x - surge),
                self.transit_kp_position * clipped_dy + self.transit_kd_velocity * (desired_body_y - sway),
                self.transit_heading_kp * heading_error - self.transit_heading_kd * yaw_rate,
            ]
        else:
            errors = (body_dx, body_dy, wrap_angle(target[2] - yaw))
            if any(value > 0.0 for value in self.hold_ki):
                # Hold-only integral is bounded and conditional: once a
                # wrench axis is saturated, do not integrate further in the
                # direction that would deepen saturation.
                dt = 0.1
                candidate_integral = [
                    max(-self.hold_integral_limit[i], min(self.hold_integral_limit[i], self.hold_integral[i] + errors[i] * dt))
                    for i in range(3)
                ]
                candidate_wrench = [
                    self.kp[i] * errors[i] - self.kd[i] * velocities[i] + self.hold_ki[i] * candidate_integral[i]
                    for i in range(3)
                ]
                for i in range(3):
                    pushing_high = candidate_wrench[i] > self.output_max[i] and errors[i] > 0.0
                    pushing_low = candidate_wrench[i] < self.output_min[i] and errors[i] < 0.0
                    if not (pushing_high or pushing_low):
                        self.hold_integral[i] = candidate_integral[i]
            else:
                self.hold_integral = [0.0, 0.0, 0.0]
            wrench = [
                self.kp[i] * errors[i] - self.kd[i] * velocities[i] + self.hold_ki[i] * self.hold_integral[i]
                for i in range(3)
            ]
            if self.observer_bandwidth_hz > 0.0:
                wrench = [wrench[i] - self.observer_estimate[i] for i in range(3)]
        wrench = [max(self.output_min[i], min(self.output_max[i], wrench[i])) for i in range(3)]
        lever = 1.027135
        forces = [0.5 * wrench[0] - wrench[2] / (2.0 * lever),
                  0.5 * wrench[0] + wrench[2] / (2.0 * lever), wrench[1]]
        forces = [max(-100.0, min(240.0, value)) for value in forces]
        self.previous_applied_wrench = [
            forces[0] + forces[1],
            forces[2],
            lever * (forces[1] - forces[0]),
        ]
        commands = [force_to_command(value) for value in forces]
        for publisher, command in zip(self.thrust, commands):
            publisher.publish(Float32(data=command))
        for publisher in self.angle:
            publisher.publish(Float32(data=0.0))
        self.diagnostics.publish(Float32MultiArray(data=[rospy.get_time(), x, y, yaw,
                                                         target[0], target[1], target[2]] + forces + commands))

    def stop(self):
        for publisher in self.thrust:
            publisher.publish(Float32(data=0.0))
        for publisher in self.angle:
            publisher.publish(Float32(data=0.0))


def main():
    rospy.init_node("vrx_controller")
    StationKeepingNode()
    rospy.spin()


if __name__ == "__main__":
    main()
