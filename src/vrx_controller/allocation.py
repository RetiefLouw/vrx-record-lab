"""Constrained generalized-wrench to thruster-force allocation."""

from dataclasses import dataclass
from typing import List, Optional, Tuple, Union

import numpy as np


def _array(value: Union[np.ndarray, List[float]], shape: Tuple[int, ...], name: str) -> np.ndarray:
    result = np.asarray(value, dtype=float)
    if result.shape != shape:
        raise ValueError(f"{name} must have shape {shape}, got {result.shape}")
    if not np.all(np.isfinite(result)):
        raise ValueError(f"{name} must contain finite values")
    return result.copy()


@dataclass(frozen=True)
class AllocationResult:
    """Allocation result, including the achieved wrench and residual."""

    forces: np.ndarray
    achieved_wrench: np.ndarray
    requested_wrench: np.ndarray
    residual: np.ndarray
    lower_active: np.ndarray
    upper_active: np.ndarray

    @property
    def saturated(self) -> bool:
        return bool(np.any(self.lower_active | self.upper_active))


class ThrusterAllocator:
    """Solve a small box-constrained weighted least-squares allocation.

    For n thrusters, the objective is
    ``||W(B f - tau)||² + regularization ||f - f_previous||²``.
    A deterministic active-set enumeration is used for n <= 10; it gives an
    exact solution for the box-constrained convex quadratic while avoiding a
    solver dependency.  A projected-gradient fallback handles larger arrays.
    """

    def __init__(
        self,
        effectiveness: np.ndarray,
        force_min: np.ndarray,
        force_max: np.ndarray,
        wrench_weights: Optional[np.ndarray] = None,
        regularization: float = 1e-8,
        rate_limit: Optional[np.ndarray] = None,
    ) -> None:
        matrix = np.asarray(effectiveness, dtype=float)
        if matrix.ndim != 2 or matrix.shape[0] != 3 or matrix.shape[1] == 0:
            raise ValueError("effectiveness must have shape (3, n), n > 0")
        if not np.all(np.isfinite(matrix)):
            raise ValueError("effectiveness must contain finite values")
        n = matrix.shape[1]
        low = _array(force_min, (n,), "force_min")
        high = _array(force_max, (n,), "force_max")
        if np.any(low > high):
            raise ValueError("force_min must be no greater than force_max")
        weights = np.ones(3) if wrench_weights is None else _array(wrench_weights, (3,), "wrench_weights")
        if np.any(weights <= 0.0):
            raise ValueError("wrench_weights must be positive")
        if not np.isfinite(regularization) or regularization < 0.0:
            raise ValueError("regularization must be finite and non-negative")
        if rate_limit is not None:
            rates = _array(rate_limit, (n,), "rate_limit")
            if np.any(rates <= 0.0):
                raise ValueError("rate_limit values must be positive")
        else:
            rates = None
        self.effectiveness = matrix.copy()
        self.force_min = low
        self.force_max = high
        self.wrench_weights = weights
        self.regularization = float(regularization)
        self.rate_limit = rates

    @property
    def thruster_count(self) -> int:
        return self.effectiveness.shape[1]

    def bounds(self, dt: float, previous_forces: Optional[np.ndarray]) -> Tuple[np.ndarray, np.ndarray]:
        """Return static plus optional per-cycle slew-rate bounds."""

        low = self.force_min.copy()
        high = self.force_max.copy()
        if self.rate_limit is not None:
            if previous_forces is None:
                raise ValueError("previous_forces is required when rate_limit is configured")
            previous = _array(previous_forces, (self.thruster_count,), "previous_forces")
            if not np.isfinite(dt) or dt <= 0.0:
                raise ValueError("dt must be finite and positive")
            low = np.maximum(low, previous - self.rate_limit * dt)
            high = np.minimum(high, previous + self.rate_limit * dt)
        if np.any(low > high):
            raise ValueError("rate and force limits have no feasible intersection")
        return low, high

    def allocate(
        self,
        requested_wrench: np.ndarray,
        dt: float,
        previous_forces: Optional[np.ndarray] = None,
    ) -> AllocationResult:
        """Allocate a wrench subject to force and optional slew-rate bounds."""

        target = _array(requested_wrench, (3,), "requested_wrench")
        low, high = self.bounds(dt, previous_forces)
        previous = np.zeros(self.thruster_count) if previous_forces is None else _array(previous_forces, (self.thruster_count,), "previous_forces")
        weighted_b = self.wrench_weights[:, None] * self.effectiveness
        weighted_target = self.wrench_weights * target
        hessian = weighted_b.T @ weighted_b + self.regularization * np.eye(self.thruster_count)
        rhs = weighted_b.T @ weighted_target + self.regularization * previous
        if self.thruster_count <= 10:
            forces = self._active_set(hessian, rhs, low, high)
        else:
            forces = self._projected_gradient(hessian, rhs, low, high)
        achieved = self.effectiveness @ forces
        lower_active = np.isclose(forces, low, atol=1e-9)
        upper_active = np.isclose(forces, high, atol=1e-9)
        return AllocationResult(
            forces=forces,
            achieved_wrench=achieved,
            requested_wrench=target,
            residual=achieved - target,
            lower_active=lower_active,
            upper_active=upper_active,
        )

    def _active_set(self, hessian: np.ndarray, rhs: np.ndarray, low: np.ndarray, high: np.ndarray) -> np.ndarray:
        n = len(low)
        best: Optional[np.ndarray] = None
        best_objective = np.inf
        # 0 = free, 1 = lower, 2 = upper.  Lexicographic product order makes
        # degenerate solutions reproducible.
        import itertools

        for states in itertools.product(range(3), repeat=n):
            fixed = np.array([state != 0 for state in states], dtype=bool)
            candidate = np.empty(n, dtype=float)
            candidate[fixed] = np.where(
                np.array([states[i] == 1 for i in range(n)])[fixed],
                low[fixed],
                high[fixed],
            )
            free = ~fixed
            if np.any(free):
                h_ff = hessian[np.ix_(free, free)]
                rhs_f = rhs[free]
                if np.any(fixed):
                    rhs_f = rhs_f - hessian[np.ix_(free, fixed)] @ candidate[fixed]
                try:
                    candidate[free] = np.linalg.solve(h_ff, rhs_f)
                except np.linalg.LinAlgError:
                    candidate[free] = np.linalg.lstsq(h_ff, rhs_f, rcond=None)[0]
            if np.any(candidate < low - 1e-8) or np.any(candidate > high + 1e-8):
                continue
            gradient = hessian @ candidate - rhs
            # KKT: gradient >= 0 at lower bounds, <= 0 at upper bounds.
            if np.any((candidate <= low + 1e-8) & (gradient < -1e-7)):
                continue
            if np.any((candidate >= high - 1e-8) & (gradient > 1e-7)):
                continue
            objective = 0.5 * float(candidate @ hessian @ candidate) - float(rhs @ candidate)
            if objective < best_objective - 1e-12:
                best_objective = objective
                best = candidate.copy()
        if best is None:
            # Numerical fallback should only be reachable for nearly singular
            # matrices with an unusually strict KKT tolerance.
            return self._projected_gradient(hessian, rhs, low, high)
        return np.clip(best, low, high)

    @staticmethod
    def _projected_gradient(hessian: np.ndarray, rhs: np.ndarray, low: np.ndarray, high: np.ndarray) -> np.ndarray:
        eigenvalues = np.linalg.eigvalsh(hessian)
        step = 1.0 / max(float(eigenvalues[-1]), 1e-12)
        result = np.clip(np.linalg.lstsq(hessian, rhs, rcond=None)[0], low, high)
        for _ in range(2000):
            next_result = np.clip(result - step * (hessian @ result - rhs), low, high)
            if np.max(np.abs(next_result - result)) < 1e-11:
                return next_result
            result = next_result
        return result
