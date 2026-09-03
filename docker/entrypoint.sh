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
  scored-trial)
    exec /usr/local/bin/vrx-run-trial
    ;;
  phase2-trial)
    exec /usr/local/bin/vrx-run-phase2-stationkeeping
    ;;
  bash)
    shift
    exec /bin/bash "$@"
    ;;
  *)
    exec "$@"
    ;;
esac
