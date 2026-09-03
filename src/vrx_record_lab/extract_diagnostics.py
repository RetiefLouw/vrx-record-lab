"""CLI for extracting Q-03 diagnostics from one trial or a suite."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .diagnostics import DiagnosticsError, extract_diagnostics
from .jsonio import write_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="trial artifact directory or suite result directory")
    parser.add_argument("--output", type=Path, required=True, help="diagnostics JSON output path")
    args = parser.parse_args(argv)
    try:
        document = extract_diagnostics(args.input)
        write_json(args.output, document)
    except (DiagnosticsError, OSError, ValueError) as exc:
        print(f"extract_diagnostics: {exc}", file=sys.stderr)
        return 2
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
