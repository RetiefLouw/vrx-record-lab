#!/usr/bin/env bash
set -euo pipefail

source /opt/ros/melodic/setup.bash
source /opt/vrx_ws/devel/setup.bash

artifact_dir="${VRX_PHASE2_ARTIFACT_DIR:-/var/log/vrx}"
world_path="${VRX_WORLD_PATH:-}"
world_id="${VRX_WORLD_ID:-unknown}"
wall_timeout="${VRX_PHASE2_WALL_TIMEOUT_S:-840}"
mkdir -p "${artifact_dir}"

if [[ ! "${world_path}" =~ ^/opt/vrx_ws/src/vrx/vrx_gazebo/worlds/2019_phase2/stationkeeping[0-5]\.world$ ]]; then
  echo "VRX_WORLD_PATH must select one of the six public phase-2 worlds" >&2
  exit 2
fi
if [[ ! -f "${world_path}" ]]; then
  echo "selected phase-2 world is missing: ${world_path}" >&2
  exit 1
fi
expected_world_sha256="${VRX_PHASE2_EXPECTED_WORLD_SHA256:-}"
if [[ -n "${expected_world_sha256}" ]]; then
  actual_world_sha256="$(sha256sum "${world_path}" | awk '{print $1}')"
  if [[ "${actual_world_sha256}" != "${expected_world_sha256}" ]]; then
    echo "selected phase-2 world digest mismatch: expected ${expected_world_sha256}, got ${actual_world_sha256}" >&2
    exit 1
  fi
fi

run_mode="${VRX_PHASE2_RUN_MODE:-complete_scored}"
selected_world="${world_path}"
generated_dir=""
initial_override="${VRX_INITIAL_STATE_DURATION_OVERRIDE:-}"
ready_override="${VRX_READY_STATE_DURATION_OVERRIDE:-}"
running_override="${VRX_RUNNING_STATE_DURATION_OVERRIDE:-}"
if [[ -n "${initial_override}${ready_override}${running_override}" ]]; then
  run_mode="shortened_smoke"
  for value in "${initial_override}" "${ready_override}" "${running_override}"; do
    if [[ -n "${value}" && ! "${value}" =~ ^[0-9]+([.][0-9]+)?$ ]]; then
      echo "duration overrides must be non-negative decimal seconds" >&2
      exit 2
    fi
  done
  generated_dir="$(mktemp -d /tmp/vrx-phase2-world.XXXXXX)"
  trap 'rm -rf "${generated_dir}"' EXIT
  selected_world="${generated_dir}/$(basename "${world_path}")"
  cp "${world_path}" "${selected_world}"
  if [[ -n "${initial_override}" ]]; then
    sed -i "s#<initial_state_duration>[^<]*</initial_state_duration>#<initial_state_duration>${initial_override}</initial_state_duration>#" "${selected_world}"
  fi
  if [[ -n "${ready_override}" ]]; then
    sed -i "s#<ready_state_duration>[^<]*</ready_state_duration>#<ready_state_duration>${ready_override}</ready_state_duration>#" "${selected_world}"
  fi
  if [[ -n "${running_override}" ]]; then
    sed -i "s#<running_state_duration>[^<]*</running_state_duration>#<running_state_duration>${running_override}</running_state_duration>#" "${selected_world}"
  fi
fi

cp "${selected_world}" "${artifact_dir}/world.sdf"
cat > "${artifact_dir}/runtime-metadata.json" <<EOF
{
  "world_id": "${world_id}",
  "world_path": "${world_path}",
  "world_sha256": "${expected_world_sha256:-}",
  "run_mode": "${run_mode}",
  "initial_state_duration_override_s": ${initial_override:-null},
  "ready_state_duration_override_s": ${ready_override:-null},
  "running_state_duration_override_s": ${running_override:-null},
  "wall_timeout_s": ${wall_timeout}
}
EOF

launch_pid=""
cleanup() {
  set +e
  if [[ -n "${launch_pid}" ]] && kill -0 "${launch_pid}" 2>/dev/null; then
    kill -TERM -- "-${launch_pid}" 2>/dev/null || kill -TERM "${launch_pid}" 2>/dev/null || true
    wait "${launch_pid}" 2>/dev/null || true
  fi
  if [[ -n "${generated_dir}" ]]; then
    rm -rf "${generated_dir}"
  fi
}
trap cleanup EXIT INT TERM

setsid roslaunch vrx_gazebo station_keeping.launch \
  "gui:=${VRX_GUI:-false}" \
  "verbose:=${VRX_VERBOSE:-false}" \
  "namespace:=${VRX_NAMESPACE:-wamv}" \
  "world:=${selected_world}" \
  "extra_gazebo_args:=${VRX_EXTRA_GAZEBO_ARGS:-}" \
  >"${artifact_dir}/gazebo.log" 2>&1 &
launch_pid=$!

startup_deadline=$((SECONDS + 60))
until rostopic list 2>/dev/null | grep -Fxq /vrx/task/info; do
  if ! kill -0 "${launch_pid}" 2>/dev/null; then
    echo "roslaunch exited before /vrx/task/info became available" >&2
    exit 1
  fi
  if (( SECONDS >= startup_deadline )); then
    echo "timed out waiting for /vrx/task/info" >&2
    exit 124
  fi
  sleep 1
done

timeout --signal=TERM --kill-after=10 "${wall_timeout}" \
    python /usr/local/bin/vrx-collect-task-info \
    --output "${artifact_dir}/score.json" \
    --score-topic /vrx/task/info \
    --pose-error-topic /vrx/station_keeping/pose_error \
    --mean-error-topic /vrx/station_keeping/rms_error \
  >"${artifact_dir}/collector.log" 2>&1
