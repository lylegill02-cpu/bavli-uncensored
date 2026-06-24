#!/usr/bin/env python3
"""Verify famous uncensored loci appear on correct daf labels in built output."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "output"

CHECKS = [
    ("Sanhedrin", "43a", "יֵשׁוּ", "Yeshu baraita"),
    ("Sanhedrin", "67a", "סָטָדָא", "ben Stada / Pandera"),
    ("Gittin", "57a", "יֵשׁוּ", "Yeshu ha-Notzri"),
]


def main() -> None:
    lines = []
    failed = False
    for tractate, daf, needle, label in CHECKS:
        path = OUTPUT / f"{tractate.replace(' ', '_')}.json"
        if not path.exists():
            lines.append(f"MISSING FILE: {path.name} ({label})")
            failed = True
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        daf_data = data.get("dapim", {}).get(daf)
        if not daf_data:
            lines.append(f"FAIL {tractate} {daf}: daf not in output ({label})")
            failed = True
            continue
        text = " ".join(daf_data.get("gemara", []))
        ok = needle in text
        if not ok:
            failed = True
        lines.append(f"{'OK' if ok else 'FAIL'} {tractate} {daf}: {label}")

    out = ROOT / "data" / "reports" / "loci_verify.txt"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
