#!/usr/bin/env bash
set -euo pipefail

source /opt/ros/melodic/setup.bash
source /opt/barn_ws/devel/setup.bash
cd /opt/barn_ws/src/the-barn-challenge

exec python2 run.py "$@"
