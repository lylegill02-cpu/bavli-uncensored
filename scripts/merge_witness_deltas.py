#!/usr/bin/env python3
"""Merge data/witness_deltas.json into data/loci.json by locus id."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCI = ROOT / "data" / "loci.json"
DELTAS = ROOT / "data" / "witness_deltas.json"


def main() -> None:
    loci_data = json.loads(LOCI.read_text(encoding="utf-8"))
    deltas = json.loads(DELTAS.read_text(encoding="utf-8"))
    n = 0
    for loc in loci_data.get("loci", []):
        d = deltas.get(loc["id"])
        if d:
            loc["witness_delta"] = d
            n += 1
    LOCI.write_text(json.dumps(loci_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Merged witness_delta into {n}/{len(loci_data['loci'])} loci")


if __name__ == "__main__":
    main()
