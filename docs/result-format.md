# Experiment and result format

The harness has two JSON documents:

- `config/experiments/*.json` is an immutable experiment manifest. It records
  the benchmark and scorer revisions, controller source and parameters,
  container image/digest, task settings, explicit seeds, environment values,
  and the external adapter command.
- `result.json` is the canonical output of `scripts/run_suite`. Its schema is
  `schemas/result.schema.json` and it contains one normalized trial record per
  seed, aggregate statistics, provenance, artifact SHA-256 values, and an
  initially-false verification state.

Scores are calculated only from completed trials. For VRX's lower-is-better
score direction, `worst_case` is the largest trial score. Standard deviation is
the sample standard deviation. The 95% interval is a two-sided Student-t
interval; a one-trial interval is degenerate because its variance is zero.

## Adapter contract

`execution.command` is a list of executable tokens. The runner substitutes
these placeholders in individual tokens:

| Placeholder | Value |
|---|---|
| `{seed}` | trial seed |
| `{trial_id}` | stable per-suite trial identifier |
| `{output}` | absolute path for the trial JSON |
| `{artifact_dir}` | absolute directory for raw state/log artifacts |
| `{manifest}` | absolute manifest path |

The runner also exports `VRX_TRIAL_SEED`, `VRX_TRIAL_OUTPUT`,
`VRX_TRIAL_ARTIFACT_DIR`, `VRX_EXPERIMENT_MANIFEST`, and JSON-encoded task,
environment, and controller parameters. The adapter must either write a JSON
object to `VRX_TRIAL_OUTPUT` or emit exactly one JSON object on stdout. A
completed adapter object must include:

```json
{
  "completed": true,
  "score": 0.0,
  "score_components": {},
  "real_time_factor": null,
  "environment": {},
  "metrics": {}
}
```

The harness records adapter stdout/stderr and every regular file below the
artifact directory. It never computes a simulator score, launches a missing
simulator, or turns a fixture into a benchmark result.

## Commands

From a checkout:

```sh
scripts/run_trial config/experiments/your-run.json --seed 1 \
  --output results/runs/your-run/trial.json
scripts/run_suite config/experiments/your-run.json \
  --output-dir results/runs/your-run
scripts/verify_result results/runs/your-run/result.json \
  --manifest config/experiments/your-run.json \
  --write --output results/runs/your-run/verification.json
```

`verify_result` fails when an artifact is missing or modified, checksums do not
match, the aggregate has drifted from the per-trial scores, the manifest hash
does not match, any benchmark/controller/container revision is unpinned, or
the suite is incomplete. `--write` may be used to persist the verification
report after a successful audit; it does not make missing provenance valid.
`--output` writes the same report as a standalone JSON sidecar. Use both flags
for retained performance runs so the canonical result and an independently
readable verifier report cannot silently disagree.

`claim_eligible` in this schema means that the local structural, identity, and
artifact checks passed. It does not establish historical comparability,
clean-clone independence, third-party recognition, or record eligibility;
those remain separate campaign gates. New verifier reports make that explicit
with `claim_scope: local_result_integrity_only` and
`record_claim_eligible: false`.

The checked-in upstream manifest deliberately has an empty adapter command and
null historical revisions. This is an explicit unavailable-state fixture until
protocol archaeology supplies those values; it is not a benchmark result.

## Historical VRX 2019 aggregation

The reconstructed 2019 station-keeping comparator is stricter than the
engineering aggregate above. It requires exactly six complete trial records;
failed, timed-out, invalid, or missing trials cannot be dropped before taking
the task score. The task score is the unrounded arithmetic mean of those six
run scores, with lower scores better. The official public log bucket exposes
UF's exact phase-3 trial scores, but it does not expose enough evaluator and
generated-world identity to make a public phase-2 result directly comparable
to phase 3. Six-run validation alone is therefore insufficient.

Use the strict helper/CLI when checking a six-run vector or canonical result:

```sh
scripts/aggregate_2019 0.02 0.04 0.35 0.04 0.10 0.11
scripts/aggregate_2019 --result results/runs/vrx2019-phase2-public/result.json
scripts/aggregate_2019 --result candidate/result.json --reference reference/result.json
```

The command rejects a vector with the wrong number of runs or a canonical
result with any incomplete trial. `compare_vrx2019_results` additionally
reports evaluator/protocol identity mismatches instead of treating two
six-run results as directly comparable.
