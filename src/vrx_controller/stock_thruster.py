"""Mapping used by the stock VRX WAM-V thruster plugin.

The 2019 T configuration accepts ``std_msgs/Float32`` commands in [-1, 1]
and uses mapping type 1 (the documented generalized logistic function).  The
allocator works in force units, so the ROS node uses this exact mapping to
convert allocated force back into the stock command space.
"""

import math


def _glf(value, lower, upper, growth, shape, offset, midpoint):
    return lower + (upper - lower) / (offset + math.exp(-growth * (value - midpoint))) ** (1.0 / shape)


def command_to_force(command, max_forward=250.0, max_reverse=-100.0):
    """Evaluate the stock mapping for a normalized command."""

    command = max(-1.0, min(1.0, float(command)))
    if command > 0.01:
        return min(_glf(command, 0.01, 59.82, 5.0, 0.38, 0.56, 0.28), float(max_forward))
    if command == 0.0:
        return 0.0
    return max(_glf(command, -199.13, -0.09, 8.84, 5.34, 0.99, -0.57), float(max_reverse))


def force_to_command(force, max_forward=250.0, max_reverse=-100.0):
    """Invert the stock mapping with a bounded deterministic bisection."""

    force = float(force)
    if not math.isfinite(force):
        raise ValueError("force must be finite")
    if abs(force) < 0.1:
        return 0.0
    if force > 0.0:
        target = min(force, float(max_forward))
        low, high = 0.010000001, 1.0
        if target <= command_to_force(low, max_forward, max_reverse):
            return 0.01
    else:
        target = max(force, float(max_reverse))
        low, high = -1.0, -0.010000001
        if target >= command_to_force(high, max_forward, max_reverse):
            return 0.0
    for _ in range(60):
        middle = 0.5 * (low + high)
        value = command_to_force(middle, max_forward, max_reverse)
        if value < target:
            low = middle
        else:
            high = middle
    return 0.5 * (low + high)

