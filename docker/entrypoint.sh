#!/usr/bin/env bash
set -euo pipefail

source /opt/ros/melodic/setup.bash
source /opt/vrx_ws/devel/setup.bash

case "${1:-run}" in
  run)
    exec /usr/local/bin/vrx-run-stationkeeping
    ;;
  uf-mrac-practice)
    exec /usr/local/bin/vrx-run-uf-mrac-practice
    ;;
  bash)
    shift
    exec /bin/bash "$@"
    ;;
  *)
    exec "$@"
    ;;
esac
