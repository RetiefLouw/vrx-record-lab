#!/usr/bin/env python3
"""Dependency-free checks for reproducible VRX campaign records.

The commands in this module intentionally verify evidence around a benchmark;
they do not implement, modify, or score the benchmark itself.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SCHEMA = ROOT / "verification" / "result.schema.json"
DEFAULT_SEED_CONFIG = ROOT / "verification" / "seed_sets.json"
DEFAULT_INTEGRITY_CONFIG = ROOT / "verification" / "benchmark_paths.json"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class VerificationError(Exception):
    """A user-actionable verification failure."""


def load_json(path: Path) -> Any:
    """Load strict JSON and reject non-standard NaN/Infinity constants."""

    def reject_constant(value: str) -> None:
        raise VerificationError(f"{path}: non-finite JSON constant {value!r} is not allowed")

    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle, parse_constant=reject_constant)
    except FileNotFoundError as exc:
        raise VerificationError(f"JSON file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise VerificationError(f"{path}: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    raise VerificationError(f"unsupported JSON Schema type {expected!r}")


def schema_error(path: str, message: str) -> VerificationError:
    return VerificationError(f"result schema: {path}: {message}")


def validate_schema(value: Any, schema: Mapping[str, Any], path: str = "$") -> None:
    """Validate the small JSON Schema subset used by the committed result schema."""

    if "const" in schema and value != schema["const"]:
        raise schema_error(path, f"must equal {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise schema_error(path, f"must be one of {schema['enum']!r}")
    if "type" in schema and not type_matches(value, schema["type"]):
        raise schema_error(path, f"must be a {schema['type']}")
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            raise schema_error(path, f"must have at least {schema['minLength']} characters")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            raise schema_error(path, f"does not match {schema['pattern']!r}")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise schema_error(path, f"must be >= {schema['minimum']}")
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
            raise schema_error(path, f"must be > {schema['exclusiveMinimum']}")
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            raise schema_error(path, f"must contain at least {schema['minItems']} items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise schema_error(path, f"must contain at most {schema['maxItems']} items")
        if "items" in schema:
            for index, item in enumerate(value):
                validate_schema(item, schema["items"], f"{path}[{index}]")
    if isinstance(value, dict):
        for required in schema.get("required", []):
            if required not in value:
                raise schema_error(path, f"missing required property {required!r}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            unknown = sorted(set(value) - set(properties))
            if unknown:
                raise schema_error(path, f"unknown properties {unknown!r}")
        for key, item in value.items():
            if key in properties:
                validate_schema(item, properties[key], f"{path}.{key}")


def run_git(repo: Path, args: Sequence[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", "-C", str(repo), *args],
            check=check,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        raise VerificationError("git is required for this verification command") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout).strip()
        raise VerificationError(f"git {' '.join(args)} failed: {detail}") from exc


def git_ref(repo: Path, ref: str) -> str:
    return run_git(repo, ["rev-parse", "--verify", f"{ref}^{{}}"]).stdout.strip()


def repo_root(path: Path) -> Path:
    resolved = path.resolve()
    result = run_git(resolved, ["rev-parse", "--show-toplevel"]).stdout.strip()
    return Path(result).resolve()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_relative_path(path_value: str, root: Path, *, label: str) -> Path:
    if not isinstance(path_value, str) or not path_value:
        raise VerificationError(f"{label}: path must be a non-empty string")
    candidate = Path(path_value)
    if candidate.is_absolute():
        raise VerificationError(f"{label}: artifact paths must be relative: {path_value!r}")
    resolved_root = root.resolve()
    resolved = (resolved_root / candidate).resolve()
    try:
        relative = resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise VerificationError(f"{label}: path escapes root: {path_value!r}") from exc
    if relative.as_posix() != candidate.as_posix():
        raise VerificationError(f"{label}: normalized paths are not accepted: {path_value!r}")
    return relative


def manifest_entries(root: Path, *, exclude: Iterable[Path] = ()) -> list[dict[str, Any]]:
    root = root.resolve()
    if not root.is_dir():
        raise VerificationError(f"manifest root is not a directory: {root}")
    excluded = {path.resolve() for path in exclude}
    entries: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if path.resolve() in excluded:
            continue
        if path.is_symlink():
            raise VerificationError(f"manifest refuses symlink: {path}")
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        entries.append({"path": relative, "size_bytes": path.stat().st_size, "sha256": sha256_file(path)})
    return entries


def create_manifest(root: Path, output: Path) -> dict[str, Any]:
    output = output.resolve()
    entries = manifest_entries(root, exclude=(output,))
    return {
        "schema_version": "sha256-manifest/v1",
        "root": ".",
        "files": entries,
    }


def check_manifest(root: Path, manifest_path: Path, *, strict: bool = True) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    if not isinstance(manifest, dict) or manifest.get("schema_version") != "sha256-manifest/v1":
        raise VerificationError(f"{manifest_path}: expected sha256-manifest/v1")
    files = manifest.get("files")
    if not isinstance(files, list):
        raise VerificationError(f"{manifest_path}: files must be a list")
    expected: dict[str, tuple[int, str]] = {}
    for index, entry in enumerate(files):
        if not isinstance(entry, dict) or set(entry) != {"path", "size_bytes", "sha256"}:
            raise VerificationError(f"{manifest_path}: files[{index}] must contain path, size_bytes, sha256")
        relative = safe_relative_path(entry["path"], root, label=f"{manifest_path}: files[{index}]")
        key = relative.as_posix()
        if key in expected:
            raise VerificationError(f"{manifest_path}: duplicate path {key!r}")
        if not isinstance(entry["size_bytes"], int) or isinstance(entry["size_bytes"], bool) or entry["size_bytes"] < 0:
            raise VerificationError(f"{manifest_path}: invalid size for {key!r}")
        if not isinstance(entry["sha256"], str) or SHA256_RE.fullmatch(entry["sha256"]) is None:
            raise VerificationError(f"{manifest_path}: invalid SHA-256 for {key!r}")
        expected[key] = (entry["size_bytes"], entry["sha256"])

    actual_entries = manifest_entries(root, exclude=(manifest_path,))
    actual = {entry["path"]: (entry["size_bytes"], entry["sha256"]) for entry in actual_entries}
    missing = sorted(set(expected) - set(actual))
    changed = sorted(key for key in set(expected) & set(actual) if expected[key] != actual[key])
    extra = sorted(set(actual) - set(expected))
    if missing or changed or (strict and extra):
        details = []
        if missing:
            details.append(f"missing={missing}")
        if changed:
            details.append(f"changed={changed}")
        if strict and extra:
            details.append(f"extra={extra}")
        raise VerificationError(f"manifest mismatch: {'; '.join(details)}")
    return {"manifest": str(manifest_path), "files": len(expected), "strict": strict}


def extract_seed_sets(config: Mapping[str, Any]) -> dict[str, list[int]]:
    if config.get("schema_version") != "vrx-seed-sets/v1":
        raise VerificationError("seed config must declare schema_version vrx-seed-sets/v1")
    raw_sets = config.get("sets")
    if not isinstance(raw_sets, dict) or not raw_sets:
        raise VerificationError("seed config must contain a non-empty sets object")
    result: dict[str, list[int]] = {}
    for name, raw_set in raw_sets.items():
        values = raw_set.get("seeds") if isinstance(raw_set, dict) else raw_set
        if not isinstance(name, str) or not name:
            raise VerificationError("seed set names must be non-empty strings")
        if not isinstance(values, list) or not values:
            raise VerificationError(f"seed set {name!r} must contain a non-empty seeds list")
        if any(not isinstance(seed, int) or isinstance(seed, bool) for seed in values):
            raise VerificationError(f"seed set {name!r} contains a non-integer seed")
        if len(values) != len(set(values)):
            raise VerificationError(f"seed set {name!r} contains duplicate seeds")
        result[name] = values
    return result


def check_seed_sets(config_path: Path) -> dict[str, Any]:
    config = load_json(config_path)
    if not isinstance(config, dict):
        raise VerificationError(f"{config_path}: seed config must be an object")
    sets = extract_seed_sets(config)
    raw_pairs = config.get("disjoint", [])
    if not isinstance(raw_pairs, list):
        raise VerificationError("seed config disjoint must be a list of name pairs")
    pairs: list[list[str]] = []
    for pair in raw_pairs:
        if not isinstance(pair, list) or len(pair) != 2 or any(name not in sets for name in pair):
            raise VerificationError(f"invalid disjoint seed-set pair: {pair!r}")
        pairs.append(pair)
        overlap = sorted(set(sets[pair[0]]) & set(sets[pair[1]]))
        if overlap:
            raise VerificationError(f"seed sets {pair[0]!r} and {pair[1]!r} overlap: {overlap}")
    all_seen: dict[int, str] = {}
    collisions: list[dict[str, Any]] = []
    for name, values in sets.items():
        for seed in values:
            if seed in all_seen:
                collisions.append({"seed": seed, "sets": [all_seen[seed], name]})
            else:
                all_seen[seed] = name
    if collisions:
        raise VerificationError(f"seed appears in multiple sets: {collisions}")
    return {"config": str(config_path), "sets": {name: len(values) for name, values in sets.items()}, "disjoint_pairs": pairs}


def validate_result(result_path: Path, schema_path: Path, *, root: Path | None = None, seed_config: Path | None = None, manifest: Path | None = None) -> dict[str, Any]:
    result = load_json(result_path)
    schema = load_json(schema_path)
    validate_schema(result, schema)
    if not isinstance(result, dict):
        raise VerificationError("result document must be an object")

    runs = result["runs"]
    run_ids = [run["run_id"] for run in runs]
    seeds = [run["seed"] for run in runs]
    if len(run_ids) != len(set(run_ids)):
        raise VerificationError("result runs contain duplicate run_id values")
    if len(seeds) != len(set(seeds)):
        raise VerificationError("result runs contain duplicate seed values")
    aggregate = result["aggregate"]
    if aggregate["n"] != len(runs):
        raise VerificationError("aggregate.n must equal the number of runs")
    mean = sum(run["score"] for run in runs) / len(runs)
    if not math.isclose(aggregate["value"], mean, rel_tol=1e-9, abs_tol=1e-9):
        raise VerificationError(f"aggregate.value {aggregate['value']} does not equal run-score mean {mean}")

    artifact_entries = result["artifacts"]
    artifact_map: dict[str, Mapping[str, Any]] = {}
    for entry in artifact_entries:
        key = entry["path"]
        if key in artifact_map:
            raise VerificationError(f"result artifacts contain duplicate path {key!r}")
        artifact_map[key] = entry
        if SHA256_RE.fullmatch(entry["sha256"]) is None:
            raise VerificationError(f"invalid artifact SHA-256 for {key!r}")
    for index, run in enumerate(runs):
        for path in run["artifacts"]:
            if path not in artifact_map:
                raise VerificationError(f"runs[{index}] references undeclared artifact {path!r}")

    seed_summary = None
    if seed_config is not None:
        seed_summary = check_seed_sets(seed_config)
        configured = extract_seed_sets(load_json(seed_config))
        set_name = result["seed_set"]["name"]
        if set_name not in configured:
            raise VerificationError(f"result seed set {set_name!r} is not present in {seed_config}")
        if result["seed_set"]["seeds"] != configured[set_name]:
            raise VerificationError(f"result seed_set.seeds does not match configured set {set_name!r}")
        configured_sha = sha256_file(seed_config)
        if result["provenance"]["config_sha256"] != configured_sha:
            raise VerificationError(f"result provenance.config_sha256 does not match {seed_config}")
    artifact_summary = None
    if root is not None:
        root = root.resolve()
        for key, entry in artifact_map.items():
            relative = safe_relative_path(key, root, label="result artifact")
            path = root / relative
            if not path.is_file() or path.is_symlink():
                raise VerificationError(f"result artifact does not resolve to a regular file: {key!r}")
            observed_size = path.stat().st_size
            observed_sha = sha256_file(path)
            if observed_size != entry["size_bytes"] or observed_sha != entry["sha256"]:
                raise VerificationError(f"artifact digest mismatch for {key!r}")
        artifact_summary = {"checked": len(artifact_map), "root": str(root)}
    manifest_summary = None
    if manifest is not None:
        if root is None:
            raise VerificationError("--manifest requires --root")
        manifest_summary = check_manifest(root, manifest)

    comparability = result["protocol"]["comparability"]
    evidence_statuses = [item["status"] for item in result["protocol"]["evidence"]]
    if result["claim_status"] == "promoted":
        if root is None or seed_config is None or manifest is None:
            raise VerificationError("promoted claims require --root, --seed-config, and --manifest so evidence is checked")
        provenance = result["provenance"]
        required = {
            "comparability": comparability == "direct",
            "all_evidence_verified": bool(evidence_statuses) and all(status == "verified" for status in evidence_statuses),
            "candidate_matches_clean_clone": provenance["candidate_commit"] == provenance["clean_clone_commit"],
            "clean_clone_verified": provenance.get("clean_clone_verified") is True,
            "benchmark_tree_verified": provenance.get("benchmark_tree_verified") is True,
            "manifest_verified": provenance.get("manifest_verified") is True,
        }
        failed = [name for name, passed in required.items() if not passed]
        if failed:
            raise VerificationError(f"promoted claims require independently verified evidence: {failed}")

    return {
        "result": str(result_path),
        "schema": str(schema_path),
        "runs": len(runs),
        "aggregate": aggregate["value"],
        "claim_status": result["claim_status"],
        "comparability": comparability,
        "seed_check": seed_summary,
        "artifact_check": artifact_summary,
        "manifest_check": manifest_summary,
    }


def protected_path(path: str, config: Mapping[str, Any]) -> bool:
    prefixes = config.get("protected_prefixes", [])
    exact_paths = config.get("protected_exact_paths", [])
    if path in exact_paths:
        return True
    for prefix in prefixes:
        normalized = str(prefix).strip("/")
        if normalized and (path == normalized or path.startswith(normalized + "/")):
            return True
    return False


def diff_paths(repo: Path, base: str, target: str) -> list[str]:
    raw = subprocess.run(
        ["git", "-C", str(repo), "diff", "--name-status", "--find-renames", "-z", base, target],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout
    fields = raw.decode("utf-8", errors="surrogateescape").split("\0")
    changed: list[str] = []
    index = 0
    while index < len(fields) and fields[index]:
        status = fields[index]
        index += 1
        if index >= len(fields):
            break
        first = fields[index]
        index += 1
        changed.append(first)
        if status.startswith("R") or status.startswith("C"):
            if index < len(fields) and fields[index]:
                changed.append(fields[index])
                index += 1
    return sorted(set(changed))


def tree_listing(repo: Path, ref: str, pathspec: str) -> str:
    return run_git(repo, ["ls-tree", "-r", "-z", "--full-tree", ref, "--", pathspec]).stdout


def check_benchmark_tree(repo_path: Path, config_path: Path, base_ref: str, target_ref: str) -> dict[str, Any]:
    repo = repo_root(repo_path)
    config = load_json(config_path)
    if not isinstance(config, dict) or config.get("schema_version") != "vrx-benchmark-integrity/v1":
        raise VerificationError(f"{config_path}: expected vrx-benchmark-integrity/v1")
    base = git_ref(repo, base_ref)
    target = git_ref(repo, target_ref)
    changed = [path for path in diff_paths(repo, base, target) if protected_path(path, config)]
    if changed:
        raise VerificationError(f"protected benchmark/scorer paths changed from {base_ref} to {target_ref}: {changed}")

    raw_roots = config.get("protected_prefixes", [])
    raw_exact = config.get("protected_exact_paths", [])
    if not isinstance(raw_roots, list) or not isinstance(raw_exact, list):
        raise VerificationError(f"{config_path}: protected path lists must be arrays")
    roots = [str(item).strip("/") for item in raw_roots]
    exact = [str(item).strip("/") for item in raw_exact]
    specs = roots + exact
    snapshots = {}
    present = 0
    for spec in specs:
        before = tree_listing(repo, base, spec)
        after = tree_listing(repo, target, spec)
        if before != after:
            raise VerificationError(f"protected tree listing changed for {spec!r}")
        if before:
            present += 1
        snapshots[spec] = hashlib.sha256(before.encode("utf-8", errors="surrogateescape")).hexdigest()
    if present == 0 and not config.get("allow_missing", False):
        raise VerificationError("no configured benchmark/scorer paths exist; integrity check would be vacuous")
    return {
        "repository": str(repo),
        "base": base,
        "target": target,
        "protected_specs": specs,
        "present_specs": present,
        "vacuous": present == 0,
        "tree_digests": snapshots,
    }


def remote_url(repo: Path) -> str | None:
    result = run_git(repo, ["remote", "get-url", "origin"], check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def clone_source(repo_arg: str) -> str:
    candidate = Path(repo_arg)
    if candidate.exists():
        repo = repo_root(candidate)
        return remote_url(repo) or str(repo)
    parsed = urlparse(repo_arg)
    if parsed.scheme or repo_arg.startswith("git@"):
        return repo_arg
    raise VerificationError(f"repository path or URL does not exist: {repo_arg}")


def clean_clone(repo_arg: str, commit: str, ref: str | None, command: str | None) -> dict[str, Any]:
    if GIT_SHA_RE.fullmatch(commit) is None:
        raise VerificationError("--commit must be a full 40-character lowercase Git commit SHA")
    source = clone_source(repo_arg)
    with tempfile.TemporaryDirectory(prefix="vrx-clean-clone-") as temp:
        checkout = Path(temp) / "checkout"
        subprocess.run(["git", "clone", "--no-checkout", "--origin", "origin", source, str(checkout)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if ref:
            subprocess.run(["git", "-C", str(checkout), "fetch", "--no-tags", "origin", ref], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        checkout_result = subprocess.run(["git", "-C", str(checkout), "checkout", "--detach", commit], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if checkout_result.returncode != 0:
            fetch_result = subprocess.run(["git", "-C", str(checkout), "fetch", "--no-tags", "origin", commit], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if fetch_result.returncode != 0:
                detail = (fetch_result.stderr or checkout_result.stderr).strip()
                raise VerificationError(f"clean clone could not fetch commit {commit}: {detail}")
            subprocess.run(["git", "-C", str(checkout), "checkout", "--detach", commit], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        actual = subprocess.run(["git", "-C", str(checkout), "rev-parse", "HEAD"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout.strip()
        if actual != commit:
            raise VerificationError(f"clean clone checked out {actual}, expected {commit}")
        status = subprocess.run(["git", "-C", str(checkout), "status", "--porcelain", "--untracked-files=all"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout
        if status:
            raise VerificationError(f"fresh checkout is not clean: {status!r}")
        if command:
            environment = os.environ.copy()
            environment["VRX_CLEAN_CLONE"] = "1"
            completed = subprocess.run(command, shell=True, cwd=checkout, env=environment)
            if completed.returncode != 0:
                raise VerificationError(f"clean-clone command failed with exit code {completed.returncode}: {command}")
            status_after = subprocess.run(["git", "-C", str(checkout), "status", "--porcelain", "--untracked-files=all"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout
            if status_after:
                raise VerificationError(f"clean-clone command modified the checkout: {status_after!r}")
        return {"source": source, "commit": actual, "clean": True, "command": command}


def command_manifest(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root).resolve()
    if args.output and args.check:
        raise VerificationError("use either --output or --check, not both")
    if args.output:
        output = Path(args.output).resolve()
        manifest = create_manifest(root, output)
        write_json(output, manifest)
        return {"written": str(output), "files": len(manifest["files"])}
    if args.check:
        return check_manifest(root, Path(args.check).resolve(), strict=not args.allow_extra)
    raise VerificationError("manifest requires --output or --check")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    clean = subparsers.add_parser("clean-clone", help="clone and verify an exact clean commit")
    clean.add_argument("--repo", required=True, help="repository URL or local checkout with an origin remote")
    clean.add_argument("--commit", required=True, help="full commit SHA to check out")
    clean.add_argument("--ref", help="optional branch/ref to fetch before checking out the commit")
    clean.add_argument("--run-command", help="optional shell command to run from the clean checkout")

    integrity = subparsers.add_parser("benchmark-tree", help="prove configured benchmark/scorer trees did not change")
    integrity.add_argument("--repo", default=".")
    integrity.add_argument("--config", default=str(DEFAULT_INTEGRITY_CONFIG))
    integrity.add_argument("--baseline-ref", default="origin/main")
    integrity.add_argument("--target-ref", default="HEAD")

    results = subparsers.add_parser("results", help="validate a result document and optional artifact evidence")
    results.add_argument("--input", required=True)
    results.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    results.add_argument("--root", help="artifact root; omit to validate schema and result semantics only")
    results.add_argument("--seed-config")
    results.add_argument("--manifest")

    seeds = subparsers.add_parser("seeds", help="check seed uniqueness and configured disjointness")
    seeds.add_argument("--config", default=str(DEFAULT_SEED_CONFIG))

    manifest = subparsers.add_parser("manifest", help="create or verify a deterministic SHA-256 manifest")
    manifest.add_argument("--root", required=True)
    manifest.add_argument("--output")
    manifest.add_argument("--check")
    manifest.add_argument("--allow-extra", action="store_true", help="permit unlisted files during --check")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.subcommand == "clean-clone":
            result = clean_clone(args.repo, args.commit, args.ref, args.run_command)
        elif args.subcommand == "benchmark-tree":
            result = check_benchmark_tree(Path(args.repo), Path(args.config), args.baseline_ref, args.target_ref)
        elif args.subcommand == "results":
            result = validate_result(
                Path(args.input),
                Path(args.schema),
                root=Path(args.root) if args.root else None,
                seed_config=Path(args.seed_config) if args.seed_config else None,
                manifest=Path(args.manifest) if args.manifest else None,
            )
        elif args.subcommand == "seeds":
            result = check_seed_sets(Path(args.config))
        elif args.subcommand == "manifest":
            result = command_manifest(args)
        else:
            raise VerificationError(f"unknown subcommand {args.subcommand!r}")
    except VerificationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "").strip() if isinstance(exc.stderr, str) else ""
        print(f"ERROR: command failed with exit code {exc.returncode}: {detail}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
