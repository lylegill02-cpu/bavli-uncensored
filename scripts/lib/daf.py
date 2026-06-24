"""Map Sefaria export array indices to Vilna daf labels."""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ALIGN_DIR = ROOT / "data" / "alignments"
API = "https://www.sefaria.org/api"

# Tamid begins at Vilna 25a with long empty prefix in the export array.
TRACTATE_OVERRIDES: dict[str, dict[str, int]] = {
    "Tamid": {"header_offset": 48, "start_daf_num": 25},
}


def parse_daf(daf: str) -> tuple[int, str]:
    m = re.fullmatch(r"(\d+)([ab])", daf)
    if not m:
        raise ValueError(f"Invalid daf label: {daf!r}")
    return int(m.group(1)), m.group(2)


def format_daf(num: int, side: str) -> str:
    return f"{num}{side}"


def export_index_to_daf(
    index: int,
    *,
    header_offset: int = 2,
    start_daf_num: int = 2,
) -> str | None:
    """Convert merged-export array index to Vilna daf (e.g. 43a)."""
    rel = index - header_offset
    if rel < 0:
        return None
    num = start_daf_num + rel // 2
    side = "a" if rel % 2 == 0 else "b"
    return format_daf(num, side)


def daf_to_export_index(
    daf: str,
    *,
    header_offset: int = 2,
    start_daf_num: int = 2,
) -> int:
    num, side = parse_daf(daf)
    rel = (num - start_daf_num) * 2 + (0 if side == "a" else 1)
    return header_offset + rel


def _snip(text: str, n: int = 80) -> str:
    return re.sub(r"<[^>]+>", "", text)[:n]


def _api_snip(tractate: str, daf: str) -> str:
    ref = urllib.parse.quote(f"{tractate}.{daf}", safe=".")
    with urllib.request.urlopen(f"{API}/texts/{ref}?context=0", timeout=120) as resp:
        data = json.load(resp)
    return _snip(" ".join(data.get("he") or []))


def _export_snip(node: Any) -> str:
    if isinstance(node, list):
        text = " ".join(str(x) for x in node)
    else:
        text = str(node)
    return _snip(text)


def detect_alignment(tractate: str, export_text: list[Any]) -> dict[str, int]:
    """Detect export header offset by matching API Sanhedrin-style 2a, or Tamid 25b."""
    if tractate in TRACTATE_OVERRIDES:
        return dict(TRACTATE_OVERRIDES[tractate])

    target = _api_snip(tractate, "2a")
    if target.strip():
        for idx in range(min(6, len(export_text))):
            if _export_snip(export_text[idx])[:80] == target[:80]:
                return {"header_offset": idx, "start_daf_num": 2}

    # Tamid-like: first substantive slot matched against low Vilna range.
    for idx, node in enumerate(export_text[:60]):
        exp = _export_snip(node)
        if not exp.strip():
            continue
        for num in range(2, 40):
            for side in ("a", "b"):
                daf = format_daf(num, side)
                if exp[:60] == _api_snip(tractate, daf)[:60]:
                    return {"header_offset": idx, "start_daf_num": num}

    return {"header_offset": 2, "start_daf_num": 2}


def load_alignment(tractate: str, export_text: list[Any]) -> dict[str, int]:
    ALIGN_DIR.mkdir(parents=True, exist_ok=True)
    path = ALIGN_DIR / f"{tractate.replace(' ', '_')}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    alignment = detect_alignment(tractate, export_text)
    path.write_text(json.dumps(alignment, indent=2), encoding="utf-8")
    return alignment


def iter_export_dapim(
    export_text: list[Any],
    *,
    header_offset: int,
    start_daf_num: int,
) -> list[tuple[str, int]]:
    """Return ordered (daf_label, export_index) pairs."""
    pairs: list[tuple[str, int]] = []
    for i in range(header_offset, len(export_text)):
        label = export_index_to_daf(
            i, header_offset=header_offset, start_daf_num=start_daf_num
        )
        if label:
            pairs.append((label, i))
    return pairs
