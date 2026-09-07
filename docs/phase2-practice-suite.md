# Public VRX 2019 phase-2 practice suite

This repository reconstructs the six public 2019 phase-2 station-keeping
practice worlds as a runnable protocol. It is a practice suite, not the
private phase-3 evaluation and not a record claim.

## Complete scored protocol

`config/experiments/vrx2019-station-keeping-phase2.json` is the source of
truth. Trial indices `0` through `5` select, in order,
`stationkeeping0.world` through `stationkeeping5.world` from the unchanged
upstream VRX commit recorded in the manifest. The manifest records each
world's upstream path, source commit, source digest, goal, wave settings, and
wind seed.

Each trial starts a fresh `linux/amd64` container and uses the public world
as-is. Its task lifecycle is 10 seconds Initial, 10 seconds Ready, and 300
seconds of scored Running time. The adapter allows 840 seconds of wall time
for emulation and startup. A finished task message is required; a missing
message or wall timeout produces an incomplete trial and no fabricated score.

The Q-02 controller is pinned in the same manifest: the saturation-aware fast
PD controller uses GPS position feedback, odometry yaw/velocity, and the stock
T-thruster mapping. The phase-2 adapter launches
`vrx_controller_ros/scored_station_keeping.launch` for every world and passes
the controller parameters and permitted sensor topics from the manifest. The
world files and upstream scorer remain unchanged. The completed campaign pins
the image as
`sha256:9330ee0dc73ed349c30ee111f738cf1fb6af266d96efbe7e9980d40014ee33e0`.

The scorer value is extracted from the final `/vrx/task/info` message's
`score` field. The collector also retains the task messages and the public
station-keeping debug topics `/vrx/station_keeping/pose_error` and
`/vrx/station_keeping/rms_error`. For every trial, the artifact directory
contains the selected world copy, run metadata, runtime metadata, collector
output, task-info JSONL, controller-diagnostics JSONL, Gazebo output, Docker
output, and teardown output. The offline
[`scripts/extract_diagnostics`](../scripts/extract_diagnostics) command derives
Q-03 acquisition, error, and actuator-saturation metrics from those JSONL
streams without reading or recomputing the scorer. The existing
`scripts/run_suite` runner adds normalized trial JSON, SHA-256 entries, and
the aggregate result; `scripts/verify_result` checks those artifacts and the
manifest digest.

Build the pinned image, then run all six complete trials from the repository
root:

```sh
scripts/bootstrap.sh --build-only
scripts/run_suite config/experiments/vrx2019-station-keeping-phase2.json \
  --output-dir results/runs/vrx2019-phase2-public
scripts/verify_result results/runs/vrx2019-phase2-public/result.json \
  --manifest config/experiments/vrx2019-station-keeping-phase2.json \
  --write --output results/runs/vrx2019-phase2-public/verification.json
```

Q-02 completed all six worlds with scores `0.008393`, `0.122282`, `1.104897`,
`37.956130`, `4.800464`, and `5.289713`, for a strict arithmetic mean of
`8.213646343578185`. All seven local verifier gates pass. This remains a
public phase-2 practice result, not a phase-3 result or record claim.

## Smoke and shortened trials

`scripts/smoke-test.sh` checks image startup, the pinned upstream commit, the
task topic, and the configured seed. It does not score a trial.

The phase-2 container runner also supports explicit duration overrides for a
real shortened simulator trial. For example, this runs only 1 s Initial, 1 s
Ready, and 5 s Running in `stationkeeping0`; the generated world is copied to
the artifacts and the run is labelled `shortened_smoke`:

```sh
mkdir -p artifacts/phase2-shortened
VRX_ARTIFACT_DIR="$PWD/artifacts/phase2-shortened" \
docker compose --env-file config/vrx-2019.env -f compose.yaml run --rm --no-deps \
  --entrypoint /usr/local/bin/vrx-run-phase2-stationkeeping \
  -e VRX_WORLD_PATH=/opt/vrx_ws/src/vrx/vrx_gazebo/worlds/2019_phase2/stationkeeping0.world \
  -e VRX_WORLD_ID=stationkeeping0 \
  -e VRX_WIND_SEED= \
  -e VRX_INITIAL_STATE_DURATION_OVERRIDE=1 \
  -e VRX_READY_STATE_DURATION_OVERRIDE=1 \
  -e VRX_RUNNING_STATE_DURATION_OVERRIDE=5 \
  -e VRX_PHASE2_WALL_TIMEOUT_S=60 simulator
```

A shortened trial is useful for plumbing and teardown validation only. It is
not a 300-second scored run and must not be placed in the complete protocol's
result directory or used for a benchmark claim.
