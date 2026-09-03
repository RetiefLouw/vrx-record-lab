"""Validation and selection for the reconstructed public VRX 2019 suite.

The phase-2 worlds are upstream inputs.  This module only validates the
manifest's explicit mapping and never changes, scores, or vendors those
worlds.
"""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any, Mapping


class Phase2ProtocolError(ValueError):
    """The manifest does not describe the public six-world protocol."""


def _worlds(parameters: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    protocol = parameters.get("protocol")
    if not isinstance(protocol, Mapping):
        raise Phase2ProtocolError("task.parameters.protocol must be an object")
    worlds = protocol.get("worlds")
    if not isinstance(worlds, list) or len(worlds) != 6:
        raise Phase2ProtocolError("the reconstructed phase-2 protocol requires exactly six worlds")
    if not all(isinstance(world, Mapping) for world in worlds):
        raise Phase2ProtocolError("protocol.worlds entries must be objects")
    return tuple(worlds)


def validate_phase2_protocol(manifest: Mapping[str, Any]) -> None:
    """Check the public-world, timing, and score-topic contract."""

    parameters = manifest.get("task", {}).get("parameters", {})
    if not isinstance(parameters, Mapping):
        raise Phase2ProtocolError("task.parameters must be an object")
    protocol = parameters.get("protocol")
    if not isinstance(protocol, Mapping):
        raise Phase2ProtocolError("task.parameters.protocol must be an object")
    if protocol.get("run_mode") != "complete_scored":
        raise Phase2ProtocolError("the canonical phase-2 manifest must use run_mode=complete_scored")
    if protocol.get("initial_state_duration_s") != 10:
        raise Phase2ProtocolError("phase-2 initial_state_duration_s must be 10")
    if protocol.get("ready_state_duration_s") != 10:
        raise Phase2ProtocolError("phase-2 ready_state_duration_s must be 10")
    if protocol.get("scored_running_duration_s") != 300:
        raise Phase2ProtocolError("phase-2 scored_running_duration_s must be 300")
    if protocol.get("score_topic") != "/vrx/task/info":
        raise Phase2ProtocolError("phase-2 score_topic must be /vrx/task/info")
    order = protocol.get("trial_order")
    worlds = _worlds(parameters)
    if order != [world.get("id") for world in worlds]:
        raise Phase2ProtocolError("protocol.trial_order must match protocol.worlds order")
    if order != [f"stationkeeping{i}" for i in range(6)]:
        raise Phase2ProtocolError("phase-2 trial_order must be stationkeeping0 through stationkeeping5")

    seen = set()
    for world in worlds:
        world_id = world.get("id")
        relative_path = world.get("path")
        if not isinstance(world_id, str) or world_id in seen:
            raise Phase2ProtocolError("phase-2 world ids must be unique strings")
        seen.add(world_id)
        expected_path = f"vrx_gazebo/worlds/2019_phase2/{world_id}.world"
        if relative_path != expected_path:
            raise Phase2ProtocolError(f"{world_id}: path must be {expected_path}")
        path = PurePosixPath(relative_path)
        if path.is_absolute() or ".." in path.parts:
            raise Phase2ProtocolError(f"{world_id}: world path must stay inside the upstream VRX tree")
        for field in ("source_commit", "source_sha256"):
            value = world.get(field)
            if not isinstance(value, str) or not value:
                raise Phase2ProtocolError(f"{world_id}: {field} is required")
        if not isinstance(world.get("wind_seed"), int) or isinstance(world.get("wind_seed"), bool):
            raise Phase2ProtocolError(f"{world_id}: wind_seed must be an integer")


def select_phase2_world(manifest: Mapping[str, Any], seed: int) -> Mapping[str, Any]:
    """Map the manifest's stable trial index to one explicit public world."""

    validate_phase2_protocol(manifest)
    worlds = _worlds(manifest["task"]["parameters"])
    if not isinstance(seed, int) or isinstance(seed, bool) or seed < 0 or seed >= len(worlds):
        raise Phase2ProtocolError(f"phase-2 trial index must be in [0, 5], got {seed!r}")
    return worlds[seed]
