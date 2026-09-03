"""Execution adapters for one trial and for a multi-seed suite."""

from __future__ import annotations

import json
import hashlib
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, List, Mapping, Optional, Tuple

from .checksums import artifact_entry, write_checksums
from .jsonio import load_json, write_json
from .manifest import load_manifest
from .schema import validate_result
from .stats import aggregate_scores, empty_aggregate


class TrialError(ValueError):
    pass


def _render_command(command: Iterable[str], values: Mapping[str, str]) -> List[str]:
    rendered = []
    for token in command:
        try:
            rendered.append(token.format(**values))
        except (KeyError, ValueError) as exc:
            raise TrialError(f"invalid execution command placeholder in {token!r}: {exc}") from exc
    return rendered


def _read_adapter_output(output_path: Path, stdout: str) -> dict:
    if output_path.exists() and output_path.stat().st_size:
        try:
            value = load_json(output_path)
        except ValueError as exc:
            raise TrialError(str(exc)) from exc
    else:
        if not stdout.strip():
            raise TrialError("adapter produced neither VRX_TRIAL_OUTPUT nor JSON stdout")
        try:
            value = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise TrialError(f"adapter stdout is not a JSON object: {exc}") from exc
    if not isinstance(value, dict):
        raise TrialError("adapter output must be a JSON object")
    return value


def _text(value: Any) -> str:
    """Normalize subprocess timeout output across Python versions."""

    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value or ""


def _base_trial(manifest: Mapping[str, Any], trial_id: str, seed: int, status: str, wall_clock_s: float) -> dict:
    return {
        "trial_id": trial_id,
        "seed": seed,
        "status": status,
        "completed": False,
        "score": None,
        "score_components": {},
        "wall_clock_s": wall_clock_s,
        "real_time_factor": None,
        "environment": dict(manifest["trials"].get("environment", {})),
        "metrics": {},
        "artifacts": [],
    }


def _normalise_trial_output(
    value: Mapping[str, Any], manifest: Mapping[str, Any], trial_id: str, seed: int, wall_clock_s: float
) -> dict:
    if not isinstance(value.get("completed"), bool):
        raise TrialError("adapter output must contain boolean 'completed'")
    completed = bool(value["completed"])
    status = value.get("status", "completed" if completed else "failed")
    if status not in ("completed", "failed", "timeout", "invalid"):
        raise TrialError("adapter output status is invalid")
    score = value.get("score")
    if completed:
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise TrialError("a completed adapter output must contain a finite numeric score")
        if not (float("-inf") < float(score) < float("inf")):
            raise TrialError("score must be finite")
        if status != "completed":
            raise TrialError("completed=true requires status=completed")
    elif score is not None:
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not (float("-inf") < float(score) < float("inf")):
            raise TrialError("failed trial score must be null or a finite number")
    score_components = value.get("score_components", {})
    environment = value.get("environment", manifest["trials"].get("environment", {}))
    metrics = value.get("metrics", {})
    if not isinstance(score_components, dict) or not isinstance(environment, dict) or not isinstance(metrics, dict):
        raise TrialError("score_components, environment, and metrics must be objects")
    real_time_factor = value.get("real_time_factor")
    if real_time_factor is not None:
        if isinstance(real_time_factor, bool) or not isinstance(real_time_factor, (int, float)) or not (float("-inf") < float(real_time_factor) < float("inf")):
            raise TrialError("real_time_factor must be a finite number or null")
    adapter_wall_clock = value.get("wall_clock_s", wall_clock_s)
    if isinstance(adapter_wall_clock, bool) or not isinstance(adapter_wall_clock, (int, float)) or not (float("-inf") < float(adapter_wall_clock) < float("inf")):
        raise TrialError("wall_clock_s must be a finite number")
    return {
        "trial_id": trial_id,
        "seed": seed,
        "status": status,
        "completed": completed,
        "score": score,
        "score_components": score_components,
        "wall_clock_s": float(adapter_wall_clock),
        "real_time_factor": real_time_factor,
        "environment": environment,
        "metrics": metrics,
        "artifacts": [],
    }


def execute_trial(manifest_path: Path, manifest: Mapping[str, Any], seed: int, output_path: Path, trial_id: str) -> Tuple[dict, List[Path]]:
    """Run one configured adapter and save its normalized trial document.

    The configured command is an explicit boundary: this function does not
    emulate Gazebo, calculate a score, or substitute a fixture when the command
    is unavailable.
    """

    seeds = manifest["trials"]["seeds"]
    if seeds and seed not in seeds:
        raise TrialError(f"seed {seed} is not listed in the immutable manifest")
    command = manifest["execution"]["command"]
    if not command:
        raise TrialError(
            "execution.command is empty; configure the historical simulator/scorer adapter before running a benchmark"
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_dir = output_path.parent / f"{output_path.stem}.artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = output_path.parent / f"{output_path.stem}.stdout.log"
    stderr_path = output_path.parent / f"{output_path.stem}.stderr.log"
    if any(artifact_dir.rglob("*")):
        raise TrialError(f"artifact directory is not empty; use a fresh trial output directory: {artifact_dir}")
    if output_path.exists():
        output_path.unlink()
    values = {
        "seed": str(seed),
        "trial_id": trial_id,
        "output": str(output_path.resolve()),
        "artifact_dir": str(artifact_dir.resolve()),
        "manifest": str(manifest_path.resolve()),
    }
    rendered = _render_command(command, values)
    env = os.environ.copy()
    env.update(
        {
            "VRX_TRIAL_ID": trial_id,
            "VRX_TRIAL_SEED": str(seed),
            "VRX_TRIAL_OUTPUT": str(output_path.resolve()),
            "VRX_TRIAL_ARTIFACT_DIR": str(artifact_dir.resolve()),
            "VRX_EXPERIMENT_MANIFEST": str(manifest_path.resolve()),
            "VRX_TASK_ENVIRONMENT_JSON": json.dumps(manifest["trials"].get("environment", {}), sort_keys=True),
            "VRX_TASK_PARAMETERS_JSON": json.dumps(manifest["task"].get("parameters", {}), sort_keys=True),
            "VRX_CONTROLLER_PARAMETERS_JSON": json.dumps(manifest["controller"].get("parameters", {}), sort_keys=True),
        }
    )
    execution_cwd = manifest["execution"].get("cwd")
    cwd = manifest_path.parent / execution_cwd if execution_cwd else manifest_path.parent
    started = time.monotonic()
    status = "completed"
    process_error = None
    stdout = ""
    stderr = ""
    try:
        completed_process = subprocess.run(
            rendered,
            cwd=str(cwd),
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=float(manifest["execution"].get("timeout_s", 900)),
            check=False,
        )
        stdout, stderr = completed_process.stdout, completed_process.stderr
        if completed_process.returncode != 0:
            status = "failed"
            process_error = f"adapter exited with code {completed_process.returncode}"
    except subprocess.TimeoutExpired as exc:
        status = "timeout"
        stdout = _text(exc.stdout)
        stderr = _text(exc.stderr)
        process_error = f"adapter exceeded timeout of {manifest['execution'].get('timeout_s', 900)} seconds"
    except OSError as exc:
        status = "failed"
        process_error = f"could not start adapter: {exc}"
    elapsed = time.monotonic() - started
    stdout_path.write_text(stdout, encoding="utf-8", errors="replace")
    stderr_path.write_text(stderr, encoding="utf-8", errors="replace")

    if process_error:
        trial = _base_trial(manifest, trial_id, seed, status, elapsed)
        trial["error"] = process_error
    else:
        try:
            adapter_output = _read_adapter_output(output_path, stdout)
            trial = _normalise_trial_output(adapter_output, manifest, trial_id, seed, elapsed)
        except TrialError as exc:
            trial = _base_trial(manifest, trial_id, seed, "invalid", elapsed)
            trial["error"] = str(exc)
    write_json(output_path, trial)

    relative_root = output_path.parent
    artifact_paths = [output_path, stdout_path, stderr_path]
    if artifact_dir.exists():
        artifact_paths.extend(path for path in sorted(artifact_dir.rglob("*")) if path.is_file())
    trial["artifacts"] = [path.relative_to(relative_root).as_posix() for path in artifact_paths]
    write_json(output_path, trial)
    return trial, artifact_paths


def build_result(
    manifest_path: Path,
    manifest: Mapping[str, Any],
    trials: List[dict],
    artifact_paths: Iterable[Path],
    result_path: Path,
    result_id: Optional[str] = None,
) -> dict:
    result_path.parent.mkdir(parents=True, exist_ok=True)
    scores = [float(trial["score"]) for trial in trials if trial.get("completed") and trial.get("score") is not None]
    score_direction = manifest["benchmark"]["score_direction"]
    aggregate = aggregate_scores(scores, score_direction) if scores else empty_aggregate(score_direction)
    if not trials:
        status = "not_run"
    elif all(trial.get("status") == "completed" for trial in trials):
        status = "completed"
    else:
        status = "failed"
    root = result_path.parent
    entries = []
    seen = set()
    for path in artifact_paths:
        relative = path.relative_to(root).as_posix()
        if relative not in seen:
            entries.append(artifact_entry(root, relative, "trial_output" if path.suffix == ".json" else "trial_log"))
            seen.add(relative)
    checksum_path = root / "SHA256SUMS"
    write_checksums(checksum_path, entries)
    manifest_bytes = manifest_path.read_bytes()
    result = {
        "schema_version": "1.0.0",
        "result_id": result_id or f"{manifest['experiment_id']}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "experiment_id": manifest["experiment_id"],
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": status,
        "benchmark": {
            "name": manifest["benchmark"]["name"],
            "revision": manifest["benchmark"].get("revision"),
            "protocol_revision": manifest["benchmark"].get("protocol_revision"),
            "score_direction": score_direction,
            "scorer": {
                "name": manifest["benchmark"]["scorer"]["name"],
                "revision": manifest["benchmark"]["scorer"].get("revision"),
            },
        },
        "controller": {
            "name": manifest["controller"]["name"],
            "source": manifest["controller"]["source"],
            "revision": manifest["controller"].get("revision"),
            "parameters": manifest["controller"].get("parameters", {}),
        },
        "container": {
            "image": manifest["container"]["image"],
            "digest": manifest["container"].get("digest"),
        },
        "task": {
            "name": manifest["task"]["name"],
            "parameters": manifest["task"].get("parameters", {}),
        },
        "trials": trials,
        "aggregate": aggregate,
        "artifacts": sorted(entries, key=lambda item: item["path"]),
        "checksums_file": checksum_path.relative_to(root).as_posix(),
        "provenance": {
            "manifest_file": manifest_path.name,
            "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "seed_provenance": manifest["trials"].get("seed_provenance", ""),
        },
        "verification": {"verified": False, "claim_eligible": False, "checks": []},
    }
    validate_result(result)
    write_json(result_path, result)
    return result


def run_suite(manifest_path: Path, output_dir: Path, result_id: Optional[str] = None) -> Tuple[dict, Path]:
    manifest = load_manifest(manifest_path)
    seeds = list(manifest["trials"]["seeds"])
    if not manifest["execution"]["command"]:
        raise TrialError(
            "execution.command is empty; configure the historical simulator/scorer adapter before running a benchmark"
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    trials = []
    artifacts = []
    for index, seed in enumerate(seeds, start=1):
        trial_id = f"trial-{index:04d}"
        trial_path = output_dir / "trials" / f"{trial_id}.json"
        trial, trial_artifacts = execute_trial(manifest_path, manifest, seed, trial_path, trial_id)
        trials.append(trial)
        artifacts.extend(trial_artifacts)
    result_path = output_dir / "result.json"
    result = build_result(manifest_path, manifest, trials, artifacts, result_path, result_id=result_id)
    return result, result_path
