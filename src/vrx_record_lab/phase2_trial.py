"""Docker adapter for one complete public VRX 2019 phase-2 world run."""

from __future__ import annotations

import json
import math
import os
import signal
import subprocess
from pathlib import Path
from typing import Any

from .jsonio import load_json
from .manifest import load_manifest
from .phase2_protocol import Phase2ProtocolError, select_phase2_world


def _write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _output(status: str, *, score: float | None = None, error: str | None = None, **fields: Any) -> dict:
    value = {
        "completed": status == "completed",
        "status": status,
        "score": score,
        "score_components": {},
        "real_time_factor": None,
        "environment": {},
        "metrics": {},
    }
    value.update(fields)
    if error:
        value["error"] = error
    return value


def _terminate_process(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=10)


def _compose_down(repo_root: Path, env: dict[str, str], log_path: Path) -> None:
    command = [
        "docker",
        "compose",
        "--env-file",
        str(repo_root / "config/vrx-2019.env"),
        "-f",
        str(repo_root / "compose.yaml"),
        "down",
        "--remove-orphans",
    ]
    try:
        result = subprocess.run(
            command,
            cwd=repo_root,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=30,
            check=False,
        )
        log_path.write_text(result.stdout or "", encoding="utf-8", errors="replace")
    except (OSError, subprocess.TimeoutExpired) as exc:
        log_path.write_text(f"teardown error: {exc}\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    del argv
    output_path = Path(os.environ["VRX_TRIAL_OUTPUT"])
    artifact_dir = Path(os.environ["VRX_TRIAL_ARTIFACT_DIR"])
    manifest_path = Path(os.environ["VRX_EXPERIMENT_MANIFEST"])
    seed = int(os.environ["VRX_TRIAL_SEED"])
    artifact_dir.mkdir(parents=True, exist_ok=True)

    try:
        manifest = load_manifest(manifest_path)
        world = select_phase2_world(manifest, seed)
    except (KeyError, OSError, ValueError, Phase2ProtocolError) as exc:
        _write(output_path, _output("invalid", error=str(exc)))
        return 0

    repo_root = manifest_path.parents[2]
    protocol = manifest["task"]["parameters"]["protocol"]
    controller = manifest.get("controller", {})
    controller_parameters = controller.get("parameters", {})
    controller_runtime = controller.get("runtime", {})
    controller_enabled = bool(controller_runtime.get("enabled", False))
    if controller_enabled and not isinstance(controller_parameters, dict):
        _write(output_path, _output("invalid", error="controller.parameters must be an object when the phase-2 controller is enabled"))
        return 0
    if controller_enabled and controller.get("command") != ["roslaunch", "vrx_controller_ros", "scored_station_keeping.launch"]:
        _write(output_path, _output("invalid", error="phase-2 controller command must be the pinned ROS scored_station_keeping.launch"))
        return 0
    localization_topic = controller_parameters.get("localization_topic", "/wamv/robot_localization/odometry/filtered")
    position_source = controller_parameters.get("position_source", "/wamv/sensors/gps/gps/fix")
    goal_topic = controller_parameters.get("goal_topic", "/vrx/station_keeping/goal")
    diagnostics_topic = controller_parameters.get("diagnostics_topic", "/vrx_controller/diagnostics")
    if not all(isinstance(value, str) and value for value in (localization_topic, position_source, goal_topic, diagnostics_topic)):
        _write(output_path, _output("invalid", error="enabled phase-2 controller topic parameters must be non-empty strings"))
        return 0
    container_world = f"/opt/vrx_ws/src/vrx/{world['path']}"
    run_metadata = {
        "protocol": "public-vrx-2019-phase2-station-keeping",
        "run_mode": protocol["run_mode"],
        "trial_id": os.environ.get("VRX_TRIAL_ID"),
        "trial_index": seed,
        "world": dict(world),
        "world_container_path": container_world,
        "timing": {
            "initial_state_duration_s": protocol["initial_state_duration_s"],
            "ready_state_duration_s": protocol["ready_state_duration_s"],
            "scored_running_duration_s": protocol["scored_running_duration_s"],
            "wall_timeout_s": protocol["wall_timeout_s"],
        },
        "score_topic": protocol["score_topic"],
        "score_field": protocol["score_field"],
        "debug_topics": protocol["debug_topics"],
        "controller": {
            "enabled": controller_enabled,
            "name": controller.get("name"),
            "source": controller.get("source"),
            "revision": controller.get("revision"),
            "command": controller.get("command", []),
            "parameters": controller_parameters,
        },
        "source": {
            "repository": protocol["source_repository"],
            "commit": world["source_commit"],
        },
    }
    _write(artifact_dir / "run-metadata.json", run_metadata)

    env = os.environ.copy()
    env.update(
        {
            "VRX_ARTIFACT_DIR": str(artifact_dir.resolve()),
            "VRX_WORLD_PATH": container_world,
            "VRX_WORLD_ID": world["id"],
            "VRX_PHASE2_EXPECTED_WORLD_SHA256": world["source_sha256"],
            "VRX_WIND_SEED": "",
            "VRX_PHASE2_ARTIFACT_DIR": "/var/log/vrx",
            "VRX_PHASE2_WALL_TIMEOUT_S": str(protocol["wall_timeout_s"]),
            "VRX_PHASE2_EXPECTED_RUNNING_DURATION_S": str(protocol["scored_running_duration_s"]),
            "VRX_PHASE2_CONTROLLER_ENABLED": "true" if controller_enabled else "false",
            "VRX_CONTROLLER_CONFIG": controller_runtime.get(
                "controller_config", "/opt/vrx_ws/src/vrx_controller_ros/config/controller.yaml"
            ),
            "VRX_CONTROLLER_LOCALIZATION_TOPIC": localization_topic,
            "VRX_CONTROLLER_POSITION_SOURCE": position_source,
            "VRX_CONTROLLER_GOAL_TOPIC": goal_topic,
            "VRX_CONTROLLER_DIAGNOSTICS_TOPIC": diagnostics_topic,
            "VRX_CONTROLLER_PARAMETERS_JSON": json.dumps(controller_parameters, sort_keys=True),
        }
    )
    # Preserve explicit shortened-run overrides for plumbing smoke tests.
    # They are intentionally not part of the canonical manifest and are
    # rejected by the promotion gates as non-performance evidence.
    duration_overrides = {
        name: os.environ[name]
        for name in (
            "VRX_INITIAL_STATE_DURATION_OVERRIDE",
            "VRX_READY_STATE_DURATION_OVERRIDE",
            "VRX_RUNNING_STATE_DURATION_OVERRIDE",
        )
        if os.environ.get(name)
    }
    compose = [
        "docker",
        "compose",
        "--env-file",
        str(repo_root / "config/vrx-2019.env"),
        "-f",
        str(repo_root / "compose.yaml"),
        "run",
        "--rm",
        "--no-deps",
        "--entrypoint",
        "/usr/local/bin/vrx-run-phase2-stationkeeping",
        "-e",
        f"VRX_WORLD_PATH={container_world}",
        "-e",
        f"VRX_WORLD_ID={world['id']}",
        "-e",
        f"VRX_PHASE2_EXPECTED_WORLD_SHA256={world['source_sha256']}",
        "-e",
        "VRX_WIND_SEED=",
        "-e",
        f"VRX_PHASE2_CONTROLLER_ENABLED={'true' if controller_enabled else 'false'}",
        "-e",
        f"VRX_CONTROLLER_CONFIG={controller_runtime.get('controller_config', '/opt/vrx_ws/src/vrx_controller_ros/config/controller.yaml')}",
        "-e",
        f"VRX_CONTROLLER_LOCALIZATION_TOPIC={localization_topic}",
        "-e",
        f"VRX_CONTROLLER_POSITION_SOURCE={position_source}",
        "-e",
        f"VRX_CONTROLLER_GOAL_TOPIC={goal_topic}",
        "-e",
        f"VRX_CONTROLLER_DIAGNOSTICS_TOPIC={diagnostics_topic}",
        "-e",
        f"VRX_CONTROLLER_PARAMETERS_JSON={json.dumps(controller_parameters, sort_keys=True)}",
        "simulator",
    ]
    for name, value in duration_overrides.items():
        compose[-1:0] = ["-e", f"{name}={value}"]
    adapter_stdout = artifact_dir / "docker.stdout.log"
    adapter_stderr = artifact_dir / "docker.stderr.log"
    return_code = 1
    timed_out = False
    try:
        with adapter_stdout.open("w", encoding="utf-8") as stdout, adapter_stderr.open("w", encoding="utf-8") as stderr:
            process = subprocess.Popen(
                compose,
                cwd=repo_root,
                env=env,
                stdout=stdout,
                stderr=stderr,
                start_new_session=True,
            )
            try:
                return_code = process.wait(timeout=float(protocol["wall_timeout_s"]))
            except subprocess.TimeoutExpired:
                timed_out = True
                _terminate_process(process)
                return_code = 124
    except OSError as exc:
        adapter_stderr.write_text(f"could not start docker compose: {exc}\n", encoding="utf-8")
        return_code = 127
    finally:
        _compose_down(repo_root, env, artifact_dir / "compose-down.log")

    score_path = artifact_dir / "score.json"
    if timed_out or return_code == 124:
        result = _output("timeout", error=f"phase-2 container exceeded wall timeout of {protocol['wall_timeout_s']} seconds")
    elif return_code != 0:
        result = _output("failed", error=f"phase-2 container exited with code {return_code}")
    elif not score_path.is_file():
        result = _output("invalid", error="collector did not write score.json")
    else:
        try:
            score_doc = load_json(score_path)
            final = score_doc.get("final")
            score = final.get("score") if isinstance(final, dict) else None
            if score_doc.get("completed") is not True or not isinstance(score, (int, float)) or isinstance(score, bool) or not math.isfinite(float(score)):
                result = _output("invalid", error="collector did not observe a finite final finished task score")
            else:
                debug = score_doc.get("debug", {})
                result = _output(
                    "completed",
                    score=float(score),
                    score_components={"task_info_score": float(score)},
                    environment={"world_id": world["id"], "wind_seed": world["wind_seed"]},
                    metrics={
                        "task_messages": len(score_doc.get("task_messages", [])),
                        "pose_error_messages": len(debug.get("pose_error", [])) if isinstance(debug, dict) else 0,
                        "mean_error_messages": len(debug.get("mean_error", [])) if isinstance(debug, dict) else 0,
                        "controller_diagnostic_messages": int(score_doc.get("controller_diagnostics_count", 0)),
                        "controller_diagnostic_parse_errors": int(score_doc.get("controller_diagnostic_parse_errors", 0)),
                        "finished_timed_out": bool(final.get("timed_out")),
                        "scored_running_duration_s": protocol["scored_running_duration_s"],
                    },
                )
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            result = _output("invalid", error=f"could not extract score.json: {exc}")

    _write(output_path, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
