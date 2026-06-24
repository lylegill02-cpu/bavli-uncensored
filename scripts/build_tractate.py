#!/usr/bin/env python3
"""Build uncensored Bavli JSON for one tractate."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.patches import apply_substitutions, load_all_substitution_rules, strip_html
from lib.sefaria import (
    export_gemara_hebrew,
    export_rashi_hebrew,
    export_tosafot_hebrew,
    flatten_daf_lines,
)

TRACTATE_META = {
    "Avodah Zarah": {"seder": "Seder Nezikin", "daf_count": 76},
    "Sanhedrin": {"seder": "Seder Nezikin", "daf_count": 226},
    "Gittin": {"seder": "Seder Nashim", "daf_count": 180},
    "Shabbat": {"seder": "Seder Moed", "daf_count": 314},
}


def daf_label(index: int) -> str:
    """Export arrays are 0-based; daf 2a is typically index 0 in Bavli exports."""
    n = index + 2
    # Each index is one amud in merged export (2a, 2b, 3a, ...)
    side = "a" if index % 2 == 0 else "b"
    num = n if side == "a" else n - 1
    if side == "b" and index % 2 == 1:
        num = (index // 2) + 2
    # Simpler: Sefaria export index i -> daf (2 + i//2)(a/b)
    num = 2 + index // 2
    side = "a" if index % 2 == 0 else "b"
    return f"{num}{side}"


def process_layer(lines: list[str], rules, layer: str) -> tuple[list[str], list[str]]:
    out_lines = []
    meta: list[str] = []
    for line in lines:
        cleaned = strip_html(line)
        patched, applied = apply_substitutions(cleaned, rules)
        out_lines.append(patched)
        if applied:
            meta.extend([f"{layer}:{a}" for a in applied])
    return out_lines, meta


def build_tractate(name: str, max_daf: int | None = None) -> dict:
    if name not in TRACTATE_META:
        raise SystemExit(f"Unknown tractate {name!r}. Known: {', '.join(TRACTATE_META)}")
    meta = TRACTATE_META[name]
    seder = meta["seder"]
    limit = max_daf or meta["daf_count"]

    gemara = export_gemara_hebrew(seder, name)
    rashi = export_rashi_hebrew(seder, name)
    tosafot = export_tosafot_hebrew(seder, name)
    rules = load_all_substitution_rules(name)

    dapim: dict = {}
    total_patches = 0

    for i in range(min(limit, len(gemara.get("text", [])))):
        label = daf_label(i)
        g_lines = flatten_daf_lines(gemara["text"][i])
        r_lines = flatten_daf_lines(rashi.get("text", [])[i] if i < len(rashi.get("text", [])) else [])
        t_lines = flatten_daf_lines(tosafot.get("text", [])[i] if i < len(tosafot.get("text", [])) else [])

        g_out, g_meta = process_layer(g_lines, rules, "gemara")
        r_out, r_meta = process_layer(r_lines, rules, "rashi")
        t_out, t_meta = process_layer(t_lines, rules, "tosafot")
        patch_meta = g_meta + r_meta + t_meta
        total_patches += len(patch_meta)

        dapim[label] = {
            "gemara": g_out,
            "rashi": r_out,
            "tosafot": t_out,
            "patches_applied": patch_meta,
        }

    return {
        "edition": "bavli-uncensored-v1",
        "tractate": name,
        "seder": seder,
        "description": (
            "Vilna-shaped Bavli with censorship restorations applied to commentary layers. "
            "Gemara generally follows Sefaria (often already uncensored); Rashi/Tosafot patched "
            "where עובדי כוכבים replaced גוים/נכרים per Munich/Bomberg witnesses."
        ),
        "base_sources": {
            "gemara": "sefaria-export merged (Vilna)",
            "rashi": "sefaria-export Vilna Edition (Wikisource)",
            "tosafot": "sefaria-export Vilna Edition (Wikisource)",
        },
        "patch_rules": [r.id for r in rules],
        "daf_count": len(dapim),
        "total_patch_events": total_patches,
        "dapim": dapim,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build uncensored Bavli JSON")
    parser.add_argument("tractate", help='Tractate name, e.g. "Avodah Zarah"')
    parser.add_argument("--max-daf", type=int, default=None, help="Limit dapim (for testing)")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output JSON path (default: data/output/<tractate>.json)",
    )
    args = parser.parse_args()

    result = build_tractate(args.tractate, max_daf=args.max_daf)
    out = args.output or ROOT / "data" / "output" / f"{args.tractate.replace(' ', '_')}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"Wrote {out} — {result['daf_count']} dapim, "
        f"{result['total_patch_events']} patch events"
    )


if __name__ == "__main__":
    main()
