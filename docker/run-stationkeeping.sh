#!/usr/bin/env bash
set -euo pipefail

source /opt/ros/melodic/setup.bash
source /opt/vrx_ws/devel/setup.bash

gui="${VRX_GUI:-false}"
verbose="${VRX_VERBOSE:-false}"
namespace="${VRX_NAMESPACE:-wamv}"
extra_gazebo_args="${VRX_EXTRA_GAZEBO_ARGS:-}"
wind_seed="${VRX_WIND_SEED:-}"
world_arg=""
seeded_dir=""

if [[ -n "${wind_seed}" && "${wind_seed}" != "0" ]]; then
  if [[ ! "${wind_seed}" =~ ^[0-9]+$ ]]; then
    echo "VRX_WIND_SEED must be an unsigned integer, 0, or empty" >&2
    exit 2
  fi

  source_world_xacro="${VRX_SOURCE_DIR}/vrx_gazebo/worlds/stationkeeping_task.world.xacro"
  if [[ ! -f "${source_world_xacro}" ]]; then
    echo "Historical station-keeping world not found: ${source_world_xacro}" >&2
    exit 1
  fi

  seeded_dir="$(mktemp -d /tmp/vrx-seeded-world.XXXXXX)"
  trap 'rm -rf "${seeded_dir}"' EXIT
  seeded_xacro="${seeded_dir}/stationkeeping_task.world.xacro"
  seeded_world="${seeded_dir}/stationkeeping_task.world"

  if [[ "$(grep -c '<xacro:usv_wind_gazebo>' "${source_world_xacro}")" != "1" ]]; then
    echo "Expected exactly one station-keeping wind macro invocation" >&2
    exit 1
  fi

  sed "s#<xacro:usv_wind_gazebo>#<xacro:usv_wind_gazebo seed=\"${wind_seed}\">#" \
    "${source_world_xacro}" > "${seeded_xacro}"
  xacro --inorder "${seeded_xacro}" > "${seeded_world}"
  world_arg="world:=${seeded_world}"
  echo "Using explicit VRX wind seed ${wind_seed} in a generated world copy"
else
  echo "Using the upstream station-keeping world without a seed override"
fi

roslaunch_args=(
  vrx_gazebo
  station_keeping.launch
  "gui:=${gui}"
  "verbose:=${verbose}"
  "namespace:=${namespace}"
  "extra_gazebo_args:=${extra_gazebo_args}"
)
if [[ -n "${world_arg}" ]]; then
  roslaunch_args+=("${world_arg}")
fi

exec roslaunch "${roslaunch_args[@]}"
