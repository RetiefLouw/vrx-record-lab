# VRX station-keeping campaign tracker

Status: active public-practice performance campaign  
Last updated: 2026-09-03  
Canonical tracker: this file is the single plan, progress log, experiment queue, and decision register for measured VRX station-keeping performance.

This tracker covers controller performance, evaluator integrity, and evidence
quality. It deliberately excludes presentation/media work.

## 1. Objective and claim boundaries

### Objective

Build the strongest independently reproducible VRX 2019 station-keeping result
that can be measured on the public simulator, then determine whether the
historical phase-3 protocol is recoverable enough for a directly comparable
six-trial claim.

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
The exact phase-3 worlds, seeds, container/dependency revisions, scorer binary,
and raw logs are not available in the public record located for this campaign.

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
| Status | Completed public-practice task result; independently unverified |
| Claim allowed | Public-practice result only; not phase-3, SOTA, record, or UF reproduction |

The result passed local schema, artifact SHA-256, checksum-manifest,
aggregate, experiment-manifest, pinned-identity, and completed-trial checks.
The result's own verification record keeps `independent_clean_rerun` pending
and `claim_eligible` false. Its `compute_cost_usd` is recorded as `0.0`
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
| done | Campaign lead | Establish current-best ledger | `results/practice0-fast-pd-gps.json`; local result and checksum files | Q-01 independent clean rerun |
| done | Verification | Validate current-best local result | Schema, artifacts, aggregate, manifest, pinned identity, and completion checks pass; independent rerun pending | Record the verifier output beside the rerun |
| next | Independent runner | Re-run current best from a clean clone/container on seed 10 | New result directory with fresh image digest, full logs, bag, task info, and SHA-256 manifest | Same controller/config identity; no missing messages; score and protocol match Q-01 |
| next | Evaluation | Run the fixed fast-PD controller across all six public phase-2 worlds | Six complete trial records under one immutable suite result | Six/ six finished trials; no world/seed drift; aggregate and artifacts verify |
| next | Controller | Diagnose cross-world failure modes before tuning | Per-world position acquisition time, saturation time, steady-state error, yaw error, and score decomposition | Choose one hypothesis from Q-03/Q-04; do not tune against a single scalar alone |
| next | Controller | Run preregistered sensing/feedback ablations | One result per queue row; fixed worlds and evaluator identity | Improvement must hold on held-out public worlds, not just `stationkeeping0` |
| hold | Protocol | Recover exact UF VRX and vrx-docker gitlink objects | UF pointers `8c204f359effb8ab810fac6b57ebc46d13dcaf3a` and `5c9928d6d059cf6aef398b9f3bcbc2c1935a3ef4` are currently unavailable | External source recovery or organizer-provided archive |
| blocked | Historical comparison | Reproduce UF phase-3 six-run vector | Exact worlds, seeds, timing, scorer, image, and raw logs | All missing phase-3 inputs restored and independently hashed |
| hold | Promotion | Prepare accepted claim dossier | Audit template, result, artifacts, clean-clone and protected-tree checks | Gates G1–G5 all pass; otherwise label as public-practice only |

## 4. Ranked approaches

Ranking is by expected information per unit compute, with measurement validity
before controller optimization.

1. **Independent rerun of the current best.** The `0.0083` result is too large
   an improvement over `0.5016` to accept without a fresh clean-clone run. This
   is the fastest way to distinguish a real sensing/wiring improvement from a
   stale-artifact, startup, or evaluator-state issue.
2. **Complete the six public-world suite with the controller frozen.** This
   measures robustness to the known phase-2 wind/wave/goal variations and
   prevents overfitting to `stationkeeping0`.
3. **Break down acquisition versus hold.** The prior baseline shows that early
   acquisition can dominate a 300-second mean. Report time-to-radius, actuator
   saturation, peak yaw error, and steady-state error before changing gains.
4. **Pre-registered sensing ablations.** Compare GPS position feedback,
   localization odometry, and fused/filtered variants under the same stock
   thruster mapper. Keep the evaluator untouched and use held-out worlds for
   selection.
5. **Robust disturbance handling.** Only after the fixed six-world result is
   established, test observer/adaptation, anti-windup, rate/dead-zone handling,
   and gain scheduling. Use failure recovery and worst-world score as primary
   diagnostics.
6. **Source-faithful UF MRAC/LQ-RRT path.** This is historically relevant but
   lower short-term value: the external trajectory producer, exact submodules,
   and phase-3 evaluator remain incomplete. Pursue it when the missing source
   objects are recovered or when the public controller work has plateaued.
7. **Remote/GPU scale-out.** Use Vast.ai only for a bounded, reproducible batch
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
| Q-01 | Is the `0.0083` result reproducible? | Controller `fast-pd-v1-2026-09-03`; manifest [`vrx2019-station-keeping-practice0-fast-pd.json`](../config/experiments/vrx2019-station-keeping-practice0-fast-pd.json); VRX/scorer `a62df111`; seed 10; `stationkeeping0`; 10/10/300 s | Two fresh clean-clone/container runs, including the full raw artifact set and independent verification | Pass only if both trials finish, identities match, no controller crash occurs, and scores are consistent with the original within a predeclared engineering tolerance. A mismatch opens a diagnostic row; it does not get averaged away. |
| Q-02 | Does the current best generalize across the public suite? | Same controller, gains, image, scorer, and 10/10/300 s timings; suite [`vrx2019-station-keeping-phase2.json`](../config/experiments/vrx2019-station-keeping-phase2.json); worlds/seeds 0–5 as pinned by that manifest | One complete six-world suite; no gain or code changes between worlds | Pass means six/ six completed trials, all artifacts verify, and the result is labelled public-practice only. Use the six-world aggregate as the frozen baseline for later ablations. |
| Q-03 | Is the improvement acquisition-driven? | Controller and evaluator frozen at Q-02; diagnostic extraction only | Recompute per-world time-to-`0.25 m`, time-to-`0.5 m`, peak actuator saturation, max yaw error, and first/last 30-second error from bags/task info | Produces a causal diagnosis. No score claim is made from this row. |
| Q-04 | Does GPS feedback, not PD tuning, explain the jump? | Same controller gains and stock mapper; swap only position source between GPS and localization odometry; same six worlds and fresh output directories | Paired six-world runs with source order randomized before execution; record topic health and latency | Prefer the source that improves the held-out aggregate without increasing failures, saturation, or protocol ambiguity. |
| Q-05 | Can disturbance handling improve the held-out public suite? | Freeze Q-02 best controller and scorer; choose observer/adaptation change before seeing Q-02 world scores | Development seeds/worlds declared before the run; evaluation worlds held out and disjoint; maximum two candidate variants | Accept only if the held-out aggregate and worst-world score improve and all verification gates pass. |
| Q-06 | Is historical UF comparison recoverable? | Exact UF tag/submodules, event-era server, phase-3 worlds, six seeds, and scorer binary when/if recovered | Rebuild from hashes, record all dependencies, run six trials, independently recompute both public scoring interpretations | If any required artifact remains unavailable, report blocked; never substitute phase-2 worlds and call it phase-3 reproduction. |

### Queue execution rules

- Q-01 is the only performance run allowed before the current-best identity is
  independently confirmed.
- Q-02 freezes the first broad public baseline. Do not select a controller
  variant from Q-02's six scores and then reuse those same worlds as an
  unbiased evaluation set.
- Q-04 is a paired ablation, not a new best claim. Topic availability,
  timestamp freshness, and frame conversion must be logged for every trial.
- Any failed or timed-out trial is retained as evidence and reported as
  incomplete; no score is fabricated or silently dropped.

## 6. Acceptance gates

| Gate | Requirement | Evidence required | Current state |
|---|---|---|---|
| G1 — identity | Exact controller commit/config, VRX/scorer revision, container digest, OS/runtime identity | Manifest plus SHA-256/checksum files | Local current-best pass; clean rerun pending |
| G2 — protocol | Correct world, seed, Initial/Ready/Running timing, goal topic, score topic/field, and complete 300-second run | Trial protocol, task-info stream, launch metadata, raw bag/logs | Pass for public `stationkeeping0`; phase-3 unknown |
| G3 — independent rerun | A fresh clean clone and fresh container reproduce the declared result without reusing mutable artifacts | Independent result directory and verifier output | Pending Q-01 |
| G4 — breadth | All six public worlds complete under one frozen controller/evaluator identity | Six trial records, aggregate, per-world diagnostics | Pending Q-02 |
| G5 — integrity | Schema, aggregate arithmetic, artifact bytes, manifest, seeds, protected benchmark/scorer tree, and clean-clone checks pass | Machine-readable result plus audit report | Local current-best verification pass except independence; promotion blocked |
| G6 — historical comparability | Exact phase-3 inputs and scorer are restored; six reproduced scores are compared with the published vector | Hashes, build logs, six raw trials, independent score recomputation | Blocked by unavailable evaluator artifacts |
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

## 9. Open brainstorm, constrained by evidence

- The GPS-assisted jump may be real because the prior baseline spent much of
  the scored interval acquiring the goal, but it may also expose a topic/frame
  or initialization difference. Q-01 and Q-03 must answer that before any gain
  search.
- A single public world can reward a controller that is effectively tuned to
  one goal pose, wind realization, or wave condition. Q-02 is the minimum
  breadth test; do not call `stationkeeping0` a benchmark suite.
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
- The UF MRAC/LQ-RRT path remains the most historically faithful route, but it
  should not displace Q-01/Q-02: missing submodules and phase-3 artifacts are
  external blockers, not reasons to spend unbounded compute on a surrogate.

## References

- [Campaign evidence ledger](../results/README.md)
- [Current-best machine-readable result](../results/practice0-fast-pd-gps.json)
- [Public six-world experiment manifest](../config/experiments/vrx2019-station-keeping-phase2.json)
- [Current-best experiment manifest](../config/experiments/vrx2019-station-keeping-practice0-fast-pd.json)
- [UF reproduction dossier](uf-2019-station-keeping-reproduction.md)
- [Public phase-2 protocol](phase2-practice-suite.md)
- [Verification README](../verification/README.md)
- [Official VRX 2019 results](https://github.com/osrf/vrx/wiki/vrx_2019-results)
