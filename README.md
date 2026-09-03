# VRX Record Lab

Reproducible archaeology, baseline replication, and controller development for
the VRX 2019 station-keeping task.

The first reference target is the University of Florida score reported as
`0.11` in the official 2019 results. This repository does **not** claim a new
record until the historical protocol has been reconstructed, the reference
has been reproduced as closely as surviving artifacts allow, and a better
result has passed a clean independent rerun.

## Campaign status

- Target: VRX 2019 station keeping
- Status: protocol reconstruction; UF 0.11 reproduction dossier published
- Compute policy: OrbStack first; Vast.ai only through a bounded campaign
- Claim policy: independently reproduced task-level record unless recognized
  by the benchmark maintainers

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
That suite uses fresh containers, records raw task/debug output, extracts the
final `/vrx/task/info` score, aggregates all six worlds, and tears down each
container. Shortened runs are documented separately from complete 300-second
scored runs.

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

Run the deterministic unit tests with:

```bash
python -m pip install -e '.[test]'
python -m pytest
```

The controller design assumptions and all inferences made in the absence of
recovered VRX runtime interfaces are recorded in
[`docs/controller-design.md`](docs/controller-design.md).

The historical `0.11` value is a reference point, not an accepted directly
comparable record. The public evidence does not currently pin the complete
evaluation inputs needed for direct comparison; see
[`docs/vrx-2019-protocol.md`](docs/vrx-2019-protocol.md).

## Independent verification

Verification code lives under [`verification/`](verification/) and does not
implement or alter VRX benchmark or scorer logic. It checks:

- exact clean-clone commits and optional rerun commands;
- protected benchmark/scorer tree equality against a baseline ref;
- strict result schema, aggregate arithmetic, provenance, and artifact links;
- disjoint development, independent-verification, and evaluation seed sets;
- deterministic SHA-256 artifact manifests.

The checked-in result and artifact files are illustrative and deliberately have
`claim_status: unaccepted`. They are not a performance claim.

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
- [VRX repository](https://github.com/osrf/vrx)
- [UF 2019 station-keeping reproduction dossier](docs/uf-2019-station-keeping-reproduction.md)

## License

Project-authored code is released under the Apache License 2.0. Upstream VRX,
ROS, Gazebo, vessel models, and competition assets retain their own licenses.
