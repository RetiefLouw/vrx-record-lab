# VRX Record Lab

Reproducible archaeology, baseline replication, and controller development for
the VRX 2019 station-keeping task.

The first reference target is the University of Florida score reported as
`0.11` in the official 2019 results. This repository does **not** claim a new
record until the historical protocol has been reconstructed, the reference
has been reproduced as closely as surviving artifacts allow, and a better
result has passed a clean independent rerun.

## Campaign status

- Target: VRX 2019 station keeping
- Status: protocol reconstruction and environment bootstrap
- Compute policy: OrbStack first; Vast.ai only through a bounded campaign
- Claim policy: independently reproduced task-level record unless recognized
  by the benchmark maintainers

## Controller package

`src/vrx_controller` contains simulator-independent planar station-keeping
components.  It currently provides angle-safe state errors, a linear model
interface for future LQR/MPC work, anti-windup PID, a wrench disturbance
observer, constrained thruster allocation, and actuator saturation/rate/
dead-zone handling.  The package has no ROS, Gazebo, VRX, or scorer dependency.

Run the deterministic unit tests with:

```bash
python -m pip install -e '.[test]'
python -m pytest
```

The controller design assumptions and all inferences made in the absence of
recovered VRX runtime interfaces are recorded in
[`docs/controller-design.md`](docs/controller-design.md).

## Sources

- [Official VRX 2019 results](https://github.com/osrf/vrx/wiki/vrx_2019-results)
- [VRX repository](https://github.com/osrf/vrx)

## License

Project-authored code is released under the Apache License 2.0. Upstream VRX,
ROS, Gazebo, vessel models, and competition assets retain their own licenses.
