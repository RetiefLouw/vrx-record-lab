"""Validation and loading for immutable experiment manifests."""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any, Mapping

from .jsonio import load_json


class ManifestError(ValueError):
    pass


_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ManifestError(f"{name} must be a JSON object")
    return value


def validate_manifest(manifest: Mapping[str, Any]) -> None:
    if not isinstance(manifest, Mapping):
        raise ManifestError("experiment manifest must be a JSON object")
    if manifest.get("schema_version") != "1.0.0":
        raise ManifestError("schema_version must be '1.0.0'")
    experiment_id = manifest.get("experiment_id")
    if not isinstance(experiment_id, str) or not _ID.fullmatch(experiment_id):
        raise ManifestError("experiment_id must be a short stable identifier")

    benchmark = _mapping(manifest.get("benchmark"), "benchmark")
    for field in ("name", "score_direction"):
        if not isinstance(benchmark.get(field), str) or not benchmark[field]:
            raise ManifestError(f"benchmark.{field} is required")
    if benchmark["score_direction"] not in ("minimize", "maximize"):
        raise ManifestError("benchmark.score_direction must be 'minimize' or 'maximize'")
    scorer = _mapping(benchmark.get("scorer"), "benchmark.scorer")
    if not isinstance(scorer.get("name"), str) or not scorer["name"]:
        raise ManifestError("benchmark.scorer.name is required")
    for field in ("revision", "protocol_revision"):
        if benchmark.get(field) is not None and not isinstance(benchmark[field], str):
            raise ManifestError(f"benchmark.{field} must be a string or null")
    if scorer.get("revision") is not None and not isinstance(scorer["revision"], str):
        raise ManifestError("benchmark.scorer.revision must be a string or null")

    controller = _mapping(manifest.get("controller"), "controller")
    for field in ("name", "source"):
        if not isinstance(controller.get(field), str) or not controller[field]:
            raise ManifestError(f"controller.{field} is required")
    if controller.get("revision") is not None and not isinstance(controller["revision"], str):
        raise ManifestError("controller.revision must be a string or null")
    if not isinstance(controller.get("command", []), list) or not all(
        isinstance(item, str) for item in controller.get("command", [])
    ):
        raise ManifestError("controller.command must be a list of strings")
    if not isinstance(controller.get("parameters", {}), Mapping):
        raise ManifestError("controller.parameters must be an object")

    container = _mapping(manifest.get("container"), "container")
    if not isinstance(container.get("image"), str) or not container["image"]:
        raise ManifestError("container.image is required")
    if container.get("digest") is not None and not isinstance(container["digest"], str):
        raise ManifestError("container.digest must be a string or null")

    task = _mapping(manifest.get("task"), "task")
    if not isinstance(task.get("name"), str) or not task["name"]:
        raise ManifestError("task.name is required")
    if not isinstance(task.get("parameters", {}), Mapping):
        raise ManifestError("task.parameters must be an object")

    trials = _mapping(manifest.get("trials"), "trials")
    seeds = trials.get("seeds")
    if not isinstance(seeds, list) or not all(isinstance(seed, int) and not isinstance(seed, bool) for seed in seeds):
        raise ManifestError("trials.seeds must be a list of integers")
    if len(set(seeds)) != len(seeds):
        raise ManifestError("trials.seeds must not contain duplicates")
    if not isinstance(trials.get("environment", {}), Mapping):
        raise ManifestError("trials.environment must be an object")
    if not isinstance(trials.get("seed_provenance", ""), str):
        raise ManifestError("trials.seed_provenance must be a string")

    execution = _mapping(manifest.get("execution"), "execution")
    command = execution.get("command")
    if not isinstance(command, list) or not all(isinstance(item, str) for item in command):
        raise ManifestError("execution.command must be a list of strings")
    timeout = execution.get("timeout_s", 900)
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or not math.isfinite(float(timeout)) or timeout <= 0:
        raise ManifestError("execution.timeout_s must be a positive finite number")
    if execution.get("cwd") is not None and not isinstance(execution["cwd"], str):
        raise ManifestError("execution.cwd must be a string or null")


def load_manifest(path: Path) -> dict:
    manifest = load_json(path)
    validate_manifest(manifest)
    return dict(manifest)
