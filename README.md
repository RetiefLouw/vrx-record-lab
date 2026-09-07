# VRX Record Lab

Reproducible archaeology, baseline replication, and controller development for
the VRX 2019 station-keeping task.

The first reference target is the University of Florida score reported as
`0.11` in the official 2019 results. This repository does **not** claim a new
record until the historical protocol has been reconstructed, the reference
has been reproduced as closely as surviving artifacts allow, and a better
result has passed a separate clean-clone or external replication.

## Campaign status

- Primary target: LoRR 2024 Test Round task-count reference (published Team Kitty Knight `1186`)
- Secondary targets: BARN 2024 public-suite navigation and VRX 2019 station keeping
- Status: archived Kitty Knight source replayed cleanly at `1199/1186`; Team RAPID Q-31 completed `1318/1186` with zero errors; Q-32–Q-34 expose the generalization/runtime-sensitivity boundary
- Compute policy: OrbStack first; Vast.ai only through a bounded campaign
- Claim policy: independently reproduced task-level record unless recognized
  by the benchmark maintainers

The `0.00832672` result is reproducible on one easy public-practice world, but
the frozen controller's complete six-world public phase-2 mean is
`8.21364634`. Neither result is directly comparable to UF's unrecovered
phase-3 evaluation, and the broad public result does not support a record
claim. A separate ground-truth UF-port
practice run scored `0.005811`, but is explicitly non-comparable because it
uses simulator state rather than the competition localization interface.
See [`results/README.md`](results/README.md) and the machine-readable
[`results/practice0-fast-pd-gps.json`](results/practice0-fast-pd-gps.json).
The campaign conclusion and verification limits are recorded in the
[`internal audit`](docs/audit-report-practice0-fast-pd-gps.md).
The benchmark pivot and claim boundary are recorded in
[`docs/CAMPAIGN.md`](docs/CAMPAIGN.md) and
[`results/benchmark-selection.json`](results/benchmark-selection.json).

The current BARN screen scored `0.46922280825431545` on 50 canonical public
worlds, with collisions localized to worlds 228, 282, and 294. Q-21's narrow
laser shield fixed two of those worlds, but Q-22–Q-25 variants failed to
generalize; Q-24 scored `0.41717035384632806` with 44/50 successes. This remains
a local public result, not an official leaderboard re-ranking. The LiCS safety
branch is closed and the campaign is auditing the official LoRR 2024 archive
as the strongest transparent replacement benchmark; BallPark is retained as a
low-cost controller sandbox only. The official LoRR archive publishes the exact
instance, task-count reference, evaluator lineage, and winner source. A local
result remains distinct from an official leaderboard result unless organizers
accept the replay and runtime identity.

## Environment bootstrap

The pinned `linux/amd64` OrbStack environment, headless station-keeping
container, deterministic local seed override, health check, and smoke test are
documented in [the environment reproduction guide](docs/environment-reproduction.md).

```bash
./scripts/bootstrap.sh
./scripts/smoke-test.sh
```

The environment records historical-source and package-availability inferences;
it is not itself a claim to have reproduced the published `0.11` score.

## Challenge explainer and sample runs

The visual [robotics challenge explainer](docs/vrx-station-keeping-challenge.html)
now explains VRX, BARN, and LoRR, the published references, the LoRR run
lifecycle, the Q-31 local beat, and the evidence boundary around Q-32–Q-34.
It is a teaching and research artifact, not an official leaderboard update.

The closest UF MRAC public-source port can also be exercised against the
public practice world in the pinned image:

```bash
docker compose --env-file config/vrx-2019.env run --rm simulator uf-mrac-practice
```

That practice adapter uses Gazebo ground truth, a stationary goal, and a
co-located thruster mapper for legacy ROS compatibility. Its result is not
comparable to the UF phase-3 result; see [`docs/uf-mrac-port.md`](docs/uf-mrac-port.md).

## Baseline harness

The dependency-light experiment/result harness is available through
`scripts/run_trial`, `scripts/run_suite`, and `scripts/verify_result`. The
canonical result format is documented in
[`docs/result-format.md`](docs/result-format.md) and defined by
[`schemas/result.schema.json`](schemas/result.schema.json). The checked-in
upstream manifest is intentionally not runnable yet: its historical simulator,
scorer, revisions, and official seeds remain unavailable, so the harness will
refuse to fabricate a score. Fixture-driven tests exercise the full execution,
statistics, checksum, and verification path.

The six public 2019 phase-2 practice worlds are runnable through the explicit
reconstructed protocol in
[`docs/phase2-practice-suite.md`](docs/phase2-practice-suite.md) and
[`config/experiments/vrx2019-station-keeping-phase2.json`](config/experiments/vrx2019-station-keeping-phase2.json).
That suite uses fresh containers, runs the frozen fast-PD GPS controller,
records raw task/debug/controller output, extracts the final `/vrx/task/info`
score, aggregates all six worlds, and tears down each container. Use
`scripts/extract_diagnostics` for offline Q-03 metrics. Shortened runs are
documented separately from complete 300-second scored runs.

Run the tests with:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Controller package

`src/vrx_controller` contains simulator-independent planar station-keeping
components. It provides angle-safe state errors, a linear model interface for
future LQR/MPC work, anti-windup PID, a wrench disturbance observer,
constrained thruster allocation, actuator saturation/rate/dead-zone handling,
and a clearly labelled closest public-source port of UF's VRX MRAC controller.
The UF port follows the external trajectory-to-body-wrench boundary and has no
ROS, Gazebo, VRX, or scorer dependency. Its source, attribution, and deliberate
deviations are documented in [`docs/uf-mrac-port.md`](docs/uf-mrac-port.md).

The ROS bridge in `ros/vrx_controller_ros` consumes the real
`robot_localization` odometry and latched geographic goal, converts WGS84 to
local ENU, and publishes the stock `std_msgs/Float32` T-layout thruster topics.
A bounded practice-world trial is available with:

```bash
scripts/run_suite config/experiments/vrx2019-station-keeping-practice0-baseline.json \
  --output-dir /absolute/path/to/trial-output
```

Its artifact contract and runtime limitations are documented in
[`docs/ros-controller.md`](docs/ros-controller.md).

Run the deterministic unit tests with:

```bash
python -m pip install -e '.[test]'
python -m pytest
```

The controller design assumptions and all inferences made in the absence of
recovered VRX runtime interfaces are recorded in
[`docs/controller-design.md`](docs/controller-design.md).

The ROS/VRX boundary, coordinate convention, stock plugin mapping, launch
graph, and trial artifact contract are recorded in
[`docs/ros-controller.md`](docs/ros-controller.md).

The historical `0.11` value is a reference point, not an accepted directly
comparable record. The public evidence does not currently pin the complete
evaluation inputs needed for direct comparison; see
[`docs/vrx-2019-protocol.md`](docs/vrx-2019-protocol.md).

For the selected BARN public-track audit, use the dependency-light scorer once
the organizer repository has been cloned:

```bash
PYTHONPATH=src .venv/bin/python scripts/aggregate_barn \
  --log /path/to/the-barn-challenge/out.txt \
  --barn-root /path/to/the-barn-challenge
```

It requires all 50 public worlds and exactly 10 trials per world, and computes
the organizer's bounded 2024 metric without ROS or Gazebo.

For a strict six-run historical arithmetic check, use
`scripts/aggregate_2019`. It requires all six runs and computes the task score
as their arithmetic mean; it will not silently average an incomplete suite.

## Verification

Verification code lives under [`verification/`](verification/) and does not
implement or alter VRX benchmark or scorer logic. It checks:

- exact clean-clone commits and optional rerun commands;
- protected benchmark/scorer tree equality against a baseline ref;
- strict result schema, aggregate arithmetic, provenance, and artifact links;
- disjoint development, verification, and evaluation seed sets;
- deterministic SHA-256 artifact manifests.

The checked-in result and artifact files are illustrative and deliberately have
`claim_status: unaccepted`. They are not a performance claim.

The successful Q-01/Q-02 runs pass the local verifier, but they were produced
on one host and checkout. They are not represented as independent third-party
replication.

Run the dependency-free checks from the repository root:

```bash
python3 -m unittest discover -s tests -v
python3 -m verification.verify seeds
python3 -m verification.verify benchmark-tree --baseline-ref origin/main
python3 -m verification.verify results \
  --input verification/examples/result.json \
  --root verification/examples/artifacts \
  --seed-config verification/seed_sets.json \
  --manifest verification/examples/artifacts/SHA256SUMS.json
```

For a promoted run, first run the candidate commit from a clean clone and
record the output, then validate the resulting manifest and result document.
The `promoted` status is rejected unless the result states direct
comparability, all protocol evidence is verified, and clean-clone, protected
tree, and manifest checks are all recorded as successful.
## Sources

- [Official VRX 2019 results](https://github.com/osrf/vrx/wiki/vrx_2019-results)
- [Official VRX log-download instructions](https://github.com/osrf/vrx/wiki/download_logs)
- [VRX repository](https://github.com/osrf/vrx)
- [UF 2019 station-keeping reproduction dossier](docs/uf-2019-station-keeping-reproduction.md)

## License

Project-authored code is released under the Apache License 2.0. Upstream VRX,
ROS, Gazebo, vessel models, and competition assets retain their own licenses.
