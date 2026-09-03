#!/usr/bin/env bash
set -euo pipefail

source /opt/ros/melodic/setup.bash
source /opt/vrx_ws/devel/setup.bash

case "${1:-run}" in
  run)
    exec /usr/local/bin/vrx-run-stationkeeping
    ;;
  bash)
    shift
    exec /bin/bash "$@"
    ;;
  *)
    exec "$@"
    ;;
esac
