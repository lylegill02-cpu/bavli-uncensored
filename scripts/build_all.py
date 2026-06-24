#!/usr/bin/env python3
"""Build unified Bavli (primary) and optional per-tractate split files."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD_BAVLI = ROOT / "scripts" / "build_bavli.py"
BUILD_TRACTATE = ROOT / "scripts" / "build_tractate.py"

sys.path.insert(0, str(ROOT / "scripts"))
from lib.build import load_bavli_order  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Build full uncensored Bavli")
    parser.add_argument(
        "--split",
        action="store_true",
        help="Also write per-tractate files under data/output/",
    )
    parser.add_argument(
        "--api-gemara",
        action="store_true",
        help="Use live Sefaria API for gemara (cached)",
    )
    parser.add_argument("--compact", action="store_true", help="Write bavli.min.json too")
    args = parser.parse_args()

    cmd = [sys.executable, str(BUILD_BAVLI)]
    if args.compact:
        cmd.append("--compact")
    if args.api_gemara:
        cmd.append("--api-gemara")
    subprocess.run(cmd, check=True, cwd=ROOT)

    if args.split:
        for name in load_bavli_order():
            print(f"=== split: {name} ===")
            split_cmd = [sys.executable, str(BUILD_TRACTATE), name]
            if args.api_gemara:
                split_cmd.append("--api-gemara")
            subprocess.run(split_cmd, check=True, cwd=ROOT)


if __name__ == "__main__":
    main()
