#!/usr/bin/env bash
set -euo pipefail

source /opt/ros/melodic/setup.bash
source /opt/vrx_ws/devel/setup.bash

gui="${VRX_GUI:-false}"
verbose="${VRX_VERBOSE:-false}"
namespace="${VRX_NAMESPACE:-wamv}"
extra_gazebo_args="${VRX_EXTRA_GAZEBO_ARGS:-}"
wind_seed="${VRX_WIND_SEED:-}"
artifact_dir="${VRX_ARTIFACT_DIR:-/var/log/vrx}"
world_arg=""
seeded_dir=""
mkdir -p "${artifact_dir}"

if [[ -n "${wind_seed}" && "${wind_seed}" != "0" ]]; then
  if [[ ! "${wind_seed}" =~ ^[0-9]+$ ]]; then
    echo "VRX_WIND_SEED must be an unsigned integer, 0, or empty" >&2
    exit 2
  fi
  source_world_xacro="${VRX_SOURCE_DIR}/vrx_gazebo/worlds/stationkeeping_task.world.xacro"
  seeded_dir="$(mktemp -d /tmp/vrx-seeded-world.XXXXXX)"
  sed "s#<xacro:usv_wind_gazebo>#<xacro:usv_wind_gazebo seed=\"${wind_seed}\">#" \
    "${source_world_xacro}" > "${seeded_dir}/stationkeeping_task.world.xacro"
  xacro --inorder "${seeded_dir}/stationkeeping_task.world.xacro" > "${seeded_dir}/stationkeeping_task.world"
  world_arg="world:=${seeded_dir}/stationkeeping_task.world"
  echo "Using explicit VRX wind seed ${wind_seed} in a generated world copy"
fi

roslaunch_args=(
  vrx_gazebo
  station_keeping.launch
  "gui:=${gui}"
  "verbose:=${verbose}"
  "namespace:=${namespace}"
  "thrust_config:=X"
  "wamv_locked:=false"
  "vrx_sensors_enabled:=false"
  "extra_gazebo_args:=${extra_gazebo_args}"
)
if [[ -n "${world_arg}" ]]; then
  roslaunch_args+=("${world_arg}")
fi

roslaunch "${roslaunch_args[@]}" > "${artifact_dir}/uf-mrac-roslaunch.log" 2>&1 &
sim_pid=$!
cleanup() {
  kill "${sim_pid}" 2>/dev/null || true
  wait "${sim_pid}" 2>/dev/null || true
  if [[ -n "${seeded_dir}" ]]; then
    rm -rf "${seeded_dir}"
  fi
}
trap cleanup EXIT

export VRX_PRACTICE_OUTPUT="${artifact_dir}/uf-mrac-practice.json"
python /usr/local/bin/uf-mrac-practice.py > "${artifact_dir}/uf-mrac-controller.log" 2>&1
echo "UF MRAC practice trial completed; result: ${VRX_PRACTICE_OUTPUT}"
