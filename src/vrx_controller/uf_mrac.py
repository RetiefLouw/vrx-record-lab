"""Source-faithful, simulator-independent port of UF's VRX MRAC law.

This module transcribes the control-law portion of the University of Florida
``mrac_controller.py`` released at tag
``7c312eeac2dbaa888adfce5f04ad9a9d85999646``.  It intentionally stops at the
world/body wrench boundary: the historical ROS node published
``/wrench/autonomous`` and left thruster allocation to a separate mapper.

The public evidence is not sufficient for an exact 2019 reproduction.  This
class therefore has no VRX/scorer dependency and makes the recovered
assumptions explicit in :class:`UFMRACParameters`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .angles import angle_error
from .state import Pose2D, StationKeepingState


def _vector(value: object, shape: tuple[int, ...], name: str) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if array.shape != shape:
        raise ValueError(f"{name} must have shape {shape}, got {array.shape}")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain finite values")
    return array.copy()


def _positive_vector(value: object, shape: tuple[int, ...], name: str) -> np.ndarray:
    array = _vector(value, shape, name)
    if np.any(array <= 0.0):
        raise ValueError(f"{name} must be positive")
    return array


def _nonnegative_vector(value: object, shape: tuple[int, ...], name: str) -> np.ndarray:
    array = _vector(value, shape, name)
    if np.any(array < 0.0):
        raise ValueError(f"{name} must be non-negative")
    return array


def _rotation_z(yaw: float) -> np.ndarray:
    """Return the body-to-world rotation used by the UF source."""

    if not np.isfinite(yaw):
        raise ValueError("yaw must be finite")
    c = float(np.cos(yaw))
    s = float(np.sin(yaw))
    return np.array(
        [[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]],
        dtype=float,
    )


@dataclass(frozen=True)
class UFMRACParameters:
    """Recovered final VRX parameters and source constants.

    The gains and reference-model values are the values in the final UF VRX
    launch file.  The remaining constants are the corresponding defaults in
    the tagged ``mrac_controller.py``.  They are parameters of the closest
    public-source port, not claimed hidden phase-3 values.
    """

    kp_body: np.ndarray = field(default_factory=lambda: np.array([1000.0, 1000.0, 5600.0]))
    kd_body: np.ndarray = field(default_factory=lambda: np.array([1200.0, 1200.0, 6000.0]))
    ki: np.ndarray = field(default_factory=lambda: np.array([0.1, 0.1, 0.1]))
    kg: np.ndarray = field(default_factory=lambda: np.full(5, 5.0))
    mass_ref: float = 251.19
    inertia_ref: float = 500.58
    disturbance_limit: np.ndarray = field(default_factory=lambda: np.full(3, 200.0))
    drag_effort_limit: np.ndarray = field(default_factory=lambda: np.full(3, 1000.0))
    learning_radius: float = 10.0
    thrust_max: float = 220.0
    velocity_limit_body_positive: np.ndarray = field(default_factory=lambda: np.array([1.1, 0.45, 0.19]))
    velocity_limit_body_negative: np.ndarray = field(default_factory=lambda: np.array([0.68, 0.45, 0.19]))
    thruster_positions: np.ndarray = field(
        default_factory=lambda: np.array(
            [
                [-1.9000, 1.0000, -0.0123],
                [-1.9000, -1.0000, -0.0123],
                [1.6000, 0.6000, -0.0123],
                [1.6000, -0.6000, -0.0123],
            ]
        )
    )
    thruster_directions: np.ndarray = field(
        default_factory=lambda: np.array(
            [
                [0.7071, 0.7071, 0.0000],
                [0.7071, -0.7071, 0.0000],
                [0.7071, -0.7071, 0.0000],
                [0.7071, 0.7071, 0.0000],
            ]
        )
    )

    def __post_init__(self) -> None:
        for name in ("kp_body", "kd_body", "ki"):
            object.__setattr__(self, name, _vector(getattr(self, name), (3,), name))
        object.__setattr__(self, "kg", _vector(self.kg, (5,), "kg"))
        object.__setattr__(
            self,
            "disturbance_limit",
            _nonnegative_vector(self.disturbance_limit, (3,), "disturbance_limit"),
        )
        object.__setattr__(
            self,
            "drag_effort_limit",
            _nonnegative_vector(self.drag_effort_limit, (3,), "drag_effort_limit"),
        )
        object.__setattr__(
            self,
            "velocity_limit_body_positive",
            _positive_vector(self.velocity_limit_body_positive, (3,), "velocity_limit_body_positive"),
        )
        object.__setattr__(
            self,
            "velocity_limit_body_negative",
            _positive_vector(self.velocity_limit_body_negative, (3,), "velocity_limit_body_negative"),
        )
        positions = np.asarray(self.thruster_positions, dtype=float)
        directions = np.asarray(self.thruster_directions, dtype=float)
        if positions.shape != (4, 3) or not np.all(np.isfinite(positions)):
            raise ValueError("thruster_positions must be a finite (4, 3) array")
        if directions.shape != (4, 3) or not np.all(np.isfinite(directions)):
            raise ValueError("thruster_directions must be a finite (4, 3) array")
        object.__setattr__(self, "thruster_positions", positions.copy())
        object.__setattr__(self, "thruster_directions", directions.copy())
        if not np.isfinite(self.mass_ref) or self.mass_ref <= 0.0:
            raise ValueError("mass_ref must be finite and positive")
        if not np.isfinite(self.inertia_ref) or self.inertia_ref <= 0.0:
            raise ValueError("inertia_ref must be finite and positive")
        if not np.isfinite(self.learning_radius) or self.learning_radius < 0.0:
            raise ValueError("learning_radius must be finite and non-negative")
        if not np.isfinite(self.thrust_max) or self.thrust_max <= 0.0:
            raise ValueError("thrust_max must be finite and positive")

    @property
    def B_body(self) -> np.ndarray:
        """Return the six-DOF source geometry matrix ``B_body`` (6 x 4)."""

        lever_arms = np.cross(self.thruster_positions, self.thruster_directions)
        return np.concatenate((self.thruster_directions.T, lever_arms.T))

    @property
    def planar_effectiveness(self) -> np.ndarray:
        """Return the [Fx, Fy, Mz] rows used by the separate mapper."""

        return self.B_body[[0, 1, 5], :]

    @property
    def D_body_positive(self) -> np.ndarray:
        """Return the source's positive-velocity quadratic drag estimate."""

        maxima = self.B_body.dot(self.thrust_max * np.ones(4))
        signed_y = self.B_body.dot(self.thrust_max * np.array([1.0, -1.0, -1.0, 1.0]))
        signed_yaw = self.B_body.dot(self.thrust_max * np.array([-1.0, 1.0, -1.0, 1.0]))
        return np.abs(np.array([maxima[0], signed_y[1], signed_yaw[5]])) / self.velocity_limit_body_positive**2

    @property
    def D_body_negative(self) -> np.ndarray:
        """Return the source's negative-velocity quadratic drag estimate."""

        maxima = self.B_body.dot(self.thrust_max * np.ones(4))
        signed_y = self.B_body.dot(self.thrust_max * np.array([1.0, -1.0, -1.0, 1.0]))
        signed_yaw = self.B_body.dot(self.thrust_max * np.array([-1.0, 1.0, -1.0, 1.0]))
        # The tagged source uses the same selected magnitudes for positive and
        # negative velocity, then changes only the velocity-limit denominator.
        # Keep the intermediate sign-pattern calculations visible because they
        # are part of the recovered source initialization.
        return np.abs(np.array([maxima[0], signed_y[1], signed_yaw[5]])) / self.velocity_limit_body_negative**2


@dataclass(frozen=True)
class UFMRACReference:
    """External trajectory state consumed by the UF controller.

    Velocities and accelerations are expressed in the ENU/world frame.  This
    is the representation after the historical ROS node rotated the incoming
    trajectory twist by the reference quaternion.  A plain :class:`Pose2D`
    is accepted by :meth:`UFMRACController.step` as a stationary reference.
    """

    pose: Pose2D
    linear_velocity_world: np.ndarray = field(default_factory=lambda: np.zeros(2))
    yaw_rate: float = 0.0
    linear_acceleration_world: np.ndarray = field(default_factory=lambda: np.zeros(2))
    yaw_acceleration: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "linear_velocity_world", _vector(self.linear_velocity_world, (2,), "linear_velocity_world"))
        object.__setattr__(self, "linear_acceleration_world", _vector(self.linear_acceleration_world, (2,), "linear_acceleration_world"))
        if not np.isfinite(self.yaw_rate) or not np.isfinite(self.yaw_acceleration):
            raise ValueError("reference yaw rates must be finite")

    @classmethod
    def stationary(cls, pose: Pose2D) -> "UFMRACReference":
        return cls(pose=pose)


@dataclass(frozen=True)
class UFMRACOutput:
    """One UF MRAC control tick, ending at the body-frame wrench boundary."""

    pose_error_world: np.ndarray
    velocity_error_world: np.ndarray
    regressor: np.ndarray
    feedforward_wrench: np.ndarray
    proportional_derivative_wrench: np.ndarray
    disturbance_estimate: np.ndarray
    drag_parameters: np.ndarray
    drag_effort: np.ndarray
    wrench_world: np.ndarray
    wrench_body: np.ndarray
    learning_enabled: bool

    @property
    def command(self) -> np.ndarray:
        """Alias for the published body wrench for generic control tooling."""

        return self.wrench_body.copy()


class UFMRACController:
    """Closest public-source port of UF's external-trajectory MRAC controller.

    ``step`` follows the tagged source order: calculate the wrench from the
    current estimates, then update the adaptive estimates.  Consequently the
    returned wrench does not include the just-updated estimates.  Thruster
    mapping is deliberately outside this class, matching the historical
    ``/wrench/autonomous`` interface.
    """

    LEARN_WRENCHES = frozenset(("/wrench/autonomous", "autonomous"))

    def __init__(self, parameters: UFMRACParameters | None = None, learning_enabled: bool = False) -> None:
        self.parameters = UFMRACParameters() if parameters is None else parameters
        self.learning_enabled = bool(learning_enabled)
        self.only_pd = False
        self.disturbance_estimate = np.zeros(3, dtype=float)
        self.drag_parameters = np.zeros(5, dtype=float)
        self.last_output: UFMRACOutput | None = None

    @property
    def dist_est(self) -> np.ndarray:
        """Source-compatible name for the adaptive disturbance estimate."""

        return self.disturbance_estimate

    @property
    def drag_est(self) -> np.ndarray:
        """Source-compatible name for the adaptive five-parameter estimate."""

        return self.drag_parameters

    @property
    def only_PD(self) -> bool:
        """Source-compatible spelling of :attr:`only_pd`."""

        return self.only_pd

    @only_PD.setter
    def only_PD(self, value: bool) -> None:
        self.only_pd = bool(value)

    def reset(self) -> None:
        """Reset adaptive state and the last diagnostic output."""

        self.reset_adaptation()
        self.last_output = None

    def reset_adaptation(self) -> None:
        self.disturbance_estimate.fill(0.0)
        self.drag_parameters.fill(0.0)

    def set_learning(self, selected_wrench: str | bool) -> None:
        """Apply the tagged node's ``/wrench/selected`` learning semantics."""

        if isinstance(selected_wrench, str):
            enabled = selected_wrench in self.LEARN_WRENCHES
        else:
            enabled = bool(selected_wrench)
        if enabled == self.learning_enabled:
            return
        self.learning_enabled = enabled
        if not enabled:
            self.reset_adaptation()

    @staticmethod
    def drag_regressor(world_velocity: np.ndarray, yaw: float, yaw_rate: float) -> np.ndarray:
        """Return the exact five-column regressor from the UF tag."""

        velocity = _vector(world_velocity, (2,), "world_velocity")
        if not np.isfinite(yaw) or not np.isfinite(yaw_rate):
            raise ValueError("yaw and yaw_rate must be finite")
        vx, vy = velocity
        c = float(np.cos(yaw))
        s = float(np.sin(yaw))
        c2 = float(np.cos(2.0 * yaw))
        s2 = float(np.sin(2.0 * yaw))
        r = float(yaw_rate)
        return np.array(
            [
                [vx * c**2 + vy * s * c, vx / 2.0 - vx * c2 / 2.0 - vy * s2 / 2.0, -r * s, -r * c, 0.0],
                [vy / 2.0 - vy * c2 / 2.0 + vx * s2 / 2.0, vy * c**2 - vx * c * s, r * c, -r * s, 0.0],
                [0.0, 0.0, vy * c - vx * s, -vx * c - vy * s, r],
            ],
            dtype=float,
        )

    @staticmethod
    def virtual_thruster_map(wrench: np.ndarray, effectiveness: np.ndarray, thrust_max: float = 220.0) -> np.ndarray:
        """Transcribe the source's pseudoinverse map for reference-model use.

        This helper is not used by the external LQ-RRT path.  The real vessel
        still needs its separate thruster-mapper node.
        """

        target = _vector(wrench, (3,), "wrench")
        matrix = np.asarray(effectiveness, dtype=float)
        if matrix.shape != (3, 4) or not np.all(np.isfinite(matrix)):
            raise ValueError("effectiveness must be a finite (3, 4) matrix")
        if not np.isfinite(thrust_max) or thrust_max <= 0.0:
            raise ValueError("thrust_max must be finite and positive")
        command = np.linalg.pinv(matrix).dot(target)
        command_max = float(np.max(np.abs(command)))
        if command_max > thrust_max:
            command = (thrust_max / command_max) * command
        return command

    def step(self, state: StationKeepingState, reference: UFMRACReference | Pose2D, dt: float) -> UFMRACOutput:
        """Calculate one world/body wrench from measured state and reference."""

        if not np.isfinite(dt) or dt <= 0.0:
            raise ValueError("dt must be finite and positive")
        if isinstance(reference, Pose2D):
            reference = UFMRACReference.stationary(reference)
        if not isinstance(reference, UFMRACReference):
            raise TypeError("reference must be UFMRACReference or Pose2D")

        yaw = state.pose.yaw
        rotation = _rotation_z(yaw)
        body_velocity = np.concatenate((state.velocity.as_array()[:2], [0.0]))
        world_velocity = rotation.dot(body_velocity)[:2]
        yaw_rate = float(rotation.dot(np.array([0.0, 0.0, state.velocity.yaw_rate]))[2])
        pose_error_world = np.array(
            [
                reference.pose.x - state.pose.x,
                reference.pose.y - state.pose.y,
                angle_error(reference.pose.yaw, state.pose.yaw),
            ],
            dtype=float,
        )
        velocity_error_world = np.array(
            [
                reference.linear_velocity_world[0] - world_velocity[0],
                reference.linear_velocity_world[1] - world_velocity[1],
                reference.yaw_rate - yaw_rate,
            ],
            dtype=float,
        )

        kp_world = rotation.dot(np.diag(self.parameters.kp_body)).dot(rotation.T)
        kd_world = rotation.dot(np.diag(self.parameters.kd_body)).dot(rotation.T)
        proportional_derivative = kp_world.dot(pose_error_world) + kd_world.dot(velocity_error_world)
        feedforward = np.array(
            [
                self.parameters.mass_ref * reference.linear_acceleration_world[0],
                self.parameters.mass_ref * reference.linear_acceleration_world[1],
                self.parameters.inertia_ref * reference.yaw_acceleration,
            ],
            dtype=float,
        )
        regressor = self.drag_regressor(world_velocity, yaw, yaw_rate)

        if self.only_pd:
            drag_effort = np.zeros(3, dtype=float)
            self.reset_adaptation()
            wrench_world = proportional_derivative.copy()
        else:
            drag_effort = np.clip(
                regressor.dot(self.drag_parameters),
                -self.parameters.drag_effort_limit,
                self.parameters.drag_effort_limit,
            )
            wrench_world = proportional_derivative + feedforward + self.disturbance_estimate + drag_effort
            # Match the source ordering: adaptive estimates change after the
            # wrench has been formed and are therefore used next cycle.
            if self.learning_enabled and np.linalg.norm(pose_error_world[:2]) < self.parameters.learning_radius:
                self.disturbance_estimate = np.clip(
                    self.disturbance_estimate + self.parameters.ki * pose_error_world * dt,
                    -self.parameters.disturbance_limit,
                    self.parameters.disturbance_limit,
                )
                self.drag_parameters = self.drag_parameters + (
                    self.parameters.kg * (regressor.T.dot(pose_error_world + velocity_error_world)) * dt
                )

        wrench_body = rotation.T.dot(wrench_world)
        output = UFMRACOutput(
            pose_error_world=pose_error_world,
            velocity_error_world=velocity_error_world,
            regressor=regressor,
            feedforward_wrench=feedforward,
            proportional_derivative_wrench=proportional_derivative,
            disturbance_estimate=self.disturbance_estimate.copy(),
            drag_parameters=self.drag_parameters.copy(),
            drag_effort=drag_effort.copy(),
            wrench_world=wrench_world.copy(),
            wrench_body=wrench_body.copy(),
            learning_enabled=self.learning_enabled,
        )
        self.last_output = output
        return output
