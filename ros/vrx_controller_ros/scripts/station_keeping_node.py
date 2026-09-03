#!/usr/bin/env python2
"""Melodic-native conservative station-keeping baseline for the stock T WAM-V."""

import math
import threading

import rospy
from geographic_msgs.msg import GeoPoseStamped
from nav_msgs.msg import Odometry
from std_msgs.msg import Float32, Float32MultiArray


def wrap_angle(value):
    return (value + math.pi) % (2.0 * math.pi) - math.pi


def quaternion_to_yaw(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))


def wgs84_to_enu(latitude, longitude, datum_latitude, datum_longitude):
    radius = 6378137.0
    north = math.radians(latitude - datum_latitude) * radius
    east = math.radians(longitude - datum_longitude) * radius * math.cos(math.radians(datum_latitude))
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
        self.kp = rospy.get_param("/controller/pid/kp", [12.0, 12.0, 60.0])
        self.kd = rospy.get_param("/controller/pid/kd", [50.0, 50.0, 100.0])
        self.lock = threading.Lock()
        self.state = None
        self.target = None
        self.namespace = rospy.get_param("~namespace", "wamv").strip("/")
        names = ["left", "right", "lateral"]
        self.thrust = [rospy.Publisher("/{}/thrusters/{}_thrust_cmd".format(self.namespace, n), Float32, queue_size=1) for n in names]
        self.angle = [rospy.Publisher("/{}/thrusters/{}_thrust_angle".format(self.namespace, n), Float32, queue_size=1) for n in names]
        self.diagnostics = rospy.Publisher("~diagnostics", Float32MultiArray, queue_size=10)
        rospy.Subscriber(rospy.get_param("~localization_topic", "/wamv/robot_localization/odometry/filtered"), Odometry, self.on_odometry, queue_size=1)
        rospy.Subscriber("/vrx/station_keeping/goal", GeoPoseStamped, self.on_goal, queue_size=1)
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

    def on_timer(self, _event):
        with self.lock:
            state, target = self.state, self.target
        if state is None or target is None:
            self.stop()
            return
        x, y, yaw, surge, sway, yaw_rate = state
        dx, dy = target[0] - x, target[1] - y
        c, s = math.cos(yaw), math.sin(yaw)
        errors = (c * dx + s * dy, -s * dx + c * dy, wrap_angle(target[2] - yaw))
        velocities = (surge, sway, yaw_rate)
        wrench = [self.kp[i] * errors[i] - self.kd[i] * velocities[i] for i in range(3)]
        wrench[0] = max(-100.0, min(150.0, wrench[0]))
        wrench[1] = max(-100.0, min(150.0, wrench[1]))
        wrench[2] = max(-160.0, min(160.0, wrench[2]))
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
