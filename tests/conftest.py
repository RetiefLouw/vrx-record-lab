from __future__ import annotations

import numpy as np
import pytest

from vrx_controller import ActuatorLimits, ControllerConfig, PIDGains, PlanarVehicleModel


@pytest.fixture
def effectiveness() -> np.ndarray:
    # Deliberately simple full-row-rank matrix for numerical tests.  The
    # repository has no recovered VRX thruster geometry yet.
    return np.array(
        [
            [1.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 1.0],
            [1.0, -1.0, 1.0, -1.0],
        ]
    )


@pytest.fixture
def config(effectiveness: np.ndarray) -> ControllerConfig:
    return ControllerConfig(
        model=PlanarVehicleModel(
            mass=np.diag([4.0, 5.0, 2.0]),
            damping=np.diag([1.0, 1.5, 0.5]),
        ),
        pid=PIDGains(
            kp=np.array([2.0, 2.0, 1.0]),
            ki=np.array([0.3, 0.3, 0.1]),
            kd=np.array([1.0, 1.0, 0.5]),
            output_min=np.full(3, -20.0),
            output_max=np.full(3, 20.0),
            integral_min=np.full(3, -50.0),
            integral_max=np.full(3, 50.0),
            anti_windup_gain=np.full(3, 1.0),
        ),
        effectiveness=effectiveness,
        actuator_limits=ActuatorLimits(
            force_min=np.full(4, -5.0),
            force_max=np.full(4, 5.0),
            rate_limit=np.full(4, 100.0),
            dead_zone=np.full(4, 0.1),
        ),
        observer_bandwidth_hz=2.0,
        wrench_weights=np.array([1.0, 1.0, 0.5]),
    )
