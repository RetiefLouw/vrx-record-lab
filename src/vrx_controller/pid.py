"""Vector PID with back-calculation anti-windup."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def _vector(value: np.ndarray | list[float] | tuple[float, ...], name: str) -> np.ndarray:
    result = np.asarray(value, dtype=float)
    if result.shape != (3,):
        raise ValueError(f"{name} must have shape (3,), got {result.shape}")
    if not np.all(np.isfinite(result)):
        raise ValueError(f"{name} must contain finite values")
    return result.copy()


@dataclass(frozen=True)
class PIDGains:
    """Per-axis gains and limits for [surge, sway, yaw] wrench control."""

    kp: np.ndarray
    ki: np.ndarray
    kd: np.ndarray
    output_min: np.ndarray
    output_max: np.ndarray
    integral_min: np.ndarray | None = None
    integral_max: np.ndarray | None = None
    anti_windup_gain: np.ndarray | float = 1.0

    def __post_init__(self) -> None:
        kp = _vector(self.kp, "kp")
        ki = _vector(self.ki, "ki")
        kd = _vector(self.kd, "kd")
        output_min = _vector(self.output_min, "output_min")
        output_max = _vector(self.output_max, "output_max")
        if np.any(output_min > output_max):
            raise ValueError("output_min must be no greater than output_max")
        aw = np.asarray(self.anti_windup_gain, dtype=float)
        if aw.ndim == 0:
            aw = np.full(3, float(aw))
        aw = _vector(aw, "anti_windup_gain")
        if np.any(aw < 0.0):
            raise ValueError("anti_windup_gain must be non-negative")
        for name, value in (("kp", kp), ("ki", ki), ("kd", kd), ("output_min", output_min), ("output_max", output_max), ("anti_windup_gain", aw)):
            object.__setattr__(self, name, value)
        if self.integral_min is None:
            integral_min = np.full(3, -np.inf)
        else:
            integral_min = _vector(self.integral_min, "integral_min")
        if self.integral_max is None:
            integral_max = np.full(3, np.inf)
        else:
            integral_max = _vector(self.integral_max, "integral_max")
        if np.any(integral_min > integral_max):
            raise ValueError("integral_min must be no greater than integral_max")
        object.__setattr__(self, "integral_min", integral_min)
        object.__setattr__(self, "integral_max", integral_max)


class PIDController:
    """A deterministic three-axis PID controller.

    The controller separates computing a request from tracking what the
    actuator system actually achieved.  Call :meth:`track_applied` after
    allocation to prevent integrator growth during saturation.
    """

    def __init__(self, gains: PIDGains) -> None:
        self.gains = gains
        self.integral = np.zeros(3, dtype=float)
        self.last_output = np.zeros(3, dtype=float)

    def reset(self) -> None:
        self.integral.fill(0.0)
        self.last_output.fill(0.0)

    def update(self, error: np.ndarray, derivative: np.ndarray, dt: float) -> np.ndarray:
        """Advance the PID and return its per-axis, output-limited request."""

        if not np.isfinite(dt) or dt <= 0.0:
            raise ValueError("dt must be finite and positive")
        e = _vector(error, "error")
        de = _vector(derivative, "derivative")
        self.integral = np.clip(
            self.integral + e * dt,
            self.gains.integral_min,
            self.gains.integral_max,
        )
        raw = self.gains.kp * e + self.gains.ki * self.integral + self.gains.kd * de
        self.last_output = np.clip(raw, self.gains.output_min, self.gains.output_max)
        return self.last_output.copy()

    def track_applied(self, requested: np.ndarray, applied: np.ndarray, dt: float) -> None:
        """Back-calculate integrator state from an achieved wrench.

        ``applied`` should be the wrench attributable to the controller after
        allocation/actuator handling.  The back-calculation term is expressed
        in output units, so ``ki=0`` remains safe and simply disables integral
        action.
        """

        if not np.isfinite(dt) or dt <= 0.0:
            raise ValueError("dt must be finite and positive")
        requested_array = _vector(requested, "requested")
        applied_array = _vector(applied, "applied")
        difference = applied_array - requested_array
        # This is equivalent to a back-calculation correction on the integral
        # contribution.  Zero-ki axes receive no undefined division.
        correction = self.gains.anti_windup_gain * difference
        nonzero_ki = np.abs(self.gains.ki) > 1e-12
        self.integral[nonzero_ki] += dt * correction[nonzero_ki] / self.gains.ki[nonzero_ki]
        self.integral = np.clip(self.integral, self.gains.integral_min, self.gains.integral_max)
