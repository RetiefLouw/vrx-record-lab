#!/usr/bin/env bash
set -euo pipefail

artifact_dir="${VRX_TRIAL_ARTIFACT_DIR:-/var/log/vrx}"
mkdir -p "${artifact_dir}"
world="${VRX_WORLD:-${VRX_SOURCE_DIR}/vrx_gazebo/worlds/stationkeeping_task.world}"
timeout_s="${VRX_TRIAL_TIMEOUT_S:-600}"

echo "world=${world}" | tee "${artifact_dir}/trial-protocol.txt"
echo "task_info=/vrx/task/info type=vrx_gazebo/Task" | tee -a "${artifact_dir}/trial-protocol.txt"
echo "goal=/vrx/station_keeping/goal type=geographic_msgs/GeoPoseStamped" | tee -a "${artifact_dir}/trial-protocol.txt"
echo "localization=/wamv/robot_localization/odometry/filtered type=nav_msgs/Odometry" | tee -a "${artifact_dir}/trial-protocol.txt"
echo "thrusters=/wamv/thrusters/{left,right,lateral}_thrust_cmd type=std_msgs/Float32" | tee -a "${artifact_dir}/trial-protocol.txt"

roslaunch vrx_controller_ros scored_station_keeping.launch \
  world:="${world}" gui:=false verbose:=${VRX_VERBOSE:-false} \
  namespace:=${VRX_NAMESPACE:-wamv} wamv_locked:=false \
  >"${artifact_dir}/simulator.log" 2>&1 &
launch_pid=$!

cleanup() {
  set +e
  if [[ -n "${bag_pid:-}" ]]; then kill "${bag_pid}" 2>/dev/null || true; wait "${bag_pid}" 2>/dev/null || true; fi
  if [[ -n "${monitor_pid:-}" ]]; then kill "${monitor_pid}" 2>/dev/null || true; wait "${monitor_pid}" 2>/dev/null || true; fi
  kill "${launch_pid}" 2>/dev/null || true
  wait "${launch_pid}" 2>/dev/null || true
}
trap cleanup EXIT

for _ in $(seq 1 120); do
  if rostopic list 2>/dev/null | grep -Fxq /vrx/task/info; then break; fi
  if ! kill -0 "${launch_pid}" 2>/dev/null; then
    echo "roslaunch exited before /vrx/task/info appeared" >&2
    exit 1
  fi
  sleep 0.5
done
if ! rostopic list 2>/dev/null | grep -Fxq /vrx/task/info; then
  echo "Timed out waiting for /vrx/task/info" >&2
  exit 1
fi

rosbag record -O "${artifact_dir}/topics.bag" \
  /vrx/task/info /vrx/station_keeping/goal \
  /wamv/robot_localization/odometry/filtered \
  /wamv/thrusters/left_thrust_cmd /wamv/thrusters/right_thrust_cmd \
  /wamv/thrusters/lateral_thrust_cmd /wamv/thrusters/left_thrust_angle \
  /wamv/thrusters/right_thrust_angle /wamv/thrusters/lateral_thrust_angle \
  /vrx_controller/diagnostics \
  >"${artifact_dir}/rosbag.log" 2>&1 &
bag_pid=$!

VRX_TRIAL_ARTIFACT_DIR="${artifact_dir}" VRX_TRIAL_TIMEOUT_S="${timeout_s}" \
  VRX_REQUIRED_NODE="/vrx_controller" \
  rosrun vrx_controller_ros trial_monitor.py \
  >"${artifact_dir}/monitor.log" 2>&1 &
monitor_pid=$!
set +e
wait "${monitor_pid}"
monitor_status=$?
set -e
if [[ "${monitor_status}" -ne 0 ]]; then
  echo "Task monitor did not observe a completed scored trial" >&2
  exit "${monitor_status}"
fi

python3 - "${artifact_dir}/task-summary.json" "${artifact_dir}/adapter-output.json" <<'PY'
import json
import os
import sys

summary_path, output_path = sys.argv[1:]
with open(summary_path, encoding="utf-8") as stream:
    summary = json.load(stream)
if summary.get("state") != "finished":
    raise SystemExit("task summary is not finished")
result = {
    "completed": True,
    "status": "completed",
    "score": summary["score"],
    "score_components": {
        "vrx_task_score": summary["score"],
        "scorer_topic": "/vrx/task/info",
        "scorer_message_type": "vrx_gazebo/Task",
    },
    "environment": {
        "world": os.environ.get("VRX_WORLD", ""),
        "wind_seed": "world-defined",
    },
    "metrics": {
        "task_state": summary["state"],
        "task_timed_out": summary["timed_out"],
        "scored_elapsed_s": summary["elapsed_time_s"],
    },
}
with open(output_path, "w", encoding="utf-8") as stream:
    json.dump(result, stream, indent=2, sort_keys=True)
    stream.write("\n")
PY
echo "Completed real VRX scored trial with score $(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["score"])' "${artifact_dir}/task-summary.json")"
