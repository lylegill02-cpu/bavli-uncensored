#!/usr/bin/env python3
"""Verify loci against bavli.json and write enriched chart data."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.loci import enrich_loci, suppression_score  # noqa: E402

OUT = ROOT / "data" / "loci_chart.json"


def main() -> None:
    enriched = enrich_loci()
    for loc in enriched["loci"]:
        denial = loc.get("denial", {})
        loc["suppression_index"] = suppression_score(denial)
        loc["available_now"] = denial.get("in_build", 3) == 0

    OUT.write_text(json.dumps(enriched, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}")
    print(f"Verified present: {enriched['verified_count']}/{len(enriched['loci'])}")
    report = OUT.with_suffix(".txt")
    lines = []
    for loc in enriched["loci"]:
        if loc.get("ref"):
            v = loc.get("verified", {})
            mark = "OK" if v.get("present") else "MISS"
            lines.append(f"[{mark}] {loc['ref']} — {loc['id']}")
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {report}")


if __name__ == "__main__":
    main()
