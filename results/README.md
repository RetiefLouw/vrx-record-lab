# Campaign evidence ledger

No entry in this file is a SOTA or phase-3 record claim.

| Date | Run | Score | Status | Interpretation |
|---|---|---:|---|---|
| 2026-09-03 | UF public-source MRAC practice adapter | 0.00581118860928706 | Completed | Non-comparable: Gazebo ground truth and a reconstructed stationary-goal adapter. |
| 2026-09-03 | Localized conservative PD, `stationkeeping0`, seed 10 | 0.5243254330428314 | Completed | First valid controller baseline using `robot_localization`, stock thruster topics, and the untouched scorer at VRX commit `a62df111`. |
| 2026-09-03 | Fast PD with GPS position feedback, `stationkeeping0`, seed 10 | **0.008326716568191546** | Completed; independently unverified | Public-practice task result using simulated GPS, odometry yaw/velocity, stock thrusters, and untouched scorer. It is not a phase-3 or overall SOTA claim. |
| 2026-09-03 | Pre-runtime-fix diagnostic | 10.221359813302893 | Rejected | Controller had crashed due a missing runtime dependency; retained only as debugging evidence and never treated as a baseline. |

The valid localized run used image digest
`sha256:06bca6f7c12d447b86fa263e114c8e976413a4581fc3a4b7998ed4147f3e3f39`.
Its canonical local artifact directory was `artifacts/localized-practice0-valid`;
the large bag and logs are intentionally excluded from Git until promotion.
The result checksum manifest and raw files must accompany any promoted release.

The baseline converged from approximately 8.70 m and 2.47 rad error before
scoring to about 0.019 m and negligible heading error. The official 300-second
running mean was dominated by acquisition during the opening scored interval,
which makes faster, saturation-aware acquisition the next controlled experiment.

The fast-PD run passed schema, artifact SHA-256, checksum-manifest, aggregate,
experiment-manifest, pinned-identity, and completed-trial verification. Its
local canonical result SHA-256 is
`afdfd17c16d2885b00c7d4c20a600a80044dfe331db03a6fd1e8d03ca15c4f52`.
Promotion remains blocked on a clean independent rerun and broader public-world
evaluation.
