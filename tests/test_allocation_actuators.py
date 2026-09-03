from __future__ import annotations

import numpy as np

from vrx_controller import ActuatorLimiter, ActuatorLimits, ThrusterAllocator


def test_allocator_reproduces_feasible_wrench(effectiveness: np.ndarray) -> None:
    allocator = ThrusterAllocator(effectiveness, np.full(4, -10.0), np.full(4, 10.0))
    target = effectiveness @ np.array([1.0, 2.0, 3.0, 4.0])
    result = allocator.allocate(target, 0.1)
    np.testing.assert_allclose(result.achieved_wrench, target, atol=1e-7)
    assert np.all(result.forces >= -10.0)
    assert np.all(result.forces <= 10.0)
    assert not result.saturated


def test_allocator_clamps_infeasible_wrench(effectiveness: np.ndarray) -> None:
    allocator = ThrusterAllocator(effectiveness, np.full(4, -1.0), np.full(4, 1.0))
    result = allocator.allocate(np.array([100.0, 0.0, 0.0]), 0.1)
    assert result.saturated
    assert np.all(result.forces <= 1.0 + 1e-12)
    assert np.all(result.forces >= -1.0 - 1e-12)
    assert np.linalg.norm(result.residual) > 0.0


def test_allocator_can_enforce_slew_bounds(effectiveness: np.ndarray) -> None:
    allocator = ThrusterAllocator(
        effectiveness,
        np.full(4, -10.0),
        np.full(4, 10.0),
        rate_limit=np.full(4, 2.0),
    )
    result = allocator.allocate(np.full(3, 10.0), dt=0.25, previous_forces=np.zeros(4))
    assert np.all(np.abs(result.forces) <= 0.5 + 1e-9)


def test_actuator_applies_saturation_rate_limit_and_zero_dead_zone() -> None:
    limits = ActuatorLimits(
        force_min=np.array([-5.0, -5.0]),
        force_max=np.array([5.0, 5.0]),
        rate_limit=np.array([2.0, 2.0]),
        dead_zone=np.array([0.5, 0.5]),
    )
    limiter = ActuatorLimiter(limits)
    first = limiter.apply(np.array([10.0, -10.0]), 1.0)
    np.testing.assert_allclose(first.command, [2.0, -2.0])
    assert np.all(first.saturation_active)
    assert np.all(first.rate_limit_active)
    second = limiter.apply(np.array([0.2, -0.2]), 1.0)
    np.testing.assert_allclose(second.command, np.zeros(2))
    assert np.all(second.dead_zone_active)


def test_actuator_compensates_dead_zone_while_reporting_effective_force() -> None:
    limits = ActuatorLimits(
        force_min=np.array([-5.0]),
        force_max=np.array([5.0]),
        rate_limit=np.array([100.0]),
        dead_zone=np.array([0.5]),
        dead_zone_mode="compensate",
    )
    output = ActuatorLimiter(limits).apply(np.array([2.0]), 0.1)
    np.testing.assert_allclose(output.command, [2.5])
    np.testing.assert_allclose(output.effective_force, [2.0])
