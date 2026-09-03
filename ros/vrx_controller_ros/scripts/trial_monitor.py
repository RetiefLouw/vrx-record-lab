#!/usr/bin/env python3
"""Record the real VRX task state and exit only after scorer completion."""

import json
import os
import sys
import time

import rospy
from vrx_gazebo.msg import Task


class TrialMonitor(object):
    def __init__(self, output_dir):
        self.history_path = os.path.join(output_dir, "task-info.jsonl")
        self.summary_path = os.path.join(output_dir, "task-summary.json")
        self.finished = False
        self.last = None
        self.history = open(self.history_path, "w")
        rospy.Subscriber("/vrx/task/info", Task, self._on_task, queue_size=100)

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
        deadline = time.monotonic() + timeout_s
        while not rospy.is_shutdown() and not self.finished and time.monotonic() < deadline:
            # Do not use rospy.Rate here: with /use_sim_time enabled, a
            # failed Gazebo launch can leave ROS time frozen at zero.
            time.sleep(0.1)
        self.history.close()
        if self.last is None or not self.finished:
            return 2
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
