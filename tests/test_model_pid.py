from __future__ import annotations

import numpy as np

from vrx_controller import PIDController, PIDGains, PlanarVehicleModel


def test_model_acceleration_matches_declared_balance() -> None:
    model = PlanarVehicleModel(np.diag([2.0, 4.0, 8.0]), np.diag([1.0, 2.0, 4.0]))
    velocity = np.array([1.0, -2.0, 0.5])
    wrench = np.array([5.0, 6.0, 7.0])
    disturbance = np.array([1.0, 2.0, 3.0])
    expected = np.array([(5.0 + 1.0 - 1.0) / 2.0, (6.0 + 2.0 - 2.0 * -2.0) / 4.0, (7.0 + 3.0 - 4.0 * 0.5) / 8.0])
    np.testing.assert_allclose(model.acceleration(velocity, wrench, disturbance), expected)


def test_model_linearization_is_lqr_ready() -> None:
    model = PlanarVehicleModel(np.diag([2.0, 4.0, 8.0]), np.diag([1.0, 2.0, 4.0]))
    a, b = model.linearize(np.pi / 2.0)
    np.testing.assert_allclose(a[:2, 3:5], [[0.0, -1.0], [1.0, 0.0]], atol=1e-12)
    np.testing.assert_allclose(a[3:, 3:], -np.diag([0.5, 0.5, 0.5]))
    np.testing.assert_allclose(b[3:, :], np.diag([0.5, 0.25, 0.125]))
    ad, bd = model.discretize(0.1, np.pi / 2.0)
    np.testing.assert_allclose(ad, np.eye(6) + 0.1 * a)
    np.testing.assert_allclose(bd, 0.1 * b)


def test_pid_back_calculation_reduces_windup() -> None:
    gains = PIDGains(
        kp=np.ones(3),
        ki=np.ones(3),
        kd=np.zeros(3),
        output_min=np.full(3, -1.0),
        output_max=np.full(3, 1.0),
        integral_min=np.full(3, -100.0),
        integral_max=np.full(3, 100.0),
        anti_windup_gain=np.ones(3),
    )
    pid = PIDController(gains)
    requested = pid.update(np.full(3, 10.0), np.zeros(3), 1.0)
    assert np.all(requested == 1.0)
    before = pid.integral.copy()
    pid.track_applied(requested, np.zeros(3), 1.0)
    assert np.all(pid.integral < before)


def test_pid_integral_limits_are_hard_bounds() -> None:
    gains = PIDGains(
        kp=np.zeros(3),
        ki=np.ones(3),
        kd=np.zeros(3),
        output_min=np.full(3, -100.0),
        output_max=np.full(3, 100.0),
        integral_min=np.full(3, -2.0),
        integral_max=np.full(3, 2.0),
    )
    pid = PIDController(gains)
    pid.update(np.full(3, 10.0), np.zeros(3), 1.0)
    np.testing.assert_allclose(pid.integral, np.full(3, 2.0))
