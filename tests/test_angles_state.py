from __future__ import annotations

import math

import numpy as np

from vrx_controller import BodyVelocity, Pose2D, StationKeepingState, angle_error, pose_error, wrap_angle
from vrx_controller.state import world_to_body


def test_wrap_angle_is_half_open_and_deterministic() -> None:
    assert wrap_angle(math.pi) == -math.pi
    assert wrap_angle(-math.pi) == -math.pi
    assert np.isclose(wrap_angle(3.0 * math.pi), -math.pi)
    assert np.isclose(wrap_angle(-3.0 * math.pi), -math.pi)


def test_angle_error_uses_shortest_path_across_branch_cut() -> None:
    target = math.radians(-179.0)
    current = math.radians(179.0)
    assert np.isclose(angle_error(target, current), math.radians(2.0))


def test_pose_error_wraps_yaw_but_keeps_world_position() -> None:
    error = pose_error(Pose2D(5.0, -2.0, math.radians(-179.0)), Pose2D(2.0, 1.0, math.radians(179.0)))
    np.testing.assert_allclose(error, [3.0, -3.0, math.radians(2.0)])


def test_world_to_body_rotation_is_inverse_of_body_to_world() -> None:
    world = np.array([1.0, 2.0])
    body = world_to_body(world, math.pi / 2.0)
    np.testing.assert_allclose(body, [2.0, -1.0], atol=1e-12)


def test_state_defaults_to_stationary_target_velocity() -> None:
    state = StationKeepingState(Pose2D(0.0, 0.0, 0.0), BodyVelocity(1.0, 2.0, 3.0))
    np.testing.assert_allclose(state.target_velocity_array(), np.zeros(3))
