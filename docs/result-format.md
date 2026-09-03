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
  --manifest config/experiments/your-run.json
```

`verify_result` fails when an artifact is missing or modified, checksums do not
match, the aggregate has drifted from the per-trial scores, the manifest hash
does not match, any benchmark/controller/container revision is unpinned, or
the suite is incomplete. `--write` may be used to persist the verification
report after a successful audit; it does not make missing provenance valid.

The checked-in upstream manifest deliberately has an empty adapter command and
null historical revisions. This is an explicit unavailable-state fixture until
protocol archaeology supplies those values; it is not a benchmark result.
