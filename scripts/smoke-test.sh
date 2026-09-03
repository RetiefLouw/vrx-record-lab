#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT_DIR}/config/vrx-2019.env"
ARTIFACT_DIR="${ROOT_DIR}/artifacts/smoke-test"
mkdir -p "${ARTIFACT_DIR}"

set -a
source "${ENV_FILE}"
set +a

compose=(docker compose --env-file "${ENV_FILE}" -f "${ROOT_DIR}/compose.yaml")
"${compose[@]}" config > "${ARTIFACT_DIR}/compose.config.yaml"
"${compose[@]}" build --pull simulator

"${compose[@]}" run --rm --no-deps --entrypoint /bin/bash simulator -lc '
  set -euo pipefail
  source /opt/ros/melodic/setup.bash
  source /opt/vrx_ws/devel/setup.bash
  test "$(rosversion -d)" = melodic
  test "$(gazebo --version | awk "NR==1 {print \$NF}")" = 9.19.0
  test "$(git -C /opt/vrx_ws/src/vrx rev-parse HEAD)" = "'"${VRX_COMMIT}"'"
  test -f /opt/vrx_ws/src/vrx/vrx_gazebo/launch/station_keeping.launch
  test -f /opt/vrx_ws/src/vrx/vrx_gazebo/worlds/stationkeeping_task.world.xacro
  echo "Pinned image checks passed."
' | tee "${ARTIFACT_DIR}/image-check.txt"

cleanup() {
  "${compose[@]}" down > "${ARTIFACT_DIR}/compose-down.txt" 2>&1 || true
}
trap cleanup EXIT

"${compose[@]}" up --detach --wait simulator
container_id="$("${compose[@]}" ps -q simulator)"
docker inspect "${container_id}" > "${ARTIFACT_DIR}/container.inspect.json"

if [[ -n "${VRX_WIND_SEED}" && "${VRX_WIND_SEED}" != "0" ]]; then
  "${compose[@]}" exec -T -e "VRX_EXPECTED_SEED=${VRX_WIND_SEED}" simulator bash -lc '
    set -euo pipefail
    world_file="$(find /tmp/vrx-seeded-world.* -type f -name stationkeeping_task.world -print -quit)"
    test -n "${world_file}"
    grep -Fq "<random_seed>${VRX_EXPECTED_SEED}</random_seed>" "${world_file}"
    echo "Running world contains random_seed=${VRX_EXPECTED_SEED}."
  ' | tee "${ARTIFACT_DIR}/seed-check.txt"
fi

"${compose[@]}" exec --index 1 -T simulator bash -lc \
  'source /opt/ros/melodic/setup.bash && source /opt/vrx_ws/devel/setup.bash && timeout 30 rostopic echo -n1 /vrx/task/info' \
  | tee "${ARTIFACT_DIR}/task-info.txt"
"${compose[@]}" logs --no-color simulator | tee "${ARTIFACT_DIR}/simulator.log"

echo "VRX 2019 image and headless station-keeping smoke test passed."
