#!/usr/bin/env python3
"""ROS Melodic station-keeping node for the stock VRX WAM-V T layout.

Inputs are the real robot_localization odometry and VRX GeoPose goal.  The
three Float32 command topics and three Float32 angle topics are the interfaces
declared by the stock WAM-V thrust plugin.
"""

import math
import threading

import numpy as np
import rospy
from geographic_msgs.msg import GeoPoseStamped
from nav_msgs.msg import Odometry
from std_msgs.msg import Float32, Float32MultiArray

from vrx_controller import (
    ActuatorLimits,
    BodyVelocity,
    ControllerConfig,
    PIDGains,
    PlanarVehicleModel,
    Pose2D,
    StationKeepingController,
    StationKeepingState,
    force_to_command,
    quaternion_to_yaw,
    wgs84_to_local_enu,
)


class StationKeepingNode(object):
    """Bridge ROS messages into the simulator-independent controller core."""

    def __init__(self):
        self.namespace = rospy.get_param("~namespace", "wamv").strip("/")
        self.localization_topic = rospy.get_param(
            "~localization_topic", "/wamv/robot_localization/odometry/filtered"
        )
        self.goal_topic = rospy.get_param("~goal_topic", "/vrx/station_keeping/goal")
        self.control_hz = float(self._param("control_hz", 10.0))
        self.max_state_age_s = float(self._param("max_state_age_s", 1.0))
        self.datum_latitude = float(self._param("datum_latitude_deg", 21.30996))
        self.datum_longitude = float(self._param("datum_longitude_deg", -157.8901))
        self.config = self._make_config()
        self.controller = StationKeepingController(self.config)

        names = self._param("thrusters/names", ["left", "right", "lateral"])
        if len(names) != 3:
            raise ValueError("the VRX T layout requires exactly three thrusters")
        self.thruster_names = list(names)
        self.command_publishers = [
            rospy.Publisher(
                "/{}/thrusters/{}_thrust_cmd".format(self.namespace, name),
                Float32,
                queue_size=1,
            )
            for name in self.thruster_names
        ]
        self.angle_publishers = [
            rospy.Publisher(
                "/{}/thrusters/{}_thrust_angle".format(self.namespace, name),
                Float32,
                queue_size=1,
            )
            for name in self.thruster_names
        ]
        self.diagnostics_pub = rospy.Publisher("~diagnostics", Float32MultiArray, queue_size=10)
        self._lock = threading.Lock()
        self._state = None
        self._state_stamp = None
        self._target = None
        self._last_control_time = None
        self._warned_missing = False

        rospy.Subscriber(self.localization_topic, Odometry, self._on_odometry, queue_size=1)
        rospy.Subscriber(self.goal_topic, GeoPoseStamped, self._on_goal, queue_size=1)
        rospy.on_shutdown(self._stop)
        if self.control_hz <= 0.0:
            raise ValueError("control_hz must be positive")
        self._timer = rospy.Timer(rospy.Duration(1.0 / self.control_hz), self._on_timer)
        rospy.loginfo(
            "VRX station-keeping controller using %s and %s; ENU datum %.8f %.8f",
            self.localization_topic,
            self.goal_topic,
            self.datum_latitude,
            self.datum_longitude,
        )

    def _param(self, name, default):
        """Read private parameters first, then the launch-file controller map."""

        return rospy.get_param("~" + name, rospy.get_param("/controller/" + name, default))

    def _make_config(self):
        mass = np.asarray(
            self._param("mass", [320.0, 0.0, 0.0, 0.0, 320.0, 0.0, 0.0, 0.0, 446.0]),
            dtype=float,
        ).reshape(3, 3)
        damping = np.asarray(
            self._param("damping", [51.3, 0.0, 0.0, 0.0, 40.0, 0.0, 0.0, 0.0, 400.0]),
            dtype=float,
        ).reshape(3, 3)
        pid = self._param("pid", {})
        thrusters = self._param("thrusters", {})
        positions = np.asarray(
            thrusters.get("positions", [-2.373776, 1.027135, -2.373776, -1.027135, 0.0, 0.0]),
            dtype=float,
        ).reshape(3, 2)
        directions = np.asarray(
            thrusters.get("directions", [1.0, 0.0, 0.0, 1.0, 0.0, 1.0]),
            dtype=float,
        ).reshape(3, 2)
        effectiveness = np.vstack(
            (
                directions[:, 0],
                directions[:, 1],
                positions[:, 0] * directions[:, 1] - positions[:, 1] * directions[:, 0],
            )
        )
        limits = ActuatorLimits(
            force_min=np.asarray(thrusters.get("force_min", [-100.0] * 3), dtype=float),
            force_max=np.asarray(thrusters.get("force_max", [240.0] * 3), dtype=float),
            rate_limit=np.asarray(thrusters.get("rate_limit", [500.0] * 3), dtype=float),
            dead_zone=np.asarray(thrusters.get("dead_zone", [0.5] * 3), dtype=float),
        )
        return ControllerConfig(
            model=PlanarVehicleModel(mass=mass, damping=damping),
            pid=PIDGains(
                kp=pid.get("kp", [12.0, 12.0, 60.0]),
                ki=pid.get("ki", [0.0, 0.0, 0.0]),
                kd=pid.get("kd", [50.0, 50.0, 100.0]),
                output_min=pid.get("output_min", [-100.0, -100.0, -160.0]),
                output_max=pid.get("output_max", [150.0, 150.0, 160.0]),
                integral_min=pid.get("integral_min", [-1.0, -1.0, -1.0]),
                integral_max=pid.get("integral_max", [1.0, 1.0, 1.0]),
                anti_windup_gain=pid.get("anti_windup_gain", [0.0, 0.0, 0.0]),
            ),
            effectiveness=effectiveness,
            actuator_limits=limits,
            observer_bandwidth_hz=float(self._param("observer_bandwidth_hz", 0.3)),
            wrench_weights=np.asarray(self._param("wrench_weights", [1.0, 1.0, 0.5]), dtype=float),
            allocation_regularization=float(self._param("allocation_regularization", 1e-8)),
        )

    @staticmethod
    def _valid(value):
        return math.isfinite(float(value))

    def _on_goal(self, message):
        latitude = message.pose.position.latitude
        longitude = message.pose.position.longitude
        orientation = message.pose.orientation
        values = [latitude, longitude, orientation.x, orientation.y, orientation.z, orientation.w]
        if not all(self._valid(value) for value in values):
            rospy.logwarn("Ignoring non-finite VRX station-keeping goal")
            return
        x, y = wgs84_to_local_enu(latitude, longitude, self.datum_latitude, self.datum_longitude)
        yaw = quaternion_to_yaw(orientation.x, orientation.y, orientation.z, orientation.w)
        with self._lock:
            self._target = Pose2D(x, y, yaw)
        rospy.loginfo(
            "Received VRX goal lat/lon=(%.8f, %.8f) -> ENU=(%.3f, %.3f), yaw=%.3f",
            latitude,
            longitude,
            x,
            y,
            yaw,
        )

    def _on_odometry(self, message):
        pose = message.pose.pose
        twist = message.twist.twist
        values = [
            pose.position.x,
            pose.position.y,
            pose.orientation.x,
            pose.orientation.y,
            pose.orientation.z,
            pose.orientation.w,
            twist.linear.x,
            twist.linear.y,
            twist.angular.z,
        ]
        if not all(self._valid(value) for value in values):
            rospy.logwarn_throttle(5.0, "Ignoring non-finite WAM-V localization")
            return
        state = StationKeepingState(
            pose=Pose2D(
                pose.position.x,
                pose.position.y,
                quaternion_to_yaw(
                    pose.orientation.x,
                    pose.orientation.y,
                    pose.orientation.z,
                    pose.orientation.w,
                ),
            ),
            velocity=BodyVelocity(twist.linear.x, twist.linear.y, twist.angular.z),
        )
        stamp = message.header.stamp.to_sec()
        if stamp <= 0.0:
            stamp = rospy.get_time()
        with self._lock:
            self._state = state
            self._state_stamp = stamp

    def _on_timer(self, _event):
        now = rospy.get_time()
        with self._lock:
            state = self._state
            state_stamp = self._state_stamp
            target = self._target
        if state is None or target is None:
            if not self._warned_missing:
                rospy.loginfo("Waiting for WAM-V localization and VRX goal")
                self._warned_missing = True
            self._stop()
            return
        if state_stamp is not None and now > 0.0 and now - state_stamp > self.max_state_age_s:
            rospy.logwarn_throttle(5.0, "WAM-V localization is stale; publishing zero thrusters")
            self._stop()
            return
        if self._last_control_time is None or now <= self._last_control_time:
            self._last_control_time = now
            return
        dt = min(now - self._last_control_time, 0.25)
        self._last_control_time = now
        try:
            output = self.controller.step(state, target, dt)
        except ValueError as exc:
            rospy.logerr_throttle(5.0, "Controller rejected state: %s", exc)
            self._stop()
            return
        commands = [force_to_command(force) for force in output.command]
        for publisher, command in zip(self.command_publishers, commands):
            publisher.publish(Float32(data=float(command)))
        for publisher in self.angle_publishers:
            publisher.publish(Float32(data=0.0))
        self.diagnostics_pub.publish(
            Float32MultiArray(
                data=[
                    float(now),
                    float(state.pose.x),
                    float(state.pose.y),
                    float(state.pose.yaw),
                    float(target.x),
                    float(target.y),
                    float(target.yaw),
                ]
                + [float(value) for value in output.command]
                + [float(value) for value in commands]
            )
        )

    def _stop(self):
        for publisher in self.command_publishers:
            publisher.publish(Float32(data=0.0))
        for publisher in self.angle_publishers:
            publisher.publish(Float32(data=0.0))


def main():
    rospy.init_node("station_keeping_controller")
    try:
        StationKeepingNode()
    except (ValueError, KeyError) as exc:
        rospy.logfatal("Cannot configure station-keeping controller: %s", exc)
        return 2
    rospy.spin()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

