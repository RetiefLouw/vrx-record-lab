"""Composition of the reusable station-keeping controller components."""

from dataclasses import dataclass
from typing import Optional

try:
    from typing import Protocol
except ImportError:  # Python 3.6, used by the pinned ROS Melodic image.
    class Protocol(object):
        pass

import numpy as np

from .actuators import ActuatorCommand, ActuatorLimiter
from .allocation import AllocationResult
from .config import ControllerConfig
from .observer import DisturbanceObserver
from .pid import PIDController
from .state import Pose2D, StationKeepingState, pose_error, world_to_body


class ControlLaw(Protocol):
    """Protocol for replacing PID with LQR or nonlinear MPC later."""

    def reset(self) -> None: ...

    def update(self, error: np.ndarray, derivative: np.ndarray, dt: float) -> np.ndarray: ...

    def track_applied(self, requested: np.ndarray, applied: np.ndarray, dt: float) -> None: ...


@dataclass(frozen=True)
class ControllerOutput:
    """Diagnostics and actuation from one simulator-independent control tick."""

    pose_error_world: np.ndarray
    pose_error_body: np.ndarray
    velocity_error_body: np.ndarray
    disturbance_estimate: np.ndarray
    requested_wrench: np.ndarray
    compensated_wrench: np.ndarray
    allocation: AllocationResult
    actuator: ActuatorCommand

    @property
    def command(self) -> np.ndarray:
        return self.actuator.command


class StationKeepingController:
    """Station-keeping composition with seams for future LQR/MPC laws.

    The current default law is a body-frame PID.  A future nonlinear MPC can
    be passed as ``control_law`` while consuming the same state object, model,
    allocator, and actuator interfaces.
    """

    def __init__(self, config: ControllerConfig, control_law: Optional[ControlLaw] = None) -> None:
        self.config = config
        self.pid = PIDController(config.pid)
        self.control_law: ControlLaw = self.pid if control_law is None else control_law
        self.observer: DisturbanceObserver = config.observer()
        self.allocator = config.allocator()
        self.actuator = ActuatorLimiter(config.actuator_limits)
        self.previous_forces = np.zeros(config.effectiveness.shape[1], dtype=float)
        self._last_applied_wrench = np.zeros(3, dtype=float)

    def reset(self) -> None:
        self.control_law.reset()
        self.observer.reset()
        self.actuator.reset()
        self.previous_forces.fill(0.0)
        self._last_applied_wrench.fill(0.0)

    def step(self, state: StationKeepingState, target: Pose2D, dt: float) -> ControllerOutput:
        """Compute one control output from measured state and target pose."""

        if not np.isfinite(dt) or dt <= 0.0:
            raise ValueError("dt must be finite and positive")
        pose_error_world = pose_error(target, state.pose)
        position_error_body = world_to_body(pose_error_world[:2], state.pose.yaw)
        pose_error_body = np.array([position_error_body[0], position_error_body[1], pose_error_world[2]])
        velocity_error_body = state.target_velocity_array() - state.velocity.as_array()
        requested_wrench = self.control_law.update(pose_error_body, velocity_error_body, dt)
        disturbance_estimate = self.observer.update(state.velocity.as_array(), self._last_applied_wrench, dt)
        compensated_wrench = requested_wrench - disturbance_estimate
        allocation = self.allocator.allocate(compensated_wrench, dt, self.previous_forces)
        actuator = self.actuator.apply(allocation.forces, dt)
        self.previous_forces = actuator.effective_force.copy()
        applied_controller_wrench = self.config.effectiveness @ actuator.effective_force
        self.control_law.track_applied(requested_wrench, applied_controller_wrench + disturbance_estimate, dt)
        self._last_applied_wrench = applied_controller_wrench
        return ControllerOutput(
            pose_error_world=pose_error_world,
            pose_error_body=pose_error_body,
            velocity_error_body=velocity_error_body,
            disturbance_estimate=disturbance_estimate,
            requested_wrench=requested_wrench,
            compensated_wrench=compensated_wrench,
            allocation=allocation,
            actuator=actuator,
        )
