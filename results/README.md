# Campaign evidence ledger

No entry in this file is a SOTA or phase-3 record claim.
The retained local verifier summary is
[`local-verification-summary.json`](local-verification-summary.json); its scope
is explicitly narrower than clean-clone or third-party replication.

| Date | Run | Score | Status | Interpretation |
|---|---|---:|---|---|
| 2026-09-03 | UF public-source MRAC practice adapter | 0.00581118860928706 | Completed | Non-comparable: Gazebo ground truth and a reconstructed stationary-goal adapter. |
| 2026-09-03 | Localized conservative PD, `stationkeeping0`, seed 10 | 0.5243254330428314 | Completed | First valid controller baseline using `robot_localization`, stock thruster topics, and the untouched scorer at VRX commit `a62df111`. |
| 2026-09-03 | Fast PD with GPS position feedback, `stationkeeping0`, seed 10 | **0.008326716568191546** | Completed; reproduced locally | Public-practice task result using simulated GPS, odometry yaw/velocity, stock thrusters, and untouched scorer. It is not a phase-3 or overall SOTA claim. |
| 2026-09-04 | Q-01 fresh local rerun 1, same frozen `stationkeeping0` setup | **0.008340650238951723** | Completed; verified | Fresh container and output directory on the same host/checkout; all seven local verifier gates pass. |
| 2026-09-04 | Q-01 fresh local rerun 2, same frozen `stationkeeping0` setup | **0.008183191252996592** | Completed; verified | Confirms the narrow one-world result locally; failed host-stall attempts were retained and excluded. |
| 2026-09-04 | Q-02 six-world public phase-2 suite | **8.213646343578185** | Six/six completed; verified | Scores: `0.008393`, `0.122282`, `1.104897`, `37.956130`, `4.800464`, `5.289713`. Public-practice only; does not support a record claim. |
| 2026-09-04 | Q-13 BARN DWA ten-world screen | **0.23287870433096822** | Ten/ten completed; verified | Public screen on worlds `0,6,12,18,24,30,36,42,48,54`; 100% success, no collisions/timeouts. See [`barn-q13-baseline/aggregation.json`](barn-q13-baseline/aggregation.json). |
| 2026-09-04 | Q-14 published LiCS-KI world-0 smoke | **0.0** | Completed with collision; rejected | Released model loaded in a pinned CPU-PyTorch image but collided after `3.805 s`; not a suite score. See [`barn-q14-lics.json`](barn-q14-lics.json). |
| 2026-09-04 | Q-15 LiCS planner-readiness guard, world 0 | **0.5** | Completed; causal screen passed | Same model/image plus a zero-command guard until the local planner publishes a goal; completed in `6.739 s` and reached the metric cap. See [`barn-q15-lics-readiness.json`](barn-q15-lics-readiness.json). |
| 2026-09-04 | Q-16 LiCS readiness ten-world screen | **0.45** | Completed; below published leader | Nine capped successes and one world-0 collision; 90% success. See [`barn-q16-lics.json`](barn-q16-lics.json). |
| 2026-09-04 | Q-17 LiCS stable-readiness world-0 repeats | **0.5** | Three/three succeeded; causal screen passed | One-second stable global-path guard; all repeats reached the metric cap. See [`barn-q17-lics-stable-readiness.json`](barn-q17-lics-stable-readiness.json). |
| 2026-09-04 | Q-18 LiCS stable-readiness ten-world screen | **0.5** | Ten/ten succeeded; public-screen gate passed | All declared worlds reached the metric cap; this beats `0.4762` only as a local public screen, not an official re-ranking. See [`barn-q18-lics.json`](barn-q18-lics.json). |
| 2026-09-04 | Q-19 independent LiCS stable-readiness ten-world screen | **0.5** | Ten/ten succeeded again | Independent rerun confirms the Q-18 public-screen result; all-world breadth remains pending. See [`barn-q19-lics.json`](barn-q19-lics.json). |
| 2026-09-04 | Q-20 LiCS all-world public breadth screen | **0.46922280825431545** | 47/50 succeeded; breadth gate failed | Canonical worlds `0,6,12,…,294`, one trial/world. Collisions localized to 228, 282, and 294; no timeouts. One sixth-column log metric differs from evaluator recomputation because upstream `run.py` and `report_test.py` use different start poses; the strict aggregate uses evaluator OT. See [`barn-q20-lics.json`](barn-q20-lics.json) and [`barn-q20-lics/aggregation.json`](barn-q20-lics/aggregation.json). |
| 2026-09-04 | Q-21 LiCS laser collision-shield target screen | **partial** | Two collision worlds fixed; one remains | Worlds 228 and 282 succeeded, 294 collided, and world 66 improved. See [`barn-q21-lics-safe.json`](barn-q21-lics-safe.json). |
| 2026-09-04 | Q-21b wider LiCS shield target screen | **rejected** | Too conservative; timeout behavior | A 1.5 m threshold caused world 228 to time out and the remaining runs were stopped. See [`barn-q21b-lics-safe.json`](barn-q21b-lics-safe.json). |
| 2026-09-04 | Q-22 directional LiCS shield target screen | **rejected** | Three collisions | Worlds 294, 228, and 282 collided; only 66 succeeded (`0.4445`). Raw outputs are in [`barn-q22-lics-directional/`](barn-q22-lics-directional/). |
| 2026-09-04 | Q-23 LiCS + fresh EBand fallback target screen | **rejected** | One collision fixed, two reintroduced | World 294 succeeded (`0.3677`), but 228 and 282 collided and 66 regressed (`0.1858`). Raw outputs are in [`barn-q23-lics-hybrid/`](barn-q23-lics-hybrid/). |
| 2026-09-04 | Q-24 LiCS hybrid-safe 50-world breadth | **0.41717035384632806** | 44/50 succeeded; breadth gate failed | One trial on each canonical public world; six collisions, no timeouts. See [`barn-q24-lics-hybrid-safe-50.json`](barn-q24-lics-hybrid-safe-50.json) and [`barn-q24-lics-hybrid-safe-50/aggregation.json`](barn-q24-lics-hybrid-safe-50/aggregation.json). |
| 2026-09-04 | Q-25 smart hybrid target screen | **rejected** | Timeout/collision | World 294 timed out (`100.008 s`), 282 collided, 228 succeeded (`0.5`), and 66 scored `0.4404`. Raw outputs are in [`barn-q25-lics-smart-hybrid/`](barn-q25-lics-smart-hybrid/). |
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
The narrow score is reproduced in two fresh local runs, and the broader public-world
evaluation is complete. Promotion is rejected because the six-world mean is
`8.213646343578185` and the private phase-3 protocol is only partially
recovered.

The official phase-3 log bucket exposes UF's exact six scores and server-side
logs. Their exact mean is `0.110429677731685`; see
[`vrx2019-uf-phase3-log-evidence.json`](vrx2019-uf-phase3-log-evidence.json).
This improves the historical audit but does not restore the generated world
files or exact evaluator/competitor image identities required for replay.
The official 2019 phase-2 table reports UF's corresponding six-world score as
`18.76`; the local Q-02 mean of `8.213646343578185` is lower, but remains a
self-hosted reconstruction rather than a recognized historical submission.

The campaign's next primary track is recorded in
[`benchmark-selection.json`](benchmark-selection.json). It now selects the
LoRR 2024 Test Round because the archive exposes the exact input, evaluator
lineage, score fields, and archived winner source. BARN remains a reproducible
near-leader fallback; Q-12 through Q-25 establish its public-screen limits.

The first all-world breadth screen is now complete: stable-readiness LiCS
scored `0.46922280825431545` with 47/50 successes. This is below the published
`0.4762` reference and fails the declared 98% success gate. Q-21 partially
fixed the localized collisions, but Q-22, Q-23, Q-24, and Q-25 all failed to
generalize; Q-24 fell to `0.41717035384632806` with 44/50 successes. The LiCS
safety branch is closed pending a new benchmark or a materially different
planner hypothesis.

Q-26 now audits the official League of Robot Runners (LoRR) 2024 archive with
the tagged `v2.0.0` Start-Kit. Its RANDOM-01 reference is 696 completed tasks
for 100 agents in 600 ticks. A run using the current 3.x runtime or invented
delay settings is only a compatibility smoke and is not comparable. BallPark's
deterministic Python simulator remains available for cheap controller
prototyping, but it has no independent leaderboard and is not an external
record.

The audit ledger is [`lorr-q26-random01-replay.json`](lorr-q26-random01-replay.json).
It records the archive/input hashes, tagged evaluator commit, container
digests, and the archived Team RAPID source identity. The untouched v2.0.0
default planner completed validly at 492 tasks; the archived Team RAPID replay
completed the exact protocol at 690 tasks with zero errors. This is close to,
but does not exactly reproduce, the archived 696-task reference; Main Round
RANDOM-01 remains the held-out generalization check rather than an overfitting
target.
The protocol and command details are documented in
[`docs/lorr-2024-replay.md`](../docs/lorr-2024-replay.md).

Q-28's planning-window-4 diagnostic reached 693 tasks but incurred two entry
timeouts, so it is rejected and will not advance to held-out evaluation. See
[`lorr-q28-random01-planning-window4.json`](lorr-q28-random01-planning-window4.json).

The cheaper LoRR Test Round target is now the primary local iteration loop.
The exact 100-agent, 500-tick input has the archived Team Kitty Knight
reference of 1186 tasks. The archived Kitty source replayed cleanly at 1199
tasks with no timeout/error markers; this validates the source and score fields
but also shows that the competition count is not bit-for-bit deterministic
across runtimes. Team RAPID first reached 1320 tasks (+134) with zero
planner/schedule errors, but one entry timeout made Q-30 diagnostic only.
Q-31 repeated the same image, input, and storage protocol and completed at 1318
tasks (+132) with zero planner, schedule, or entry-timeout errors. Under the
declared `OMP_NUM_THREADS=1` and Docker CPU-pinned runtime, Q-35 and its fresh
Q-36 repeat each completed 1325 tasks (+139) with zero planner, schedule, or
entry-timeout errors and byte-identical compact outputs. See
[`lorr-q30-test-round-random100-kitty.json`](lorr-q30-test-round-random100-kitty.json)
[`lorr-q30-test-round-random100-team-rapid.json`](lorr-q30-test-round-random100-team-rapid.json)
[`lorr-q31-test-round-random100-team-rapid.json`](lorr-q31-test-round-random100-team-rapid.json),
[`lorr-q35-test-round-random100-team-rapid-cpuset1.json`](lorr-q35-test-round-random100-team-rapid-cpuset1.json),
and [`lorr-q36-test-round-random100-team-rapid-cpuset1-repeat.json`](lorr-q36-test-round-random100-team-rapid-cpuset1-repeat.json).
The first detached Q-31 launch hit a local Docker host stall before producing
an output file; it is retained as an infrastructure diagnostic, not a failed
score. Q-32 failed the held-out generalization gate, and Q-34 failed to
stabilize the timeout behavior. The clean pinned Q-37 held-out replay reached
1181 tasks versus the 1260-task RANDOM-02 archive reference, so the Q-35/Q-36
margin remains an instance-scoped local replay result pending a planner change
and broader validation. The dedicated [LoRR explainer](../docs/lorr-challenge-explainer.html)
and [campaign plan](../docs/lorr-improvement-plan.md) collect the visual and
methodological evidence.

The upstream LiCS-KI artifact audit is retained in
[`barn-lics-upstream-public-check.json`](barn-lics-upstream-public-check.json).
Its 500 checked-in trial lines recompute to `0.4889133891483272` with the
strict local scorer. This is evidence about the published artifact and metric,
not an independent LiCS controller rerun.
