"""Angle utilities with explicit shortest-path semantics."""

import math


def wrap_angle(angle: float) -> float:
    """Return ``angle`` in the half-open interval [-pi, pi).

    The explicit ``-pi`` tie-break makes the function deterministic at the
    branch cut.  Callers should not use ordinary subtraction for heading
    errors; ``angle_error(target, current)`` is the intended API.
    """

    angle = float(angle)
    if not math.isfinite(angle):
        raise ValueError("angle must be finite")
    wrapped = (angle + math.pi) % (2.0 * math.pi) - math.pi
    # Guard against a platform returning +pi at the upper endpoint.
    return -math.pi if wrapped >= math.pi else wrapped


def angle_error(target: float, current: float) -> float:
    """Return the shortest signed rotation from ``current`` to ``target``."""

    return wrap_angle(float(target) - float(current))
