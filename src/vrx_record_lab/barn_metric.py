"""Strict scorer for the public BARN navigation log format.

The BARN challenge reports one line per trial as::

    world_idx succeeded collided timeout traversal_time

The organizer's 2024 metric is ``success * OT / clip(AT, 2*OT, 8*OT)``.
This module deliberately keeps scoring independent of ROS/Gazebo so a saved
log can be audited in a clean environment.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import numpy as np


@dataclass(frozen=True)
class BarnRun:
    world_idx: int
    succeeded: bool
    collided: bool
    timeout: bool
    traversal_time_s: float
    logged_metric: float | None = None


def parse_log(lines: Iterable[str]) -> list[BarnRun]:
    """Parse BARN output lines and reject malformed/non-finite records."""

    runs: list[BarnRun] = []
    for line_number, raw in enumerate(lines, 1):
        text = raw.strip()
        if not text:
            continue
        fields = text.split()
        if len(fields) not in (5, 6):
            raise ValueError(f"line {line_number}: expected 5 fields (or 6 with a logged metric)")
        try:
            world_idx = int(fields[0])
            flags = [int(value) for value in fields[1:4]]
            traversal_time_s = float(fields[4])
            if len(fields) == 6:
                logged_metric = float(fields[5])
        except ValueError as exc:
            raise ValueError(f"line {line_number}: invalid field") from exc
        if world_idx < 0 or any(flag not in (0, 1) for flag in flags):
            raise ValueError(f"line {line_number}: invalid world or flag")
        if not math.isfinite(traversal_time_s) or traversal_time_s < 0:
            raise ValueError(f"line {line_number}: traversal time must be finite")
        if len(fields) == 6 and (not math.isfinite(logged_metric) or logged_metric < 0):
            raise ValueError(f"line {line_number}: logged metric must be finite and non-negative")
        runs.append(
            BarnRun(
                world_idx,
                bool(flags[0]),
                bool(flags[1]),
                bool(flags[2]),
                traversal_time_s,
                logged_metric if len(fields) == 6 else None,
            )
        )
    return runs


def path_length_to_optimal_time(
    path_file: str | Path,
    *,
    init_position: tuple[float, float] = (-2.0, 3.0),
    goal_offset: tuple[float, float] = (0.0, 10.0),
    radius_m: float = 0.075,
    max_speed_mps: float = 2.0,
) -> float:
    """Convert an official BARN path ``.npy`` file into OT seconds."""

    points = np.asarray(np.load(path_file), dtype=float)
    if points.ndim != 2 or points.shape[1] != 2 or len(points) == 0:
        raise ValueError(f"invalid BARN path array: {path_file}")
    scale = 2.0 * radius_m
    r_shift = -radius_m - (30 * radius_m * 2)
    c_shift = radius_m + 5.0
    gazebo = np.column_stack((points[:, 0] * scale + r_shift, points[:, 1] * scale + c_shift))
    gazebo = np.vstack((init_position, gazebo, (init_position[0] + goal_offset[0], init_position[1] + goal_offset[1])))
    path_length = float(np.linalg.norm(np.diff(gazebo, axis=0), axis=1).sum())
    optimal_time = path_length / max_speed_mps
    if not math.isfinite(optimal_time) or optimal_time <= 0:
        raise ValueError(f"invalid optimal time for {path_file}")
    return optimal_time


def score_run(run: BarnRun, optimal_time_s: float, *, lower_ot: float = 2.0, upper_ot: float = 8.0) -> float:
    """Score one run using the organizer's bounded 2024 metric."""

    if not math.isfinite(optimal_time_s) or optimal_time_s <= 0:
        raise ValueError("optimal time must be finite and positive")
    if lower_ot <= 0 or upper_ot < lower_ot:
        raise ValueError("invalid OT clipping bounds")
    if not run.succeeded:
        return 0.0
    denominator = min(max(run.traversal_time_s, lower_ot * optimal_time_s), upper_ot * optimal_time_s)
    return optimal_time_s / denominator


def aggregate(
    runs: Sequence[BarnRun],
    optimal_times_s: Mapping[int, float],
    *,
    expected_worlds: Sequence[int] | None = None,
    trials_per_world: int = 10,
) -> dict[str, object]:
    """Strictly aggregate a complete, balanced BARN public suite."""

    worlds = tuple(expected_worlds if expected_worlds is not None else sorted(optimal_times_s))
    if not worlds or trials_per_world <= 0:
        raise ValueError("expected worlds and trials_per_world are required")
    counts: dict[int, int] = {world: 0 for world in worlds}
    per_world: dict[int, list[float]] = {world: [] for world in worlds}
    success = collision = timeout = 0
    logged_metric_mismatches = 0
    max_logged_metric_delta = 0.0
    for run in runs:
        if run.world_idx not in optimal_times_s or run.world_idx not in counts:
            raise ValueError(f"unexpected world index {run.world_idx}")
        counts[run.world_idx] += 1
        if counts[run.world_idx] > trials_per_world:
            raise ValueError(f"duplicate/excess trial for world {run.world_idx}")
        score = score_run(run, optimal_times_s[run.world_idx])
        if run.logged_metric is not None:
            delta = abs(run.logged_metric - score)
            max_logged_metric_delta = max(max_logged_metric_delta, delta)
            # Some upstream BARN outputs log a metric using run.py's -2.25 m
            # start while report_test.py recomputes OT from -2.0 m. Preserve
            # the discrepancy as audit metadata and score from the evaluator's
            # recomputation, rather than silently trusting the sixth column.
            if delta > 5.1e-4:
                logged_metric_mismatches += 1
        per_world[run.world_idx].append(score)
        success += int(run.succeeded)
        collision += int(run.collided)
        timeout += int(run.timeout)
    missing = [world for world, count in counts.items() if count != trials_per_world]
    if missing:
        raise ValueError(f"incomplete worlds: {missing}")
    world_means = {str(world): float(sum(values) / len(values)) for world, values in per_world.items()}
    all_scores = [score for values in per_world.values() for score in values]
    return {
        "world_count": len(worlds),
        "trials_per_world": trials_per_world,
        "trial_count": len(all_scores),
        "overall_score": float(sum(world_means.values()) / len(world_means)),
        "mean_trial_score": float(sum(all_scores) / len(all_scores)),
        "success_rate": success / len(all_scores),
        "collision_rate": collision / len(all_scores),
        "timeout_rate": timeout / len(all_scores),
        "logged_metric_mismatches": logged_metric_mismatches,
        "max_logged_metric_delta": max_logged_metric_delta,
        "per_world_score": world_means,
    }
