"""Fetch Bavli layers from Sefaria API."""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any


API = "https://www.sefaria.org/api"
EXPORT = "https://storage.googleapis.com/sefaria-export/json"


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
