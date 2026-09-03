# Controller design and inference log

This document records the design boundary for the initial controller package.
It is intentionally separate from the VRX protocol and scorer reconstruction.
No item below is a benchmark result or a claim about the historical VRX
implementation.

## Scope

The package in `src/vrx_controller` is a simulator-independent control layer.
It accepts numeric state objects and returns numeric wrench, thruster-force,
and actuator-command data.  It does not import ROS, Gazebo, VRX, or scorer
code.  This keeps numerical tests independent of simulator timing and makes
the allocation/model seams reusable by a later LQR or nonlinear MPC law.

## Inference log

| ID | Inference or chosen convention | Reason and consequence |
|---|---|---|
| I-001 | Python 3.10+ with NumPy is the initial runtime. | The repository had no code, build metadata, or language contract. Python and NumPy provide compact, deterministic numerical primitives; this is a package choice, not an upstream VRX requirement. |
| I-002 | The initial model is planar 3-DOF: surge, sway, and yaw. | The repository target is VRX 2019 station keeping, but no recovered vehicle interface was present. Six state coordinates are exposed as pose errors plus three body velocities; heave/roll/pitch are intentionally out of scope. |
| I-003 | Position is metres, yaw is radians, body velocity is [m/s, m/s, rad/s], and wrench is [N, N, N m]. | These are SI conventions selected because no simulator adapter or unit metadata exists in the repository. An adapter must convert external units before calling the package. |
| I-004 | World x/y is right-handed and yaw is positive counter-clockwise; body x/y follows the standard planar rotation. | The repository does not yet contain a coordinate-frame contract. `world_to_body` and `PlanarVehicleModel.linearize` make this convention explicit so a future adapter has one place to validate or replace it. |
| I-005 | A missing target velocity means zero, and the current PID controls body-frame position error plus target-minus-current body velocity. | Station keeping implies a stationary target, while a moving-target API is useful for later extensions. The target velocity is therefore optional and does not alter the state object shape. |
| I-006 | Heading errors use the shortest path in [-pi, pi), with the exact pi tie broken to -pi. | Direct subtraction creates discontinuities at the branch cut. The half-open interval gives deterministic behavior for exact antipodal headings. |
| I-007 | The model is `M nu_dot + D nu = tau + d`, with constant positive-definite mass and a supplied damping matrix. | No hydrodynamic identification is available. This transparent linear balance is enough for an LQR-ready local model and observer without implying VRX fidelity. |
| I-008 | `linearize` is around zero velocity and a supplied reference yaw; `discretize` uses forward Euler. | The future LQR/MPC boundary needs explicit A/B matrices. A dependency-free Euler discretization is predictable, but it must be replaced or validated for a real simulator sample period. |
| I-009 | The disturbance observer estimates an additive body wrench using the model residual and a first-order low-pass pole. | No sensor/noise/timing contract is available. The observer initializes history without an impulse and uses an exact pole factor; bandwidth remains configuration, not a claimed tuned value. |
| I-010 | Allocation minimizes weighted wrench residual plus a small previous-force regularizer under per-thruster box limits; optional allocator slew limits are supported. | Thruster geometry, reversibility, and priority policy were not recovered. The effectiveness matrix is therefore injected by configuration, and no geometry is hard-coded. |
| I-011 | Actuator processing applies force saturation, then slew rate, then a configurable dead-zone policy. | This ordering is a control-layer choice that keeps diagnostics interpretable. `zero` models a physical dead band; `compensate` adds the configured threshold to nonzero commands and reports the resulting effective force. |
| I-012 | Controller anti-windup tracks the wrench actually attributable to the actuator, after allocation and dead-zone handling, with the observer estimate added back for comparison. | Allocation and actuator limits can saturate across axes, so per-axis PID clipping alone is insufficient. This is a pragmatic back-calculation interface; it is not validated against a VRX thruster plugin. |
| I-013 | The test effectiveness matrix and numeric defaults are synthetic fixtures. | The repository contains no thruster geometry, identified dynamics, or scorer code. Tests validate invariants and determinism only; they must not be interpreted as benchmark runs. |

## Integration boundary

An adapter for a simulator should:

1. Convert simulator state into `Pose2D`, `BodyVelocity`, and SI units.
2. Supply a configuration-specific 3-by-n thruster effectiveness matrix.
3. Pass the returned actuator `command` to the simulator and use measured
   state on the next cycle.
4. Preserve the controller diagnostics and configuration with each run.

The controller package does not select worlds, seeds, durations, scorer
versions, or benchmark aggregation. Those remain part of the separate protocol
reconstruction and reproducibility work.
