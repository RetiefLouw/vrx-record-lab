"""CLI for checking result structure, aggregates, and SHA-256 artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .jsonio import load_json, write_json
from .verify import verify_result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--write", action="store_true", help="write verification fields back to the result")
    parser.add_argument("--output", type=Path, default=None, help="write the standalone verification report to this path")
    args = parser.parse_args(argv)
    try:
        report = verify_result(args.result, args.manifest)
        if args.write:
            result = load_json(args.result)
            result["verification"] = report
            write_json(args.result, result)
        if args.output is not None:
            write_json(args.output, report)
    except (OSError, ValueError) as exc:
        print(f"verify_result: {exc}", file=sys.stderr)
        return 2
    for check in report["checks"]:
        print(f"{'PASS' if check['passed'] else 'FAIL'} {check['name']}: {check['details']}")
    return 0 if report["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
