"""CLI for executing every seed in an immutable experiment manifest."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .runner import TrialError, run_suite


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--result-id", default=None)
    args = parser.parse_args(argv)
    try:
        result, result_path = run_suite(args.manifest, args.output_dir, result_id=args.result_id)
    except (OSError, ValueError) as exc:
        print(f"run_suite: {exc}", file=sys.stderr)
        return 2
    print(result_path)
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
