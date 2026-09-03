"""Small, deterministic statistics implementation with no SciPy dependency."""

from __future__ import annotations

import math
from statistics import mean, median
from typing import Iterable, List


# Two-sided 95% Student-t critical values for df 1..30.  The normal value is
# used after df 30. Keeping this table in source makes CI and clean-clone runs
# independent of the installed statistics stack.
_T95 = {
    1: 12.706,
    2: 4.303,
    3: 3.182,
    4: 2.776,
    5: 2.571,
    6: 2.447,
    7: 2.365,
    8: 2.306,
    9: 2.262,
    10: 2.228,
    11: 2.201,
    12: 2.179,
    13: 2.160,
    14: 2.145,
    15: 2.131,
    16: 2.120,
    17: 2.110,
    18: 2.101,
    19: 2.093,
    20: 2.086,
    21: 2.080,
    22: 2.074,
    23: 2.069,
    24: 2.064,
    25: 2.060,
    26: 2.056,
    27: 2.052,
    28: 2.048,
    29: 2.045,
    30: 2.042,
}


def finite_scores(scores: Iterable[float]) -> List[float]:
    values = [float(score) for score in scores]
    if not values:
        raise ValueError("at least one score is required")
    if not all(math.isfinite(value) for value in values):
        raise ValueError("scores must be finite numbers")
    return values


def sample_stddev(values: Iterable[float]) -> float:
    scores = finite_scores(values)
    if len(scores) < 2:
        return 0.0
    average = mean(scores)
    return math.sqrt(sum((score - average) ** 2 for score in scores) / (len(scores) - 1))


def aggregate_scores(scores: Iterable[float], score_direction: str = "minimize") -> dict:
    """Compute the aggregate fields required by the result schema.

    The interval is a two-sided 95% Student-t interval for the mean. A single
    observation has a degenerate interval because its sample variance is zero;
    that is reported explicitly rather than inventing uncertainty.
    """

    values = finite_scores(scores)
    average = mean(values)
    deviation = sample_stddev(values)
    n = len(values)
    if n == 1:
        half_width = 0.0
    else:
        critical = _T95.get(n - 1, 1.959964)
        half_width = critical * deviation / math.sqrt(n)
    if score_direction == "minimize":
        worst = max(values)
    elif score_direction == "maximize":
        worst = min(values)
    else:
        raise ValueError("score_direction must be 'minimize' or 'maximize'")
    return {
        "count": n,
        "mean": average,
        "median": median(values),
        "stddev": deviation,
        "confidence_interval_95": {
            "low": average - half_width,
            "high": average + half_width,
            "method": "student_t_two_sided_95_percent",
        },
        "worst_case": worst,
        "score_direction": score_direction,
    }


def empty_aggregate(score_direction: str = "minimize") -> dict:
    return {
        "count": 0,
        "mean": None,
        "median": None,
        "stddev": None,
        "confidence_interval_95": {
            "low": None,
            "high": None,
            "method": "student_t_two_sided_95_percent",
        },
        "worst_case": None,
        "score_direction": score_direction,
    }


def aggregates_match(expected: dict, actual: dict, tolerance: float = 1e-9) -> bool:
    """Compare an aggregate to a recomputed aggregate, including null fields."""

    numeric_fields = ("mean", "median", "stddev", "worst_case")
    if expected.get("count") != actual.get("count"):
        return False
    if expected.get("score_direction") != actual.get("score_direction"):
        return False
    for field in numeric_fields:
        left, right = expected.get(field), actual.get(field)
        if left is None or right is None:
            if left is not right:
                return False
        elif not math.isclose(float(left), float(right), rel_tol=tolerance, abs_tol=tolerance):
            return False
    expected_ci = expected.get("confidence_interval_95", {})
    actual_ci = actual.get("confidence_interval_95", {})
    if expected_ci.get("method") != actual_ci.get("method"):
        return False
    for field in ("low", "high"):
        left, right = expected_ci.get(field), actual_ci.get(field)
        if left is None or right is None:
            if left is not right:
                return False
        elif not math.isclose(float(left), float(right), rel_tol=tolerance, abs_tol=tolerance):
            return False
    return True
