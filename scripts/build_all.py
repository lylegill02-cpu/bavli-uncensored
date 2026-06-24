#!/usr/bin/env python3
"""Build all tractates listed in data/tractates.json."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "scripts" / "build_tractate.py"
TRACTATES_PATH = ROOT / "data" / "tractates.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build all Bavli tractates")
    parser.add_argument(
        "--only",
        nargs="*",
        help="Build only these tractate names (default: all 37)",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip tractates whose output JSON already exists",
    )
    args = parser.parse_args()

    catalog = json.loads(TRACTATES_PATH.read_text(encoding="utf-8"))
    names = sorted(args.only) if args.only else sorted(catalog)

    for name in names:
        if name not in catalog:
            raise SystemExit(f"Unknown tractate {name!r}")
        out = ROOT / "data" / "output" / f"{name.replace(' ', '_')}.json"
        if args.skip_existing and out.exists():
            print(f"=== {name} (skip existing) ===")
            continue
        print(f"=== {name} ===")
        subprocess.run(
            [sys.executable, str(BUILD), name],
            check=False,
            cwd=ROOT,
        )


if __name__ == "__main__":
    main()
