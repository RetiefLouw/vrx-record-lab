"""Reusable, simulator-independent station-keeping control components.

The package operates on SI-valued NumPy arrays and small immutable data
objects.  It deliberately has no ROS, Gazebo, VRX, or scorer dependency.
"""

from .actuators import ActuatorCommand, ActuatorLimiter, ActuatorLimits
from .allocation import AllocationResult, ThrusterAllocator
from .angles import angle_error, wrap_angle
from .config import ControllerConfig
from .model import PlanarVehicleModel
from .observer import DisturbanceObserver
from .pid import PIDController, PIDGains
from .geo import quaternion_to_yaw, wgs84_to_local_enu
from .stock_thruster import command_to_force, force_to_command
from .state import BodyVelocity, Pose2D, StationKeepingState, pose_error
from .station_keeping import ControlLaw, ControllerOutput, StationKeepingController
from .uf_mrac import UFMRACController, UFMRACOutput, UFMRACParameters, UFMRACReference

__all__ = [
    "ActuatorCommand",
    "ActuatorLimiter",
    "ActuatorLimits",
    "AllocationResult",
    "BodyVelocity",
    "ControllerConfig",
    "ControlLaw",
    "ControllerOutput",
    "DisturbanceObserver",
    "command_to_force",
    "force_to_command",
    "PIDController",
    "PIDGains",
    "PlanarVehicleModel",
    "Pose2D",
    "quaternion_to_yaw",
    "StationKeepingController",
    "StationKeepingState",
    "ThrusterAllocator",
    "UFMRACController",
    "UFMRACOutput",
    "UFMRACParameters",
    "UFMRACReference",
    "angle_error",
    "pose_error",
    "wrap_angle",
    "wgs84_to_local_enu",
]
