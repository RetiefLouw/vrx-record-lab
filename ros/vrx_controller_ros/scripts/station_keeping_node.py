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
        errors = (c * dx + s * dy, -s * dx + c * dy, wrap_angle(target[2] - yaw))
        velocities = (surge, sway, yaw_rate)
        wrench = [self.kp[i] * errors[i] - self.kd[i] * velocities[i] for i in range(3)]
        wrench = [max(self.output_min[i], min(self.output_max[i], wrench[i])) for i in range(3)]
        lever = 1.027135
        forces = [0.5 * wrench[0] - wrench[2] / (2.0 * lever),
                  0.5 * wrench[0] + wrench[2] / (2.0 * lever), wrench[1]]
        forces = [max(-100.0, min(240.0, value)) for value in forces]
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
