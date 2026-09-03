# Independent verification audit report

Use one copy of this template per promoted result. Replace every bracketed
field. Do not convert `unknown`, `inferred`, or `not accepted` into a positive
claim without new evidence.

## Decision

- Claim status: `[unaccepted | candidate | reproduced | promoted]`
- Exact claim language: `[one sentence; name the task, metric, aggregate, and comparator]`
- Result file: `[path]`
- Audit date and auditor: `[date / name or handle]`
- Decision: `[accepted | conditional reproduction only | rejected]`
- Reason for decision: `[short, evidence-backed explanation]`

`promoted` is allowed only when the machine-checkable result passes schema,
seed, artifact, benchmark-tree, and clean-clone checks. A historical value
must not be called a record merely because a local result is numerically lower
or higher.

## Reference and comparability

| Field | Candidate value | Historical/reference value | Status | Evidence |
|---|---|---|---|---|
| Challenge and task | `[value]` | `[value]` | `[verified/inferred/unknown]` | `[URL or artifact]` |
| Metric and direction | `[value]` | `[value]` | `[verified/inferred/unknown]` | `[URL or artifact]` |
| Per-run count and aggregation | `[value]` | `[value]` | `[verified/inferred/unknown]` | `[URL or artifact]` |
| Initial/ready/running/finished timing | `[value]` | `[value]` | `[verified/inferred/unknown]` | `[URL or artifact]` |
| World, poses, duration, timeout, resets | `[value]` | `[value]` | `[verified/inferred/unknown]` | `[URL or artifact]` |
| Environment and randomization | `[value]` | `[value]` | `[verified/inferred/unknown]` | `[URL or artifact]` |
| Scorer implementation and revision | `[value]` | `[value]` | `[verified/inferred/unknown]` | `[URL or artifact]` |

Comparability conclusion: `[direct | conditional | not comparable | unknown]`.

If any comparison dimension is unknown, state exactly what remains unknown and
why the result is not an accepted record claim.

## Provenance

| Evidence | Value | SHA-256 / digest | Check result |
|---|---|---|---|
| Repository URL | `[URL]` | `[n/a]` | `[pass/fail]` |
| Candidate commit | `[40-char SHA]` | `[n/a]` | `[pass/fail]` |
| Benchmark commit/tree | `[value]` | `[tree digest]` | `[pass/fail]` |
| Scorer commit/tree | `[value]` | `[tree digest]` | `[pass/fail]` |
| Controller commit | `[40-char SHA]` | `[n/a]` | `[pass/fail]` |
| Container image | `[image reference]` | `[sha256:...]` | `[pass/fail]` |
| Configuration | `[path]` | `[64-char SHA]` | `[pass/fail]` |

## Seeds and runs

- Development seed set: `[name and exact list or manifest]`
- Independent verification seed set: `[name and exact list or manifest]`
- Hidden evaluation seed set: `[name and exact list; do not publish secrets]`
- Disjointness command and output: `[command / artifact path]`
- Run count: `[n]`
- Aggregate method and value: `[mean / value]`
- Run-level result file: `[path]`

The evaluator must verify the exact sets, not just their names. If a hidden
set is externally supplied and cannot be inspected by the auditor, mark the
separation as unknown.

## Artifact integrity

- Manifest path: `[path]`
- Manifest root: `[path]`
- Manifest check command: `[command]`
- Manifest check result: `[pass/fail]`
- Raw logs retained: `[yes/no; paths]`
- Missing, extra, or changed artifacts: `[none or details]`

## Clean-clone rerun

- Clone source: `[URL]`
- Exact commit: `[40-char SHA]`
- Ref fetched: `[ref]`
- Command: `[full command]`
- Checkout clean before run: `[yes/no]`
- Rerun output/artifact paths: `[paths]`
- Reproduced aggregate: `[value]`
- Tolerance and rationale: `[value and rationale]`

## Benchmark/scorer integrity

- Baseline ref: `[ref and resolved SHA]`
- Candidate ref: `[ref and resolved SHA]`
- Protected path configuration: `[path]`
- Protected tree check command: `[command]`
- Protected tree result: `[pass/fail; include vacuous warning if no paths exist]`
- Any benchmark/scorer edits: `[none or exact paths]`

## Reproducibility checklist

- [ ] Historical source and evaluator revisions are pinned.
- [ ] Protocol dimensions are verified or explicitly marked unknown.
- [ ] Candidate result passes `verification/result.schema.json`.
- [ ] Development and evaluation seeds are proven disjoint.
- [ ] Candidate was run from an exact clean-clone commit.
- [ ] Benchmark/scorer tree check passed against the declared baseline.
- [ ] Raw run artifacts and a strict SHA-256 manifest are retained.
- [ ] Aggregate arithmetic matches the listed run scores.
- [ ] Claim language does not overstate comparability or recognition.

## Open issues

1. `[issue, owner, and evidence required]`
2. `[issue, owner, and evidence required]`
