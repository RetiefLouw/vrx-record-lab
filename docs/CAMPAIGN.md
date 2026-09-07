# Robotics benchmark campaign tracker

Status: active public-practice performance campaign  
Last updated: 2026-09-07
Canonical tracker: this file is the single plan, progress log, experiment queue, and decision register for the VRX, BARN, and LoRR evidence campaign.

This tracker covers controller performance, evaluator integrity, and evidence
quality. It deliberately excludes presentation/media work.

## 0. Campaign pivot: a locally tractable public record

The historical VRX phase-3 record remains useful research, but it is a poor
primary target for an LLM iteration demonstration: the generated worlds and
exact scorer binary are unavailable, and the published `0.11` cannot be
replayed from the surviving public inputs. The primary demonstration track is
therefore the **LoRR 2024 Test Round**, while BARN remains the embodied-
navigation fallback and VRX remains the secondary maritime-control track.

### Why BARN was selected, and why it is now being reassessed

The BARN organizers publish the task, public dataset, baseline stacks, scoring
formula, and standardized evaluation pipeline. The 2024 simulation leaderboard
reports LiCS-KI at `0.4762`, AIMS at `0.4723`, and the open LfLH baseline at
`0.4354`. The metric is explicit and bounded:

```text
s_i = success_i * OT_i / clip(AT_i, 2*OT_i, 8*OT_i)
overall = mean(s_i over 50 evaluation worlds and 10 trials/world)
```

The BARN dataset supplies 300 public Gazebo worlds, path lengths, and the
environment generator. The public LiCS-KI submission is available as a
starting point, and the organizers document a single-world command plus a
50-world/10-trial report. This makes short screening runs practical and lets
an LLM change one navigation mechanism at a time (recovery state machine,
clearance/speed policy, local-planner parameters) with an executable score
feedback loop.

The exact 2024 competition score still used 50 newly generated private worlds,
so a local result is **not** an official re-ranking unless the organizers run
the submitted stack. Our defensible local claim will instead be:

> independently reproducible BARN public-suite score, computed by the
> organizer's evaluator, compared with the published baselines and the
> published LiCS-KI reference.

This is a materially stronger and cheaper claim than the current VRX phase-3
track because the evaluator and public inputs are inspectable. It also leaves
an unambiguous final step: submit the frozen container to BARN for organizer
evaluation if a public-suite score exceeds `0.4762`.

The external LiCS-KI winner is verified to use the same *formula protocol*:
its public `run.py` and `report_test.py` implement
`success * OT / clip(AT, 2*OT, 8*OT)`, matching the organizer specification.
That does not verify the hidden `0.4762` arithmetic end-to-end: the 50 private
worlds and organizer-side run trace are unavailable. Our audit therefore marks
formula equivalence as verified, but final-score reproduction as unverified.

Primary sources: [BARN 2024 rules and leaderboard](https://people.cs.gmu.edu/~xiao/Research/BARN_Challenge/BARN_Challenge24.html),
[BARN dataset](https://www.cs.utexas.edu/~xiao/BARN/BARN.html), and the
[LiCS-KI submission](https://github.com/damanikjosh/the-barn-challenge).

### Reassessment: LoRR is the strongest next audit; BallPark is a cheap sandbox

The League of Robot Runners (LoRR) is now the strongest candidate for a
definitive, externally reported target. Its official Benchmark Archive
publishes evaluation instances, best-known solutions, team names, and source
commit links. For example, the 2024 Main Round RANDOM-01 reference is 696
completed tasks for 100 agents in 600 ticks. The official Start-Kit is open
source and includes a local evaluator, so a controller can be iterated without
paying for a hosted service.

The compatibility risk is material: the archive is from the 2024 protocol,
whereas the current Start-Kit is version 3.x and adds delayed execution and a
different executor pipeline. A current-runtime run with an invented delay
configuration is therefore only a smoke test, not a 2024 score. Q-26 must use
the tagged `v2.0.0` Start-Kit (the release that documents the 2024 format), the
unmodified archived RANDOM-01 JSON, and the archived best-solution container
or source commit before any score comparison is accepted.

BallPark is retained as a low-cost algorithm sandbox rather than an external
record. Its public deterministic Python simulator makes LLM-guided iteration
fast: the stock MPPI stack reproduced `0.95` success and `0.934` SPL on 20
dynamic seeds twice, while a guarded-MPPI safety wrapper fell to `0.85` and is
rejected. The repository is newly published and has no independent leaderboard
or organizer-run result, so these numbers are useful engineering evidence but
not a defensible external record claim.

### Final target choice after held-out and repeat tests

The campaign now has a defensible demonstration target even though it does not
have a general LoRR algorithmic win. The official Test Round instance
`random_32_32_20_100.json` publishes **1186** completed tasks. The unchanged
archived Team RAPID implementation produced **1318** tasks in Q-31 with the
matching v2.0.0 evaluator, exact input hash, makespan 500, and zero planner,
schedule, and entry-timeout errors. That is the primary local beat to show an
LLM-guided workflow against a reported score.

The boundary is equally important. Q-32 on held-out RANDOM-02 reached 1202
against 1260 with three timeouts, Q-33 reached 1311 with five timeouts, and Q-34
reached 1322 with one timeout under `OMP_NUM_THREADS=1`. Q-35 and Q-36 then
used the declared deterministic runtime control (`OMP_NUM_THREADS=1` plus a
single pinned container CPU): both reached **1325**, with zero errors and
byte-identical compact outputs. Q-37 applied the same control to held-out
RANDOM-02 and reached 1181 versus 1260, with zero errors. Therefore the result
must be described as an **instance-scoped local replay beat under a pinned
runtime condition**, not a generalizable algorithmic improvement or official
leaderboard re-ranking. The bounded runtime-validation loop is now closed;
the next meaningful experiment is an auditable planner variant or organizer
run, not more blind sampling.

## 1. Objective and claim boundaries

### Benchmark-selection rule (updated 2026-09-05)

The campaign now separates three claims that are often conflated:

1. **Published reference exists:** an organizer or competition archive reports
   a score/task count and identifies the run or team.
2. **Protocol replay exists:** the exact public instance, evaluator version, and
   score fields run locally without substitutions.
3. **A local beat exists:** a controller/planner exceeds the reference under
   the same protocol; a stronger algorithmic claim additionally requires
   held-out cases and independent zero-error reruns.

Only the third is a successful demonstration of LLM-guided improvement. A
benchmark is promoted to the primary track only when it scores at least 2/2 on
the first two gates, has a CPU-feasible iteration loop, and leaves a plausible
engineering margin over the reference. This prevents another VRX-like result
where a very low local number is real but incomparable.

The current evidence ranks LoRR above BARN for provenance, BARN above LoRR for
iteration speed, and BallPark above both for iteration speed but below both for
external legitimacy. The intended workflow is therefore: use LoRR Test Round
as the instance-scoped demonstration target, use BallPark for rapid controller
idea prototyping, and retain BARN as the near-leader control.

### Objective

Build an independently reproducible robotics result that demonstrates cheap,
LLM-guided improvement against a published score. The primary route is the
LoRR Test Round replay, where the evaluator, input, winner source, and score
field are inspectable. Retain BARN as a near-leader fallback and determine
whether VRX's historical phase-3 protocol is recoverable enough for a directly
comparable six-trial claim.

The optimization direction is minimize score. The primary engineering target is
low error across all six public phase-2 practice worlds, not a one-world score
on `stationkeeping0`.

### Historical reference

The official VRX 2019 results page reports University of Florida station
keeping as task rank 1 with six displayed run scores:

```text
0.02, 0.04, 0.35, 0.04, 0.10, 0.11  -> displayed mean 0.11
```

`0.11` is a historical phase-3 reference, not the current campaign's score.
Official server-side logs and exact UF trial scores are public, but the
generated phase-3 worlds, complete seeds/configuration, container/dependency
revisions, scorer identity, and controller-side traces remain unresolved.
The official phase-2 table reports UF at `18.76` on the six released scenario
patterns. The local Q-02 result is numerically lower at `8.213646343578185`,
but is a self-hosted reconstruction rather than a recognized submission.

### Current best measured result

| Field | Value |
|---|---|
| Score | **0.008326716568191546** |
| Scope | One public practice world: `2019_practice/stationkeeping0.world` |
| Seed | `10`, world-defined |
| Scored duration | `300.0 s` |
| Controller | Saturation-aware fast PD, GPS position feedback, odometry yaw/velocity, stock T-thruster mapping |
| Controller revision | `fast-pd-v1-2026-09-03` |
| VRX/scorer revision | `a62df11109ee95c206111c37a37c60d39bc7b705` |
| Container digest | `sha256:c67d1d45abebe34ec6c5a101cb8bf16320855807c58f6d0775caabec5e26ab98` |
| Evidence | [`results/practice0-fast-pd-gps.json`](../results/practice0-fast-pd-gps.json), [`artifacts/localized-practice0-fast-pd-gps/result.json`](../artifacts/localized-practice0-fast-pd-gps/result.json) |
| Status | Reproduced twice in Q-01; complete Q-02 public-suite mean is `8.213646343578185` |
| Claim allowed | Public-practice result only; not phase-3, SOTA, record, or UF reproduction |

The result passed local schema, artifact SHA-256, checksum-manifest,
aggregate, experiment-manifest, pinned-identity, and completed-trial checks.
Two fresh same-checkout/container reruns pass all local verifier gates. A
separate clean-clone or external replication remains pending, and no result is
claim-eligible. The original run's `compute_cost_usd` is recorded as `0.0`
(local OrbStack execution).

### Non-comparability rules

1. Never compare the single-world `0.008326716568191546` result directly with
   UF's six-world phase-3 aggregate `0.11`.
2. Never use the `0.00581118860928706` UF-port practice score as a controller
   result: that adapter uses simulator ground truth and a reconstructed
   stationary-goal path, so it bypasses the competition localization boundary.
3. A shortened trial is a plumbing test, not a performance result.
4. A lower score is not a record claim until the evaluator identity, protocol,
   seeds, artifacts, independent rerun, and protected benchmark/scorer tree
   all pass the acceptance gates below.
5. Preserve both public scoring interpretations: the v1.4 task description
   specifies weighted RMS pose error, while the nearest public event-era code
   accumulates a mean of `sqrt(dx² + dy²) + heading_error`. Do not silently
   substitute one for the other when reporting a result.

## 2. Prior attempts and lessons

| Date / commit | Attempt | Measured outcome | Evidence | Lesson for the campaign |
|---|---|---:|---|---|
| 2026-09-03 / `a62df111` runtime image | Pre-runtime-fix diagnostic | `10.221359813302893` | [`artifacts/localized-practice0-fixed/result.json`](../artifacts/localized-practice0-fixed/result.json) | Rejected. A controller/runtime dependency failure made the measurement unsuitable as a baseline. Keep startup and topic-health checks ahead of scoring. |
| 2026-09-03 / `8442133` lineage | UF public-source MRAC practice adapter | `0.00581118860928706` | [`results/README.md`](../results/README.md) | Useful source-path archaeology only. Ground truth and a reconstructed adapter make it non-comparable to the competition interface. |
| 2026-09-03 / `b5eb5d2` | Localized conservative PD, `stationkeeping0`, seed 10 | `0.5243254330428314` | [`artifacts/localized-practice0-valid/result.json`](../artifacts/localized-practice0-valid/result.json) | First valid localized baseline. It converged to about `0.019 m`, but acquisition dominated the 300-second running mean; fast, saturation-aware acquisition is the highest-value next change. |
| 2026-09-03 / post-`b5eb5d2` | Fast PD v1, same public world | `0.501616083452644` | [`artifacts/localized-practice0-fast-pd-v1/result.json`](../artifacts/localized-practice0-fast-pd-v1/result.json) | Faster PD alone did not solve the measurement; preserve the exact controller/config/container identity when changing sensing or wiring. |
| 2026-09-03 / `cca878f` | Fast PD with GPS position feedback, same public world | **`0.008326716568191546`** | [`artifacts/localized-practice0-fast-pd-gps/result.json`](../artifacts/localized-practice0-fast-pd-gps/result.json) | Strong candidate, but surprising improvement requires independent rerun and six-world evaluation before tuning or promotion. |

### Historical implementation work that enabled measurement

- `e8244dd` reconstructed the public protocol and documented the RMS-versus-
  mean-pose scoring discrepancy.
- `8ba7c09` added the six-world public phase-2 suite with explicit world/seed
  provenance and 300-second scored runs.
- `9e2112a`, `81e8dd6`, and `960a4c5` established the ROS scored-controller
  boundary, fixed runtime startup, and bridged Melodic ROS I/O to the Python 3
  controller.
- `3d54ddb` and follow-up verification work added schema, checksum, seed,
  protected-tree, and clean-clone checks.

## 3. Task board

Status vocabulary: `done` means evidence is checked in; `next` means it is
safe to run without changing the declared protocol; `blocked` means an
external artifact is missing; `hold` means do not spend compute until a prior
gate passes.

| Status | Owner | Work item | Evidence / output | Next gate |
|---|---|---|---|---|
| done | Campaign lead | Establish current-best ledger | `results/practice0-fast-pd-gps.json`; local result and checksum files | Local reproduction and breadth evaluation complete |
| done | Verification | Validate current-best local result | Schema, artifacts, aggregate, manifest, pinned identity, and completion checks pass | Standalone verifier reports retained beside successful local runs |
| done | Implementation | Wire the frozen fast-PD GPS controller into the six-world Q-02 runner and emit Q-03 diagnostics | Phase-2 manifest/controller launch wiring; named task/controller JSONL; offline extractor and tests | Completed and exercised by Q-02 |
| done | Local rerun | Re-run current best from fresh containers/result directories on seed 10 | Scores `0.008340650238951723` and `0.008183191252996592`; both fully verify | Local reproducibility confirmed; separate clean-clone/external replication remains open |
| done | Evaluation | Run the fixed fast-PD controller across all six public phase-2 worlds | Six complete trials; strict mean `8.213646343578185`; all local verifier gates pass | Public breadth measured; no record claim |
| done | Controller | Diagnose cross-world failure modes before tuning | Q-03 diagnostics show acquisition/saturation dominate hard worlds, especially `stationkeeping3` | Choose one preregistered robustness hypothesis before more runs |
| done | Controller | Screen Q-07 hybrid transit/hold guidance on hard world 3 | Full trial score `38.02656831042876` vs frozen baseline `37.95612985923057`; candidate rejected | Do not promote transit-only change; retain acquisition diagnostics |
| done | Controller | Screen Q-08 bounded hold integral on disturbed world 2 | Full trial score `1.1042453888647972` vs frozen baseline `1.1048966380251557`; marginal single-world improvement | Requires six-world paired evaluation before selection; not enough to justify promotion |
| done | Controller | Screen Q-09 stronger hold integral on disturbed world 2 | Full trial score `1.105672372538201`; regressed vs baseline and Q-08 | Reject stronger integral; return to observer/feed-forward hypothesis |
| done | Controller | Implement and screen Q-10 low-bandwidth disturbance observer/feed-forward | World-2 score `1.1060880824407322`; world-5 score `5.297878486341276`; both slightly worse than Q-02 baseline | Reject observer variant; avoid six-world spend and return to sensing/trajectory design |
| hold | Controller | Screen Q-11 allocator-aware rotate/sprint/brake guidance | World-3 full trial, followed by world 5 only if world 3 materially improves | Deferred while Q-26 audits a more tractable public benchmark; do not spend compute until the benchmark choice is settled |
| done | Benchmark pivot | Q-12 BARN feasibility and identity capture | [`results/barn-q12-runtime.json`](../results/barn-q12-runtime.json); pinned amd64 image completed public world 0 and emitted organizer-compatible fields | Use the captured identity for a declared 10-world/1-trial screen; retain single-world result as feasibility evidence only |
| done | Benchmark pivot | Q-13 reproduce a BARN published baseline | [`results/barn-q13-baseline/aggregation.json`](../results/barn-q13-baseline/aggregation.json); pinned DWA image completed all ten declared worlds, strict mean `0.23287870433096822`, success `1.0` | Baseline is healthy; compare the published LiCS-KI controller next before new planner edits |
| done | Benchmark pivot | Q-14 run the published LiCS-KI controller | [`results/barn-q14-lics.json`](../results/barn-q14-lics.json); model loads in the pinned CPU-PyTorch image, but world 0 collides after `3.805 s` | Reject for the ten-world screen pending ROS/Python and command-boundary diagnosis; retain DWA as the healthy baseline |
| done | Benchmark pivot | Q-15 test LiCS planner-readiness guard | [`results/barn-q15-lics-readiness.json`](../results/barn-q15-lics-readiness.json); world 0 completed in `6.739 s` at capped metric `0.5` | Advance to the declared ten-world LiCS screen using the frozen readiness image |
| done | Benchmark pivot | Q-16 LiCS readiness ten-world screen | [`results/barn-q16-lics/aggregation.json`](../results/barn-q16-lics/aggregation.json); nine capped successes and one world-0 collision, strict mean `0.45`, success `0.9` | Do not promote against `0.4762`; stabilize world-0 startup before another suite spend |
| done | Benchmark pivot | Q-17 stable-path LiCS readiness guard | [`results/barn-q17-lics-stable-readiness.json`](../results/barn-q17-lics-stable-readiness.json); three world-0 repeats all succeeded at metric `0.5` | Advance to the ten-world stable-readiness screen |
| done | Benchmark pivot | Q-18 stable-readiness LiCS ten-world screen | [`results/barn-q18-lics.json`](../results/barn-q18-lics.json); all ten capped at `0.5`, 100% success, no collisions/timeouts | Public-screen gate passed; retain official-win boundary and perform an independent rerun |
| done | Benchmark pivot | Q-19 independent LiCS public-screen rerun | [`results/barn-q19-lics.json`](../results/barn-q19-lics.json); all ten again capped at `0.5`, 100% success | Screen is reproducible; test all 50 canonical worlds once before any 50×10 spend |
| done | Benchmark pivot | Q-20 all-world LiCS public screen | [`results/barn-q20-lics/aggregation.json`](../results/barn-q20-lics/aggregation.json); 50 canonical worlds, 47/50 success, strict mean `0.46922280825431545` | Failed the `>0.4762` / `>=0.98` breadth gate; target the three collision worlds before any 50×10 spend |
| done | Benchmark pivot | Q-21 LiCS laser collision shield | [`results/barn-q21-lics-safe/`](../results/barn-q21-lics-safe/); worlds 228 and 282 fixed, 294 still collided, world 66 improved | Partial causal win; do not run a full suite until world-294 behavior is addressed |
| done | Benchmark pivot | Q-21b wider LiCS clearance shield | [`results/barn-q21b-lics-safe/`](../results/barn-q21b-lics-safe/); wider 1.5 m threshold timed out on world 228 and was stopped on 282/294/66 | Reject: prevents progress rather than robustly navigating |
| done | Benchmark pivot | Q-22 directional emergency shield | [`results/barn-q22-lics-directional/`](../results/barn-q22-lics-directional/); 294, 228, and 282 collided; only 66 succeeded | Rejected: directional sectors did not preserve Q-21's two repairs |
| done | Benchmark pivot | Q-23 fresh EBand fallback | [`results/barn-q23-lics-hybrid/`](../results/barn-q23-lics-hybrid/); 294 succeeded, but 228 and 282 collided and 66 regressed | Rejected: fixes one failure mode while reintroducing the others |
| done | Benchmark pivot | Q-24 hybrid-safe full breadth | [`results/barn-q24-lics-hybrid-safe-50/aggregation.json`](../results/barn-q24-lics-hybrid-safe-50/aggregation.json); 50 worlds, 44/50 success, strict mean `0.41717035384632806` | Rejected: below Q-20 and published `0.4762`; no further 50×10 spend |
| done | Benchmark pivot | Q-25 smart hybrid directional EBand | [`results/barn-q25-lics-smart-hybrid/`](../results/barn-q25-lics-smart-hybrid/); 294 timed out and 282 collided | Rejected: no generalizable safety policy found |
| done | Benchmark reassessment | Q-35/Q-36 pinned-runtime Test Round repeats | Q-35 and Q-36 used the exact Test Round input/source/image with `OMP_NUM_THREADS=1` and `--cpuset-cpus=0`; both reached 1325 with zero errors and the same output hash | Retain as the strongest local beat evidence; the pinned runtime is part of the reproduction record, not an official leaderboard claim |
| done | Benchmark reassessment | Q-37 pinned-runtime held-out RANDOM-02 | Same source/image/config/runtime control completed RANDOM-02 at 1181 versus 1260 with zero errors | Reject generalization; close the runtime-validation loop and require a declared planner variant or organizer run next |
| hold | Controller | Run preregistered sensing/feedback ablations | One result per queue row; fixed worlds and evaluator identity | Resume after the dominant world-3 acquisition failure is addressed |
| hold | Protocol | Recover exact UF VRX and vrx-docker gitlink objects | UF pointers `8c204f359effb8ab810fac6b57ebc46d13dcaf3a` and `5c9928d6d059cf6aef398b9f3bcbc2c1935a3ef4` are currently unavailable | External source recovery or organizer-provided archive |
| next | Historical comparison | Recover UF phase-3 runtime inputs from the public log bucket | Exact trial scores and server-side Gazebo/task logs are public; generated world SDFs and image identities remain missing | Extract goals, initial poses, timing, and environment evidence from all six logs before judging replay feasibility |
| hold | Promotion | Prepare accepted claim dossier | Audit template, result, artifacts, clean-clone and protected-tree checks | Gates G1–G5 all pass; otherwise label as public-practice only |

## 4. Ranked approaches

Ranking is by expected information per unit compute, with measurement validity
before controller optimization.

0. **LoRR 2024 Test Round (highest-confidence local target).** The exact
   100-agent, 500-tick Test Round input and v2.0.0 evaluator now have two
   byte-identical zero-error RAPID replays under a declared pinned runtime
   (`OMP_NUM_THREADS=1`, one container CPU). The archive's 1186-task reference
   and open winner sources make this the cheapest credible local beat loop.
   Held-out RANDOM-02 is clean under the same control but remains below its
   1260-task reference, so the result is not a general algorithmic win.
1. **BARN public-suite track (reproducible near-leader fallback).** First make one BARN
   baseline run reproducible, then use 10-world/1-trial screens for LLM-led
   changes. Start from the public LfLH or DWA stack and add one narrowly scoped
   recovery/clearance policy per iteration. Promote only after a frozen
   50-world/10-trial public run beats the local baseline and is independently
   rerun. The stretch target is `>0.4762`, the published 2024 LiCS-KI score;
   an organizer-run submission is required before calling it an official
   leaderboard win.
2. **Allocator-aware rotate/sprint/brake guidance (VRX secondary).** World 3 starts about
   `190.44 m` from the goal with a `-148.2 deg` bearing error. The baseline and
   Q-07 both traverse almost the entire leg backwards, holding the two surge
   thrusters near their weaker `-100 N` reverse limit while the independent
   wrench/force clipping removes the requested yaw authority. First rotate the
   hull using a yaw-priority allocation, then sprint on the stronger forward
   branch and switch to a stopping-distance-based brake/hold capture. This is
   the highest-upside change that preserves the stock vehicle and benchmark.
3. **Four-thruster X layout with constrained allocation.** If Q-11 proves that
   transit authority is the limiting factor, reproduce UF's four-thruster
   geometry and allocate the full wrench under per-thruster limits. This is a
   larger vehicle/configuration change and therefore follows the stock-layout
   causal test rather than preceding it.
4. **Robust hold control.** Test bounded hold-only integral action, observer
   compensation, anti-windup, and gain scheduling against world 2's persistent
   disturbed-state error.
5. **Pre-registered sensing ablations.** Compare GPS position feedback,
   localization odometry, and fused/filtered variants under the same stock
   thruster mapper. Keep the evaluator untouched and use held-out worlds for
   selection.
6. **Robust disturbance handling.** Only after the fixed six-world result is
   established, test observer/adaptation, anti-windup, rate/dead-zone handling,
   and gain scheduling. Use failure recovery and worst-world score as primary
   diagnostics.
7. **Source-faithful UF MRAC/LQ-RRT path.** This is historically relevant. The
   public UF mission and MRAC source plus official server-side phase-3 logs now
   support a closer reconstruction, but the external trajectory producer,
   generated worlds, exact submodules, and image identities remain incomplete.
8. **BallPark deterministic sandbox.** Use its Python-only simulator for rapid
   MPPI/recovery experiments and regression tests, but never label its
   self-published scores as an external record until an independent organizer or
   leaderboard exists.
9. **Remote/GPU scale-out.** Use Vast.ai only for a bounded, reproducible batch
   after local six-world behavior and container identity are stable. More
   trials cannot repair an unresolved protocol mismatch.

## 5. Immutable experiment queue

These rows are preregistered decisions. Once a row starts, do not change its
controller, evaluator, world set, seed set, timing, or output interpretation.
Any change creates a new queue row with a new ID. Store the exact Git commit,
manifest SHA-256, image digest, command, and raw artifact manifest in the
result directory.

| ID | Question | Frozen inputs | Run plan | Pass / fail decision |
|---|---|---|---|---|
| Q-01 | Is the `0.0083` result locally reproducible? | Controller `fast-pd-v1-2026-09-03`; manifest [`vrx2019-station-keeping-practice0-fast-pd.json`](../config/experiments/vrx2019-station-keeping-practice0-fast-pd.json); VRX/scorer `a62df111`; seed 10; `stationkeeping0`; 10/10/300 s | Two fresh same-checkout container runs, including the full raw artifact set and local verification | Passed locally. Separate clean-clone or external replication remains a distinct open gate. |
| Q-02 | Does the current best generalize across the public suite? | Same controller, gains, image, scorer, and 10/10/300 s timings; suite [`vrx2019-station-keeping-phase2.json`](../config/experiments/vrx2019-station-keeping-phase2.json); worlds/seeds 0–5 as pinned by that manifest | One complete six-world suite; no gain or code changes between worlds | Pass means six/ six completed trials, all artifacts verify, and the result is labelled public-practice only. Use the six-world aggregate as the frozen baseline for later ablations. |
| Q-03 | Is the improvement acquisition-driven? | Controller and evaluator frozen at Q-02; diagnostic extraction only | Recompute per-world time-to-`0.25 m`, time-to-`0.5 m`, peak actuator saturation, max yaw error, and first/last 30-second error from bags/task info | Produces a causal diagnosis. No score claim is made from this row. |
| Q-04 | Does GPS feedback, not PD tuning, explain the jump? | Same controller gains and stock mapper; swap only position source between GPS and localization odometry; same six worlds and fresh output directories | Paired six-world runs with source order randomized before execution; record topic health and latency | Prefer the source that improves the held-out aggregate without increasing failures, saturation, or protocol ambiguity. |
| Q-05 | Can disturbance handling improve the held-out public suite? | Freeze Q-02 best controller and scorer; choose observer/adaptation change before seeing Q-02 world scores | Development seeds/worlds declared before the run; evaluation worlds held out and disjoint; maximum two candidate variants | Accept only if the held-out aggregate and worst-world score improve and all verification gates pass. |
| Q-06 | Is historical UF comparison recoverable? | Exact UF tag/submodules, event-era server, phase-3 worlds, six seeds, and scorer binary when/if recovered | Rebuild from hashes, record all dependencies, run six trials, independently recompute both public scoring interpretations | If any required artifact remains unavailable, report blocked; never substitute phase-2 worlds and call it phase-3 reproduction. |
| Q-07 | Does bounded velocity transit improve the farthest public world? | Candidate manifest [`vrx2019-station-keeping-phase2-hybrid-transit.json`](../config/experiments/vrx2019-station-keeping-phase2-hybrid-transit.json); hybrid transit radius 8 m, speed cap 2.5 m/s; world 3 only for screening | One complete 300-second world-3 trial; compare with frozen Q-02 world-3 score and inspect acquisition/final-window diagnostics | Reject unless score and acquisition improve without a final-window regression. **Rejected:** `38.02656831042876` vs `37.95612985923057`. |
| Q-08 | Does bounded hold-only integral reduce persistent disturbed error? | Candidate manifest [`vrx2019-station-keeping-phase2-hybrid-hold-integral.json`](../config/experiments/vrx2019-station-keeping-phase2-hybrid-hold-integral.json); Q-07 transit plus hold `ki=[0.6,0.6,1.2]`, bounded integrals; world 2 screen | One complete 300-second world-2 trial; preserve Q-02 baseline and compare last-window error | Advance only to a paired six-world evaluation if the gain is material and no acquisition/failure penalty appears. **Screen gain:** `1.1042453888647972` vs `1.1048966380251557`; insufficient alone. |
| Q-09 | Does stronger bounded integral improve world-2 rejection? | Candidate manifest [`vrx2019-station-keeping-phase2-hybrid-hold-integral-strong.json`](../config/experiments/vrx2019-station-keeping-phase2-hybrid-hold-integral-strong.json); hold `ki=[4,4,8]`, tighter bounds | One complete 300-second world-2 trial | Reject if score regresses or oscillation/saturation rises. **Rejected:** `1.105672372538201`. |
| Q-10 | Can low-frequency disturbance feed-forward reduce disturbed holding error without integral windup? | New opt-in observer; freeze Q-02 gains, stock T mapper, and six public worlds; bandwidth candidates 0.15 and 0.30 Hz declared before execution | Screen worlds 2 and 5, then run one paired six-world evaluation for the better candidate | Advance only when both screens improve and the paired aggregate/worst-world score beat Q-02; otherwise reject and retain baseline |
| Q-11 | Can allocation-aware rotate/sprint/brake guidance eliminate the reverse-transit failure? | Freeze Q-02 scorer, worlds, sensing, hold PD, stock T layout, and actuator curves. Change only transit state logic and allocation: rotate with translation suppressed until bearing error is small, sprint on the stronger forward thrust branch, then brake from measured along-track speed and hand off to frozen hold control. | One full world-3 screen. If score and acquisition pass, run world 5 as the disturbed/alignment safety screen; only then consider a paired six-world run. | World 3 must beat `37.95612985923057` by at least 10%, reach `0.5 m` before `115.56 s` (10% faster than `128.403 s`), and preserve the final-window error below `0.01 m`. World 5 must not regress score by more than 2%. Otherwise reject or revise under a new queue ID. |
| Q-12 | Can the BARN evaluator run locally with a pinned identity? | BARN dataset, evaluator, and baseline repositories pinned by commit; x86 container/runtime captured; no controller changes | Run one public world and retain stdout, episode status, traversal time, OT, and computed metric. Do not infer a score from a video or a timeout. | Pass only if the run completes and the report fields required by the organizer's `report_test.py` are present and independently recomputable. |
| Q-13 | Can an LLM iteration beat a published BARN baseline at low cost? | Q-12 identity; public worlds only; baseline frozen; screen seed/world list declared before edits | Screen 10 worlds × 1 trial for each candidate. Keep at most three candidates. Run 50 worlds × 10 trials only for the selected candidate and baseline. | Candidate must improve mean metric, success rate, and 25th-percentile traversal time on the held-out public set; all trial logs and evaluator outputs must be retained. A score above `0.4762` is a stretch result, not an official win until organizer evaluation. |
| Q-15 | Does a planner-readiness guard remove LiCS startup collisions? | LiCS model/image frozen from Q-14; only the readiness patch changes; world 0 | Build [`docker/barn-lics-ready.Dockerfile`](../docker/barn-lics-ready.Dockerfile), run one complete world-0 trial, preserve raw output and patch/image hashes | **Passed:** world 0 completed at `0.5`; advance to Q-16. |
| Q-16 | Does the readiness-fixed published LiCS controller generalize beyond world 0? | Q-15 readiness image frozen; worlds `0,6,12,18,24,30,36,42,48,54`; one trial/world | Run ten containers sequentially, preserve raw lines and console logs, independently recompute metrics with the report-script OT | **Screen result:** mean `0.45`, success `0.9`; better than Q-13 but below `0.4762` because world 0 collided. |
| Q-17 | Does a stable-path guard remove nondeterministic world-0 startup collisions? | Q-16 model and evaluator frozen; only readiness condition changes; world 0 repeated three times | Build the updated readiness image and run three independent world-0 trials, preserving raw lines and image/patch hashes | **Passed:** all three succeeded at `0.5`; advance to Q-18. |
| Q-18 | Does stable-readiness LiCS beat the published leader on the public screen? | Q-17 image frozen; worlds `0,6,12,18,24,30,36,42,48,54`; one trial/world | Run ten containers sequentially, preserve raw lines and console logs, independently recompute metrics | **Passed:** mean `0.5`, success `1.0`, no runtime drift; official win still requires organizer private evaluation. |
| Q-19 | Is the Q-18 public-screen win independently reproducible? | Q-18 image, worlds, scorer, and readiness patch frozen; fresh output directory | Repeat the same ten-world screen once; preserve independent logs and recomputation | **Passed:** mean `0.5`, success `1.0`; proceed to all-world breadth screen. |
| Q-20 | Does stable-readiness LiCS generalize across all 50 canonical public worlds? | Q-19 image frozen; world indices `0,6,12,…,294`; one trial/world | Run 50 containers sequentially, preserve raw lines and console logs, independently recompute metrics | Breadth gate: mean `>0.4762`, success `>=0.98`, and no runtime drift; only then consider 50×10 confirmation |
| Q-21 | Can a bounded laser shield remove the observed LiCS collision failures without changing the learned policy? | Q-20 LiCS image frozen; only `set_velocity` safety layer added; front threshold `0.75 m`, scale zone to `1.10 m`; worlds 228, 282, 294, 66 | One trial per target world; preserve image digest and raw logs | **Partial:** 228 `0.2345` and 282 `0.3866` succeeded, 66 improved to `0.4732`, but 294 still collided; retain as causal evidence, not a promoted controller |
| Q-21b | Does an earlier/wider 1.5 m clearance threshold solve the remaining collision? | Q-21 image frozen; only front sector widened and threshold changed to `1.50 m`; same four worlds | One trial per target; stop a run if the candidate remains stationary until timeout | **Rejected:** world 228 timed out at `100.055 s`, and the remaining runs were stopped; the wider shield is too conservative |
| Q-22 | Can directional emergency braking fix world 294 while preserving Q-21's two fixes? | Q-21 image and thresholds frozen; add commanded-direction scan sectors and a near-obstacle emergency stop/turn; no model, planner, or evaluator changes | Screen worlds `294,228,282,66` in randomized order; require 294 success and no regressions on the other three | **Rejected:** 294, 228, and 282 collided; only 66 succeeded (`0.4445`). |
| Q-23 | Can a fresh EBand command rescue the near-obstacle LiCS cases? | Q-21 model/evaluator frozen; use fresh `/move_base/cmd_vel` only inside the `<0.90 m` front range band | Screen worlds `294,228,282,66`; compare collision status and traversal time to Q-21 | **Rejected:** 294 succeeded (`0.3677`), but 228 and 282 collided and 66 regressed (`0.1858`). |
| Q-24 | Does combining Q-21 shield and Q-23 EBand fallback generalize? | Q-24 image frozen; all 50 canonical public worlds, one trial/world | Run 50 containers and strictly recompute with report-script OT | **Rejected:** mean `0.41717035384632806`, success `0.88` (44/50), below Q-20 and `0.4762`. |
| Q-25 | Can EBand override be gated by directional agreement? | Q-24 stack frozen; permit EBand override only when its angular direction agrees with the clearer side | Target worlds `294,228,282,66`; retain all raw output | **Rejected:** 294 timed out (`100.008 s`) and 282 collided; 228 succeeded (`0.5`) and 66 scored `0.4404`. |
| Q-26 | Can the official LoRR 2024 archive be replayed with its matching evaluator? | LoRR Benchmark Archive 2024 Main Round RANDOM-01; tagged Start-Kit `v2.0.0`; unmodified archive JSON; archived best-known source/solution identity | Default v2.0.0 replay completed validly at 492 tasks; archived Team RAPID source built in a pinned image; no delay settings or current 3.x executor are used | Accept the protocol as replayable only after the tagged runtime and score fields are captured; retain the archived 696-task output as a reference, not as a local result |
| Q-27 | Does the archived Team RAPID implementation reproduce its published RANDOM-01 count? | Team RAPID source identity `3635cb44497727271f173582a86a2cea72e9e17e`; Start-Kit v2.0.0; exact RANDOM-01; `-s 600`; explicit file-storage path; fixed compiler/image digest | One clean replay with full output, exit code, and runtime metadata | **Completed validly at 690 tasks**, with makespan 600 and zero planner/schedule/entry errors. This is a six-task gap to the archived 696 reference; do not call it an exact winner reproduction |
| Q-28 | Does a single LaCAM2 planning-window change move the near-winner result? | Q-27 Team RAPID source; exact RANDOM-01; `planning_window=4` instead of `3`; same v2.0.0 image/toolchain and explicit storage path | One diagnostic replay on RANDOM-01; held-out follow-up is gated on the result | **Diagnostic only:** 693 tasks (+3), but 2 entry timeouts; reject for promotion and do not carry it to held-out evaluation |
| Q-29 | Can a selected planner/configuration change beat the archived count on held-out LoRR instances? | Q-27 winner baseline; RANDOM-02 and RANDOM-03 held out; one declared change at a time (planning window, neighborhood size, ordering, or cache policy) | Screen at most three variants on one held-out instance, then confirm the selected variant on the second held-out instance | Accept only if task count improves on both held-out instances with zero errors; then rerun RANDOM-01 for an apples-to-apples comparison |
| Q-30 | Is the LoRR Test Round 100-agent instance a cheaper, independently reported target? | Untouched Test Round `random_32_32_20_100.json`; 500 ticks; Team RAPID v2.0.0 image as a common baseline; archived reference 1186 tasks from Team Kitty Knight | Baseline replay completed at 1320 tasks, but with one entry timeout; a zero-error rerun is required before promotion | **Promising but not yet claimable:** +134 tasks over the archived reference, exact protocol fields, but the timeout violates the integrity gate |
| Q-30-ref | Does the archived Team Kitty Knight source and score format replay on the exact Test Round input? | Team Kitty Knight source `c45dfe0c26258930d0205aa4d5e77e22c8392a16`; Start-Kit v2.0.0; exact 100-agent input; `-s 500` | One clean source replay with output fields and log scan | **Completed:** 1199 tasks, `AllValid=Yes`, zero timeout/error markers; retain 1186 as the published reference because counts vary across runtimes |
| Q-31 | Can the Team RAPID Test Round beat survive a clean zero-timeout rerun? | Q-30 RAPID image digest `sha256:4a49d3b7720b8caf93cc72a00af8eeb8e91178b9d44ab95396df2ec0eeb27309`; exact input; explicit storage; `-s 500` | Repeat without source/config changes; require zero entry timeouts and no planner/schedule errors | **Completed:** 1318 tasks (+132 over 1186), makespan 500, and zero planner/schedule/entry errors; verified local protocol beat, not an official leaderboard claim |
| Q-32 | Does the Q-31 improvement generalize to a held-out Main Round instance? | Same Team RAPID source/image and v2.0.0 runtime; untouched archived RANDOM-02; no Test Round tuning | Run one declared held-out instance with zero planner/schedule/entry errors | **Failed generalization:** 1202 tasks versus 1260, with 3 entry timeouts; keep the Test Round claim instance-scoped |
| Q-33 | Is the Test Round local beat independently reproducible? | Same Team RAPID image, exact Test Round input, 500 ticks, explicit storage; no source/config changes | One independent clean rerun; require >=1186 tasks and zero errors | **Failed clean gate:** 1311 tasks (+125), but five entry timeouts; retain as runtime-sensitivity evidence |
| Q-34 | Does the documented single-thread setting stabilize the Test Round run? | Same source/image/input; set `OMP_NUM_THREADS=1`; no planner/config edits | One run; compare task count, timeout count, and wall-clock cost to Q-31/Q-33 | **Completed/rejected:** 1322 tasks (+136) but one entry timeout; more wall time and no clean stabilization. Close blind sampling and require a declared planner change |
| Q-35 | Does a declared CPU-pinned runtime remove the residual Test Round entry timeout? | Same Q-34 source/image/config/input; `OMP_NUM_THREADS=1`; Docker `--cpuset-cpus=0`; default 1000 ms planner limit; `-s 500` | One exact Test Round replay; retain input/config/binary/image/output hashes, all error counters, exit code, and wall time | **Completed:** 1325 tasks (+139), makespan 500, zero planner/schedule/entry errors; retain as clean local beat under the pinned runtime condition |
| Q-36 | Is the Q-35 pinned-runtime result independently repeatable? | Byte-for-byte same Q-35 input/source/config/image/runtime and protocol flags; fresh output directory and output filename | One independent repeat; compare all counters and output hash | **Completed:** 1325 tasks (+139), zero errors, and output SHA-256 identical to Q-35; supports deterministic replay under the declared control |
| Q-37 | Does the pinned runtime generalize the unchanged RAPID planner to held-out RANDOM-02? | Same Q-35/Q-36 source/image/config/runtime; untouched Main Round `RANDOM-02.json`; `-s 600` | One held-out replay; preserve the same hashes, counters, and wall time | **Completed as negative control:** 1181 tasks versus 1260 (-79), zero errors; reject a generalization claim and close blind runtime sampling |

Q-12 runtime entry point (after Docker build) is:

```bash
docker build --platform linux/amd64 -f docker/barn.Dockerfile -t vrx-record-lab:barn-dwa .
docker run --rm --platform linux/amd64 --network host \
  -v "$PWD/results/barn-q12:/out" vrx-record-lab:barn-dwa \
  --world_idx 0 --out /out/world-0.txt
```

The image pins the BARN, Jackal, simulator, desktop, and EBand repositories
by commit. The command is intentionally a one-world gate; do not start the
50-world batch until the episode reaches a terminal status and its log passes
`scripts/aggregate_barn`.

Q-12 passed on 2026-09-04: world 0 completed in 37.258 seconds with raw line
`0 1 0 0 37.2580 0.1824`. Recomputing with the report-script start pose gives
`0.18025371645174834`; the `0.002146283548251665` difference is the known
`run.py` versus `report_test.py` coordinate mismatch. See
[`results/barn-q12-runtime.json`](../results/barn-q12-runtime.json).

Q-13 baseline screen declaration (2026-09-04): run the pinned DWA image once
on worlds `0, 6, 12, 18, 24, 30, 36, 42, 48, 54`. These are the first ten
canonical public evaluation worlds (`world_idx = 6*k`). Preserve one raw line
per world, the container console output, and a recomputed metric table. This is
a local baseline screen only; it is not the hidden 2024 leaderboard evaluation.

Q-13 completed on 2026-09-04: all ten worlds succeeded with no collisions or
timeouts. The strict report-script mean is `0.23287870433096822`; per-world
metrics and raw lines are in
[`results/barn-q13-baseline/aggregation.json`](../results/barn-q13-baseline/aggregation.json).

Q-14 was run on 2026-09-04 because LiCS-KI is the published 2024 leader and
its controller code/model are public. The model loaded, but world 0 collided
after `3.805 s` and emitted `0 0 1 0 3.8050 0.0000`. This rejects a blind
ten-world screen for now. The likely next diagnostic is to compare the public
controller's expected `/cmd_vel`, laser preprocessing, and planner frame
against the pinned ROS Melodic runtime; no code change should be promoted until
that boundary is understood.

Q-15 passed on 2026-09-04: the readiness guard held zero velocity until a
nonzero local goal was available, and world 0 completed in `6.739 s` with the
capped report-script metric `0.5`. Q-16 is now the next controlled experiment.

Q-17 passed on 2026-09-04: requiring one second of a stable nonempty global
path produced three independent world-0 successes at `0.5`. Q-18 is the
result-bearing ten-world screen.

Q-18 completed on 2026-09-04: all ten declared public worlds succeeded and
recomputed to the metric cap, mean `0.5`. This exceeds the published hidden
leader `0.4762` only on a local public screen; it is not an official result.
Q-19 repeats the screen before any larger batch.

Q-19 completed on 2026-09-04 with the same `0.5`/100% result. Q-20 expands
to every canonical public evaluation world once, reducing the risk that the
ten-world screen is an easy-world artifact.

Q-20 completed on 2026-09-04: 47/50 worlds succeeded, with collisions on
worlds 228, 282, and 294. The strict report-script mean was
`0.46922280825431545`, just below the published hidden reference `0.4762`,
so the breadth gate failed. The result is still valuable because it localizes
the deficit to three obstacle interactions rather than evaluator/runtime
drift.

Q-21 added a bounded laser shield at the command boundary. It fixed worlds
228 and 282 and improved world 66, but world 294 still collided. Q-21b widened
the shield to 1.5 m; it timed out on world 228 and was stopped on the remaining
targets, demonstrating that indiscriminate early braking is too conservative.
Q-22's directional variant collided on 294, 228, and 282. Q-23's EBand fallback
rescued 294 but reintroduced collisions on 228 and 282. Q-24 combined both
mechanisms and failed the 50-world breadth test (`0.41717035384632806`, 44/50),
and Q-25's directional gate still timed out/collided. The LiCS safety branch is
therefore closed; Q-26 now audits whether the official LoRR 2024 archive offers
a cleaner, genuinely reproducible public target.

### Queue execution rules

- Q-01 and Q-02 are complete. Future candidates start from their frozen local
  evidence and must not retroactively change those manifests or results.
- Q-02 freezes the first broad public baseline. Do not select a controller
  variant from Q-02's six scores and then reuse those same worlds as an
  unbiased evaluation set.
- Q-04 is a paired ablation, not a new best claim. Topic availability,
  timestamp freshness, and frame conversion must be logged for every trial.
- Q-07 showed that a bounded transit law can reach the far goal but did not
  improve the frozen world-3 score. Treat it as a useful acquisition control,
  not a promoted controller.
- Q-08's small world-2 gain is below the margin needed to justify six-world
  spend; Q-09 regressed when integral authority was increased. The next
  robustness change should estimate/feed forward disturbance rather than add
  more integral authority.
- Q-10's model-residual observer was slightly worse on both disturbed screens.
  This suggests that the nominal mass/damping model or stock-T wrench estimate
  is not accurate enough for direct feed-forward. Retire this variant and
  prioritize sensor fusion, trajectory braking, or a learned disturbance map
  validated on declared development worlds.
- Q-11 takes priority over Q-04 because the existing diagnostics identify a
  specific actuator-allocation failure with much larger score leverage than
  the small hold-error changes seen in Q-08--Q-10. Keep the stock T vehicle for
  this causal test; a four-thruster layout becomes a separate follow-up.
- Any failed or timed-out trial is retained as evidence and reported as
  incomplete; no score is fabricated or silently dropped.
- Candidate manifests may use the local `extends` field to inherit the frozen
  six-world protocol. The loader deep-merges the overlay and records the
  candidate file's own SHA-256, so protocol reuse is explicit rather than a
  hand-copied duplicate.

## 6. Acceptance gates

| Gate | Requirement | Evidence required | Current state |
|---|---|---|---|
| G1 — identity | Exact controller commit/config, VRX/scorer revision, container digest, OS/runtime identity | Manifest plus SHA-256/checksum files | Pass for Q-01/Q-02 public-practice runs |
| G2 — protocol | Correct world, seed, Initial/Ready/Running timing, goal topic, score topic/field, and complete 300-second run | Trial protocol, task-info stream, launch metadata, raw bag/logs | Pass for the six public phase-2 worlds; phase-3 only partially recovered from public logs |
| G3 — independent rerun | A fresh clean clone and fresh container reproduce the declared result without reusing mutable artifacts | Independent result directory and verifier output | Two fresh same-checkout container runs reproduce about `0.0083`; separate clean-clone/external independence remains open |
| G4 — breadth | All six public worlds complete under one frozen controller/evaluator identity | Six trial records, aggregate, per-world diagnostics | Pass for execution; performance mean `8.213646343578185` rejects promotion |
| G5 — integrity | Schema, aggregate arithmetic, artifact bytes, manifest, seeds, protected benchmark/scorer tree, and clean-clone checks pass | Machine-readable result plus audit report | Local artifact gates pass; protected-tree check remains vacuous and raw evidence is Git-ignored |
| G6 — historical comparability | Exact phase-3 inputs and scorer are restored; six reproduced scores are compared with the official log values | Hashes, build logs, six raw trials, independent score recomputation | Partial: exact UF trial scores and server logs are public; generated worlds and exact image/source identities remain unavailable |
| G7 — promotion | Claim language matches the strongest gate actually passed | Signed/committed dossier with explicit caveats | No promoted record claim |

## 7. Compute budget and stopping policy

### Measured cost anchor

The current best used local OrbStack execution and reports `wall_clock_s =
357.8615491249948` for one 300-second scored trial. Nearby baseline runs took
approximately 359–370 seconds wall time. Budget planning should therefore use
about 7 minutes per full trial, plus container startup/build overhead.

### Campaign budget

| Stage | Allocation | Exit condition |
|---|---:|---|
| Q-01 identity check | 2 full reruns on seed 10 | Stop after two successful confirmations or after two identity/startup failures; investigate before spending more |
| Q-02 public breadth | 6 full trials | Stop when all six complete and the fixed baseline is verified |
| Q-03 diagnosis | No new simulator runs initially | Use existing bags/task info; run more only if a required signal is absent |
| Q-04 sensing ablation | 2 × 6 full trials | Stop after the paired comparison; no third variant until the result is interpreted |
| Q-05 robustness | Maximum 2 candidate variants × 6 evaluation trials, with disjoint development/held-out worlds | Stop if neither candidate beats the frozen baseline or if failure rate increases |
| Remote compute | Zero until Q-01 and Q-02 pass; then a bounded maximum of 12 full trials | Reconcile every remote artifact and cost before any follow-on batch |
| BARN feasibility | 1 single-world run, then 10-world/1-trial screens | Stop immediately on container/evaluator drift; do not begin a 500-episode batch until the metric is independently recomputable |
| BARN public promotion | Baseline + selected candidate, 50 worlds × 10 trials | Spend the full batch only after the screen improves success and metric on held-out worlds; estimated as a bounded Gazebo batch, not an open-ended search |

The local-first policy is intentional. The recorded current-best cost is
`$0.00`; remote spend is not justified while evaluator identity and public
generalization remain unresolved. A shortened run may be used to debug plumbing
but does not consume performance budget or enter the evidence ledger as a
score.

### Stopping rules

- Stop optimization if a change improves `stationkeeping0` but degrades the
  frozen six-world baseline or worst-world score.
- Stop and diagnose if topic freshness, frame conversion, container identity,
  or task completion differs between paired trials.
- Stop the historical-claim track while any phase-3 input in G6 is unavailable.
- Stop remote execution if artifact upload, hashing, or environment capture is
  incomplete for any trial.

## 8. Progress log

| Date | Event | Decision |
|---|---|---|
| 2026-09-03 | Public VRX protocol, phase-2 worlds, and UF evidence dossier assembled | Treat UF `0.11` as a historical reference only; preserve RMS-versus-mean ambiguity |
| 2026-09-03 | UF public-source MRAC practice adapter measured `0.00581118860928706` | Keep as non-comparable source-path evidence; do not use as controller leaderboard score |
| 2026-09-03 | ROS scored-controller runtime brought up; pre-fix diagnostic measured `10.221359813302893` | Reject diagnostic; add startup/dependency health checks |
| 2026-09-03 | Localized conservative PD baseline measured `0.5243254330428314` | Confirm valid localization/stock-thruster boundary; prioritize acquisition latency |
| 2026-09-03 | Fast PD v1 measured `0.501616083452644` | Faster PD alone insufficient; preserve identity and inspect sensor path |
| 2026-09-03 | GPS fast PD measured **`0.008326716568191546`** on `stationkeeping0`, seed 10 | Freeze as current best; require Q-01 before tuning or broad claims |
| 2026-09-03 | Campaign tracker created on clean `main` at parent snapshot `cca878f` | This file becomes the canonical performance plan and decision register |
| 2026-09-03 | Q-03/Q-02 infrastructure added without simulator execution | Fast-PD GPS is now reusable from the six-world manifest; named controller/task JSONL and offline extraction are ready. Q-01 remains first; no paid compute used. |
| 2026-09-04 | Q-01 reproduced the one-world score twice (`0.00834065`, `0.00818319`) | Accept the narrow reproducibility result; retain failed host-stall attempts separately |
| 2026-09-04 | Q-02 completed six/six public worlds with mean `8.213646343578185` | Reject record promotion; acquisition transients dominate harder worlds |
| 2026-09-04 | Official phase-3 S3 logs located and exact UF scores recovered | Replace the rounded-only evidence claim: exact mean is `0.110429677731685`; retain non-comparability until generated worlds and image identities are recovered |
| 2026-09-04 | Q-07 hybrid transit/hold implementation added; world-3 screen scored `38.02656831042876` | Candidate reached the far goal but regressed the frozen world-3 baseline by `0.07043845119819`; reject transit-only promotion |
| 2026-09-04 | Q-08 bounded hold integral screened on world 2 at `1.1042453888647972` | Marginal improvement of `0.0006512491603585`; retain as a hypothesis, but require paired six-world evidence |
| 2026-09-04 | Q-09 stronger hold integral screened on world 2 at `1.105672372538201` | Rejected: stronger integral is worse than both frozen baseline and Q-08; Q-10 observer screen was preregistered as the follow-up |
| 2026-09-04 | Q-10 low-bandwidth disturbance observer screened on worlds 2 and 5 | Scores `1.1060880824407322` and `5.297878486341276` versus baselines `1.1048966380251557` and `5.289713085241316`; reject observer-only feed-forward |
| 2026-09-04 | Post-Q-10 trajectory review found that world 3 begins `190.44 m` away at `-148.2 deg` to the goal bearing; baseline and Q-07 both drive the leg backwards near the weaker reverse-force limits | Prioritize Q-11 yaw-priority rotate/sprint/brake control on the stock T layout; defer sensing and four-thruster changes until this causal screen is resolved |
| 2026-09-04 | Benchmark review compared VRX phase-3, BARN, and other public robotics challenges; BARN 2024 exposes a clear metric, public worlds, baseline code, and an open winning submission | Make BARN Q-12/Q-13 the primary low-cost LLM iteration track; keep VRX Q-11 as a secondary controller experiment and reserve all official-record language for organizer-verified evaluation |
| 2026-09-04 | Cloned LiCS-KI commit `f7bd87cc232b04f6ce9edd10a6a05b84a6c7dfaa` and independently recomputed its checked-in 500-line output with the new strict scorer | Public artifact scores `0.4889133891483272` (98% success), above the published hidden-test `0.4762`; treat this as upstream-artifact arithmetic evidence, not our controller result or an official re-ranking |
| 2026-09-04 | Audited LiCS-KI's optional sixth-column per-run metrics and formula | Public `run.py`/`report_test.py` match the organizer formula, but 12 lines differ from `report_test.py` by up to `0.00482` because `run.py` uses start `[-2.25, 3]` while `report_test.py` recomputes OT from `[-2, 3]`; mark formula equivalence verified and hidden final-score reproduction unverified |
| 2026-09-04 | BARN runtime reconnaissance: the local `osrf/ros:melodic-desktop-full-bionic` image builds the Jackal/BARN catkin workspace under `linux/amd64` emulation after `apt-get update`; the base image lacks PyTorch required by LiCS | Q-12 remains open for a real one-world run; use a pinned DWA baseline or a separately built CPU-PyTorch image before attempting the LiCS stack |
| 2026-09-04 | First DWA smoke reached `roslaunch` but failed before Gazebo startup because the ephemeral image lacked `lms1xx` (and related Jackal sensor packages) | Do not repeat ad-hoc package installs per trial; build one pinned BARN Docker image with the complete rosdep closure, then rerun Q-12 once and capture the image digest |
| 2026-09-04 | Pinned BARN DWA image built successfully and world 0 completed (`37.258 s`, runner metric `0.1824`; report-script metric `0.18025371645174834`) | Mark Q-12 done. Begin only a declared 10-world/1-trial screen; keep the one-world run as feasibility evidence, not a benchmark claim |
| 2026-09-04 | Q-13 pinned DWA baseline screen completed on worlds `0,6,12,18,24,30,36,42,48,54` | All ten succeeded; strict mean `0.23287870433096822`; baseline is healthy and ready for a LiCS comparison |
| 2026-09-04 | Q-14 LiCS-KI smoke loaded the released Transformer model but collided on world 0 after `3.805 s` | Do not spend on a ten-world LiCS run yet; diagnose ROS/Python and command-boundary compatibility first |
| 2026-09-04 | Q-15 readiness guard rerun completed world 0 in `6.739 s` at metric `0.5` | Accept the causal startup fix for a ten-world screen; preserve the unguarded collision as the paired failure control |
| 2026-09-04 | Q-17 stable-path readiness repeated world 0 three times | All three succeeded at metric `0.5`; accept the guard as the frozen Q-18 candidate |
| 2026-09-04 | Q-18 stable-readiness LiCS ten-world screen completed | Ten/ten capped successes; strict mean `0.5` versus published `0.4762`; authorize one independent rerun before full public-suite spend |
| 2026-09-04 | Q-19 independent stable-readiness LiCS ten-world screen completed | Ten/ten capped successes again; authorize all-world breadth screen, not yet 50×10 |
| 2026-09-04 | Q-20 all-world LiCS public breadth screen completed | 47/50 success, strict mean `0.46922280825431545`; collisions localized to worlds 228, 282, and 294; do not spend on 50×10 yet |
| 2026-09-04 | Q-21 laser collision shield screened on the three failures plus world 66 | Fixed 228 and 282 and improved 66, but 294 still collided; retain as a partial causal improvement |
| 2026-09-04 | Q-21b wider shield screened and rejected | 1.5 m threshold caused a world-228 timeout and was stopped on remaining targets; prefer directional emergency logic over blanket braking |
| 2026-09-04 | Q-22 directional shield screened and rejected | Worlds 294, 228, and 282 collided; only 66 succeeded; directional sectors did not preserve Q-21's partial fixes |
| 2026-09-04 | Q-23 EBand fallback screened and rejected | World 294 succeeded, but 228 and 282 collided and 66 regressed; one-case rescue did not generalize |
| 2026-09-04 | Q-24 hybrid-safe full breadth completed and rejected | 44/50 success, strict mean `0.41717035384632806`; below Q-20 and the published `0.4762` |
| 2026-09-04 | Q-25 smart hybrid screened and rejected | World 294 timed out and 282 collided; close the LiCS safety branch and audit LoRR 2024 as Q-26 |
| 2026-09-04 | BallPark sandbox audit | Stock MPPI reproduced `0.95` success / `0.934` SPL on 20 dynamic seeds twice; guarded-MPPI wrapper fell to `0.85` and was rejected | Retain BallPark for cheap controller prototyping only; its new repository has no independent competition leaderboard |
| 2026-09-05 | Q-26 LoRR audit | Retrieved the official 2024 Benchmark Archive and best-solution output; fetched Start-Kit history and selected tagged `v2.0.0` rather than current 3.x | The untouched RANDOM-01 replay with the default v2.0.0 planner completed validly at 492 tasks; archived Team RAPID source built in a pinned image and was ready for Q-27 |
| 2026-09-05 | Q-27 LoRR Team RAPID replay | Exact 2024 RANDOM-01 replay completed with 690 tasks, makespan 600, and zero planner/schedule/entry errors | Protocol is locally replayable; the archived 696-task winner is not exactly reproduced, leaving a concrete six-task optimization target for Q-28 |
| 2026-09-05 | Q-28 LaCAM2 planning-window diagnostic | Changing `planning_window` from 3 to 4 reached 693 tasks but introduced two entry timeouts | Reject for promotion; the +3 gain is not robust enough to test on held-out worlds, and Q-29 must start from the zero-error Q-27 baseline |
| 2026-09-05 | Q-30 LoRR Test Round RANDOM-100 baseline | Team RAPID v2.0.0 reached 1320 tasks in 500 ticks versus the archived Team Kitty Knight reference of 1186 (+134), with zero planner/schedule errors but one entry timeout | Treat as the most promising low-cost target; repeat with a zero-timeout run before calling it a verified local beat |
| 2026-09-05 | Q-30-ref archived Team Kitty Knight replay | Exact Test Round input and v2.0.0 evaluator; archived source completed 1199 tasks with `AllValid=Yes` and no timeout/error markers | Confirms the winner source and score schema are locally runnable; runtime nondeterminism explains why the historical 1186 count is not reproduced exactly |
| 2026-09-05 | Q-31 zero-timeout RAPID confirmation | Same exact Test Round input/image/storage as Q-30; detached clean rerun launched | Host-stall diagnostic: Docker API became unresponsive before an output file was written; no score inferred. Retry after container-service recovery; timeout count remains the promotion gate |
| 2026-09-05 | Q-31 clean RAPID confirmation | Same exact Test Round input/image/storage after graceful OrbStack restart; 1318 tasks, makespan 500, zero planner/schedule/entry errors | Promote as a verified local +132 task beat over the published 1186 reference; keep official-claim boundary and move to held-out Q-32 |
| 2026-09-06 | Q-32 held-out RANDOM-02 replay | Same Team RAPID/v2.0.0 stack on the archived 200-agent, 600-tick Main Round instance; 1202 tasks versus 1260, 3 entry timeouts | Reject generalization claim; retain the declared Test Round target and require an independent clean rerun |
| 2026-09-06 | Q-33 clean Test Round confirmation | Same exact Test Round input/image/storage as Q-31; completed at 1311 tasks with five entry timeouts | Count margin reproduced but zero-error reproducibility failed; retain as runtime-sensitivity evidence |
| 2026-09-06 | Q-33 completed stress rerun | 1311 tasks versus 1186 (+125), but five entry timeouts | Count margin reproduced; zero-error reproducibility failed, so test documented thread control once and then stop iterating if unstable |
| 2026-09-07 | Q-35 pinned-runtime Test Round replay | Same exact Q-31/Q-34 input, source, image, and v2.0.0 evaluator; `OMP_NUM_THREADS=1` plus Docker `--cpuset-cpus=0`; 1325 tasks versus 1186 (+139), zero errors, 478.405 s wall time | Runtime control removed the residual timeout; retain as a clean local beat with the execution condition explicitly declared |
| 2026-09-07 | Q-36 pinned-runtime repeat | Independent fresh output directory under the exact Q-35 condition; 1325 tasks, zero errors, 477.367 s wall time, output hash identical to Q-35 | Byte-identical replay supports deterministic evidence under the pinned condition; close repeated Test Round sampling |
| 2026-09-07 | Q-37 pinned-runtime held-out RANDOM-02 | Same runtime control on untouched Main Round RANDOM-02; 1181 tasks versus 1260 (-79), zero errors, 572.793 s wall time | Clean negative control rejects a generalization claim for the unchanged RAPID planner; require a declared planner variant or organizer evaluation next |

## 9. Open brainstorm, constrained by evidence

- Q-01 confirms the GPS-assisted result locally, while Q-03 shows that broad
  performance is split between long-range acquisition and disturbed holding.
- A single public world can reward a controller that is effectively tuned to
  one goal pose, wind realization, or wave condition. Q-02 is the minimum
  breadth test; do not call `stationkeeping0` a benchmark suite.
- LoRR's entry timeout is an execution-budget event, not a task-count metric.
  Q-35/Q-36 show that explicitly pinning the amd64 container to one virtual CPU
  while keeping the default 1000 ms planner limit yields two byte-identical,
  zero-error Test Round replays. Record this runtime control as part of the
  claim instead of silently presenting it as an algorithmic improvement.
- The paired Q-37 held-out negative control is important: the same clean
  runtime condition reaches 1181 versus the published 1260 on RANDOM-02.
  Thus the strongest defensible story is a reproducible **instance-scoped
  local replay beat**, while generalization remains unproven and the unchanged
  RAPID planner is not promoted as a broad improvement.
- Compare score trajectories, not only final means. The public scorer's running
  mean is especially sensitive to early acquisition, while the task description
  calls the metric RMS and leaves `W` unpublished.
- GPS is allowed in the released public UF sensor summary, but using a sensor
  in this local public-practice controller does not make the result equivalent
  to the historical phase-3 run. Sensor availability and evaluator identity
  are separate claims.
- Robustness work should target the failure envelope: actuator saturation,
  yaw wrap, dead zones, rate limits, wind/wave disturbance, and localization
  freshness. Every new mechanism must be evaluated against a frozen baseline.
- The UF MRAC/LQ-RRT path remains the most historically faithful route. Public
  phase-3 logs make forensic reconstruction worthwhile, but missing generated
  worlds and image identities still prevent an exact historical rerun.
- The Q-02 phase-2 manifest pins the completed controller image, and its full
  six-world result and diagnostics are the frozen public robustness baseline.

## References

- [Campaign evidence ledger](../results/README.md)
- [Current-best machine-readable result](../results/practice0-fast-pd-gps.json)
- [Public six-world experiment manifest](../config/experiments/vrx2019-station-keeping-phase2.json)
- [Current-best experiment manifest](../config/experiments/vrx2019-station-keeping-practice0-fast-pd.json)
- [Q-07–Q-09 controller screen summary](../results/q07-q09-controller-screen-summary.json)
- [Q-10 observer screen summary](../results/q10-controller-screen-summary.json)
- [UF reproduction dossier](uf-2019-station-keeping-reproduction.md)
- [Public phase-2 protocol](phase2-practice-suite.md)
- [Verification README](../verification/README.md)
- [Q-03 diagnostics extractor](../scripts/extract_diagnostics)
- [Official VRX 2019 results](https://github.com/osrf/vrx/wiki/vrx_2019-results)
- [BARN 2024 rules and leaderboard](https://people.cs.gmu.edu/~xiao/Research/BARN_Challenge/BARN_Challenge24.html)
- [BARN dataset and public baseline instructions](https://www.cs.utexas.edu/~xiao/BARN/BARN.html)
- [LiCS-KI 2024 winning submission](https://github.com/damanikjosh/the-barn-challenge)
- [BARN upstream artifact audit](../results/barn-lics-upstream-public-check.json)
- [LoRR 2024 Benchmark Archive](https://github.com/MAPF-Competition/Benchmark-Archive)
- [LoRR Start-Kit](https://github.com/MAPF-Competition/Start-Kit)
- [BallPark deterministic sandbox](https://github.com/Manas-arumalla/ballpark)
- [Q-26 LoRR replay ledger](../results/lorr-q26-random01-replay.json)
- [Q-31 clean Test Round local beat](../results/lorr-q31-test-round-random100-team-rapid.json)
- [Q-35 pinned-runtime Test Round replay](../results/lorr-q35-test-round-random100-team-rapid-cpuset1.json)
- [Q-36 pinned-runtime exact repeat](../results/lorr-q36-test-round-random100-team-rapid-cpuset1-repeat.json)
- [Q-37 pinned-runtime held-out negative control](../results/lorr-q37-random02-team-rapid-cpuset1.json)
- [LoRR replay audit](lorr-2024-replay.md)
