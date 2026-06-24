#!/usr/bin/env python3
"""Build the unified Bavli JSON — single source of truth."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.build import build_bavli  # noqa: E402

DEFAULT_OUT = ROOT / "data" / "bavli.json"
COMPACT_OUT = ROOT / "data" / "bavli.min.json"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build unified uncensored Bavli (one JSON file)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Output path (default: {DEFAULT_OUT.relative_to(ROOT)})",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Also write compact minified JSON (bavli.min.json)",
    )
    parser.add_argument(
        "--max-daf",
        type=int,
        default=None,
        help="Limit dapim per tractate (testing)",
    )
    parser.add_argument(
        "--api-gemara",
        action="store_true",
        help="Fetch gemara from live Sefaria API (cached; slower first run)",
    )
    parser.add_argument(
        "--tractate",
        action="append",
        dest="tractates",
        help="Build only these tractates (repeatable)",
    )
    args = parser.parse_args()

    result = build_bavli(
        max_daf=args.max_daf,
        use_api_gemara=args.api_gemara,
        tractates=args.tractates,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    size_mb = args.output.stat().st_size / (1024 * 1024)
    print(
        f"Wrote {args.output} — {result['meta']['daf_count']} dapim, "
        f"{result['meta']['tractate_count']} tractates, "
        f"{result['meta']['total_patch_events']} patch events ({size_mb:.1f} MB)"
    )

    if args.compact:
        COMPACT_OUT.write_text(
            json.dumps(result, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        c_mb = COMPACT_OUT.stat().st_size / (1024 * 1024)
        print(f"Wrote {COMPACT_OUT} ({c_mb:.1f} MB)")


if __name__ == "__main__":
    main()
