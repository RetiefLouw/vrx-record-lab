# Contributing

Changes to benchmark code, scoring, or task definitions must remain separate
from controller changes and must never be used for a record claim. Every
reported run must identify its source commit, container digest, configuration,
seeds, raw outputs, and checksums.

Do not commit credentials, rented-instance state, large bags, or videos.

Before promoting a run, update `verification/benchmark_paths.json` with the
exact benchmark and scorer roots used by the evaluator. Run the checks in the
README and attach a completed `docs/audit-report-template.md` to the result
record. A check that reports `vacuous: true` is a configuration warning, not
evidence that an external benchmark tree was protected.
