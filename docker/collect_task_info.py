#!/usr/bin/env python2
"""Collect task and station-keeping debug topics until the task finishes."""

import argparse
import json
import math
import os

import rospy
from std_msgs.msg import Float32MultiArray, Float64
from vrx_gazebo.msg import Task


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--score-topic", default="/vrx/task/info")
    parser.add_argument("--pose-error-topic", default="/vrx/station_keeping/pose_error")
    parser.add_argument("--mean-error-topic", default="/vrx/station_keeping/rms_error")
    parser.add_argument("--controller-diagnostics-topic", default="/vrx_controller/diagnostics")
    parser.add_argument("--position-source", default="unspecified")
    parser.add_argument("--require-controller-diagnostics", action="store_true")
    args = parser.parse_args()

    task_messages = []
    debug_messages = {"pose_error": [], "mean_error": []}
    debug_samples = {"pose_error": [], "mean_error": []}
    output_dir = os.path.dirname(os.path.abspath(args.output))
    task_info_path = os.path.join(output_dir, "task-info.jsonl")
    task_info_stream = open(task_info_path, "w")
    controller_diagnostics_path = os.path.join(output_dir, "controller-diagnostics.jsonl")
    controller_diagnostics_stream = open(controller_diagnostics_path, "w")
    counters = {"controller_diagnostics": 0, "controller_diagnostic_parse_errors": 0}
    state = {"final": None}

    def task_callback(message):
        value = {
            "recorded_at_s": rospy.Time.now().to_sec(),
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
        task_info_stream.write(json.dumps(value, sort_keys=True) + "\n")
        task_info_stream.flush()
        if message.state == "finished":
            state["final"] = value
            rospy.signal_shutdown("task finished")

    def pose_callback(message):
        debug_messages["pose_error"].append(float(message.data))
        debug_samples["pose_error"].append({"stamp_s": rospy.Time.now().to_sec(), "value": float(message.data)})

    def mean_callback(message):
        debug_messages["mean_error"].append(float(message.data))
        debug_samples["mean_error"].append({"stamp_s": rospy.Time.now().to_sec(), "value": float(message.data)})

    def controller_callback(message):
        data = [float(value) for value in message.data]
        if len(data) != 13 or any(math.isnan(value) or math.isinf(value) for value in data):
            counters["controller_diagnostic_parse_errors"] += 1
            return
        value = {
            "stamp_s": data[0],
            "recorded_at_ros_s": rospy.Time.now().to_sec(),
            "position_source": args.position_source,
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
        controller_diagnostics_stream.write(json.dumps(value, sort_keys=True) + "\n")
        controller_diagnostics_stream.flush()
        counters["controller_diagnostics"] += 1

    rospy.init_node("vrx_record_lab_phase2_collector", anonymous=False)
    rospy.Subscriber(args.score_topic, Task, task_callback, queue_size=100)
    rospy.Subscriber(args.pose_error_topic, Float64, pose_callback, queue_size=100)
    rospy.Subscriber(args.mean_error_topic, Float64, mean_callback, queue_size=100)
    rospy.Subscriber(args.controller_diagnostics_topic, Float32MultiArray, controller_callback, queue_size=100)
    rospy.spin()
    task_info_stream.close()
    controller_diagnostics_stream.close()

    completed = state["final"] is not None and (not args.require_controller_diagnostics or counters["controller_diagnostics"] > 0)
    document = {
        "completed": completed,
        "final": state["final"],
        "task_messages": task_messages,
        "task_info_file": os.path.basename(task_info_path),
        "debug": debug_messages,
        "debug_samples": debug_samples,
        "controller_diagnostics_file": os.path.basename(controller_diagnostics_path),
        "controller_diagnostics_count": counters["controller_diagnostics"],
        "controller_diagnostic_parse_errors": counters["controller_diagnostic_parse_errors"],
        "controller_diagnostics_topic": args.controller_diagnostics_topic,
        "position_source": args.position_source,
    }
    with open(args.output, "w") as stream:
        json.dump(document, stream, indent=2, sort_keys=True)
        stream.write("\n")
    return 0 if completed else 1


if __name__ == "__main__":
    raise SystemExit(main())
