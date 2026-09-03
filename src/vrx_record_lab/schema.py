"""Structural validation for canonical result documents.

The repository also publishes JSON Schema files for tool interoperability. This
module intentionally performs the small required subset itself so verification
works in a clean Python installation without downloading dependencies.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any


class ResultSchemaError(ValueError):
    pass


def _object(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ResultSchemaError(f"{name} must be an object")
    return value


def _string(value: Any, name: str, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    if not isinstance(value, str) or not value:
        raise ResultSchemaError(f"{name} must be a non-empty string")


def _number(value: Any, name: str, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ResultSchemaError(f"{name} must be a finite number")


def validate_result(result: Mapping[str, Any]) -> None:
    _object(result, "result")
    if result.get("schema_version") != "1.0.0":
        raise ResultSchemaError("schema_version must be '1.0.0'")
    for field in ("result_id", "experiment_id", "created_at"):
        _string(result.get(field), f"result.{field}")
    if result.get("status") not in ("completed", "failed", "not_run"):
        raise ResultSchemaError("result.status is invalid")

    benchmark = _object(result.get("benchmark"), "result.benchmark")
    _string(benchmark.get("name"), "result.benchmark.name")
    _string(benchmark.get("score_direction"), "result.benchmark.score_direction")
    if benchmark["score_direction"] not in ("minimize", "maximize"):
        raise ResultSchemaError("result.benchmark.score_direction is invalid")
    _string(benchmark.get("revision"), "result.benchmark.revision", nullable=True)
    _string(benchmark.get("protocol_revision"), "result.benchmark.protocol_revision", nullable=True)
    scorer = _object(benchmark.get("scorer"), "result.benchmark.scorer")
    _string(scorer.get("name"), "result.benchmark.scorer.name")
    _string(scorer.get("revision"), "result.benchmark.scorer.revision", nullable=True)

    controller = _object(result.get("controller"), "result.controller")
    _string(controller.get("name"), "result.controller.name")
    _string(controller.get("source"), "result.controller.source")
    _string(controller.get("revision"), "result.controller.revision", nullable=True)
    _object(controller.get("parameters", {}), "result.controller.parameters")
    container = _object(result.get("container"), "result.container")
    _string(container.get("image"), "result.container.image")
    _string(container.get("digest"), "result.container.digest", nullable=True)
    task = _object(result.get("task"), "result.task")
    _string(task.get("name"), "result.task.name")
    _object(task.get("parameters", {}), "result.task.parameters")

    trials = result.get("trials")
    if not isinstance(trials, list):
        raise ResultSchemaError("result.trials must be a list")
    trial_ids = set()
    for index, trial in enumerate(trials):
        trial = _object(trial, f"result.trials[{index}]")
        _string(trial.get("trial_id"), f"result.trials[{index}].trial_id")
        if trial["trial_id"] in trial_ids:
            raise ResultSchemaError("trial_id values must be unique")
        trial_ids.add(trial["trial_id"])
        if not isinstance(trial.get("seed"), int) or isinstance(trial.get("seed"), bool):
            raise ResultSchemaError(f"result.trials[{index}].seed must be an integer")
        if trial.get("status") not in ("completed", "failed", "timeout", "invalid"):
            raise ResultSchemaError(f"result.trials[{index}].status is invalid")
        if not isinstance(trial.get("completed"), bool):
            raise ResultSchemaError(f"result.trials[{index}].completed must be boolean")
        _number(trial.get("score"), f"result.trials[{index}].score", nullable=True)
        _object(trial.get("score_components", {}), f"result.trials[{index}].score_components")
        _number(trial.get("wall_clock_s"), f"result.trials[{index}].wall_clock_s")
        _number(trial.get("real_time_factor"), f"result.trials[{index}].real_time_factor", nullable=True)
        _object(trial.get("environment", {}), f"result.trials[{index}].environment")
        _object(trial.get("metrics", {}), f"result.trials[{index}].metrics")
        if not isinstance(trial.get("artifacts", []), list):
            raise ResultSchemaError(f"result.trials[{index}].artifacts must be a list")

    aggregate = _object(result.get("aggregate"), "result.aggregate")
    if not isinstance(aggregate.get("count"), int) or aggregate["count"] < 0:
        raise ResultSchemaError("result.aggregate.count must be a non-negative integer")
    for field in ("mean", "median", "stddev", "worst_case"):
        _number(aggregate.get(field), f"result.aggregate.{field}", nullable=True)
    _string(aggregate.get("score_direction"), "result.aggregate.score_direction")
    ci = _object(aggregate.get("confidence_interval_95"), "result.aggregate.confidence_interval_95")
    _number(ci.get("low"), "result.aggregate.confidence_interval_95.low", nullable=True)
    _number(ci.get("high"), "result.aggregate.confidence_interval_95.high", nullable=True)
    _string(ci.get("method"), "result.aggregate.confidence_interval_95.method")

    artifacts = result.get("artifacts")
    if not isinstance(artifacts, list):
        raise ResultSchemaError("result.artifacts must be a list")
    for index, artifact in enumerate(artifacts):
        artifact = _object(artifact, f"result.artifacts[{index}]")
        _string(artifact.get("path"), f"result.artifacts[{index}].path")
        _string(artifact.get("sha256"), f"result.artifacts[{index}].sha256")
        if len(artifact["sha256"]) != 64:
            raise ResultSchemaError(f"result.artifacts[{index}].sha256 must be SHA-256")
        _string(artifact.get("kind"), f"result.artifacts[{index}].kind")
    _string(result.get("checksums_file"), "result.checksums_file")
    provenance = _object(result.get("provenance"), "result.provenance")
    _string(provenance.get("manifest_sha256"), "result.provenance.manifest_sha256")
    _string(provenance.get("manifest_file"), "result.provenance.manifest_file")
    verification = _object(result.get("verification"), "result.verification")
    if not isinstance(verification.get("verified"), bool) or not isinstance(verification.get("claim_eligible"), bool):
        raise ResultSchemaError("result.verification.verified and claim_eligible must be boolean")
    if not isinstance(verification.get("checks", []), list):
        raise ResultSchemaError("result.verification.checks must be a list")
