# Internal audit: fast-PD GPS public-practice campaign

Audit date: 2026-09-04
Decision: **verified public-practice measurements; no record, SOTA, phase-3, or UF-reproduction claim**

## Evidence and result

The original `stationkeeping0` score, `0.008326716568191546`, was reproduced
twice in fresh result directories with the frozen controller and newly pinned
container image:

| Run | Score | Verification |
|---|---:|---|
| Original | `0.008326716568191546` | Historical manifest no longer byte-identical |
| Q-01 rerun 1 | `0.008340650238951723` | All seven local verifier gates pass |
| Q-01 rerun 2 | `0.008183191252996592` | All seven local verifier gates pass |

The rerun mean is `0.008261920745974156`. These local reruns support the narrow claim that
the controller reproducibly achieves about `0.0083` on the single public
practice world. Failed infrastructure attempts are retained under
`artifacts/q01-practice-rerun-2*` and were not averaged into the result.

Q-02 then executed all six public phase-2 worlds, unchanged and in declared
order, under the same controller/evaluator identity:

| World / trial seed | Score |
|---|---:|
| `stationkeeping0` / 0 | `0.008393142291132288` |
| `stationkeeping1` / 1 | `0.1222816566868139` |
| `stationkeeping2` / 2 | `1.1048966380251557` |
| `stationkeeping3` / 3 | `37.95612985923057` |
| `stationkeeping4` / 4 | `4.800463679994123` |
| `stationkeeping5` / 5 | `5.289713085241316` |

The strict reconstructed 2019 arithmetic mean is
`8.213646343578185` (sum `49.281878061469115`). The canonical verifier passes
schema, artifact digests, checksum manifest, aggregate arithmetic, experiment
manifest digest, pinned identity, and six completed trials. The diagnostic
extractor found a finished task and roughly 3,000 running controller samples
per world with no parse errors.

For context, the official phase-2 results table reports UF scores of `0.98`,
`1.01`, `1.26`, `67.36`, `13.58`, and `28.38`, with a displayed mean of
`18.76`. Q-02 is numerically lower than that historical phase-2 entry, but the
local reconstruction is self-hosted and uses a separately pinned public source
snapshot, so this is context rather than a recognized leaderboard claim.

## Audit interpretation

The six-world result does not support a public-suite performance record. The
large `stationkeeping3` score is acquisition-driven: its first-30-second mean
position error is about `164.46 m`, it takes about `130.20 s` to reach
`0.25 m`, and force saturation occupies about `39.8%` of the run. Worlds 4 and
5 also have large acquisition transients. The final 30-second position errors
are small, showing that the one-world success reflects an unusually easy
initial condition rather than broad robustness.

The reconstructed aggregation code separately reproduces UF's displayed
arithmetic: `(0.02 + 0.04 + 0.35 + 0.04 + 0.10 + 0.11) / 6 = 0.11`. It also
rejects incomplete or non-six-run inputs and reports identity mismatches.
That arithmetic does **not** make Q-02 directly comparable with UF: Q-02 uses
public phase-2 worlds, while UF's reported value came from unrecovered private
phase-3 inputs. The official public log bucket does retain UF's exact trial
scores and server-side Gazebo/task logs: their unrounded mean is
`0.110429677731685`. The generated phase-3 world SDFs, exact evaluator image,
competitor image, complete source identities, and controller-side diagnostics
remain unavailable, so those logs do not by themselves make exact replay
possible.

This is an internal project audit, not an independent third-party audit. The
reruns used fresh containers and output directories on the same host and
checkout. They are not an external replication or a rerun from a separately
cloned checkout, so that stronger independence gate remains open.

The separate protected-tree verifier remains vacuous (`present_specs: 0`) for
this repository because the upstream scorer lives inside the pinned image,
not a protected local tree. Raw bags and logs are intentionally ignored by
Git and remain workspace evidence; compact checked-in summaries alone are not
a clean-clone reproduction bundle.

## Defensible claim

The strongest defensible statement is:

> Two fresh local reruns confirm that the frozen fast-PD GPS controller scores
> about 0.0083 on the
> public `stationkeeping0` practice world. Across the complete reconstructed
> six-world public phase-2 suite it scores 8.213646343578185, so it does not
> beat UF's reported 0.11 under either a direct-comparability standard or even
> a naive arithmetic comparison. No VRX 2019 record is claimed.

Evidence: Q-01 directories under `artifacts/q01-practice-rerun-*`, the Q-02
canonical result and diagnostics under `results/runs/vrx2019-phase2-public`,
and compact aggregation summaries under `results/`.
