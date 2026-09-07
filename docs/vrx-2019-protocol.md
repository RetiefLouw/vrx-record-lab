# VRX 2019 station-keeping protocol

Status: partially recovered. Research date: 2026-09-03.

This document reconstructs the public evidence for the 2019 Virtual RobotX
(VRX) station-keeping task. It is deliberately not a claim that the hidden
phase-3 evaluator can be reproduced byte-for-byte. Every value below is
labelled as **confirmed**, **inferred**, or **unavailable**. Claim-level source
metadata and hashes are in [`vrx-2019-provenance.json`](vrx-2019-provenance.json).

## Bottom line

The official task description defines the station-keeping score as an RMS pose
error with a heading weight `W`. It does not publish a numeric `W`. The
strongest public code evidence from the final submission window is different:
the station-keeping plugin computes an arithmetic mean of the instantaneous
error

```text
sqrt(dx^2 + dy^2) + (1 - abs(abs(goal_yaw - current_yaw) - pi) / pi)
```

and sends that mean to the generic task score. The public source calls the
debug topic `rms_error`, although the value assigned to it is a mean. This is
a confirmed specification/code discrepancy, not something to silently
resolve in favor of either source.

The University of Florida (UF) result is still an official published result:
the result page lists six station-keeping run scores, `0.02, 0.04, 0.35, 0.04,
0.10, 0.11`, and reports a task score of `0.11`. The arithmetic mean of those
published values is exactly `0.11`. Because the values are displayed to two
decimal places and the evaluator's exact checkout is not pinned publicly,
this arithmetic is a provenance check, not a source-level re-score.

## Evidence labels and source anchors

- **Confirmed** means directly stated by an official document or directly
  present at an immutable repository/wiki revision.
- **Inferred** means the best reconstruction from public evidence, with the
  reasoning stated. It must not be treated as a proven evaluator setting.
- **Unavailable** means the public record located for this campaign does not
  expose the value. `null` in the JSON manifest means unavailable; it is not a
  zero or a default.

The primary anchors are:

| Source | Revision or identity | Use |
| --- | --- | --- |
| [VRX 2019 Task Descriptions v1.4](https://github.com/osrf/vrx/wiki/files/VRX2019_Task_Descriptions_v1.4.pdf) | v1.4, SHA-256 `d67a48560b25e6dae2ff595cc046697651c67a0bed6737fb15ee44291543d352` | Published task state machine, RMS formula, task ranking rules. |
| [VRX 2019 Technical Guide v1.2](https://github.com/osrf/vrx/wiki/files/VRX2019_Technical%20Guide_V1.2.pdf) | v1.2, SHA-256 `3742c434f78980b0a08db4728f627c1358e6878c7e0cbdd3bab18ea50c5390d7` | Platform requirements, run lifecycle, initial-state behavior, and environmental envelope. |
| [2019 official results](https://github.com/osrf/vrx/wiki/vrx_2019-results/0305065c335a2511141e9bd03136afe1f85eba69) | wiki revision `0305065c335a2511141e9bd03136afe1f85eba69` | UF run scores, six-trial summary, task ranks, and overall aggregation. |
| [Phase 3 competition page](https://github.com/osrf/vrx/wiki/vrx_2019-phase3_competition/32984d15beb6f24091ec7ca9455ca03d0469010f) | wiki revision `32984d15beb6f24091ec7ca9455ca03d0469010f` | Confirms multiple scenario-specific trials and unreleased evaluation configurations. |
| [VRX 2019 system requirements](https://github.com/osrf/vrx/wiki/vrx_2019-system_requirements) | Official VRX wiki page | Ubuntu 18.04, ROS Melodic, and Gazebo 9.11.0+ requirements. The wiki API did not expose an immutable revision for this page. |
| [VRX tag 1.3.0](https://github.com/osrf/vrx/tree/7a784814c90f203cebf1e471e5af64fbb76be53d) | commit `7a784814c90f203cebf1e471e5af64fbb76be53d` | Public VRX package, launch files, worlds, and station-keeping plugin. |
| [VRX final-window tip](https://github.com/osrf/vrx/tree/dd6187ca2eb24838b4288bf1154031556bb73cf6) | commit `dd6187ca2eb24838b4288bf1154031556bb73cf6`, 2019-11-22 | Best public code anchor near the final submission window; exact evaluator checkout is inferred, not confirmed. |
| [VRX Docker phase-3 harness](https://github.com/osrf/vrx-docker/tree/ce6a9b4a11d30767e2b44d62b0097630e9d3fd69) | commit `ce6a9b4a11d30767e2b44d62b0097630e9d3fd69`, 2019-11-23 | Public trial launch and score collection. Its Dockerfile clones VRX unpinned. |

## Platform and repository identity

| Item | Finding | Status |
| --- | --- | --- |
| Host OS | Ubuntu Desktop 18.04 Bionic, 64-bit | Confirmed by the official system requirements page. |
| ROS | ROS Melodic | Confirmed by the official system requirements page and the Docker default `DIST=melodic`. |
| Gazebo | Gazebo 9.11.0 or newer | Confirmed by the official system requirements page. The public Dockerfile installs the unpinned `gazebo9` package. |
| VRX package | `vrx_gazebo` package version `1.3.0` in the public `1.3.0` tag | Confirmed. This is a package version, not proof of the evaluator's checkout. |
| WAM-V | Standard VRX WAM-V model; model modification prohibited for the competition | Confirmed by the Technical Guide. Exact evaluator asset/package revision is unavailable. |
| Best source commit | `dd6187ca2eb24838b4288bf1154031556bb73cf6` | Inferred as a final-window code anchor: it was the public VRX tip on 2019-11-22 and contains the final-era scorer, but the evaluator Dockerfile did not pin it. |
| Exact evaluator commit and apt package versions | Not recorded in the public harness | Unavailable. |

The relevant source files are [`stationkeeping_scoring_plugin.cc`](https://github.com/osrf/vrx/blob/dd6187ca2eb24838b4288bf1154031556bb73cf6/vrx_gazebo/src/stationkeeping_scoring_plugin.cc),
[`stationkeeping_scoring_plugin.hh`](https://github.com/osrf/vrx/blob/dd6187ca2eb24838b4288bf1154031556bb73cf6/vrx_gazebo/include/vrx_gazebo/stationkeeping_scoring_plugin.hh),
[`sandisland.launch`](https://github.com/osrf/vrx/blob/dd6187ca2eb24838b4288bf1154031556bb73cf6/vrx_gazebo/launch/sandisland.launch),
and the public [phase-2 station-keeping worlds](https://github.com/osrf/vrx/tree/7a784814c90f203cebf1e471e5af64fbb76be53d/vrx_gazebo/worlds/2019_phase2).

## Run lifecycle, launch, and timing

The official task description defines each run as `Initial -> Ready -> Running
-> Finished`:

1. **Initial:** the USV is initialized at a random location in the operating
   area and the transient is stabilized. The Technical Guide says X, Y, and
   yaw are locked; Z, pitch, and roll may still settle.
2. **Ready:** the goal is published on `/vrx/station_keeping/goal`. The
   vehicle is released, but scoring has not started.
3. **Running:** the scoring timer is active.
4. **Finished:** scoring stops at task completion or timeout.

The public station-keeping world and xacro set
`initial_state_duration=10`, `ready_state_duration=10`, and
`running_state_duration=300`. Therefore the public nominal timeout is 300
seconds of scored running time, or 320 seconds from the simulation state clock
if all three phases begin at zero. **Confirmed for the public world; exact
phase-3 hidden-world timing is unavailable.**

The public phase-3 harness launches a fresh Gazebo process for each trial via
[`run_vrx_trial.sh`](https://github.com/osrf/vrx-docker/blob/ce6a9b4a11d30767e2b44d62b0097630e9d3fd69/vrx_server/vrx-server/run_vrx_trial.sh),
using `sandisland.launch`, `gui:=false`, `non_competition_mode:=false`, and a
trial-specific generated world. It records Gazebo state with
`--record_period 0.01`, but that is a Gazebo log-recording period, not the
station-keeping scorer's sample interval. The harness stores `/vrx/task/info`
in a rosbag and extracts the last task score.

The standalone [`station_keeping.launch`](https://github.com/osrf/vrx/blob/7a784814c90f203cebf1e471e5af64fbb76be53d/vrx_gazebo/launch/station_keeping.launch)
is a tutorial/demo launch using `stationkeeping_task.world` by default. It
should not be mistaken for the private final evaluator launch.

### Initial pose

The public `sandisland.launch` defaults are local pose
`x=158, y=108, z=0.1, roll=0, pitch=0, yaw=-2.76`. The public trial script
does not pass pose overrides, so those are the confirmed defaults of that
public path. The Technical Guide separately states that starting pose varies
between runs. Whether the phase-3 private harness overrode the public defaults
is **unavailable**; the two facts must not be conflated.

### Goal pose

The station-keeping world expresses the goal as latitude, longitude, and yaw.
The plugin converts latitude/longitude through the world's spherical WGS84
coordinates to local X/Y, and publishes a `geographic_msgs/GeoPoseStamped` on
`/vrx/station_keeping/goal` with a yaw quaternion. The public xacro default is
latitude `21.31091`, longitude `-157.88868`, heading `0.0`; generated practice
worlds override it. Exact phase-3 goal poses are **unavailable** because the
evaluation configurations were not released before the deadline.

### Environment parameters

The Technical Guide gives an allowed envelope, not the final per-trial
settings. Its listed controls are:

| Subsystem | Publicly documented envelope |
| --- | --- |
| Fog color | RGBA `[0.7, 0.7, 0.7, 1]` to `[0.9, 0.9, 0.9, 1]` |
| Fog density | `0` to `0.1` |
| Ambient light | RGBA `[0.3, 0.3, 0.3, 1]` to `[1, 1, 1, 1]` |
| Wind mean velocity | `0` to `8` |
| Wind variance gain | `0` to `8` |
| Wind variance time | `2` to `20` |
| Wind direction | `0` to `360` degrees |
| Waves | Pierson-Moskowitz (PMS) model; peak period and gain bounded by Figure 7 in the guide; direction and angle `0` to `360` degrees |
| Water current | No current parameter appears in the enumerated official envelope; the actual use or non-use of a current in hidden evaluation is **unavailable**, not proven absent. |

The public tag also contains six phase-2 practice worlds. They are useful
fixtures for a smoke test and for showing the parameter names, but they are
not the hidden phase-3 record runs. Common wave fields in these files are PMS,
`number=3`, `scale=1.5`, `angle=0.4`, `tau=2.0`, `amplitude=0`, and
`steepness=0`; the wave update rate is 30 Hz and wind update rate is 10 Hz.

| Run/world | Goal `(lat, lon, yaw)` | Waves `(gain, period, direction vector)` | Wind `(mean, variance gain, variance time, direction, seed)` |
| --- | --- | --- | --- |
| `stationkeeping0.world` | `(21.31085, -157.88860, 1.05)` | `(0.0, 7.0, (1.0, 0.0))` | `(0, 0, 1, 240, 10)` |
| `stationkeeping1.world` | `(21.31099, -157.88870, 3.0)` | `(0.2, 8.0, (1.0, 0.0))` | `(4.0, 2.0, 2, 192, 15)` |
| `stationkeeping2.world` | `(21.31092, -157.88874, 2.35)` | `(0.7, 3.0, (1.0, 0.0))` | `(8.0, 8.0, 2, 45, 11)` |
| `stationkeeping3.world` | `(21.31080, -157.89060, 0.0)` | `(0.0, 7.0, (1.0, 0.0))` | `(0, 0, 1, 240, 10)` |
| `stationkeeping4.world` | `(21.31050, -157.88940, -2.27)` | `(0.2, 7.0, (0.5, 0.5))` | `(5.0, 0.0, 2, 50, 42)` |
| `stationkeeping5.world` | `(21.31100, -157.88990, 2.0)` | `(0.7, 3.0, (1.0, 0.0))` | `(4.0, 4.0, 10, 45, 12)` |

## Scoring implementation and specification discrepancy

### Published task specification: RMS

The task description gives the run score as

```text
RMS = sqrt( sum_i [ (x_i - x_o)^2 + (y_i - y_o)^2 + W (h_i - h_o)^2 ] / n )
```

where `W` has units of meters and heading is in radians. The document does
not specify the numeric value of `W`, angle wrapping, or an exact scorer
sampling period. It says that the pose error debug value is published at 1 Hz
and that these debug values are not available to the team in final scored
runs.

### Public final-era executable code: arithmetic mean

At the final-window source anchor, the station-keeping plugin does the
following while the generic task state is `running`:

```text
dhdg       = abs(goal_yaw - current_yaw)
head_error = 1 - abs(dhdg - pi) / pi
pose_error = sqrt(dx^2 + dy^2) + head_error
mean_error = sum(pose_error) / sample_count
score      = mean_error
```

The update is connected to Gazebo's `WorldUpdateBegin`, so the scorer samples
on every world update rather than at a documented fixed 1 Hz interval. The
debug publishers are throttled to 1 Hz. The source advertises:

- `/vrx/station_keeping/goal`
- `/vrx/station_keeping/pose_error`
- `/vrx/station_keeping/rms_error` (a misleading name for the mean value)

The public history shows the RMS implementation was replaced by a mean-pose
implementation before the final event and corrected to remove an extra square
root. This makes the executable formula **confirmed for the cited public
revision**, and makes it **inferred** that the same code produced the published
phase-3 scores because the public Dockerfile clones VRX without a revision.

There is no station-keeping-specific timeout score or penalty in the public
station-keeping world/plugin. Scoring is suppressed during Initial and Ready,
then stops at Finished. Exact private evaluator penalties or wrapper behavior
are **unavailable**.

## Trial selection and leaderboard aggregation

The phase-3 page says performance is assessed over multiple trials, with each
trial representing a specific scenario, and that new evaluation configurations
were not released before the deadline. The official results page explicitly
says the task summary is over six trial runs. For UF station keeping it lists:

```text
Run 0: 0.02
Run 1: 0.04
Run 2: 0.35
Run 3: 0.04
Run 4: 0.10
Run 5: 0.11
```

The public [`get_task_score.py`](https://github.com/osrf/vrx-docker/blob/ce6a9b4a11d30767e2b44d62b0097630e9d3fd69/utils/get_task_score.py)
collects the scores from all trial directories and writes them as a
comma-separated list; it does not choose a best run or calculate the mean.
Therefore the six-run selection is **confirmed from the official result**,
while the exact hidden world files, directory contents, and any private
filtering before publication are **unavailable**.

The official aggregation is:

1. A task score is the mean of that task's run scores.
2. Teams are ranked low-to-high on each task score.
3. The overall total is the sum of task ranks; the lowest total wins.
4. A DNF/DSQ receives a rank equal to the number of teams for that task.

For UF, station keeping was task rank `1`. UF's overall total was `25`, giving
overall rank `5` on the official table.

### UF's published `0.11` check

Using the displayed run values:

```text
(0.02 + 0.04 + 0.35 + 0.04 + 0.10 + 0.11) / 6
= 0.66 / 6
= 0.11
```

This confirms the published task-level arithmetic to the displayed precision.
The official public log bucket additionally exposes exact `trial_score.txt`
values whose mean is `0.110429677731685`. It does not recover the generated
world configurations, exact VRX checkout, or whether the evaluator used the
PDF RMS formula or the public mean-pose implementation.

## Reproduction posture and unresolved fields

The public practice worlds and the `1.3.0` source are sufficient to build a
historically plausible station-keeping smoke test. They are not sufficient to
reproduce the UF phase-3 record. The following remain unavailable:

- the exact VRX commit and dependency package versions used by the evaluator;
- the six private phase-3 world files and their goal/initial poses;
- the final per-trial wind, wave, fog, light, and any current settings;
- the numeric RMS heading weight `W`, if the published specification was used;
- generated phase-3 world SDFs and controller-side UF trajectory/wrench logs;
- any private wrapper logic around the public Docker harness.

The machine-readable manifest records these gaps explicitly so a later primary
source can fill them without changing the meaning of existing evidence.
