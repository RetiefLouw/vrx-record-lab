# Independent verification: `cca878fea8f234a1e4ee195cfd3cab0f1dab3819`

Date: 2026-09-03 (Africa/Johannesburg)

## Verdict

The checked-in public-practice claim is **not independently reproduced as an
exact result**. A clean rerun of the exact fast-PD manifest completed the full
300-second scored interval and produced `0.008305020475788282`, compared with
the claimed `0.008326716568191546`:

| value | score |
|---|---:|
| checked-in claim | 0.008326716568191546 |
| independent rerun | 0.008305020475788282 |
| rerun minus claim | -0.000021696092403264 |
| relative difference | -0.2605599965554743% |

This independently confirms the same public-practice task and performance
scale, but not the exact scalar claim or its original runtime provenance. It
must remain labelled independently unverified and must not be promoted to a
phase-3/SOTA result.

## Identity and execution

- Candidate commit: `cca878fea8f234a1e4ee195cfd3cab0f1dab3819`
- Clean-clone check: passed; GitHub source was checked out at exactly that SHA
  with a clean worktree.
- Isolated verifier branch: `codex/verify-cca878f`
- Experiment manifest SHA-256:
  `4decbfefced851f03a7f85c7ae3a6fbf77513e2e824f3d2b39df355c033a01ca`
- Pinned VRX source: `a62df11109ee95c206111c37a37c60d39bc7b705`
- Rebuilt image: `vrx-record-lab:2019-amd64`
- Rebuilt image digest: `sha256:1f30eae37b14e0d492d2473ec5e89aebdabe4ab0fa10997c81e7f119dcb6b4d8`
- Rebuilt image platform: `linux/amd64`
- Claimed image digest in the manifest/result:
  `sha256:c67d1d45abebe34ec6c5a101cb8bf16320855807c58f6d0775caabec5e26ab98`
- The claimed image digest was not present locally after the rebuild; the
  digest mismatch is therefore unresolved provenance, not a verified match.
- World: `2019_practice/stationkeeping0.world`, random seed `10`.
- World schedule observed in the image: initial `10 s`, ready `10 s`, running
  `300 s`.
- Scorer result: `/vrx/task/info`, final state `finished`, elapsed `300.0 s`,
  score `0.008305020475788282`.
- The task message reported `timed_out: true` at the natural 300-second end;
  this is how this scorer signals the configured task timeout and did not
  prevent the monitor from accepting the finished task.
- Trial wall time: `344.9227103329995 s`.
- Controller diagnostics observed by the monitor: `3100` samples.

## Artifact checksums

The rerun's canonical result and `SHA256SUMS` were validated with
`scripts/verify_result`; all schema, artifact, checksum, aggregate, manifest,
identity, and completion checks passed. The rerun output was kept outside the
repository at `/tmp/vrx-verify-cca878f.QMdtZh`.

Canonical output hashes:

- `result.json`: `fa76e23a89374e1cb17fbb0d23bf6b98dcf5ca044f22b1c1cd9e7ba2243c772c`
- `SHA256SUMS`: `1af9737d0514bfa3bf0cdae563ef3d47892f2070100b6da0baca7554c9f3f7c2`

Entries in the rerun checksum manifest:

| path | SHA-256 |
|---|---|
| `trials/trial-0001.artifacts/adapter-output.json` | `ef354b6c39cb05149be38a21f5ae799f9bef156e04d8b3ad5e3d613898a2df6c` |
| `trials/trial-0001.artifacts/monitor.log` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `trials/trial-0001.artifacts/rosbag.log` | `75144523821d0d6aece928de082d589ef566fa4635cdf7942503d42f5bd0cf05` |
| `trials/trial-0001.artifacts/simulator.log` | `e04a9d6287fe4ef116471aa8e36b2587ffbbcacfc3ba76baec171305a4070d29` |
| `trials/trial-0001.artifacts/task-info.jsonl` | `f0d106b91906d9a8c721fb20cac8eafddfb4a163ebef2abf224d5bdca7157825` |
| `trials/trial-0001.artifacts/task-summary.json` | `8baad4c41fd1c5e57817cb36f4633b3bfcca8188011ccd6e71399d76b7f26864` |
| `trials/trial-0001.artifacts/topics.bag` | `c6ea1fcfc59fdebbe93959b838cbb9351b8bb55df4456a60fea87c8de2fc7da0` |
| `trials/trial-0001.artifacts/trial-protocol.txt` | `67102927c9b2a296f8357aceaac360205ffd5fdd909dcdf8c2d7d812d67172fc` |
| `trials/trial-0001.json` | `d80ad2b4ca8c56a8206f4a8029059658cf47a86f034d06e3f24dd8605e67481c` |
| `trials/trial-0001.stderr.log` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `trials/trial-0001.stdout.log` | `41c6bef65a7ade9a94c2a577d18afb7c443d5b7c45738fddeae5ecfc2d986480` |

## Immutability and scorer audit

- The candidate commit changes no paths under the repository's configured
  `benchmark`, `benchmarks`, `scorer`, or `scoring` prefixes.
- The repository integrity command passed with `present_specs: 0` and
  `vacuous: true`. Because `verification/benchmark_paths.json` permits missing
  protected roots, this is only a warning and is not proof that a benchmark or
  scorer tree was protected.
- Inside the rebuilt image, the upstream VRX checkout was at the pinned SHA.
  The tracked station-keeping scorer and `stationkeeping0.world` matched their
  Git object hashes exactly. The checkout had two untracked generated model
  files after the build/run, but neither was a scorer or world file:
  `vrx_gazebo/models/dock_2018_dynamic/model.sdf` and
  `vrx_gazebo/models/robotx_2018_qualifying_avoid_obstacles_buoys/model.sdf`.
- The scorer source hash in the image was
  `e7142d0064e9f390e39ed60766f823a568863e4fb5e7477f9f5291bfd52b4e9b`.
  The practice world hash was
  `495377886a0cc0a17361b6a551e6b7a7d0d7adc2b36e9b12c1be9287886b4728`.
- The scorer computes the score from the vehicle model pose in the unchanged
  upstream plugin and publishes the task result; the controller does not read
  `/vrx/task/info` or a scorer pose-error topic.

## GPS feedback legitimacy

The fast-PD node subscribes to `/wamv/sensors/gps/gps/fix` and uses its ENU
position for x/y control. It uses localization odometry only for yaw and
velocity, and receives the geographic goal from
`/vrx/station_keeping/goal`. The unchanged launch enables the VRX sensor suite;
the upstream WAM-V xacro supplies that GPS topic via
`libhector_gazebo_ros_gps`, with zero configured Gaussian noise, drift, and
offset. This is a simulator sensor topic, not the scorer's ground-truth pose
topic, and the node contains no scorer feedback subscription.

The bag does not include the GPS topic, so raw GPS samples cannot be audited
from the saved recording. The node emitted `3103` diagnostics, and its code
emits diagnostics only after a GPS fix has populated `gps_xy`; the bag also
contains finite, nonzero thruster commands. That supports actual GPS-path use
but is weaker than recording the GPS topic directly. The node accepts any
finite latitude/longitude without checking `NavSatFix.status`, covariance, or
sample freshness, and reuses the last fix indefinitely; these are legitimacy
and robustness gaps for a future promoted run.

## Controller-output acceptance guard

The monitor's acceptance condition is `state == "finished"` plus at least one
`/vrx_controller/diagnostics` message. It does not subscribe to or validate
the thruster command/angle topics. In this rerun, the bag independently showed
finite command streams with these counts and nonzero scalar values:

| topic | messages | nonzero values |
|---|---:|---:|
| `/wamv/thrusters/left_thrust_cmd` | 3190 | 1222 |
| `/wamv/thrusters/right_thrust_cmd` | 3180 | 1211 |
| `/wamv/thrusters/lateral_thrust_cmd` | 3190 | 2766 |
| each thrust-angle topic | 3190 | 0 (fixed zero angle) |

Thus this run did produce accepted controller outputs, but the monitor guard
would not detect a controller that published diagnostics while failing to
publish valid actuator commands. The rosbag itself was valid, although
`rosbag.log` retained a Python-2 signal-handler traceback during shutdown.

## Checked-in claim evidence audit

`results/practice0-fast-pd-gps.json` is a hand-authored
`campaign-evidence-1.0` document. It fails the repository's independent
verifier schema (`verification/result.schema.json`, missing required
`campaign_id`) and fails the canonical result validator because its
`schema_version` is not `1.0.0`. The referenced canonical result and checksum
hashes are not present in the commit, nor are the raw artifacts. Therefore its
claims that schema, artifact SHA-256, checksum-manifest, and canonical result
verification passed cannot be independently checked from this repository.

## Tests

- `python3 -m verification.verify seeds`: passed.
- `python3 -m verification.verify benchmark-tree --baseline-ref origin/main`:
  passed, but vacuous as noted above.
- Clean-clone exact-SHA check: passed.
- Dependency-complete project test suite: `47 passed, 2 subtests passed`.
- Rebuilt-image runtime checks for ROS Melodic, Gazebo 9.19.0, pinned VRX
  commit, and Python compilation: passed.
