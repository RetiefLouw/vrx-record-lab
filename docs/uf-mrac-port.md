# UF MRAC station-keeping port

Status: closest public-source reimplementation; not an exact reproduction and
not a claim to reproduce UF's published `0.11` score.

This repository contains a simulator-independent NumPy implementation in
[`src/vrx_controller/uf_mrac.py`](../src/vrx_controller/uf_mrac.py). It is a
clean transcription of the control-law boundary in the University of Florida
NaviGator source released at the immutable tag
[`7c312eeac2dbaa888adfce5f04ad9a9d85999646`](https://github.com/uf-mil/mil/tree/7c312eeac2dbaa888adfce5f04ad9a9d85999646),
principally `NaviGator/gnc/navigator_controller/nodes/mrac_controller.py`.
No UF source file is vendored in this repository.

## Runtime path

`UFMRACController` models the public external-trajectory path:

1. The caller supplies the measured planar pose/body velocity and the latest
   external trajectory reference.
2. Body velocity is rotated into ENU/world coordinates.
3. Body-diagonal `kp` and `kd` are rotated into the world frame.
4. The controller computes the position/yaw and velocity/yaw-rate errors,
   reference-model inertial feedforward, and the tagged five-column drag
   regressor.
5. The resulting world wrench is rotated back to a body wrench.
6. A separate thruster mapper remains responsible for converting that wrench
   to actuator commands, matching UF's `/wrench/autonomous` boundary.

The default configuration is the final VRX launch configuration recovered in
the dossier: `kp_body=[1000,1000,5600]`, `kd_body=[1200,1200,6000]`,
`ki=[0.1,0.1,0.1]`, `kg=[5,5,5,5,5]`, `mass_ref=251.19`, and
`inertia_ref=500.58`. The source's ±200 disturbance estimate and ±1000
applied drag-effort limits are retained. Adaptation is disabled by default,
as in the source node, and is enabled by `set_learning("autonomous")` when
the wrench arbiter selects the autonomous wrench.

The port also retains the source's virtual pseudoinverse mapper as an explicit
helper for reference-model calculations. It is not used by the external
LQ-RRT path and is not a substitute for the separate vessel mapper.

## Deliberate deviations

- ROS messages, `rospy`, `tf`, Gazebo, LQ-RRT, and the scorer are not imported;
  small typed data objects provide the message boundary instead.
- Quaternion operations are reduced to planar yaw and use the repository's
  deterministic shortest-angle convention.
- The historical node's ROS publication and callback scheduling are outside
  the class; the caller supplies `dt` from message timestamps.
- The historical internal reference generator is not the nominal path because
  the public tag sets `use_external_tgen=True`. Its source geometry constants
  are retained only for the documented virtual mapper and diagnostics.
- Exact phase-3 worlds, submodule objects, container provenance, scorer binary,
  and UF controller-side traces remain unavailable. Official server-side
  Gazebo/task logs and exact scores are public, but they are insufficient to
  infer a score or record from this implementation.

## Attribution and licensing

The original UF NaviGator controller identifies the Machine Intelligence Lab
copyright and licensing terms in
[`licenses/uf-mil-navigator-license.txt`](../licenses/uf-mil-navigator-license.txt).
The implementation here is new project-authored code, not a wholesale copy of
that file, and is covered by this repository's Apache-2.0 license. The source
tag and the relevant file path are retained above for attribution and audit.

## Example

```python
import numpy as np

from vrx_controller import (
    BodyVelocity,
    Pose2D,
    StationKeepingState,
    UFMRACController,
    UFMRACReference,
)

controller = UFMRACController(learning_enabled=False)
controller.set_learning("autonomous")
output = controller.step(
    StationKeepingState(Pose2D(1.0, -2.0, 0.1), BodyVelocity(0.0, 0.0, 0.0)),
    UFMRACReference(Pose2D(0.0, 0.0, 0.0)),
    dt=0.02,
)
body_wrench = output.wrench_body
```
