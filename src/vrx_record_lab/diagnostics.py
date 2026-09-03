"""Offline extraction of controller and task diagnostics from trial artifacts.

The extractor intentionally consumes JSONL emitted by the ROS-side monitor and
phase-2 collector. It does not import ROS, read a rosbag, or recompute the VRX
score. Its metrics are engineering diagnostics for Q-03: acquisition time,
position/heading error, actuator saturation, and first/last-window error.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping


DIAGNOSTICS_SCHEMA_VERSION = "vrx-controller-diagnostics/v1"
FORCE_MIN_N = (-100.0, -100.0, -100.0)
FORCE_MAX_N = (240.0, 240.0, 240.0)
FORCE_SATURATION_TOLERANCE_N = 1e-6


class DiagnosticsError(ValueError):
    """A diagnostics stream is missing, malformed, or internally inconsistent."""


def _finite(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise DiagnosticsError(f"{name} must be a finite number")
    value = float(value)
    if not math.isfinite(value):
        raise DiagnosticsError(f"{name} must be a finite number")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise DiagnosticsError(f"cannot read diagnostics input {path}: {exc}") from exc
    rows = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise DiagnosticsError(f"invalid JSON on line {line_number} of {path}: {exc}") from exc
        if not isinstance(value, dict):
            raise DiagnosticsError(f"line {line_number} of {path} is not a JSON object")
        rows.append(value)
    return rows


def _stamp(row: Mapping[str, Any], *, path: Path, line_number: int) -> float:
    for field in ("stamp_s", "ros_time_s", "recorded_at_s", "recorded_at_ros_s"):
        if field in row:
            return _finite(row[field], f"{path}:{line_number}:{field}")
    raise DiagnosticsError(f"{path}:{line_number} has no timestamp field")


def _wrap_angle(value: float) -> float:
    return (value + math.pi) % (2.0 * math.pi) - math.pi


def _normalise_controller_rows(rows: Iterable[Mapping[str, Any]], path: Path) -> list[dict[str, Any]]:
    normalised = []
    required = (
        "measured_x_m",
        "measured_y_m",
        "measured_yaw_rad",
        "target_x_m",
        "target_y_m",
        "target_yaw_rad",
        "force_left_n",
        "force_right_n",
        "force_lateral_n",
    )
    for line_number, row in enumerate(rows, start=1):
        if not all(field in row for field in required):
            missing = [field for field in required if field not in row]
            raise DiagnosticsError(f"{path}:{line_number} missing controller fields: {', '.join(missing)}")
        stamp = _stamp(row, path=path, line_number=line_number)
        values = {field: _finite(row[field], f"{path}:{line_number}:{field}") for field in required}
        values["stamp_s"] = stamp
        values["position_source"] = str(row.get("position_source", "unspecified"))
        values["position_error_m"] = math.hypot(
            values["target_x_m"] - values["measured_x_m"],
            values["target_y_m"] - values["measured_y_m"],
        )
        values["heading_error_rad"] = abs(_wrap_angle(values["target_yaw_rad"] - values["measured_yaw_rad"]))
        normalised.append(values)
    if not normalised:
        raise DiagnosticsError(f"controller diagnostics stream is empty: {path}")
    return normalised


def _task_rows(path: Path) -> list[dict[str, Any]]:
    rows = _read_jsonl(path)
    if not rows:
        raise DiagnosticsError(f"task diagnostics stream is empty: {path}")
    normalised = []
    for line_number, row in enumerate(rows, start=1):
        state = row.get("state")
        if not isinstance(state, str) or not state:
            raise DiagnosticsError(f"{path}:{line_number} has no task state")
        normalised.append({"state": state, "stamp_s": _stamp(row, path=path, line_number=line_number)})
    return normalised


def _running_window(task_rows: Iterable[Mapping[str, Any]], controller_rows: list[Mapping[str, Any]]) -> tuple[float, float]:
    running = [float(row["stamp_s"]) for row in task_rows if row["state"] == "running"]
    finished = [float(row["stamp_s"]) for row in task_rows if row["state"] == "finished"]
    if not running:
        raise DiagnosticsError("task diagnostics contain no running state")
    start = min(running)
    end = min(finished) if finished else max(float(row["stamp_s"]) for row in controller_rows)
    if end <= start:
        raise DiagnosticsError(f"invalid running window: start={start}, end={end}")
    return start, end


def _mean(rows: list[Mapping[str, Any]], field: str) -> float | None:
    values = [float(row[field]) for row in rows]
    return sum(values) / len(values) if values else None


def _first_at_or_below(rows: list[Mapping[str, Any]], field: str, threshold: float, start: float) -> float | None:
    for row in rows:
        if float(row[field]) <= threshold:
            return max(0.0, float(row["stamp_s"]) - start)
    return None


def _saturated(force: float, lower: float, upper: float) -> bool:
    return force <= lower + FORCE_SATURATION_TOLERANCE_N or force >= upper - FORCE_SATURATION_TOLERANCE_N


def extract_trial_diagnostics(
    trial_dir: Path,
    *,
    task_path: Path | None = None,
    controller_path: Path | None = None,
) -> dict[str, Any]:
    """Extract Q-03 metrics from one trial artifact directory."""

    trial_dir = trial_dir.resolve()
    task_path = task_path or trial_dir / "task-info.jsonl"
    controller_path = controller_path or trial_dir / "controller-diagnostics.jsonl"
    if not task_path.is_file():
        raise DiagnosticsError(f"missing task diagnostics JSONL: {task_path}")
    if not controller_path.is_file():
        raise DiagnosticsError(f"missing controller diagnostics JSONL: {controller_path}")
    task_rows = _task_rows(task_path)
    controller_rows = _normalise_controller_rows(_read_jsonl(controller_path), controller_path)
    start, end = _running_window(task_rows, controller_rows)
    running_rows = [row for row in controller_rows if start <= row["stamp_s"] <= end]
    if not running_rows:
        raise DiagnosticsError("controller diagnostics contain no samples in the running window")
    running_rows.sort(key=lambda row: row["stamp_s"])
    duration = end - start
    window = min(30.0, duration)
    first_rows = [row for row in running_rows if row["stamp_s"] <= start + window]
    last_rows = [row for row in running_rows if row["stamp_s"] >= end - window]
    forces = [row[field] for row in running_rows for field in ("force_left_n", "force_right_n", "force_lateral_n")]
    saturation_rows = [
        row
        for row in running_rows
        if any(
            _saturated(row[field], FORCE_MIN_N[index], FORCE_MAX_N[index])
            for index, field in enumerate(("force_left_n", "force_right_n", "force_lateral_n"))
        )
    ]
    result = {
        "schema_version": DIAGNOSTICS_SCHEMA_VERSION,
        "source": {
            "trial_directory": str(trial_dir),
            "task_file": str(task_path),
            "controller_file": str(controller_path),
            "position_source": running_rows[0]["position_source"],
        },
        "run_window": {
            "start_s": start,
            "end_s": end,
            "duration_s": duration,
            "sample_count": len(running_rows),
        },
        "metrics": {
            "time_to_0_25_m_s": _first_at_or_below(running_rows, "position_error_m", 0.25, start),
            "time_to_0_5_m_s": _first_at_or_below(running_rows, "position_error_m", 0.5, start),
            "max_position_error_m": max(row["position_error_m"] for row in running_rows),
            "max_yaw_error_rad": max(row["heading_error_rad"] for row in running_rows),
            "peak_force_abs_n": max(abs(value) for value in forces),
            "force_saturation_fraction": len(saturation_rows) / len(running_rows),
            "first_window_s": window,
            "first_window_mean_position_error_m": _mean(first_rows, "position_error_m"),
            "last_window_mean_position_error_m": _mean(last_rows, "position_error_m"),
            "first_window_mean_heading_error_rad": _mean(first_rows, "heading_error_rad"),
            "last_window_mean_heading_error_rad": _mean(last_rows, "heading_error_rad"),
        },
        "quality": {
            "task_message_count": len(task_rows),
            "controller_message_count": len(controller_rows),
            "running_controller_message_count": len(running_rows),
            "task_finished_observed": any(row["state"] == "finished" for row in task_rows),
        },
    }
    score = _read_optional_score(trial_dir)
    if score is not None:
        result["score"] = score
    return result


def _read_optional_score(trial_dir: Path) -> float | None:
    candidates = [trial_dir / "score.json", trial_dir / "trial.json", trial_dir.parent / "trial.json"]
    for path in candidates:
        if not path.is_file():
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if isinstance(value, dict):
            for candidate in (value.get("score"), (value.get("final") or {}).get("score") if isinstance(value.get("final"), dict) else None):
                if isinstance(candidate, (int, float)) and not isinstance(candidate, bool) and math.isfinite(float(candidate)):
                    return float(candidate)
    return None


def discover_trial_directories(input_path: Path) -> list[Path]:
    """Return one or more artifact directories in stable order."""

    input_path = input_path.resolve()
    if (input_path / "task-info.jsonl").is_file() or (input_path / "controller-diagnostics.jsonl").is_file():
        return [input_path]
    candidates = sorted({path.parent for path in input_path.rglob("task-info.jsonl")}) if input_path.is_dir() else []
    if not candidates:
        raise DiagnosticsError(f"no trial task-info.jsonl found below {input_path}")
    return candidates


def extract_diagnostics(input_path: Path) -> dict[str, Any]:
    """Extract one trial or a suite of trial diagnostics."""

    directories = discover_trial_directories(input_path)
    trials = [extract_trial_diagnostics(directory) for directory in directories]
    if len(trials) == 1:
        return trials[0]
    return {
        "schema_version": DIAGNOSTICS_SCHEMA_VERSION,
        "scope": {"input_directory": str(input_path.resolve()), "trial_count": len(trials)},
        "trials": trials,
    }
