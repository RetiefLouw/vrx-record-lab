"""Per-thruster saturation, slew-rate, and dead-zone handling."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def _vector(value: np.ndarray | list[float], size: int, name: str) -> np.ndarray:
    result = np.asarray(value, dtype=float)
    if result.shape != (size,):
        raise ValueError(f"{name} must have shape ({size},), got {result.shape}")
    if not np.all(np.isfinite(result)):
        raise ValueError(f"{name} must contain finite values")
    return result.copy()


@dataclass(frozen=True)
class ActuatorLimits:
    """Physical force limits and command-space nonlinearities."""

    force_min: np.ndarray
    force_max: np.ndarray
    rate_limit: np.ndarray
    dead_zone: np.ndarray
    dead_zone_mode: str = "zero"

    def __post_init__(self) -> None:
        raw_force_min = np.asarray(self.force_min)
        if raw_force_min.ndim != 1 or raw_force_min.size == 0:
            raise ValueError("force_min must be a non-empty vector")
        n = raw_force_min.size
        low = _vector(self.force_min, n, "force_min")
        high = _vector(self.force_max, n, "force_max")
        rate = _vector(self.rate_limit, n, "rate_limit")
        dead_zone = _vector(self.dead_zone, n, "dead_zone")
        if np.any(low > high):
            raise ValueError("force_min must be no greater than force_max")
        if np.any(rate <= 0.0):
            raise ValueError("rate_limit must be positive")
        if np.any(dead_zone < 0.0):
            raise ValueError("dead_zone must be non-negative")
        if np.any(dead_zone > np.maximum(np.abs(low), np.abs(high))):
            raise ValueError("dead_zone cannot exceed the available force range")
        if self.dead_zone_mode not in {"zero", "compensate"}:
            raise ValueError("dead_zone_mode must be 'zero' or 'compensate'")
        for name, value in (("force_min", low), ("force_max", high), ("rate_limit", rate), ("dead_zone", dead_zone)):
            object.__setattr__(self, name, value)


@dataclass(frozen=True)
class ActuatorCommand:
    """Processed commands and diagnostics for one control cycle."""

    requested: np.ndarray
    saturated: np.ndarray
    rate_limited: np.ndarray
    command: np.ndarray
    effective_force: np.ndarray
    saturation_active: np.ndarray
    rate_limit_active: np.ndarray
    dead_zone_active: np.ndarray


class ActuatorLimiter:
    """Apply actuator limits without requiring a simulator-specific API."""

    def __init__(self, limits: ActuatorLimits) -> None:
        self.limits = limits
        self.previous_command = np.zeros(len(limits.force_min), dtype=float)

    def reset(self, command: np.ndarray | None = None) -> None:
        if command is None:
            self.previous_command.fill(0.0)
            return
        self.previous_command = _vector(command, len(self.previous_command), "command")

    def apply(self, requested: np.ndarray, dt: float) -> ActuatorCommand:
        """Process force requests in order: saturation, rate limit, dead zone."""

        n = len(self.previous_command)
        req = _vector(requested, n, "requested")
        if not np.isfinite(dt) or dt <= 0.0:
            raise ValueError("dt must be finite and positive")
        low = self.limits.force_min
        high = self.limits.force_max
        saturated = np.clip(req, low, high)
        saturation_active = ~np.isclose(saturated, req, atol=1e-12)
        max_delta = self.limits.rate_limit * dt
        rate_limited = np.clip(saturated, self.previous_command - max_delta, self.previous_command + max_delta)
        rate_limit_active = ~np.isclose(rate_limited, saturated, atol=1e-12)
        if self.limits.dead_zone_mode == "zero":
            command = np.where(np.abs(rate_limited) <= self.limits.dead_zone, 0.0, rate_limited)
            effective = command.copy()
        else:
            uncompensated_command = np.where(
                np.abs(rate_limited) <= 1e-12,
                0.0,
                rate_limited + np.sign(rate_limited) * self.limits.dead_zone,
            )
            command = np.clip(uncompensated_command, low, high)
            saturation_active |= ~np.isclose(command, uncompensated_command, atol=1e-12)
            effective = np.where(np.abs(command) <= self.limits.dead_zone, 0.0, command - np.sign(command) * self.limits.dead_zone)
        dead_zone_active = ~np.isclose(command, rate_limited, atol=1e-12)
        self.previous_command = command.copy()
        return ActuatorCommand(
            requested=req,
            saturated=saturated,
            rate_limited=rate_limited,
            command=command,
            effective_force=effective,
            saturation_active=saturation_active,
            rate_limit_active=rate_limit_active,
            dead_zone_active=dead_zone_active,
        )
