"""Result verification independent of simulator execution."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import List, Optional

from .checksums import ArtifactError, read_checksums, safe_artifact_path, sha256_file
from .jsonio import load_json, write_json
from .schema import ResultSchemaError, validate_result
from .stats import aggregate_scores, aggregates_match, empty_aggregate


def _check(name: str, passed: bool, details: str) -> dict:
    return {"name": name, "passed": bool(passed), "details": details}


def verify_result(result_path: Path, manifest_path: Optional[Path] = None) -> dict:
    result = load_json(result_path)
    checks: List[dict] = []
    try:
        validate_result(result)
        checks.append(_check("schema", True, "canonical result structure is valid"))
    except ResultSchemaError as exc:
        checks.append(_check("schema", False, str(exc)))
        return {
            "verified": False,
            "claim_eligible": False,
            "claim_scope": "local_result_integrity_only",
            "record_claim_eligible": False,
            "checks": checks,
        }

    root = result_path.parent
    artifact_ok = True
    artifact_errors = []
    expected_by_path = {}
    for entry in result["artifacts"]:
        path_name = entry["path"]
        if path_name in expected_by_path:
            artifact_ok = False
            artifact_errors.append(f"duplicate result artifact {path_name}")
            continue
        expected_by_path[path_name] = entry["sha256"]
        try:
            actual = sha256_file(safe_artifact_path(root, path_name))
            if actual != entry["sha256"]:
                artifact_ok = False
                artifact_errors.append(f"digest mismatch for {path_name}")
        except ArtifactError as exc:
            artifact_ok = False
            artifact_errors.append(str(exc))
    checks.append(_check("artifact_sha256", artifact_ok, "; ".join(artifact_errors) if artifact_errors else "all artifact digests match"))

    checksum_ok = True
    checksum_errors = []
    try:
        checksum_entries = read_checksums(safe_artifact_path(root, result["checksums_file"]))
        if checksum_entries != expected_by_path:
            checksum_ok = False
            checksum_errors.append("SHA256SUMS does not match result.artifacts")
        for path_name, expected in checksum_entries.items():
            actual = sha256_file(safe_artifact_path(root, path_name))
            if actual != expected:
                checksum_ok = False
                checksum_errors.append(f"digest mismatch in SHA256SUMS for {path_name}")
    except ArtifactError as exc:
        checksum_ok = False
        checksum_errors.append(str(exc))
    checks.append(_check("checksums_file", checksum_ok, "; ".join(checksum_errors) if checksum_errors else "SHA256SUMS matches all artifacts"))

    scores = [float(trial["score"]) for trial in result["trials"] if trial["completed"] and trial["score"] is not None]
    expected_aggregate = aggregate_scores(scores, result["benchmark"]["score_direction"]) if scores else empty_aggregate(result["benchmark"]["score_direction"])
    aggregate_ok = aggregates_match(result["aggregate"], expected_aggregate)
    checks.append(_check("aggregate", aggregate_ok, "aggregate matches completed trial scores" if aggregate_ok else "aggregate does not match completed trial scores"))

    if manifest_path is not None:
        expected_digest = result["provenance"]["manifest_sha256"]
        actual_digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        manifest_ok = actual_digest == expected_digest
        checks.append(_check("manifest_sha256", manifest_ok, "manifest digest matches" if manifest_ok else "manifest digest mismatch"))
    else:
        checks.append(_check("manifest_sha256", False, "pass --manifest to verify the experiment manifest digest"))

    identity_fields = (
        result["benchmark"].get("revision"),
        result["benchmark"].get("protocol_revision"),
        result["benchmark"]["scorer"].get("revision"),
        result["controller"].get("revision"),
        result["container"].get("digest"),
    )
    identity_ok = all(isinstance(value, str) and bool(value) for value in identity_fields)
    checks.append(_check("pinned_identity", identity_ok, "benchmark, scorer, controller, and container revisions are pinned" if identity_ok else "one or more revisions/digests are unavailable"))

    complete_ok = result["status"] == "completed" and bool(scores) and all(trial["status"] == "completed" for trial in result["trials"])
    checks.append(_check("completed_trials", complete_ok, "all listed trials completed with scores" if complete_ok else "result is incomplete or has no scored trials"))
    verified = all(item["passed"] for item in checks)
    return {
        "verified": verified,
        "claim_eligible": verified,
        "claim_scope": "local_result_integrity_only",
        "record_claim_eligible": False,
        "checks": checks,
    }
