"""A deterministic low-pass disturbance observer for the planar model."""

from __future__ import annotations

import numpy as np

from .model import PlanarVehicleModel


class DisturbanceObserver:
    """Estimate an additive body wrench disturbance from velocity history.

    The estimate is based on the residual of
    ``M nu_dot + D nu = tau + d`` and filtered with an exact first-order
    discrete pole.  The first update initializes history and returns zero,
    avoiding a false impulse from an unknown initial velocity.
    """

    def __init__(self, model: PlanarVehicleModel, bandwidth_hz: float = 1.0) -> None:
        if not np.isfinite(bandwidth_hz) or bandwidth_hz <= 0.0:
            raise ValueError("bandwidth_hz must be finite and positive")
        self.model = model
        self.bandwidth_hz = float(bandwidth_hz)
        self.estimate = np.zeros(3, dtype=float)
        self._previous_velocity: np.ndarray | None = None

    def reset(self) -> None:
        self.estimate.fill(0.0)
        self._previous_velocity = None

    def update(self, velocity: np.ndarray, applied_wrench: np.ndarray, dt: float) -> np.ndarray:
        """Update and return the estimated external wrench."""

        nu = np.asarray(velocity, dtype=float)
        tau = np.asarray(applied_wrench, dtype=float)
        if nu.shape != (3,) or tau.shape != (3,):
            raise ValueError("velocity and applied_wrench must have shape (3,)")
        if not np.all(np.isfinite(np.concatenate([nu, tau]))):
            raise ValueError("velocity and applied_wrench must be finite")
        if not np.isfinite(dt) or dt <= 0.0:
            raise ValueError("dt must be finite and positive")
        if self._previous_velocity is None:
            self._previous_velocity = nu.copy()
            return self.estimate.copy()
        acceleration = (nu - self._previous_velocity) / dt
        residual = self.model.mass @ acceleration + self.model.damping @ nu - tau
        alpha = 1.0 - np.exp(-2.0 * np.pi * self.bandwidth_hz * dt)
        self.estimate += alpha * (residual - self.estimate)
        self._previous_velocity = nu.copy()
        return self.estimate.copy()
