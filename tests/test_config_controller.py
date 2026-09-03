from __future__ import annotations

import json

import numpy as np

from vrx_controller import BodyVelocity, ControllerConfig, Pose2D, StationKeepingController, StationKeepingState


def test_configuration_json_round_trip(config: ControllerConfig) -> None:
    restored = ControllerConfig.from_json(json.dumps(config.to_dict()))
    np.testing.assert_allclose(restored.model.mass, config.model.mass)
    np.testing.assert_allclose(restored.pid.kp, config.pid.kp)
    np.testing.assert_allclose(restored.effectiveness, config.effectiveness)
    assert restored.actuator_limits.dead_zone_mode == config.actuator_limits.dead_zone_mode


def test_station_controller_is_deterministic_and_angle_safe(config: ControllerConfig) -> None:
    state_sequence = [
        StationKeepingState(Pose2D(1.0, -2.0, np.deg2rad(179.0)), BodyVelocity(0.0, 0.0, 0.0)),
        StationKeepingState(Pose2D(0.95, -1.9, np.deg2rad(-179.0)), BodyVelocity(0.1, -0.1, 0.01)),
        StationKeepingState(Pose2D(0.8, -1.8, np.deg2rad(-178.0)), BodyVelocity(0.1, -0.1, 0.01)),
    ]
    target = Pose2D(0.0, 0.0, np.deg2rad(-179.0))
    first = StationKeepingController(config)
    second = StationKeepingController(config)
    first_outputs = [first.step(state, target, 0.1) for state in state_sequence]
    second_outputs = [second.step(state, target, 0.1) for state in state_sequence]
    for left, right in zip(first_outputs, second_outputs):
        np.testing.assert_allclose(left.command, right.command)
        np.testing.assert_allclose(left.disturbance_estimate, right.disturbance_estimate)
    # The first yaw error is 2 degrees, not a -358 degree numerical jump.
    assert np.isclose(first_outputs[0].pose_error_body[2], np.deg2rad(2.0))
    assert np.all(np.isfinite(first_outputs[-1].command))
