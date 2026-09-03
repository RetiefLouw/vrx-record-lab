"""Minimal linear vehicle model exposed for PID and future LQR/MPC laws."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def _matrix3(value: np.ndarray | list[list[float]], name: str) -> np.ndarray:
    matrix = np.asarray(value, dtype=float)
    if matrix.shape != (3, 3):
        raise ValueError(f"{name} must have shape (3, 3), got {matrix.shape}")
    if not np.all(np.isfinite(matrix)):
        raise ValueError(f"{name} must contain only finite values")
    return matrix.copy()


@dataclass(frozen=True)
class PlanarVehicleModel:
    """Planar 3-DOF model ``M nu_dot + D nu = tau + d``.

    ``nu`` is body-frame [surge, sway, yaw-rate], ``tau`` and ``d`` are body
    wrench vectors [force_x, force_y, moment_z].  The state exposed by
    :meth:`linearize` is [world_x_error, world_y_error, yaw_error, nu_error].
    This is a local model around zero velocity, suitable as an LQR/MPC-ready
    interface but not a VRX dynamics claim.
    """

    mass: np.ndarray
    damping: np.ndarray

    def __post_init__(self) -> None:
        mass = _matrix3(self.mass, "mass")
        damping = _matrix3(self.damping, "damping")
        if not np.allclose(mass, mass.T, atol=1e-12):
            raise ValueError("mass must be symmetric")
        try:
            np.linalg.cholesky(mass)
        except np.linalg.LinAlgError as exc:
            raise ValueError("mass must be positive definite") from exc
        object.__setattr__(self, "mass", mass)
        object.__setattr__(self, "damping", damping)

    @property
    def inverse_mass(self) -> np.ndarray:
        return np.linalg.inv(self.mass)

    def acceleration(self, velocity: np.ndarray, wrench: np.ndarray, disturbance: np.ndarray | None = None) -> np.ndarray:
        """Compute body acceleration from the declared linear model."""

        nu = np.asarray(velocity, dtype=float)
        tau = np.asarray(wrench, dtype=float)
        if nu.shape != (3,) or tau.shape != (3,):
            raise ValueError("velocity and wrench must have shape (3,)")
        d = np.zeros(3, dtype=float) if disturbance is None else np.asarray(disturbance, dtype=float)
        if d.shape != (3,):
            raise ValueError("disturbance must have shape (3,)")
        if not np.all(np.isfinite(np.concatenate([nu, tau, d]))):
            raise ValueError("velocity, wrench, and disturbance must be finite")
        return self.inverse_mass @ (tau + d - self.damping @ nu)

    def linearize(self, reference_yaw: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
        """Return continuous-time ``(A, B)`` for a stationary reference pose."""

        if not np.isfinite(reference_yaw):
            raise ValueError("reference_yaw must be finite")
        c = float(np.cos(reference_yaw))
        s = float(np.sin(reference_yaw))
        rotation = np.array([[c, -s], [s, c]], dtype=float)
        a = np.zeros((6, 6), dtype=float)
        a[:2, 3:5] = rotation
        a[2, 5] = 1.0
        a[3:, 3:] = -self.inverse_mass @ self.damping
        b = np.zeros((6, 3), dtype=float)
        b[3:, :] = self.inverse_mass
        return a, b

    def discretize(self, dt: float, reference_yaw: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
        """Return a deterministic forward-Euler discrete linearization.

        Euler is intentionally explicit here because this package has no
        scipy dependency and the caller controls the sampling period.  A
        higher-fidelity discretizer can consume :meth:`linearize` later.
        """

        if not np.isfinite(dt) or dt <= 0.0:
            raise ValueError("dt must be finite and positive")
        a, b = self.linearize(reference_yaw)
        return np.eye(6) + dt * a, dt * b
