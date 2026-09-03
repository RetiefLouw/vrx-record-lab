"""CLI for executing one explicit simulator/scorer adapter trial."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .manifest import load_manifest
from .runner import TrialError, execute_trial


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True, help="per-trial JSON output path")
    parser.add_argument("--trial-id", default=None)
    args = parser.parse_args(argv)
    try:
        manifest = load_manifest(args.manifest)
        trial_id = args.trial_id or f"trial-seed-{args.seed}"
        trial, _ = execute_trial(args.manifest, manifest, args.seed, args.output, trial_id)
    except (OSError, ValueError) as exc:
        print(f"run_trial: {exc}", file=sys.stderr)
        return 2
    print(trial["status"])
    if trial["status"] != "completed":
        if trial.get("error"):
            print(trial["error"], file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
