"""Shared search helpers for CLI and API."""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

from lib.hebrew import normalize_hebrew, query_variants

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "bavli.db"
DEFAULT_JSON = ROOT / "data" / "bavli.json"


def snippet(text: str, query: str, width: int = 160) -> str:
    needles = query_variants(query)
    pos = -1
    for needle in needles:
        pos = text.find(needle)
        if pos != -1:
            break
    if pos == -1:
        norm_text = normalize_hebrew(text)
        for needle in needles:
            pos = norm_text.find(normalize_hebrew(needle))
            if pos != -1:
                break
    if pos == -1:
        return text[:width]
    start = max(0, pos - width // 3)
    end = min(len(text), pos + len(query) + width // 2)
    out = text[start:end]
    if start > 0:
        out = "…" + out
    if end < len(text):
        out = out + "…"
    return out


def search_lines(
    query: str,
    *,
    db_path: Path = DEFAULT_DB,
    tractate: str | None = None,
    layer: str | None = None,
    limit: int = 20,
    regex: bool = False,
) -> list[dict]:
    if not db_path.exists():
        raise FileNotFoundError(
            f"Search index missing: {db_path}. Run: python scripts/build_index.py"
        )

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    if regex:
        sql = "SELECT ref, tractate, daf, layer, line_no, text FROM lines"
        clauses: list[str] = []
        params: list[str] = []
        if tractate:
            clauses.append("tractate = ?")
            params.append(tractate)
        if layer:
            clauses.append("layer = ?")
            params.append(layer)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        rows = conn.execute(sql, params).fetchall()
        pattern = re.compile(query)
        hits = []
        for row in rows:
            if pattern.search(row["text"]):
                hit = dict(row)
                hit["snippet"] = snippet(hit["text"], query)
                hits.append(hit)
                if len(hits) >= limit:
                    break
        conn.close()
        return hits

    norm_q = normalize_hebrew(query)
    sql = """
        SELECT ref, tractate, daf, layer, line_no, text
        FROM lines
        WHERE text_norm LIKE ?
    """
    params: list[str | int] = [f"%{norm_q}%"]
    if tractate:
        sql += " AND tractate = ?"
        params.append(tractate)
    if layer:
        sql += " AND layer = ?"
        params.append(layer)
    sql += " ORDER BY ref, line_no LIMIT ?"
    params.append(limit)

    rows = conn.execute(sql, params).fetchall()
    conn.close()
    hits = []
    for row in rows:
        hit = dict(row)
        hit["snippet"] = snippet(hit["text"], query)
        hits.append(hit)
    return hits


def get_daf(ref: str, *, source: Path = DEFAULT_JSON) -> dict | None:
    if not source.exists():
        raise FileNotFoundError(f"Corpus missing: {source}")
    data = json.loads(source.read_text(encoding="utf-8"))
    entry = data.get("refs", {}).get(ref)
    if not entry:
        return None
    return {
        "ref": ref,
        "seder": entry.get("seder"),
        "tractate": entry.get("tractate"),
        "daf": entry.get("daf"),
        "gemara": entry.get("gemara", []),
        "rashi": entry.get("rashi", []),
        "tosafot": entry.get("tosafot", []),
    }


def list_tractates(*, source: Path = DEFAULT_JSON) -> list[dict]:
    data = json.loads(source.read_text(encoding="utf-8"))
    return data.get("meta", {}).get("tractates", [])
