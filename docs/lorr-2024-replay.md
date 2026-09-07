# LoRR 2024 replay audit

This audit establishes a locally runnable, externally reported robotics target
without claiming that the archived winner has already been reproduced.

## Frozen reference

The official [2024 Benchmark Archive](https://github.com/MAPF-Competition/Benchmark-Archive)
lists Main Round RANDOM-01 at 696 completed tasks for 100 agents over 600
ticks, with Team RAPID implementation
`3635cb44497727271f173582a86a2cea72e9e17e`. The untouched instance is
`RANDOM-01.json` and has SHA-256
`c09782a2d79e7779b82457095f8881b9fd5a08a6a6e4c68035a5e56a12445302`.

## Local replay

The matching [Start-Kit](https://github.com/MAPF-Competition/Start-Kit) release
is `v2.0.0` (`6425dcd720ecc79b34bc1352a77166265144482b`). The default planner
completed the untouched instance validly at 492 tasks. The archived Team RAPID
source was built with a pinned Ubuntu 22.04/Boost/spdlog image and replayed with
an explicit file-storage path:

```bash
./build/lifelong --inputFile RANDOM-01.json --simulationTime 600 \
  --output random01-rapid-600.json --fileStoragePath storage/
```

The result is recorded in
[`results/lorr-q27-random01-team-rapid.json`](../results/lorr-q27-random01-team-rapid.json):
690 tasks, makespan 600, and zero planner/schedule/entry errors. The six-task
gap to 696 is not silently rounded away. It may reflect compiler/runtime
differences or a missing competition-side detail, so any planner optimization
must use held-out instances before an optimization claim.

The archived best-solution JSON is a reference output, not a local run. A
current 3.x Start-Kit with invented delay settings is excluded from comparison
because its executor semantics differ from the 2024 protocol.

## Test Round cross-check

The same v2.0.0 evaluator and exact archived input
`random_32_32_20_100.json` (100 agents, 500 ticks) provide a cheaper second
target. The archive lists Team Kitty Knight at 1186 completed tasks. Its
archived source replayed locally at 1199 tasks with `AllValid=Yes` and no
timeout/error markers, recorded in
[`results/lorr-q30-test-round-random100-kitty.json`](../results/lorr-q30-test-round-random100-kitty.json).
This validates the source/protocol path, but not bit-for-bit determinism of the
historical count.

Team RAPID first reached 1320 tasks on the same input, but one entry timeout was
observed. Q-31 repeated it with identical image, input, 500-tick limit, and
explicit file-storage path, completing at 1318 tasks with zero planner,
schedule, or entry-timeout errors. This is a verified local +132 task beat;
Q-32 tested generalization on a held-out Main Round instance and failed the
zero-error gate; Q-34 also failed to stabilize runtime timeouts. Further work
requires a declared planner change rather than more blind reruns.

## Score-semantics verification

For LoRR 2024, the published leaderboard quantity is **total tasks finished**
for the declared agent count and simulation time. The archived winner output
and the v2.0.0 competition system both expose `numTaskFinished`, `teamSize`,
`makespan`, and error counters; there is no hidden weighted scalar comparable
to the VRX station-keeping formula. We therefore verify that the external
winner and our replay use the same task-count field and 2024 runtime schema,
but not that they produce bit-identical counts across machines. The archive's
1186 is the authoritative published reference; local 1199/1318 counts are
replay measurements, not a retroactive change to the leaderboard.
