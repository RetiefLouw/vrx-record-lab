#!/usr/bin/env python
"""Python 2.7 ROS adapter for a public-world UF MRAC practice run.

The control equations mirror ``src/vrx_controller/uf_mrac.py``. This adapter
exists only because the pinned ROS Melodic image has Python 2.7/3.6 while the
project package targets modern Python. It uses Gazebo ground truth, a known
public-world ENU origin, a stationary goal, and a co-located X-thruster mapper;
these are practice deviations from UF's localized /odom plus external LQ-RRT
/trajectory/cmd runtime path.
"""

from __future__ import division

import json
import math
import os

import numpy as np
import rospy
import tf.transformations as transformations
from gazebo_msgs.msg import ModelStates
from geographic_msgs.msg import GeoPoseStamped
from geometry_msgs.msg import WrenchStamped
from std_msgs.msg import Float32
from vrx_gazebo.msg import Task


ORIGIN_LAT = 21.30996
ORIGIN_LON = -157.8901
EARTH_SEMI_MAJOR = 6378137.0
EARTH_ECCENTRICITY_SQUARED = 6.6943799901413165e-3


def wrap_angle(value):
    return (value + math.pi) % (2.0 * math.pi) - math.pi


def spherical_to_local(latitude, longitude):
    lat = math.radians(latitude)
    lat0 = math.radians(ORIGIN_LAT)
    lon = math.radians(longitude)
    lon0 = math.radians(ORIGIN_LON)
    sin_lat0 = math.sin(lat0)
    meridian = EARTH_SEMI_MAJOR * (1.0 - EARTH_ECCENTRICITY_SQUARED) / (
        (1.0 - EARTH_ECCENTRICITY_SQUARED * sin_lat0 * sin_lat0) ** 1.5
    )
    prime_vertical = EARTH_SEMI_MAJOR / math.sqrt(
        1.0 - EARTH_ECCENTRICITY_SQUARED * sin_lat0 * sin_lat0
    )
    return np.array(
        [
            (lon - lon0) * prime_vertical * math.cos(lat0),
            (lat - lat0) * meridian,
        ],
        dtype=float,
    )


class PracticeMRAC(object):
    """Source-law mirror for legacy ROS, ending at a body wrench."""

    def __init__(self):
        self.kp_body = np.diag([1000.0, 1000.0, 5600.0])
        self.kd_body = np.diag([1200.0, 1200.0, 6000.0])
        self.ki = np.array([0.1, 0.1, 0.1])
        self.kg = np.array([5.0, 5.0, 5.0, 5.0, 5.0])
        self.dist_limit = np.array([200.0, 200.0, 200.0])
        self.drag_limit = np.array([1000.0, 1000.0, 1000.0])
        self.dist_est = np.zeros(3)
        self.drag_est = np.zeros(5)
        positions = np.array(
            [
                [-2.373776, 1.027135, 0.318237],
                [-2.373776, -1.027135, 0.318237],
                [1.6, 0.7, 0.25],
                [1.6, -0.7, 0.25],
            ]
        )
        directions = np.array(
            [
                [0.7071, 0.7071, 0.0],
                [0.7071, -0.7071, 0.0],
                [0.7071, -0.7071, 0.0],
                [0.7071, 0.7071, 0.0],
            ]
        )
        lever_arms = np.cross(positions, directions)
        self.mapper = np.concatenate((directions[:, :2].T, lever_arms[:, 2:3].T))

    @staticmethod
    def regressor(world_velocity, yaw, yaw_rate):
        vx, vy = world_velocity
        c = math.cos(yaw)
        s = math.sin(yaw)
        return np.array(
            [
                [vx * c ** 2 + vy * s * c, vx / 2.0 - vx * math.cos(2.0 * yaw) / 2.0 - vy * math.sin(2.0 * yaw) / 2.0, -yaw_rate * s, -yaw_rate * c, 0.0],
                [vy / 2.0 - vy * math.cos(2.0 * yaw) / 2.0 + vx * math.sin(2.0 * yaw) / 2.0, vy * c ** 2 - vx * c * s, yaw_rate * c, -yaw_rate * s, 0.0],
                [0.0, 0.0, vy * c - vx * s, -vx * c - vy * s, yaw_rate],
            ],
            dtype=float,
        )

    @staticmethod
    def force_to_command(force):
        if force > 250.0:
            return 1.0
        if force < -100.0:
            return -1.0
        if force > 3.27398:
            return -0.2 * math.log(-0.246597 * (0.56 - 4.73341 / ((-0.01 + force) ** 0.38)))
        if force < 0.0:
            return -0.113122 * math.log(-154.285 * (0.99 - 1.88948e12 / ((199.13 + force) ** 5.34)))
        return 0.01 * force / 3.27398

    def wrench_to_commands(self, body_wrench):
        forces = np.linalg.lstsq(self.mapper, body_wrench, rcond=-1)[0]
        forces = np.clip(forces, -100.0, 250.0)
        return [self.force_to_command(float(force)) for force in forces]

    def step(self, position, yaw, body_velocity, goal, dt):
        c = math.cos(yaw)
        s = math.sin(yaw)
        rotation = np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])
        world_velocity = rotation.dot(np.array([body_velocity[0], body_velocity[1], 0.0]))[:2]
        pose_error = np.array([goal[0] - position[0], goal[1] - position[1], wrap_angle(goal[2] - yaw)])
        velocity_error = np.array([-world_velocity[0], -world_velocity[1], -body_velocity[2]])
        pd = rotation.dot(self.kp_body).dot(rotation.T).dot(pose_error)
        pd += rotation.dot(self.kd_body).dot(rotation.T).dot(velocity_error)
        regressor = self.regressor(world_velocity, yaw, body_velocity[2])
        drag_effort = np.clip(regressor.dot(self.drag_est), -self.drag_limit, self.drag_limit)
        wrench_world = pd + self.dist_est + drag_effort
        if np.linalg.norm(pose_error[:2]) < 10.0:
            self.dist_est = np.clip(self.dist_est + self.ki * pose_error * dt, -self.dist_limit, self.dist_limit)
            self.drag_est += self.kg * regressor.T.dot(pose_error + velocity_error) * dt
        return rotation.T.dot(wrench_world)


class PracticeNode(object):
    def __init__(self):
        self.controller = PracticeMRAC()
        self.goal = None
        self.task = None
        self.last_time = None
        self.wrench_pub = rospy.Publisher("/wrench/autonomous", WrenchStamped, queue_size=1)
        self.thruster_pubs = [
            rospy.Publisher("/wamv/thrusters/left_rear_thrust_cmd", Float32, queue_size=1),
            rospy.Publisher("/wamv/thrusters/right_rear_thrust_cmd", Float32, queue_size=1),
            rospy.Publisher("/wamv/thrusters/left_front_thrust_cmd", Float32, queue_size=1),
            rospy.Publisher("/wamv/thrusters/right_front_thrust_cmd", Float32, queue_size=1),
        ]
        rospy.Subscriber("/vrx/station_keeping/goal", GeoPoseStamped, self.goal_callback, queue_size=1)
        rospy.Subscriber("/vrx/task/info", Task, self.task_callback, queue_size=1)
        rospy.Subscriber("/gazebo/model_states", ModelStates, self.model_callback, queue_size=1)

    def goal_callback(self, msg):
        local = spherical_to_local(msg.pose.position.latitude, msg.pose.position.longitude)
        yaw = transformations.euler_from_quaternion(
            [msg.pose.orientation.x, msg.pose.orientation.y, msg.pose.orientation.z, msg.pose.orientation.w]
        )[2]
        self.goal = np.array([local[0], local[1], yaw], dtype=float)
        rospy.loginfo("UF MRAC practice goal in public-world ENU: %.3f %.3f %.3f", *self.goal)

    def task_callback(self, msg):
        if msg.name == "stationkeeping":
            self.task = msg
            if msg.state == "finished":
                self.write_result()
                rospy.signal_shutdown("practice world finished")

    def model_callback(self, msg):
        if self.goal is None or "wamv" not in msg.name:
            return
        index = msg.name.index("wamv")
        pose = msg.pose[index]
        twist = msg.twist[index]
        yaw = transformations.euler_from_quaternion(
            [pose.orientation.x, pose.orientation.y, pose.orientation.z, pose.orientation.w]
        )[2]
        c = math.cos(yaw)
        s = math.sin(yaw)
        body_velocity = np.array(
            [c * twist.linear.x + s * twist.linear.y, -s * twist.linear.x + c * twist.linear.y, twist.angular.z],
            dtype=float,
        )
        now = rospy.get_time()
        dt = 0.02 if self.last_time is None else now - self.last_time
        self.last_time = now
        if dt <= 0.0 or dt > 0.2:
            dt = 0.02
        body_wrench = self.controller.step(
            np.array([pose.position.x, pose.position.y]), yaw, body_velocity, self.goal, dt
        )
        wrench_msg = WrenchStamped()
        wrench_msg.header.stamp = rospy.Time.now()
        wrench_msg.header.frame_id = "/base_link"
        wrench_msg.wrench.force.x = body_wrench[0]
        wrench_msg.wrench.force.y = body_wrench[1]
        wrench_msg.wrench.torque.z = body_wrench[2]
        self.wrench_pub.publish(wrench_msg)
        for publisher, command in zip(self.thruster_pubs, self.controller.wrench_to_commands(body_wrench)):
            publisher.publish(command)

    def write_result(self):
        if self.task is None:
            return
        score = float(self.task.score)
        # In the public scorer, reaching the normal 300 s end transitions the
        # task to finished and also sets timed_out=true. A finite final score
        # is therefore a completed scored trial, while timed_out is retained
        # as a diagnostic rather than treated as process failure.
        timed_out = bool(self.task.timed_out)
        result = {
            "completed": self.task.state == "finished" and bool(np.isfinite(score)),
            "status": "completed" if self.task.state == "finished" and bool(np.isfinite(score)) else "timeout",
            "score": score if self.task.state == "finished" and bool(np.isfinite(score)) else None,
            "score_components": {"public_practice_scorer_running_mean": score},
            "metrics": {
                "task_state": self.task.state,
                "timed_out": timed_out,
                "controller": "uf-mrac-public-source-port",
                "state_source": "gazebo/model_states ground truth (practice deviation)",
            },
        }
        output_path = os.environ.get("VRX_PRACTICE_OUTPUT", "/var/log/vrx/uf-mrac-practice.json")
        with open(output_path, "w") as output_file:
            json.dump(result, output_file, indent=2, sort_keys=True)
            output_file.write("\n")
        rospy.loginfo("UF MRAC practice result written to %s: score=%s", output_path, score)


if __name__ == "__main__":
    rospy.init_node("uf_mrac_practice")
    PracticeNode()
    rospy.spin()
