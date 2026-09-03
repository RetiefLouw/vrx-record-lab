# VRX 2019 station-keeping protocol

Status: reconstruction in progress; the historical `0.11` is not currently
directly comparable. The current evidence and closest reimplementation design
are recorded in the [UF 2019 station-keeping reproduction dossier](uf-2019-station-keeping-reproduction.md).

The official results report a station-keeping value of `0.11` for the
University of Florida entry. Before treating that number as a directly
comparable record, this campaign must recover and pin:

- VRX, WAM-V, Gazebo, ROS, and scoring revisions;
- task world, initial pose, target pose, duration, timeout, and reset behavior;
- wind, wave, and current configuration plus randomization seeds;
- scorer formula, sampling interval, transient handling, and penalties;
- preliminary/final run selection and leaderboard aggregation.

Unknown values are never silently replaced. Any reconstructed setting will be
marked as inferred and accompanied by its evidence.

## Independent comparability finding (2026-09-03)

The [official VRX 2019 results page](https://github.com/osrf/vrx/wiki/vrx_2019-results)
reports the University of Florida station-keeping task score as `0.11`. It
also reports six individual station-keeping run scores: `0.02`, `0.04`,
`0.35`, `0.04`, `0.10`, and `0.11`; their arithmetic mean is `0.11`.

The [2019 Competition and Task Descriptions, version 1.4](https://github.com/osrf/vrx/wiki/files/VRX2019_Task_Descriptions_v1.4.pdf)
defines a station-keeping run score as RMS pose error and the task score as the
mean of the run scores. The [2019 Technical Guide, version 1.2](https://github.com/osrf/vrx/wiki/files/VRX2019_Technical%20Guide_V1.2.pdf)
describes an initial transient state, a scored running state, and different
environmental configurations across runs; it says that exact final
characteristics were to be released as part of the final technical
specification.

Those sources establish what the published number means, but they do not by
themselves pin the exact six final world/configuration inputs, random seeds,
goal and initial poses, score weight and numerical implementation, VRX/ROS/
Gazebo revisions, evaluator image digest, or the complete raw log set. The
public results page says logs are available, but a link or a table entry is not
treated as evidence that the logs have been independently recovered and
verified.

Therefore the campaign records `0.11` as a historical reference only. A new
result may be labelled `direct` only after those inputs and artifacts are
recovered, hashed, run from a clean clone, and shown to use unchanged
benchmark/scorer trees. Until then, a result can be a conditional reproduction
of a reconstructed protocol, but it must not be described as beating or tying
the official record.

### Evidence ledger

| Item | Status | Evidence or required follow-up |
|---|---|---|
| UF station-keeping task score is `0.11` | Verified | Official results page, scoring table |
| Six reported UF station-keeping runs average to `0.11` | Verified | Official results page, station-keeping table |
| Run metric is RMS pose error; task aggregation is the mean | Verified | 2019 task descriptions v1.4 |
| Runs use varied environmental conditions and task states include an unscored initial period | Verified | 2019 technical guide v1.2 |
| Exact final six world/configuration inputs and seeds | Unknown | Recover evaluator artifacts/logs; do not infer |
| VRX, ROS, Gazebo, benchmark, and scorer revisions used for UF | Unknown | Recover submission/evaluator provenance |
| Container image digest and complete raw logs | Unknown | Recover and verify image/log artifacts |
| Direct comparability of a new local run to `0.11` | Not accepted | Remains `not_comparable` until unknowns are closed |

The machine-checkable result fixture mirrors this finding: it uses
`claim_status: unaccepted` and `comparability: not_comparable`.
