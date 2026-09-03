"""SHA-256 artifact handling with path traversal protection."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable, Mapping


class ArtifactError(ValueError):
    pass


def safe_artifact_path(root: Path, relative_path: str) -> Path:
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ArtifactError(f"artifact path is not relative to result root: {relative_path}")
    root_resolved = root.resolve()
    path = (root / relative).resolve()
    try:
        path.relative_to(root_resolved)
    except ValueError as exc:
        raise ArtifactError(f"artifact path escapes result root: {relative_path}") from exc
    return path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise ArtifactError(f"cannot hash artifact {path}: {exc}") from exc
    return digest.hexdigest()


def artifact_entry(root: Path, relative_path: str, kind: str = "artifact") -> dict:
    path = safe_artifact_path(root, relative_path)
    if not path.is_file():
        raise ArtifactError(f"artifact is not a regular file: {relative_path}")
    return {"path": Path(relative_path).as_posix(), "sha256": sha256_file(path), "kind": kind}


def write_checksums(path: Path, entries: Iterable[Mapping[str, str]]) -> None:
    lines = [f"{entry['sha256']}  {entry['path']}" for entry in sorted(entries, key=lambda item: item["path"])]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(line + "\n" for line in lines), encoding="utf-8")


def read_checksums(path: Path) -> dict:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ArtifactError(f"cannot read checksum file {path}: {exc}") from exc
    parsed = {}
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        parts = line.split("  ", 1)
        if len(parts) != 2 or len(parts[0]) != 64:
            raise ArtifactError(f"invalid checksum line {line_number} in {path}")
        digest, relative_path = parts
        if relative_path in parsed:
            raise ArtifactError(f"duplicate checksum path {relative_path}")
        parsed[relative_path] = digest
    return parsed
