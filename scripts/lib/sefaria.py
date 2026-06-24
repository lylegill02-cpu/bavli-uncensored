"""Fetch Bavli layers from Sefaria API."""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


API = "https://www.sefaria.org/api"
EXPORT = "https://storage.googleapis.com/sefaria-export/json"
CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "cache" / "gemara"


def _get_json(url: str) -> Any:
    with urllib.request.urlopen(url, timeout=120) as resp:
        return json.load(resp)


def api_text(ref: str) -> dict:
    encoded = urllib.parse.quote(ref.replace("_", " "), safe=".")
    return _get_json(f"{API}/texts/{encoded}?context=0")


def api_v3_hebrew(book: str, daf: str) -> list[str] | None:
    encoded = urllib.parse.quote(book, safe="")
    data = _get_json(f"{API}/v3/texts/{encoded}.{daf}?version=hebrew")
    for version in data.get("versions", []):
        if version.get("actualLanguage") == "he" and version.get("text"):
            return version["text"]
    return None


def _quote_path(path: str) -> str:
    return "/".join(urllib.parse.quote(part, safe="") for part in path.split("/"))


def export_gemara_hebrew(seder: str, tractate: str) -> dict:
    path = _quote_path(f"Talmud/Bavli/{seder}/{tractate}/Hebrew/merged.json")
    return _get_json(f"{EXPORT}/{path}")


def export_rashi_hebrew(seder: str, tractate: str) -> dict:
    path = _quote_path(
        f"Talmud/Bavli/Rishonim on Talmud/Rashi/{seder}/Rashi on {tractate}/Hebrew/Vilna Edition.json"
    )
    try:
        return _get_json(f"{EXPORT}/{path}")
    except Exception:
        return {"text": []}


def export_tosafot_hebrew(seder: str, tractate: str) -> dict:
    path = _quote_path(
        f"Talmud/Bavli/Rishonim on Talmud/Tosafot/{seder}/Tosafot on {tractate}/Hebrew/Vilna Edition.json"
    )
    try:
        return _get_json(f"{EXPORT}/{path}")
    except Exception:
        return {"text": []}


def flatten_daf_lines(daf_node: Any) -> list[str]:
    """Normalize nested Sefaria structures to a list of line strings."""
    if daf_node is None:
        return []
    if isinstance(daf_node, str):
        return [daf_node] if daf_node.strip() else []
    if isinstance(daf_node, list):
        lines: list[str] = []
        for item in daf_node:
            if isinstance(item, str):
                if item.strip():
                    lines.append(item)
            elif isinstance(item, list):
                chunk = " ".join(x for x in item if isinstance(x, str) and x.strip())
                if chunk.strip():
                    lines.append(chunk)
            elif item:
                lines.append(str(item))
        return lines
    return [str(daf_node)]


def _cache_path(tractate: str, daf: str) -> Path:
    safe = tractate.replace(" ", "_")
    return CACHE_DIR / safe / f"{daf}.json"


def api_gemara_lines(tractate: str, daf: str) -> list[str]:
    data = api_text(f"{tractate}.{daf}")
    return flatten_daf_lines(data.get("he"))


def gemara_lines_for_daf(
    tractate: str, daf: str, export_fallback: list[str]
) -> list[str]:
    """Prefer live Sefaria API gemara (cached); fall back to export if API empty."""
    path = _cache_path(tractate, daf)
    if path.exists():
        cached = json.loads(path.read_text(encoding="utf-8"))
        if cached.get("lines"):
            return cached["lines"]

    try:
        lines = api_gemara_lines(tractate, daf)
        if lines:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps({"lines": lines}, ensure_ascii=False), encoding="utf-8"
            )
            return lines
    except Exception:
        pass
    return export_fallback
