"""Launch boundary for the unchanged upstream/reference controller.

The historical controller is intentionally not reimplemented here. The
manifest's ``controller.command`` must point at the upstream launch command
when that source and ROS environment are available. This wrapper only supplies
the trial identity and manifest parameters, preserving the upstream process as
an external reproducibility anchor.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from .manifest import load_manifest
from .runner import _render_command


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--trial-id", default=None)
    args = parser.parse_args(argv)
    try:
        manifest = load_manifest(args.manifest)
        command = manifest["controller"].get("command", [])
        if not command:
            raise ValueError("controller.command is empty; upstream controller source is not available in this checkout")
        trial_id = args.trial_id or f"trial-seed-{args.seed}"
        env = os.environ.copy()
        env.update(
            {
                "VRX_TRIAL_ID": trial_id,
                "VRX_TRIAL_SEED": str(args.seed),
                "VRX_EXPERIMENT_MANIFEST": str(args.manifest.resolve()),
                "VRX_TASK_ENVIRONMENT_JSON": json.dumps(manifest["trials"].get("environment", {}), sort_keys=True),
                "VRX_TASK_PARAMETERS_JSON": json.dumps(manifest["task"].get("parameters", {}), sort_keys=True),
                "VRX_CONTROLLER_PARAMETERS_JSON": json.dumps(manifest["controller"].get("parameters", {}), sort_keys=True),
            }
        )
        rendered = _render_command(command, {"seed": str(args.seed), "trial_id": trial_id, "manifest": str(args.manifest.resolve())})
        return subprocess.run(rendered, cwd=str(args.manifest.parent), env=env, check=False).returncode
    except (OSError, ValueError) as exc:
        print(f"reference_controller: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
