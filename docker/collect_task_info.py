#!/usr/bin/env python3
"""Collect task and station-keeping debug topics until the task finishes."""

import argparse
import json

import rospy
from std_msgs.msg import Float64
from vrx_gazebo.msg import Task


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--score-topic", default="/vrx/task/info")
    parser.add_argument("--pose-error-topic", default="/vrx/station_keeping/pose_error")
    parser.add_argument("--mean-error-topic", default="/vrx/station_keeping/rms_error")
    args = parser.parse_args()

    task_messages = []
    debug_messages = {"pose_error": [], "mean_error": []}
    state = {"final": None}

    def task_callback(message):
        value = {
            "name": message.name,
            "state": message.state,
            "ready_time_s": message.ready_time.to_sec(),
            "running_time_s": message.running_time.to_sec(),
            "elapsed_time_s": message.elapsed_time.to_sec(),
            "remaining_time_s": message.remaining_time.to_sec(),
            "timed_out": bool(message.timed_out),
            "score": float(message.score),
        }
        task_messages.append(value)
        if message.state == "finished":
            state["final"] = value
            rospy.signal_shutdown("task finished")

    def pose_callback(message):
        debug_messages["pose_error"].append(float(message.data))

    def mean_callback(message):
        debug_messages["mean_error"].append(float(message.data))

    rospy.init_node("vrx_record_lab_phase2_collector", anonymous=False)
    rospy.Subscriber(args.score_topic, Task, task_callback, queue_size=100)
    rospy.Subscriber(args.pose_error_topic, Float64, pose_callback, queue_size=100)
    rospy.Subscriber(args.mean_error_topic, Float64, mean_callback, queue_size=100)
    rospy.spin()

    document = {
        "completed": state["final"] is not None,
        "final": state["final"],
        "task_messages": task_messages,
        "debug": debug_messages,
    }
    with open(args.output, "w") as stream:
        json.dump(document, stream, indent=2, sort_keys=True)
        stream.write("\n")
    return 0 if state["final"] is not None else 1


if __name__ == "__main__":
    raise SystemExit(main())
