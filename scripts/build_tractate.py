#!/usr/bin/env python3
"""Build uncensored Bavli JSON for one tractate."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.daf import iter_export_dapim, load_alignment
from lib.patches import apply_substitutions, load_all_substitution_rules, strip_html
from lib.sefaria import (
    export_gemara_hebrew,
    export_rashi_hebrew,
    export_tosafot_hebrew,
    flatten_daf_lines,
)

TRACTATES_PATH = ROOT / "data" / "tractates.json"


def load_tractate_catalog() -> dict[str, str]:
    return json.loads(TRACTATES_PATH.read_text(encoding="utf-8"))


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
    catalog = load_tractate_catalog()
    if name not in catalog:
        raise SystemExit(f"Unknown tractate {name!r}. Known: {', '.join(sorted(catalog))}")
    seder = catalog[name]

    gemara = export_gemara_hebrew(seder, name)
    rashi = export_rashi_hebrew(seder, name)
    tosafot = export_tosafot_hebrew(seder, name)
    rules = load_all_substitution_rules(name)

    gemara_text = gemara.get("text", [])
    rashi_text = rashi.get("text", [])
    tosafot_text = tosafot.get("text", [])

    alignment = load_alignment(name, gemara_text)
    header_offset = alignment["header_offset"]
    start_daf_num = alignment["start_daf_num"]

    dapim: dict = {}
    total_patches = 0

    for label, i in iter_export_dapim(
        gemara_text,
        header_offset=header_offset,
        start_daf_num=start_daf_num,
    ):
        if max_daf is not None and len(dapim) >= max_daf:
            break

        g_lines = flatten_daf_lines(gemara_text[i])
        r_lines = flatten_daf_lines(rashi_text[i] if i < len(rashi_text) else [])
        t_lines = flatten_daf_lines(tosafot_text[i] if i < len(tosafot_text) else [])

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
            "Gemara follows Sefaria export (merged Vilna; often already uncensored in the main column). "
            "Rashi/Tosafot patched where עובדי כוכבים replaced גוים/נכרים per Munich/Bomberg witnesses."
        ),
        "base_sources": {
            "gemara": "sefaria-export merged (Vilna)",
            "rashi": "sefaria-export Vilna Edition (Wikisource)",
            "tosafot": "sefaria-export Vilna Edition (Wikisource)",
        },
        "export_alignment": {
            "header_offset": header_offset,
            "start_daf_num": start_daf_num,
            "notes": (
                "Sefaria merged.json arrays include two leading slots before 2a for most tractates; "
                "Tamid uses a long empty prefix before 25a."
            ),
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
