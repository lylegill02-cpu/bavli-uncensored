"""Load and verify curated loci against built corpus."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCI_PATH = ROOT / "data" / "loci.json"
BAVLI_PATH = ROOT / "data" / "bavli.json"


def load_loci(path: Path = LOCI_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_locus(locus: dict, refs: dict) -> dict:
    """Attach runtime verification fields."""
    out = dict(locus)
    ref = locus.get("ref")
    needle = locus.get("needle")
    layer = locus.get("layer", "gemara")

    if not ref or not needle:
        out["verified"] = {"skipped": True, "reason": "pattern or aggregate row"}
        return out

    entry = refs.get(ref)
    if not entry:
        out["verified"] = {"present": False, "reason": "ref missing from bavli.json"}
        return out

    if layer == "gemara":
        text = " ".join(entry.get("gemara", []))
    elif layer == "rashi":
        text = " ".join(entry.get("rashi", []))
    elif layer == "tosafot":
        text = " ".join(entry.get("tosafot", []))
    else:
        text = " ".join(
            entry.get("gemara", [])
            + entry.get("rashi", [])
            + entry.get("tosafot", [])
        )

    present = needle in text
    out["verified"] = {
        "present": present,
        "ref": ref,
        "layer": layer,
        "snippet": text[:240] if text else "",
    }
    if present:
        out["denial"] = dict(locus.get("denial", {}))
        out["denial"]["in_build"] = 0
    else:
        out["denial"] = dict(locus.get("denial", {}))
        out["denial"]["in_build"] = 3

    return out


def enrich_loci(
    loci_data: dict | None = None,
    bavli_path: Path = BAVLI_PATH,
) -> dict:
    data = loci_data or load_loci()
    refs = {}
    if bavli_path.exists():
        refs = json.loads(bavli_path.read_text(encoding="utf-8")).get("refs", {})

    enriched = []
    for locus in data.get("loci", []):
        enriched.append(verify_locus(locus, refs))

    return {
        **{k: v for k, v in data.items() if k != "loci"},
        "loci": enriched,
        "verified_count": sum(
            1 for x in enriched if x.get("verified", {}).get("present")
        ),
    }


def suppression_score(denial: dict) -> int:
    """Higher = more suppressed historically; in_build weighted separately."""
    keys = ("print_historical", "commentary_residue", "modern_digital")
    vals = [denial.get(k, 0) for k in keys]
    return max(vals) if vals else 0
