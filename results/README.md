# Campaign evidence ledger

No entry in this file is a SOTA or phase-3 record claim.

| Date | Run | Score | Status | Interpretation |
|---|---|---:|---|---|
| 2026-09-03 | UF public-source MRAC practice adapter | 0.00581118860928706 | Completed | Non-comparable: Gazebo ground truth and a reconstructed stationary-goal adapter. |
| 2026-09-03 | Localized conservative PD, `stationkeeping0`, seed 10 | 0.5243254330428314 | Completed | First valid controller baseline using `robot_localization`, stock thruster topics, and the untouched scorer at VRX commit `a62df111`. |
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
