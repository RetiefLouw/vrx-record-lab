#!/usr/bin/env python2
"""Record the real VRX task state and exit only after scorer completion."""

import json
import math
import os
import sys
import time

import rospy
import rosnode
from std_msgs.msg import Float32MultiArray
from vrx_gazebo.msg import Task


class TrialMonitor(object):
    def __init__(self, output_dir):
        self.history_path = os.path.join(output_dir, "task-info.jsonl")
        self.summary_path = os.path.join(output_dir, "task-summary.json")
        self.finished = False
        self.controller_samples = 0
        self.controller_diagnostic_parse_errors = 0
        self.last = None
        self.history = open(self.history_path, "w")
        self.controller_path = os.path.join(output_dir, "controller-diagnostics.jsonl")
        self.controller_stream = open(self.controller_path, "w")
        self.position_source = os.environ.get("VRX_CONTROLLER_POSITION_SOURCE", "unspecified")
        controller_topic = os.environ.get("VRX_CONTROLLER_DIAGNOSTICS_TOPIC", "/vrx_controller/diagnostics")
        rospy.Subscriber("/vrx/task/info", Task, self._on_task, queue_size=100)
        rospy.Subscriber(controller_topic, Float32MultiArray, self._on_controller, queue_size=100)

    def _on_controller(self, _message):
        data = [float(value) for value in _message.data]
        if len(data) != 13 or any(math.isnan(value) or math.isinf(value) for value in data):
            self.controller_diagnostic_parse_errors += 1
            return
        value = {
            "stamp_s": data[0],
            "recorded_at_ros_s": rospy.Time.now().to_sec(),
            "position_source": self.position_source,
            "measured_x_m": data[1],
            "measured_y_m": data[2],
            "measured_yaw_rad": data[3],
            "target_x_m": data[4],
            "target_y_m": data[5],
            "target_yaw_rad": data[6],
            "force_left_n": data[7],
            "force_right_n": data[8],
            "force_lateral_n": data[9],
            "command_left": data[10],
            "command_right": data[11],
            "command_lateral": data[12],
        }
        self.controller_stream.write(json.dumps(value, sort_keys=True) + "\n")
        self.controller_stream.flush()
        self.controller_samples += 1

    def _close_streams(self):
        if not self.history.closed:
            self.history.close()
        if not self.controller_stream.closed:
            self.controller_stream.close()

    def _on_task(self, message):
        value = {
            "ros_time_s": rospy.Time.now().to_sec(),
            "name": message.name,
            "state": message.state,
            "ready_time_s": message.ready_time.to_sec(),
            "running_time_s": message.running_time.to_sec(),
            "elapsed_time_s": message.elapsed_time.to_sec(),
            "remaining_time_s": message.remaining_time.to_sec(),
            "timed_out": bool(message.timed_out),
            "score": float(message.score),
        }
        self.last = value
        self.history.write(json.dumps(value, sort_keys=True) + "\n")
        self.history.flush()
        if message.state == "finished":
            self.finished = True

    def run(self, timeout_s):
        # Use wall time for the watchdog.  ROS time can remain at zero when
        # Gazebo fails before publishing /clock, and must not make a broken
        # launch hang the harness indefinitely.
        # Use the Melodic-native Python 2 runtime for generated message
        # compatibility. time.time is wall clock and remains valid when
        # /use_sim_time is enabled or Gazebo is paused.
        deadline = time.time() + timeout_s
        while not rospy.is_shutdown() and not self.finished and time.time() < deadline:
            required_node = os.environ.get("VRX_REQUIRED_NODE", "/vrx_controller")
            if required_node and required_node not in rosnode.get_node_names():
                rospy.logerr("Required controller node disappeared: %s", required_node)
                self._close_streams()
                return 3
            # Do not use rospy.Rate here: with /use_sim_time enabled, a
            # failed Gazebo launch can leave ROS time frozen at zero.
            time.sleep(0.1)
        self._close_streams()
        if self.last is None or not self.finished or self.controller_samples == 0:
            if self.controller_samples == 0:
                rospy.logerr("No controller diagnostic samples were observed")
            return 2
        self.last["controller_samples"] = self.controller_samples
        self.last["controller_diagnostic_parse_errors"] = self.controller_diagnostic_parse_errors
        self.last["controller_diagnostics_file"] = os.path.basename(self.controller_path)
        with open(self.summary_path, "w") as stream:
            json.dump(self.last, stream, indent=2, sort_keys=True)
            stream.write("\n")
        return 0


def main():
    output_dir = os.environ.get("VRX_TRIAL_ARTIFACT_DIR", "/var/log/vrx")
    timeout_s = float(os.environ.get("VRX_TRIAL_TIMEOUT_S", "600"))
    rospy.init_node("vrx_trial_monitor")
    return TrialMonitor(output_dir).run(timeout_s)


if __name__ == "__main__":
    sys.exit(main())
