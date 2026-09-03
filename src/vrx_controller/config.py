"""Validated controller configuration with explicit, serializable fields."""

from __future__ import annotations

from dataclasses import dataclass, field
import json

import numpy as np

from .actuators import ActuatorLimits
from .allocation import ThrusterAllocator
from .model import PlanarVehicleModel
from .observer import DisturbanceObserver
from .pid import PIDGains


def _json_optional_vector(values: np.ndarray) -> list[float | None] | None:
    if np.all(~np.isfinite(values)):
        return None
    return [float(value) if np.isfinite(value) else None for value in values]


def _parse_optional_vector(value: object, negative_infinity: bool) -> np.ndarray | None:
    if value is None:
        return None
    values = np.asarray(value, dtype=object)
    if values.shape != (3,):
        raise ValueError("integral bounds must have shape (3,)")
    infinity = -np.inf if negative_infinity else np.inf
    return np.array([infinity if item is None else float(item) for item in values], dtype=float)


@dataclass(frozen=True)
class ControllerConfig:
    """All numeric choices needed to assemble a station-keeping controller."""

    model: PlanarVehicleModel
    pid: PIDGains
    effectiveness: np.ndarray
    actuator_limits: ActuatorLimits
    observer_bandwidth_hz: float = 1.0
    wrench_weights: np.ndarray = field(default_factory=lambda: np.ones(3))
    allocation_regularization: float = 1e-8

    def __post_init__(self) -> None:
        matrix = np.asarray(self.effectiveness, dtype=float)
        if matrix.ndim != 2 or matrix.shape[0] != 3:
            raise ValueError("effectiveness must have shape (3, n)")
        if matrix.shape[1] != len(self.actuator_limits.force_min):
            raise ValueError("effectiveness columns must match actuator count")
        if not np.all(np.isfinite(matrix)):
            raise ValueError("effectiveness must contain finite values")
        weights = np.asarray(self.wrench_weights, dtype=float)
        if weights.shape != (3,) or np.any(~np.isfinite(weights)) or np.any(weights <= 0.0):
            raise ValueError("wrench_weights must be a finite positive vector of shape (3,)")
        if not np.isfinite(self.observer_bandwidth_hz) or self.observer_bandwidth_hz <= 0.0:
            raise ValueError("observer_bandwidth_hz must be finite and positive")
        if not np.isfinite(self.allocation_regularization) or self.allocation_regularization < 0.0:
            raise ValueError("allocation_regularization must be finite and non-negative")
        object.__setattr__(self, "effectiveness", matrix.copy())
        object.__setattr__(self, "wrench_weights", weights.copy())

    def allocator(self) -> ThrusterAllocator:
        return ThrusterAllocator(
            self.effectiveness,
            self.actuator_limits.force_min,
            self.actuator_limits.force_max,
            self.wrench_weights,
            self.allocation_regularization,
        )

    def observer(self) -> DisturbanceObserver:
        return DisturbanceObserver(self.model, self.observer_bandwidth_hz)

    def to_dict(self) -> dict[str, object]:
        """Return JSON-compatible configuration data."""

        return {
            "model": {"mass": self.model.mass.tolist(), "damping": self.model.damping.tolist()},
            "pid": {
                "kp": self.pid.kp.tolist(),
                "ki": self.pid.ki.tolist(),
                "kd": self.pid.kd.tolist(),
                "output_min": self.pid.output_min.tolist(),
                "output_max": self.pid.output_max.tolist(),
                "integral_min": _json_optional_vector(self.pid.integral_min),
                "integral_max": _json_optional_vector(self.pid.integral_max),
                "anti_windup_gain": self.pid.anti_windup_gain.tolist(),
            },
            "effectiveness": self.effectiveness.tolist(),
            "actuator_limits": {
                "force_min": self.actuator_limits.force_min.tolist(),
                "force_max": self.actuator_limits.force_max.tolist(),
                "rate_limit": self.actuator_limits.rate_limit.tolist(),
                "dead_zone": self.actuator_limits.dead_zone.tolist(),
                "dead_zone_mode": self.actuator_limits.dead_zone_mode,
            },
            "observer_bandwidth_hz": self.observer_bandwidth_hz,
            "wrench_weights": self.wrench_weights.tolist(),
            "allocation_regularization": self.allocation_regularization,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "ControllerConfig":
        """Construct a validated configuration from JSON-like mappings."""

        model_data = data["model"]
        pid_data = data["pid"]
        actuator_data = data["actuator_limits"]
        if not isinstance(model_data, dict) or not isinstance(pid_data, dict) or not isinstance(actuator_data, dict):
            raise ValueError("model, pid, and actuator_limits must be mappings")
        model = PlanarVehicleModel(model_data["mass"], model_data["damping"])
        pid = PIDGains(
            pid_data["kp"],
            pid_data["ki"],
            pid_data["kd"],
            pid_data["output_min"],
            pid_data["output_max"],
            _parse_optional_vector(pid_data.get("integral_min"), negative_infinity=True),
            _parse_optional_vector(pid_data.get("integral_max"), negative_infinity=False),
            pid_data.get("anti_windup_gain", 1.0),
        )
        actuator_limits = ActuatorLimits(
            actuator_data["force_min"],
            actuator_data["force_max"],
            actuator_data["rate_limit"],
            actuator_data["dead_zone"],
            actuator_data.get("dead_zone_mode", "zero"),
        )
        return cls(
            model=model,
            pid=pid,
            effectiveness=data["effectiveness"],
            actuator_limits=actuator_limits,
            observer_bandwidth_hz=data.get("observer_bandwidth_hz", 1.0),
            wrench_weights=data.get("wrench_weights", np.ones(3)),
            allocation_regularization=data.get("allocation_regularization", 1e-8),
        )

    @classmethod
    def from_json(cls, text: str) -> "ControllerConfig":
        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            raise ValueError("controller configuration JSON must contain an object")
        return cls.from_dict(parsed)
