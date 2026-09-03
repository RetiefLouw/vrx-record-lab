from __future__ import annotations

import numpy as np

from vrx_controller import DisturbanceObserver, PlanarVehicleModel


def test_observer_converges_to_constant_additive_wrench() -> None:
    model = PlanarVehicleModel(np.diag([2.0, 3.0, 4.0]), np.diag([1.0, 1.5, 0.5]))
    observer = DisturbanceObserver(model, bandwidth_hz=4.0)
    disturbance = np.array([2.0, -1.0, 0.5])
    velocity = np.zeros(3)
    dt = 0.02
    observer.update(velocity, np.zeros(3), dt)
    estimates = []
    for _ in range(250):
        velocity = velocity + dt * model.acceleration(velocity, np.zeros(3), disturbance)
        estimates.append(observer.update(velocity, np.zeros(3), dt))
    np.testing.assert_allclose(estimates[-1], disturbance, atol=0.04)


def test_observer_reset_discards_velocity_history() -> None:
    model = PlanarVehicleModel(np.eye(3), np.eye(3))
    observer = DisturbanceObserver(model)
    observer.update(np.zeros(3), np.zeros(3), 0.1)
    observer.update(np.ones(3), np.zeros(3), 0.1)
    observer.reset()
    np.testing.assert_allclose(observer.update(np.ones(3), np.zeros(3), 0.1), np.zeros(3))
