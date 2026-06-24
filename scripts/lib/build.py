"""Core Bavli build logic — one tractate in memory."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from lib.daf import iter_export_dapim, load_alignment
from lib.patches import apply_substitutions, load_all_substitution_rules, strip_html
from lib.sefaria import (
    export_gemara_hebrew,
    export_rashi_hebrew,
    export_tosafot_hebrew,
    flatten_daf_lines,
    gemara_lines_for_daf,
)

ROOT = Path(__file__).resolve().parents[2]
TRACTATES_PATH = ROOT / "data" / "tractates.json"
ORDER_PATH = ROOT / "data" / "bavli_order.json"


def load_tractate_catalog() -> dict[str, str]:
    return json.loads(TRACTATES_PATH.read_text(encoding="utf-8"))


def load_bavli_order() -> list[str]:
    order = json.loads(ORDER_PATH.read_text(encoding="utf-8"))
    catalog = load_tractate_catalog()
    missing = [t for t in catalog if t not in order]
    if missing:
        order = order + sorted(missing)
    return order


def process_layer(lines: list[str], rules, layer: str) -> tuple[list[str], list[str]]:
    out_lines: list[str] = []
    meta: list[str] = []
    for line in lines:
        cleaned = strip_html(line)
        patched, applied = apply_substitutions(cleaned, rules)
        out_lines.append(patched)
        if applied:
            meta.extend([f"{layer}:{a}" for a in applied])
    return out_lines, meta


def build_tractate(
    name: str,
    *,
    max_daf: int | None = None,
    use_api_gemara: bool = False,
) -> dict:
    catalog = load_tractate_catalog()
    if name not in catalog:
        raise ValueError(f"Unknown tractate {name!r}")
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

        export_g = flatten_daf_lines(gemara_text[i])
        if use_api_gemara:
            g_lines = gemara_lines_for_daf(name, label, export_g)
        else:
            g_lines = export_g

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
        "tractate": name,
        "seder": seder,
        "export_alignment": {
            "header_offset": header_offset,
            "start_daf_num": start_daf_num,
        },
        "daf_count": len(dapim),
        "total_patch_events": total_patches,
        "dapim": dapim,
    }


def tractate_to_refs(tractate_data: dict) -> dict[str, dict]:
    """Flatten tractate dapim into ref-keyed entries (Sanhedrin.43a)."""
    name = tractate_data["tractate"]
    seder = tractate_data["seder"]
    refs: dict[str, dict] = {}
    for daf, layers in tractate_data["dapim"].items():
        ref = f"{name}.{daf}"
        refs[ref] = {
            "seder": seder,
            "tractate": name,
            "daf": daf,
            "gemara": layers["gemara"],
            "rashi": layers["rashi"],
            "tosafot": layers["tosafot"],
        }
    return refs


def build_bavli(
    *,
    max_daf: int | None = None,
    use_api_gemara: bool = False,
    tractates: list[str] | None = None,
) -> dict:
    order = tractates or load_bavli_order()
    refs: dict[str, dict] = {}
    index: list[str] = []
    tractate_meta: list[dict] = []
    total_patches = 0

    for name in order:
        tractate_data = build_tractate(
            name, max_daf=max_daf, use_api_gemara=use_api_gemara
        )
        tractate_refs = tractate_to_refs(tractate_data)
        for daf in tractate_data["dapim"]:
            index.append(f"{name}.{daf}")
        refs.update(tractate_refs)
        total_patches += tractate_data["total_patch_events"]
        tractate_meta.append(
            {
                "tractate": name,
                "seder": tractate_data["seder"],
                "daf_count": tractate_data["daf_count"],
                "patch_events": tractate_data["total_patch_events"],
            }
        )

    return {
        "meta": {
            "edition": "bavli-uncensored-v2",
            "title": "Babylonian Talmud — uncensored Vilna edition",
            "language": "he",
            "built_at": datetime.now(timezone.utc).isoformat(),
            "daf_count": len(index),
            "tractate_count": len(tractate_meta),
            "total_patch_events": total_patches,
            "description": (
                "Single-file Bavli: gemara, Rashi, and Tosafot per Vilna daf ref. "
                "Censorship euphemisms restored to pre-print readings (גוים/גוי) "
                "using Munich 95 and Bomberg witnesses. Gemara follows Sefaria "
                "(export-aligned; use --api-gemara to refresh from live API)."
            ),
            "sources": {
                "gemara": "sefaria-export merged (Vilna) or Sefaria API when --api-gemara",
                "rashi": "sefaria-export Vilna Edition",
                "tosafot": "sefaria-export Vilna Edition",
            },
            "tractates": tractate_meta,
        },
        "index": index,
        "refs": refs,
    }
