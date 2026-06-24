#!/usr/bin/env python3
"""Build uncensored Bavli JSON for one tractate (optional split output)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.build import build_tractate  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build one tractate (split file; use build_bavli.py for unified source)"
    )
    parser.add_argument("tractate", help='Tractate name, e.g. "Avodah Zarah"')
    parser.add_argument("--max-daf", type=int, default=None, help="Limit dapim (testing)")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output JSON path (default: data/output/<tractate>.json)",
    )
    parser.add_argument(
        "--api-gemara",
        action="store_true",
        help="Fetch gemara from live Sefaria API (cached)",
    )
    args = parser.parse_args()

    result = build_tractate(
        args.tractate,
        max_daf=args.max_daf,
        use_api_gemara=args.api_gemara,
    )
    out = args.output or ROOT / "data" / "output" / f"{args.tractate.replace(' ', '_')}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"Wrote {out} — {result['daf_count']} dapim, "
        f"{result['total_patch_events']} patch events"
    )


if __name__ == "__main__":
    main()
