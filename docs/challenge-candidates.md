# Runnable and reproducible challenge candidates

This table records the campaign shortlist. “Self-hosted” means the historical
software/protocol remains reproducible but the original competition server is
closed; such results require precise claim language.

| Challenge | Domain | Current execution status | Reference date | Record opportunity |
|---|---|---|---|---|
| VRX 2019 | Maritime autonomy | Self-hosted public simulator and results | 2019 | Neglected individual tasks; current campaign target |
| BARN Challenge | LiDAR navigation | Public 300-world Gazebo dataset, organizer evaluator, baseline and LiCS-KI code available | 2024 | Reproducible near-leader fallback; published LiCS-KI reference `0.4762`; organizer-run submission required for an official win |
| **League of Robot Runners (LoRR) 2024** | Lifelong multi-agent path finding | Official Benchmark Archive publishes 2024 instances, best-known task counts, team/source links, and an open Start-Kit; matching `v2.0.0` evaluator is available locally | 2024 | **Primary target:** Test Round reference 1186 tasks; first prove zero-error replay, then optimize with Main Round held out |
| LoRR 2024 Test Round RANDOM-100 | Lifelong multi-agent path finding | Same official archive/evaluator, 100 agents and 500 ticks; archived best-known output is 1186 tasks | 2024 | Cheapest serious target to screen before the larger Main Round worlds; local improvement still requires exact protocol and clean rerun |
| BallPark | 2-D LiDAR navigation | Newly published deterministic Python simulator with fixed-seed 20-episode benchmarks and controller code | 2026 | Fast sandbox for LLM iteration; no independent leaderboard, so not an external record claim |
| 3we Benchmark | ROS 2 mobile navigation | Public `office_v2` scenes, fixed-seed episodes, runner/SDK, and leaderboard documentation; Gazebo path requires ROS 2 Jazzy, while a mock backend is also shipped | 2026 | Promising low-cost candidate if the real Gazebo evaluator is identity-stable; mock-backend scores are excluded |
| Astral closed-loop drone benchmark | Drone control | Public methodology, dataset, scoring, and modular baseline; Isaac Sim 4.x with about 16 GB VRAM required | 2025 | Technically transparent but not a low-cost local iteration target |
| ROS 2 Online Robot Racing | Mobile-robot racing | Historical browser project; official event closed | 2025 | Organizer-approved rerun or reproduced lap record |
| Real Robot Challenge | Manipulation | Public simulator and protocol | 2020 | Independently reproduced simulation result |
| REAL 2020 | Autonomous learning | Public starter kit/evaluator | 2020 | Old closed challenge with reproducible evaluator |
| RoboTHOR Challenge | Embodied navigation | Public simulator/data; historical EvalAI event | 2020 | Self-hosted task or split record |
| ROBEL | Robot learning/control | Public benchmark and hardware designs | 2020 | New reproducible score against old baselines |
| CSIRO manipulation benchmark | Sim-to-real manipulation fidelity | Public benchmark materials | 2019 | Simulator/configuration-specific result |
| BOP 2019 protocol | 6D object pose | Submission form and shared leaderboard remain available | 2019; later submissions | Narrow dataset/object track |
| OpenDriveLab Challenge 2024 | Autonomous driving | Test servers reported active | 2024 | Niche track rather than crowded main track |
| Open Navigation Robotics Workload | ROS 2 warehouse workload | Public Dockerized workload; early community results | 2026 | First strong public systems benchmark |
| DARPA SubT Virtual Testbed | Multi-robot exploration | Open virtual testbed; competition closed | 2021 | Individual circuit/task reproduction |

## Verified selection record

### Decision matrix

| Candidate | Published reference | Exact local evaluator | Cheap CPU iteration | Current decision |
|---|---:|---:|---:|---|
| LoRR 2024 | Yes (`1186` Test Round tasks; `696` RANDOM-01 tasks) | Yes for tagged v2.0.0; winner source replayed | Medium (minutes per 500–600-tick run) | Primary audit target |
| BARN 2024 | Yes (`0.4762` LiCS-KI) | Yes on public worlds | Low-to-medium, but LiCS safety variants failed breadth | Reproducible near-leader fallback |
| BallPark | No independent organizer result | Yes, deterministic Python | Very high (20 seeds in seconds) | Sandbox only |
| 3we | Public leaderboard exists | Real Gazebo path not yet verified here | Unknown; ROS 2 Jazzy required | Do not promote yet |

BARN remains a reproducible fallback because its organizer page exposes all of
the information needed for a cheap, auditable local loop:

- 2024 simulation leader: **LiCS-KI, `0.4762`**; open LfLH baseline: `0.4354`.
- Per-world score: `success × OT / clip(AT, 2×OT, 8×OT)`; overall score is the
  arithmetic mean over 50 worlds and 10 trials per world.
- Public assets: 300 pre-generated worlds, path/OT data, environment generator,
  baseline stacks, and `report_test.py`-style evaluation instructions.
- Local claim boundary: the competition's 50 newly generated test worlds were
  private. A local score is a public-suite reproduction, not an official
  re-ranking, unless the organizers execute the submitted container.

As a feasibility check, the checked-in LiCS-KI `out.txt` artifact (500 trial
lines) was recomputed locally as `0.4889133891483272` with 98% success. This is
above the published `0.4762` but is explicitly attributed to the upstream
artifact; it is not evidence that this repository has independently beaten the
winner. The artifact also exposes a small reproducibility hazard: its logged
sixth-column metrics use a `[-2.25, 3]` start while the published report script
uses `[-2, 3]`. Our scorer follows the report script and records the 12 resulting
mismatches rather than silently accepting them.

The winner's metric formula is verified at the protocol level: the public
`run.py` and `report_test.py` implement
`success * OT / clip(AT, 2×OT, 8×OT)`, matching the organizer's 2024 rules.
The hidden `0.4762` final score is not independently reproducible because the
50 evaluation worlds and organizer-side execution trace were private.

## Reassessment after the LiCS breadth screen

The BARN track remains a valid, transparent benchmark, but it no longer meets
the campaign's strongest low-cost iteration criterion for the current LiCS
branch. Stable-readiness LiCS reached `0.46922280825431545` on 50 public worlds
(47/50), while the Q-24 hybrid-safe variant fell to `0.41717035384632806`
(44/50). Four targeted safety variants therefore failed to generalize, so the
campaign will not spend a 50×10 confirmation batch on them.

LoRR is now the primary candidate because its official archive exposes
both the evaluation instances and the best-known solution provenance. The
2024 archive reports 696 tasks on RANDOM-01 (100 agents, 600 ticks), but the
current Start-Kit is 3.x and changed execution semantics. The matching v2.0.0
release must be used; a current-runtime run with added delay settings is only a
compatibility smoke and must not be compared with the archived count.

BallPark is a useful fallback for low-cost controller prototyping. Its stock
MPPI reproduced 0.95 success and 0.934 SPL on 20 dynamic seeds in two runs;
the guarded-MPPI experiment dropped to 0.85 and was rejected. These are local
engineering results from a new repository, not a verified external record.

The 3we benchmark remains a secondary candidate because its documentation
describes deterministic simulation, fixed seeds, 100-episode PointNav runs,
and public trajectory/evaluator tooling. The public repository was inspected
at commit `6073a1bd0a30b6ca1348027ac35b05832b97bfe9`; its checked-in leaderboard
also contains mock-backend entries, so those values are not acceptable robotics
evidence. A real Gazebo `office_v2` smoke, scorer recomputation, and runtime
identity capture are required before selecting 3we. If that gate fails, retain
BARN Q-20 as a reproducible near-leader case rather than claiming a new record.

Astral is not selected despite its open methodology because its Isaac Sim and
GPU requirements conflict with the campaign's low-cost iteration constraint.

Primary sources: [LoRR 2024 Benchmark Archive](https://github.com/MAPF-Competition/Benchmark-Archive),
[LoRR v2.0.0 Start-Kit](https://github.com/MAPF-Competition/Start-Kit/releases/tag/v2.0.0),
[BARN 2024 rules and leaderboard](https://people.cs.gmu.edu/~xiao/Research/BARN_Challenge/BARN_Challenge24.html),
[BARN dataset](https://www.cs.utexas.edu/~xiao/BARN/BARN.html), and the
[LiCS-KI submission](https://github.com/damanikjosh/the-barn-challenge),
[3we benchmark documentation](https://docs.3we.org/leaderboard/),
[3we repository](https://github.com/3we-org/3we), and
[Astral benchmark](https://astral.us/benchmark).
