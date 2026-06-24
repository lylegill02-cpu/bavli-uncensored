#!/usr/bin/env python3
"""Verify famous uncensored loci in unified bavli.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "bavli.json"

CHECKS = [
    ("Sanhedrin.43a", "יֵשׁוּ", "Yeshu baraita"),
    ("Sanhedrin.67a", "סָטָדָא", "ben Stada / Pandera"),
    ("Gittin.57a", "יֵשׁוּ", "Yeshu ha-Notzri"),
]


def main() -> None:
    if not SOURCE.exists():
        print(f"MISSING: {SOURCE}")
        sys.exit(1)

    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    refs = data.get("refs", {})
    failed = False
    lines = []

    for ref, needle, label in CHECKS:
        entry = refs.get(ref)
        if not entry:
            lines.append(f"FAIL {ref}: not in source ({label})")
            failed = True
            continue
        text = " ".join(entry.get("gemara", []))
        ok = needle in text
        if not ok:
            failed = True
        lines.append(f"{'OK' if ok else 'FAIL'} {ref}: {label}")

    out = ROOT / "data" / "reports" / "loci_verify.txt"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    for line in lines:
        print(line)
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
