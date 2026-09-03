from __future__ import annotations

import numpy as np

from vrx_controller import (
    BodyVelocity,
    Pose2D,
    StationKeepingState,
    UFMRACController,
    UFMRACParameters,
    UFMRACReference,
)


def state(x=0.0, y=0.0, yaw=0.0, surge=0.0, sway=0.0, yaw_rate=0.0):
    return StationKeepingState(Pose2D(x, y, yaw), BodyVelocity(surge, sway, yaw_rate))


def test_defaults_are_the_recovered_final_vrx_values() -> None:
    parameters = UFMRACParameters()
    np.testing.assert_allclose(parameters.kp_body, [1000.0, 1000.0, 5600.0])
    np.testing.assert_allclose(parameters.kd_body, [1200.0, 1200.0, 6000.0])
    np.testing.assert_allclose(parameters.ki, [0.1, 0.1, 0.1])
    np.testing.assert_allclose(parameters.kg, np.full(5, 5.0))
    assert parameters.mass_ref == 251.19
    assert parameters.inertia_ref == 500.58
    np.testing.assert_allclose(parameters.disturbance_limit, [200.0, 200.0, 200.0])
    np.testing.assert_allclose(parameters.drag_effort_limit, [1000.0, 1000.0, 1000.0])


def test_regressor_matches_tagged_source_formula() -> None:
    velocity = np.array([2.0, 3.0])
    yaw = 0.4
    yaw_rate = 0.5
    c = np.cos(yaw)
    s = np.sin(yaw)
    expected = np.array(
        [
            [2 * c**2 + 3 * s * c, 2 / 2 - 2 * np.cos(2 * yaw) / 2 - 3 * np.sin(2 * yaw) / 2, -0.5 * s, -0.5 * c, 0],
            [3 / 2 - 3 * np.cos(2 * yaw) / 2 + 2 * np.sin(2 * yaw) / 2, 3 * c**2 - 2 * c * s, 0.5 * c, -0.5 * s, 0],
            [0, 0, 3 * c - 2 * s, -2 * c - 3 * s, 0.5],
        ]
    )
    np.testing.assert_allclose(UFMRACController.drag_regressor(velocity, yaw, yaw_rate), expected)


def test_step_rotates_body_velocity_and_wrench_through_world_frame() -> None:
    parameters = UFMRACParameters(
        kp_body=np.array([2.0, 4.0, 6.0]),
        kd_body=np.zeros(3),
        ki=np.zeros(3),
        kg=np.zeros(5),
    )
    controller = UFMRACController(parameters)
    output = controller.step(
        state(yaw=np.pi / 2.0, surge=1.0),
        UFMRACReference(Pose2D(0.0, 1.0, 0.0)),
        0.1,
    )
    # A body surge of +1 at yaw=+90° is +1 world-y.  The body-frame
    # proportional response is the inverse rotation of the world wrench.
    np.testing.assert_allclose(output.velocity_error_world, [-0.0, -1.0, 0.0], atol=1e-12)
    np.testing.assert_allclose(output.pose_error_world, [0.0, 1.0, -np.pi / 2.0])
    np.testing.assert_allclose(output.wrench_world, [0.0, 2.0, -3 * np.pi], atol=1e-12)
    np.testing.assert_allclose(output.wrench_body, [2.0, 0.0, -3 * np.pi], atol=1e-12)


def test_adaptation_is_gated_and_applied_after_current_wrench() -> None:
    parameters = UFMRACParameters(
        kp_body=np.ones(3),
        kd_body=np.zeros(3),
        ki=np.ones(3),
        kg=np.ones(5),
    )
    controller = UFMRACController(parameters, learning_enabled=True)
    output = controller.step(state(x=-1.0, y=-2.0), Pose2D(0.0, 0.0, 0.0), 1.0)
    np.testing.assert_allclose(output.wrench_world, [1.0, 2.0, 0.0])
    np.testing.assert_allclose(output.disturbance_estimate, [1.0, 2.0, 0.0])
    np.testing.assert_allclose(controller.drag_parameters, np.zeros(5))

    # The just-updated disturbance is used on the following source cycle.
    next_output = controller.step(state(x=-1.0, y=-2.0), Pose2D(0.0, 0.0, 0.0), 1.0)
    np.testing.assert_allclose(next_output.wrench_world, [2.0, 4.0, 0.0])

    outside = controller.step(state(x=-20.0), Pose2D(0.0, 0.0, 0.0), 1.0)
    np.testing.assert_allclose(outside.disturbance_estimate, [2.0, 4.0, 0.0])


def test_learning_selection_reset_matches_wrench_selected_callback() -> None:
    controller = UFMRACController(learning_enabled=False)
    controller.disturbance_estimate[:] = [1.0, 2.0, 3.0]
    controller.drag_parameters[:] = [1.0, 2.0, 3.0, 4.0, 5.0]
    controller.set_learning("autonomous")
    assert controller.learning_enabled
    controller.set_learning("manual")
    assert not controller.learning_enabled
    np.testing.assert_allclose(controller.disturbance_estimate, np.zeros(3))
    np.testing.assert_allclose(controller.drag_parameters, np.zeros(5))


def test_only_pd_ignores_feedforward_and_clears_adaptation() -> None:
    controller = UFMRACController()
    controller.only_PD = True
    controller.disturbance_estimate[:] = [4.0, 5.0, 6.0]
    controller.drag_parameters[:] = [1.0, 2.0, 3.0, 4.0, 5.0]
    output = controller.step(
        state(),
        UFMRACReference(
            Pose2D(0.0, 0.0, 0.0),
            linear_acceleration_world=np.array([10.0, 20.0]),
            yaw_acceleration=3.0,
        ),
        0.1,
    )
    np.testing.assert_allclose(output.wrench_world, np.zeros(3))
    np.testing.assert_allclose(output.drag_effort, np.zeros(3))
    np.testing.assert_allclose(controller.disturbance_estimate, np.zeros(3))
    np.testing.assert_allclose(controller.drag_parameters, np.zeros(5))


def test_virtual_mapper_is_separate_and_uses_source_scaling() -> None:
    effectiveness = np.eye(3, 4)
    output = UFMRACController.virtual_thruster_map(np.array([440.0, 0.0, 0.0]), effectiveness)
    np.testing.assert_allclose(output, [220.0, 0.0, 0.0, 0.0])
