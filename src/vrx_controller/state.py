"""Small state objects shared by controller components."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .angles import angle_error


def _finite_vector(value: np.ndarray | list[float] | tuple[float, ...], size: int, name: str) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if array.shape != (size,):
        raise ValueError(f"{name} must have shape ({size},), got {array.shape}")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain only finite values")
    return array.copy()


@dataclass(frozen=True)
class Pose2D:
    """Planar pose in a right-handed world frame; position is metres, yaw radians."""

    x: float
    y: float
    yaw: float

    def __post_init__(self) -> None:
        if not np.all(np.isfinite([self.x, self.y, self.yaw])):
            raise ValueError("pose values must be finite")


@dataclass(frozen=True)
class BodyVelocity:
    """Body-frame velocity [surge, sway, yaw-rate] in m/s, m/s, rad/s."""

    surge: float
    sway: float
    yaw_rate: float

    def as_array(self) -> np.ndarray:
        return _finite_vector([self.surge, self.sway, self.yaw_rate], 3, "velocity")


@dataclass(frozen=True)
class StationKeepingState:
    """Measured state and optional target velocity, independent of a simulator."""

    pose: Pose2D
    velocity: BodyVelocity
    target_velocity: BodyVelocity | None = None

    def target_velocity_array(self) -> np.ndarray:
        if self.target_velocity is None:
            return np.zeros(3, dtype=float)
        return self.target_velocity.as_array()


def pose_error(target: Pose2D, current: Pose2D) -> np.ndarray:
    """Return [target_x-current_x, target_y-current_y, shortest yaw error]."""

    return np.array(
        [target.x - current.x, target.y - current.y, angle_error(target.yaw, current.yaw)],
        dtype=float,
    )


def world_to_body(vector_xy: np.ndarray, yaw: float) -> np.ndarray:
    """Rotate a world-frame planar vector into the current body frame."""

    vector = _finite_vector(vector_xy, 2, "vector_xy")
    c = float(np.cos(yaw))
    s = float(np.sin(yaw))
    return np.array([c * vector[0] + s * vector[1], -s * vector[0] + c * vector[1]])
