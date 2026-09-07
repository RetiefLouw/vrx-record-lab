# LoRR 2024 improvement and validation plan

Status: planning document for the next declared LoRR experiment. Updated
2026-09-07. This file is deliberately narrower than the campaign tracker: it
focuses on the LoRR source, timeout behaviour, repeatability, and the evidence
needed before calling a result an innovation.

## Executive recommendation

The runtime-validation loop has now passed under a declared execution
condition: Q-35 and Q-36 used `OMP_NUM_THREADS=1` plus Docker `cpuset-cpus=0`
and both completed 1,325 tasks with zero errors in about 478 seconds. Their
compact output files are byte-identical. Treat this as a reproducible runtime
baseline, not as a source innovation: Q-37 used the same control on held-out
RANDOM-02 and completed cleanly but only 1,181 tasks versus the archive's
1,260.

The next experiment should therefore target density-scaled throughput and
assignment/planning quality at 200--400 agents, while retaining the pinned
runtime and a hard internal deadline as regression guards. Stable tie-breaking
and explicit seed control remain useful portability tests, but they are no
longer the highest-upside explanation for the current gap. Do not start by
increasing the planning window again: Q-28 gained only three tasks on
RANDOM-01 but incurred two entry timeouts.

Q-27 (Main Round `RANDOM-01`) stores the archive-input digest as
`instance_sha256`; that value equals the `input_sha256` recorded by Q-31,
Q-33, and Q-34 for Test Round `random_32_32_20_100.json`. The Q-30 Team RAPID
record has no input-hash field, so do not infer one from that result. The
matching digest is plausible because the official archive exposes both JSON
files with the same map, agent file, task file, team size, and reveal
multiplier; the round and simulation horizon are supplied separately. Still
recompute the digest from the exact extracted JSON used by each run and
record the round plus `simulationTime` as part of the protocol identity. If
the bytes differ from the archive, amend the result metadata or mark the
identity gate blocked. This check is more important than another favourable
rerun.

The current strongest result is Q-35/Q-36, and its strongest defensible
wording is an instance-scoped local replay comparison under a pinned runtime:

> On the exact public LoRR 2024 Test Round instance, the archived Team RAPID
> implementation completed 1,325 tasks in each of two byte-identical local
> v2.0.0 replays, versus the archive's published 1,186-task reference. Both
> runs used `OMP_NUM_THREADS=1` and Docker CPU pinning, and emitted zero
> planner, schedule, and entry-timeout errors. This is a repeatable local
> replay comparison under that runtime condition, not an official leaderboard
> result.

Q-37 strengthens the boundary: the same pinned stack completed held-out
RANDOM-02 with zero errors but 1,181 tasks versus 1,260. Thus the clean Test
Round result is still not a general algorithmic win. The source archive is the
historical Team RAPID implementation, not an LLM-created change. An innovation
claim starts only after a source/configuration diff is declared before the
run, its mechanism is explained, and the result survives held-out inputs and
independent repeats.

## Evidence baseline and boundaries

The official [2024 Benchmark Archive](https://github.com/MAPF-Competition/Benchmark-Archive/tree/25ffd5b6a39b6fe30e5bc6cb5e22720a9531ea8a/2024%20Competition)
reports these task-count references:

| Target | Archive reference | Local evidence | What it establishes |
|---|---:|---:|---|
| Main `RANDOM-01`, 100 agents, 600 ticks | 696 (Team RAPID) | Q-27: 690, zero errors | Tagged protocol replay; historical count not reproduced exactly. |
| Main `RANDOM-02`, 200 agents, 600 ticks | 1,260 (Team Kitty Knight) | Q-32: 1,202, three entry timeouts; Q-37: 1,181, zero errors | Held-out stress case; pinning removes the timeout but not the throughput/generalisation gap. |
| Main `RANDOM-03`, 400 agents, 800 ticks | 2,368 (Team No_Man's_Sky) | Not yet run | Higher-density held-out check; use only after the source variant is frozen. |
| Test `random_32_32_20_100.json`, 100 agents, 500 ticks | 1,186 (Team Kitty Knight) | Q-35/Q-36: 1,325 each, zero errors, byte-identical under `OMP_NUM_THREADS=1`, `cpuset-cpus=0`; ~478 s wall time | Clean local replay beat repeated under a declared pinned runtime; source is unchanged. |

The local ledgers are [Q-27](../results/lorr-q27-random01-team-rapid.json),
[Q-30 reference replay](../results/lorr-q30-test-round-random100-kitty.json),
[Q-31](../results/lorr-q31-test-round-random100-team-rapid.json),
[Q-32](../results/lorr-q32-random02-team-rapid.json),
[Q-33](../results/lorr-q33-test-round-random100-team-rapid.json),
[Q-34](../results/lorr-q34-test-round-random100-team-rapid-omp1.json),
[Q-35](../results/lorr-q35-test-round-random100-team-rapid-cpuset1.json),
[Q-36](../results/lorr-q36-test-round-random100-team-rapid-cpuset1-repeat.json), and
[Q-37](../results/lorr-q37-random02-team-rapid-cpuset1.json). The protocol
audit is [lorr-2024-replay.md](lorr-2024-replay.md).

The archive table is authoritative for the published references. A local
count is a replay measurement, not an official re-ranking. Q-35 and Q-36 add
important evidence: the exact same binary/configuration/input under the same
single-CPU runtime control produced the same 1,325-task output hash twice.
They also report the same binary SHA-256
`61e44618a391130db384df3285f7749931d6582cfb1b4dfa8234c3c27e5b7a05` and
configuration SHA-256
`356a1ae00629582a1927e8faf85d95df79fa4fb1459d20a3dcaa69783f283af0`.
Q-37 then cleanly fails to match the RANDOM-02 reference, so the runtime
condition explains the timeout instability but not the cross-instance
throughput gap.

### Current claim status

- **Runtime validation:** achieved for the declared arm64-host,
  `linux/amd64`, `OMP_NUM_THREADS=1`, `cpuset-cpus=0` condition. Q-35 and Q-36
  are byte-identical clean repeats.
- **Strongest local result:** 1,325 tasks versus 1,186 on the exact Test Round
  input, repeated twice with zero errors (+139 tasks per run).
- **Held-out boundary:** Q-37 is clean but 1,181 versus 1,260 on 200-agent
  RANDOM-02. The unchanged RAPID planner therefore has no broad
  generalisation claim.
- **Innovation status:** no new source innovation has yet been demonstrated;
  the next meaningful result must improve the Q-37 density/throughput gap
  while preserving the Q-35/Q-36 clean runtime condition.

## Source audit: where time and variance enter

The observations below come from the tagged
[Start-Kit v2.0.0](https://github.com/MAPF-Competition/Start-Kit/tree/6425dcd720ecc79b34bc1352a77166265144482b)
and its [submission instructions](https://github.com/MAPF-Competition/Start-Kit/blob/6425dcd720ecc79b34bc1352a77166265144482b/Prepare_Your_Submission.md).
The archived Team RAPID tree is not present in this worktree, so RAPID-specific
function names and diffs must be confirmed after fetching commit
`3635cb44497727271f173582a86a2cea72e9e17e`.

The concrete upstream locations audited are
[CompetitionSystem.cpp](https://github.com/MAPF-Competition/Start-Kit/blob/6425dcd720ecc79b34bc1352a77166265144482b/src/CompetitionSystem.cpp),
[Entry.cpp](https://github.com/MAPF-Competition/Start-Kit/blob/6425dcd720ecc79b34bc1352a77166265144482b/src/Entry.cpp),
[TaskScheduler.cpp](https://github.com/MAPF-Competition/Start-Kit/blob/6425dcd720ecc79b34bc1352a77166265144482b/src/TaskScheduler.cpp),
[MAPFPlanner.cpp](https://github.com/MAPF-Competition/Start-Kit/blob/6425dcd720ecc79b34bc1352a77166265144482b/src/MAPFPlanner.cpp),
[planner.cpp](https://github.com/MAPF-Competition/Start-Kit/blob/6425dcd720ecc79b34bc1352a77166265144482b/default_planner/planner.cpp),
[flow.cpp](https://github.com/MAPF-Competition/Start-Kit/blob/6425dcd720ecc79b34bc1352a77166265144482b/default_planner/flow.cpp), and
[search_node.h](https://github.com/MAPF-Competition/Start-Kit/blob/6425dcd720ecc79b34bc1352a77166265144482b/default_planner/search_node.h).

### The deadline is shared across scheduler and planner

In v2.0.0, `BaseSystem::plan()` starts `Entry::compute()` on a worker thread
and waits for `planTimeLimit`. If the previous worker is still running, it
waits again and records a planner timeout if it still has not finished. The
worker is not cancelled. A single overrun can therefore overlap the next
planning episode and create a timeout cascade.

The default [Entry.cpp](https://github.com/MAPF-Competition/Start-Kit/blob/6425dcd720ecc79b34bc1352a77166265144482b/src/Entry.cpp)
calls the scheduler and then the planner. Both receive the top-level limit,
but the limit is measured from `env->plan_start_time`; the scheduler's default
wrapper reserves half for scheduling and the planner uses the time remaining
after scheduling. The [input/output contract](https://github.com/MAPF-Competition/Start-Kit/blob/6425dcd720ecc79b34bc1352a77166265144482b/Input_Output_Format.md)
states that an over-time planner causes wait actions for that timestep. A
candidate must therefore return before the deadline with a fully sized,
valid action vector; an empty or partially filled vector is not a safe
fallback.

### The default planner spends a wall-clock budget in several phases

The v2.0.0 default planner uses a traffic-flow/Frank–Wolfe phase, route
updates using A* and cached heuristics, and then causal PIBT action selection.
The source computes an end time by subtracting a PIBT reserve and a timing
tolerance. `frank_wolfe()` continues while the wall clock is before its
deadline and may invoke `update_traj()` repeatedly. This is a good place for
an allowed planner implementation to add a bounded iteration count, an early
deadline guard before each expensive route update, and an explicit reserve for
the final valid-action pass.

The default scheduler is a nested greedy loop over free agents and unreached
tasks. It computes a route-distance estimate for each candidate task. On a
large task pool this can consume the budget before path planning begins. An
allowed scheduler implementation can cache task summaries and score a small,
deterministically ordered candidate shortlist, but should first measure the
stage split rather than assume scheduling is the bottleneck.

### There are avoidable sources of nondeterminism in the reference code

The v2.0.0 source seeds `rand()`/`mt19937` to zero in the default planner, but
that does not make a wall-clock-bounded search deterministic. More
importantly, `default_planner/search_node.h` uses `rand() % 2` inside two
`std::sort` comparison paths when all keys tie. A comparator that changes its
answer between calls is not a strict weak ordering, so its ordering and work
can vary with compiler, library, and timing. Other tie-breakers are generated
from global `rand()` state; the flow and PIBT sorts then depend on those
runtime-generated keys. The default `ids` sort also has no final agent-id
tie-break when priorities are equal.

These files are listed as unmodifiable by the official
[evaluation-environment rules](https://github.com/MAPF-Competition/Start-Kit/blob/6425dcd720ecc79b34bc1352a77166265144482b/Evaluation_Environment.md).
Do not patch the evaluator or protected default planner tree and call the
result an official submission. If the selected track allows a replacement
planner, implement stable keys in that planner; otherwise treat this as an
upstream/runtime confound and report it. In either case, seed control is a
measurement factor, not permission to choose the luckiest seed after seeing
the score.

### Runtime pinning is now a validated control condition

Q-35 and Q-36 held source, binary, configuration, input, v2.0.0 evaluator,
image, `OMP_NUM_THREADS=1`, and `cpuset-cpus=0` fixed. Both ran on the same
arm64 host under `linux/amd64` emulation for about 478 seconds, completed 500
ticks at 1,325 tasks, reported zero planner/schedule/entry timeouts, and
produced the same compact output SHA-256. This validates the practical
reproduction condition used by the local dossier: CPU/thread pinning is now a
control, not an unresolved hypothesis.

It does not prove portability to the official x86_64 evaluation VM, and it is
not itself an algorithmic improvement. Q-37 is the key counter-check: the
same control produced a clean 1,181 tasks on 200-agent RANDOM-02 versus the
1,260 archive reference. Future source work should keep the Q-35/Q-36 runtime
condition frozen so that throughput changes are not confounded by host
scheduling.

### Track constraints matter

The official rules permit a planner-track submission to implement the planner
only, a scheduler-track submission to implement the scheduler only, and a
combined-track submission to implement both plus `Entry`. The next source
change must state its track and list the exact files changed. In particular,
changing the evaluator's timeout handling, simulator, task manager, or score
field would invalidate the comparison.

## Ranked improvement hypotheses

Ranking is now by expected information and cross-instance throughput under the
validated Q-35/Q-36 runtime condition. Timeout reduction remains a hard safety
constraint, but it is no longer the primary score hypothesis: pinning removed
timeouts on Q-37 without recovering its 79-task deficit. Impact is the
plausible upside if the mechanism is the actual bottleneck, not a prediction of
a leaderboard result.

| Rank | Hypothesis / concrete change | Expected impact | Cost | Risk / falsifier | First test |
|---:|---|---|---|---|---|
| 1 | **Density-scaled assignment and planning.** Treat agent count and task-pool density as first-class inputs. Use bounded queue-aware assignment, preserve good assignments with hysteresis, and allocate work so the 200/400-agent cases do not inherit the 100-agent schedule assumptions. | High potential throughput gain on Q-37/RANDOM-02 and later RANDOM-03; directly targets the clean 79-task gap. | High | Assignment churn or extra scoring can consume the budget and create schedule errors. Reject if the Test Round regresses or any held-out integrity error appears. | One scheduler or combined-track variant on RANDOM-02, then RANDOM-03. |
| 2 | **Incremental route/heuristic reuse with density-aware work caps.** Replan only agents whose goal, state deviation, or conflict neighbourhood changed; cache task summaries and cap A*/flow work per timestep as agent count rises. | Medium-to-high speedup at 200--400 agents; more time for valid final actions. | High | Stale routes, invalidation bugs, and hidden starvation can reduce completed tasks. | Test Round control followed by Q-37 conditions; instrument p95 stage time. |
| 3 | **Conflict-hotspot and deadlock recovery.** Use short-lived corridor/intersection reservations, deterministic priority boosts, and a bounded recovery action when progress stalls. | Medium-to-high gain on dense RANDOM-02/03 if congestion is causal. | High | A global shield can reduce throughput; reject if waits rise without fewer conflicts or if the Test Round loses its margin. | RANDOM-02 development screen, then RANDOM-03. |
| 4 | **Adaptive planning window and stage budget.** Keep window 3 as baseline; use window 2 under high occupancy/low slack and window 4 only with measured headroom. Bound flow iterations and reserve the final action-validity pass. | Medium gain if Q-28's extra planning work was useful; protects the now-clean timeout condition. | Medium | Q-28's two timeouts are the warning. Reject any candidate with a worse zero-error rate, even if its best count rises. | Paired Test Round and RANDOM-02 runs under cpuset1. |
| 5 | **Hard-deadline planner with valid fallback.** Give scheduler, route-update, flow, and PIBT stages explicit sub-budgets; commit a new plan only when complete and collision-checked; otherwise return a validated prior action or waits. | High integrity value; score upside is now secondary because pinning already removes observed timeouts. | Medium | A wait fallback can lose tasks. Keep as a guardrail unless a source variant reintroduces timeouts. | Unit tests plus one regression run on Test Round and RANDOM-02. |
| 6 | **Deterministic priority and tie-breaking.** Replace random comparator decisions with precomputed keys such as `(cost, progress, last_replan, agent_id)` or a declared hash. Never call RNG from a comparator; expose seed metadata. | Medium portability and repeatability value; lower immediate score upside after Q-35/Q-36. | Medium | If output remains byte-identical only under one host, cross-platform variance remains unresolved. | Test Round and RANDOM-02, seeds 0/1/2/17/42. |
| 7 | **Runtime/thread discipline as a frozen control.** Keep CPU affinity, `OMP_NUM_THREADS=1`, fresh storage, and environment capture. Do not treat further pinning as an innovation. | Evidence quality and repeatability; no algorithmic claim. | Low | Different host/architecture may still vary. Keep the condition explicit in every result. | Use Q-35/Q-36 as the control for every candidate. |
| 8 | **Seed or instance-specific tuning.** Search seeds, windows, or thresholds until one run looks best. | Low scientific value; can make a demo look better. | Low | Overfitting/cherry-picking unless preregistered and held-out confirmed. Never promote by itself. | Robustness appendix only. |

## Source-change design for the first variant

The first score-seeking candidate should be one cohesive, reviewable
density-scaled assignment/planning change, not a rewrite of the evaluator. It
should preserve the validated Q-35/Q-36 runtime controls and the deadline
contract below as guardrails. If source inspection shows that the archived
RAPID code already contains a queue-aware branch, select incremental route
reuse or conflict-hotspot recovery instead; do not relabel an existing RAPID
mechanism as a new innovation.

The deadline/fallback contract is:

```text
at compute entry:
  deadline = env.plan_start_time + top_level_limit - safety_margin
  actions = last_valid_actions or all waits
  schedule = last_valid_schedule

run only bounded scheduler work while now < scheduler_deadline
refresh goals and route candidates only while now < route_deadline
run bounded flow/A* work only while now < flow_deadline
run final collision-safe action selection before final_deadline

if the candidate action vector is complete and valid:
  commit it and its schedule
otherwise:
  return the previously validated vector or waits
```

The implementation should keep the safety margin conservative at first (for
example, 10--20 ms on the 2024 millisecond budget) and measure the actual
slack before tuning it. It should not silently increase the official
`planTimeLimit`, detach work, alter signal handlers, or modify protected
evaluator files. The fallback path must be tested with synthetic near-deadline
unit cases, including zero available route time, an empty task pool, a changed
goal, and a conflict at the first action.

For instrumentation, retain in memory and emit after the run (not on every
hot-loop iteration): scheduler milliseconds, route/heuristic milliseconds,
flow iterations, PIBT milliseconds, remaining slack, number of agents
replanned, fallback count, and timeout timestep. The official output already
contains `plannerTimes`, `plannerPaths`, `actualPaths`, schedules, events,
`errors`, and `scheduleErrors`; those fields should be retained in the raw
artifact rather than summarized away.

## Experiment matrix

The order below separates identity, runtime variance, source hypotheses, and
held-out confirmation. A run is not a seed if the source does not record the
seed; record the actual mechanism that controls ordering.

| ID | Build / factor | Development input | Held-out input | Repeats | Keep / reject rule |
|---|---|---|---|---:|---|
| A0 | Recompute exact extracted JSON hashes; verify archive path, map, agents, tasks, round, and command | None | None | 1 | Verify Q-27 `instance_sha256` against Q-31/Q-33/Q-34 `input_sha256`; Q-30 Team RAPID has no input-hash field. Accept the digest match only after confirming the archive JSONs are byte-identical; always record round and `simulationTime`. |
| A1 | Frozen Team RAPID image/source; `OMP_NUM_THREADS=1`; Docker `cpuset-cpus=0`; exact input/storage/command | Test Round | None | 2 | **Completed:** Q-35/Q-36 both 1,325 tasks, zero errors, same output SHA, ~478 s. Runtime pinning validation achieved. |
| A2 | Same frozen build and pinned runtime as A1 | None | RANDOM-02 | 1 | **Completed:** Q-37 1,181 vs 1,260, zero errors. Clean held-out control; generalisation/throughput gate fails. |
| A3 | Optional extra frozen baseline repeats under A1 controls | Test Round | None | 3 | Use only for a five-run distribution claim; never discard Q-35/Q-36 or pick the best count. |
| B1 | Queue-aware, density-scaled assignment only; preserve assignments with hysteresis | Test Round | RANDOM-02 | 3 | Advance only if all Test Round repeats are clean and the held-out count improves materially over Q-37 without errors. |
| B2 | Incremental route/heuristic reuse and density-aware work caps only | Test Round | RANDOM-02 | 3 | Require measured p95 stage-time reduction, zero errors, and no material loss versus A1. |
| B3 | Conflict-hotspot/deadlock recovery only | Test Round | RANDOM-02, then RANDOM-03 | 3 | Advance only if conflicts/waits fall and throughput improves on dense held-out input. |
| B4 | Adaptive window 2/3/4 with a fixed deterministic policy plus deadline fallback | Test Round | RANDOM-02 | 3 | Reject any timeout increase, even if one count is higher; Q-28 remains the negative control. |
| B5 | Deterministic tie-breaks and declared seed handling only | Test Round | RANDOM-02 | 2/seed | Report the full seed distribution; use for portability, not best-seed selection. |
| C1 | Frozen finalist; no more tuning | Test Round | RANDOM-01, RANDOM-02, RANDOM-03 (where inputs are available) | 5 / 3 each | Final held-out dossier; report all trials, not only the best. |
| C2 | Frozen finalist from a fresh checkout and independently recreated image | Same as C1 | Same as C1 | 2 each | Independent replication gate; preserve build logs and digests. |

### Seed protocol

Use seed 0 as the legacy/canonical condition when comparing the archived
source. If the source is changed to expose a seed, preregister the sequence
`0, 1, 2, 17, 42` before looking at results. Run each seed at least twice for
screening and repeat the finalist with fresh processes. Report the median and
full range, not the maximum. A seed is a robustness factor; it is not a new
benchmark instance. If the official interface does not expose a seed, retain
the source's documented seed and report runtime variance separately.

### Interleaving and stopping

Interleave baseline and candidate processes (for example B, C, B, C) to
reduce host-load confounding. Use the same image digest, exact input bytes,
storage path policy, CPU/thread settings, and simulation ticks. Stop a
candidate immediately for a planner error, schedule error, invalid action, or
repeated timeout cascade; retain the incomplete artifact as evidence. Never
rerun a frozen binary until a clean sample appears and then discard the
unfavourable runs.

## Validation gates

| Gate | Requirement | Evidence to retain |
|---|---|---|
| V0 identity | Test Round and Main Round extracted JSONs are independently verified against the archive. Record Q-27 as `instance_sha256`, Q-31/Q-33/Q-34 as `input_sha256`, and Q-30 Team RAPID as having no input-hash field. A digest match is acceptable only when the archive files are byte-identical; round and `simulationTime` must still be recorded. | Hash manifest plus a short identity report. |
| V1 protocol | Start-Kit exactly `v2.0.0` (`6425dcd…`), correct team size/ticks, unchanged evaluator and score field, explicit storage path, source commit, image digest. | Command line, git tree hashes, image digest, environment snapshot. |
| V2 source legality | The candidate changes only files allowed by its declared track. No evaluator, simulator, task-manager, signal-handler, or score-field edits. | Patch/diff and track declaration. |
| V3 clean episode | Every returned action vector is complete and valid; `numPlannerErrors = 0`, `numScheduleErrors = 0`, `numEntryTimeouts = 0`. | Raw output, log scan, and verifier result for each trial. |
| V4 repeatability | **Runtime pinning sub-gate passed:** Q-35/Q-36 are two independent exact repeats under fixed source/binary/config/input, `OMP_NUM_THREADS=1`, and `cpuset-cpus=0`; both are clean and byte-identical. Five repeats remain recommended for a distribution/CI claim. | One row per run; same output SHA and environment metadata for Q-35/Q-36; no selective omission. |
| V5 development effect | A declared variant beats or stabilizes its paired baseline under the same input and seed. The next source variant must preserve the clean A1 condition and improve dense-instance throughput, not merely remove timeouts. | Paired table, source diff, predeclared hypothesis, stage timings. |
| V6 held-out generalization | After freezing the variant, evaluate untouched Main Round instances. Q-37 is a clean held-out control but fails the task-count reference (1,181 vs 1,260). A broad algorithmic claim requires zero errors and a non-negative paired effect on every held-out input; ideally meet each archive reference (696, 1,260, 2,368 where applicable). | Held-out raw outputs and all failures. |
| V7 independent replay | Fresh checkout/process and independently recreated environment reproduce the direction of the result. A second host is stronger than a second run on one host. | Build log, digest, hashes, output checksum, environment details. |
| V8 claim discipline | Wording names the exact input, runtime, source, count, error status, and local/official scope. | Final dossier and HTML link to raw evidence. |

The clean local-beat threshold for this project is at least 1,186 tasks on the
Test Round with zero errors. Q-35/Q-36 now pass the two-run pinned-runtime
repeatability gate at 1,325 tasks each, with byte-identical output and about
478 seconds wall time. Five out of five clean runs and a lower bound at or
above 1,186 remain the recommended stronger distribution claim. Q-37 passes
the clean-error part of the held-out gate but scores 1,181 versus the 1,260
archive reference, so generalisation is still rejected. The stronger
algorithmic threshold is not a single Test Round count: it requires a
declared code change, paired baseline, zero-error held-out results, and
independent replay.

## Evidence visualisations for the dedicated LoRR HTML

The page should make the evidence boundary visible instead of showing only a
large number. These figures can be generated from the raw JSON outputs once
the full `plannerTimes`, paths, schedules, and logs are retained:

1. **Count versus reference:** a dot/interval plot by input and run, with a
   horizontal archive-reference line and red timeout markers. Show Q-35/Q-36
   as the repeated 1,325-task pair, then Q-37 as the clean but below-reference
   held-out result; retain Q-31/Q-33/Q-34 as the pre-pinning controls.
2. **Cumulative completions:** task completions over simulation timestep for
   baseline and candidate. Annotate the first timeout and reveal/assignment
   events; this distinguishes throughput from a late-run lucky burst.
3. **Deadline budget stack:** per-episode scheduler, route, flow, PIBT, and
   slack milliseconds, with the top-level deadline line. Use p50/p95/p99 and
   the number of episodes crossing the margin.
4. **Repeatability matrix:** rows are runs, columns are seed/input; each cell
   contains `tasks / planner errors / schedule errors / entry timeouts`.
   Highlight the byte-identical Q-35/Q-36 cells and the clean Q-37 cell. This
   makes the effect of runtime pinning visible without calling it innovation.
5. **Held-out generalisation bars:** candidate and archive reference for
   RANDOM-01/02/03, with an adjacent error-count strip. Do not combine counts
   from different team sizes into one score.
6. **Innovation chain:** source diff → intended mechanism → measurable
   observable → task-count result → claim allowed. This prevents an archived
   source replay from being mistaken for a newly invented method.

## Honest claim language

### Allowed now, after the V0 identity check

> We locally replayed the archived Team RAPID implementation on the exact
> public LoRR 2024 Test Round protocol. Under `OMP_NUM_THREADS=1` and Docker
> `cpuset-cpus=0`, two independent Q-35/Q-36 runs each completed 1,325 tasks
> versus the archive's published 1,186-task reference, with zero planner,
> schedule, and entry-timeout errors and byte-identical compact output. This
> is a repeatable instance-scoped local replay comparison under a declared
> runtime condition, not an official leaderboard result.

### Allowed if a source variant passes and held-out gates are met

> We implemented a declared density-scaled planner/scheduler change in the
> permitted [track]. Against the pinned Q-35/Q-36 runtime baseline, the
> variant improved completed-task throughput on the held-out 200-agent
> RANDOM-02 case without introducing planner, schedule, or entry-timeout
> errors, and preserved the Test Round result. The result is an independently
> reproducible local algorithmic improvement; it is not an official
> leaderboard re-ranking unless accepted by the organizers.

### Not allowed from the current evidence

- “We won LoRR.”
- “We beat Team RAPID generally.”
- “We set the 2024 record” or “we are SOTA.”
- “The LLM invented the winning planner,” when the run is the unchanged
  archived Team RAPID source.
- “The result is deterministic on all machines”; the evidence supports only
  byte-identical replay under the declared pinned runtime.

## References and implementation checklist

- [LoRR 2024 archive and reference table](https://github.com/MAPF-Competition/Benchmark-Archive/tree/25ffd5b6a39b6fe30e5bc6cb5e22720a9531ea8a/2024%20Competition)
- [Start-Kit v2.0.0 release](https://github.com/MAPF-Competition/Start-Kit/releases/tag/v2.0.0)
- [Start-Kit v2.0.0 timing/source files](https://github.com/MAPF-Competition/Start-Kit/tree/6425dcd720ecc79b34bc1352a77166265144482b)
- [Start-Kit evaluation restrictions](https://github.com/MAPF-Competition/Start-Kit/blob/6425dcd720ecc79b34bc1352a77166265144482b/Evaluation_Environment.md)
- [LoRR replay audit](lorr-2024-replay.md)
- [Campaign tracker](CAMPAIGN.md)
- [Q-35 pinned Test Round replay](../results/lorr-q35-test-round-random100-team-rapid-cpuset1.json)
- [Q-36 byte-identical pinned repeat](../results/lorr-q36-test-round-random100-team-rapid-cpuset1-repeat.json)
- [Q-37 clean held-out RANDOM-02 control](../results/lorr-q37-random02-team-rapid-cpuset1.json)

Before implementation begins:

1. Recompute and document the digest field mapping: Q-27's
   `instance_sha256` equals the Q-31/Q-33/Q-34 `input_sha256` value, while the
   Q-30 Team RAPID record has no input-hash field. Include the round and
   `simulationTime` fields that distinguish the two protocols.
2. Fetch and pin the full Team RAPID source tree; record its tree hash and
   track (planner, scheduler, or combined).
3. Preserve Q-35/Q-36 as the frozen pinned-runtime controls, including their
   identical output hash, binary/configuration hashes, and ~478-second wall
   time. Add three more only if a five-run distribution claim is needed.
4. Declare one source change (B1, B2, or B3), its expected density/throughput
   observable, seed set, and stopping rule in the ledger before running it.
5. Evaluate the source variant on Test Round first, then freeze and run
   RANDOM-02/RANDOM-03 as held-out confirmation. A successful variant must
   improve the clean Q-37 throughput gap, not just reproduce Q-35/Q-36.
6. Only after those gates pass should the dedicated HTML explainer present the
   variant as LLM-guided innovation; keep Q-35/Q-36 labelled as runtime
   validation of the archived source.
