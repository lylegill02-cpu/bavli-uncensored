#!/usr/bin/env python3
"""Look up a daf from the unified bavli.json source."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "data" / "bavli.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Query unified Bavli by ref")
    parser.add_argument("ref", help='Daf ref, e.g. "Sanhedrin.43a"')
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT,
        help="Path to bavli.json",
    )
    parser.add_argument(
        "--layer",
        choices=("gemara", "rashi", "tosafot", "all"),
        default="all",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    if not args.source.exists():
        raise SystemExit(f"Missing {args.source}. Run: python scripts/build_bavli.py")

    data = json.loads(args.source.read_text(encoding="utf-8"))
    entry = data.get("refs", {}).get(args.ref)
    if not entry:
        raise SystemExit(f"Ref not found: {args.ref}")

    if args.json:
        payload = entry if args.layer == "all" else entry[args.layer]
        sys.stdout.buffer.write(
            (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        )
        return

    if args.layer in ("all", "gemara"):
        print(f"=== {args.ref} — Gemara ===")
        for line in entry["gemara"]:
            print(line)
    if args.layer in ("all", "rashi") and entry.get("rashi"):
        print(f"\n=== {args.ref} — Rashi ===")
        for line in entry["rashi"]:
            print(line)
    if args.layer in ("all", "tosafot") and entry.get("tosafot"):
        print(f"\n=== {args.ref} — Tosafot ===")
        for line in entry["tosafot"]:
            print(line)


if __name__ == "__main__":
    main()
