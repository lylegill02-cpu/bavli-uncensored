#!/usr/bin/env python3
"""Search the Bavli full-text index."""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "bavli.db"


def snippet(text: str, query: str, width: int = 120) -> str:
    """Return a short context window around the first match."""
    if not query.strip():
        return text[:width]
    # Try literal match first (Hebrew phrases)
    pos = text.find(query)
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


def search(
    db_path: Path,
    query: str,
    *,
    tractate: str | None = None,
    layer: str | None = None,
    limit: int = 20,
    regex: bool = False,
) -> list[dict]:
    if not db_path.exists():
        raise SystemExit(
            f"Missing {db_path}. Run: python scripts/build_index.py"
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
                hits.append(dict(row))
                if len(hits) >= limit:
                    break
        conn.close()
        return hits

    # FTS5 phrase / token search
    fts_query = query.replace('"', '""')
    if " " in query.strip():
        fts_query = f'"{fts_query}"'
    sql = """
        SELECT ref, tractate, daf, layer, line_no, text
        FROM lines
        WHERE text MATCH ?
    """
    params: list[str] = [fts_query]
    if tractate:
        sql += " AND tractate = ?"
        params.append(tractate)
    if layer:
        sql += " AND layer = ?"
        params.append(layer)
    sql += " LIMIT ?"
    params.append(str(limit))

    try:
        rows = conn.execute(sql, params).fetchall()
    except sqlite3.OperationalError:
        # Fallback: substring scan when FTS tokenization misses Hebrew forms
        sql = "SELECT ref, tractate, daf, layer, line_no, text FROM lines WHERE text LIKE ?"
        params = [f"%{query}%"]
        if tractate:
            sql += " AND tractate = ?"
            params.append(tractate)
        if layer:
            sql += " AND layer = ?"
            params.append(layer)
        sql += " LIMIT ?"
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()

    conn.close()
    return [dict(r) for r in rows]


def main() -> None:
    parser = argparse.ArgumentParser(description="Search unified Bavli text")
    parser.add_argument("query", help="Hebrew search term or phrase")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--tractate", help='Limit to tractate, e.g. "Sanhedrin"')
    parser.add_argument(
        "--layer",
        choices=("gemara", "rashi", "tosafot"),
        help="Limit to one layer",
    )
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--regex", action="store_true", help="Treat query as regex")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    hits = search(
        args.db,
        args.query,
        tractate=args.tractate,
        layer=args.layer,
        limit=args.limit,
        regex=args.regex,
    )

    if args.json:
        sys.stdout.buffer.write(
            (json.dumps(hits, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        )
        return

    if not hits:
        print("No results.")
        sys.exit(1)

    for hit in hits:
        ctx = snippet(hit["text"], args.query)
        sys.stdout.buffer.write(
            (
                f"{hit['ref']} [{hit['layer']}:{hit['line_no']}]\n"
                f"  {ctx}\n\n"
            ).encode("utf-8")
        )

    print(f"{len(hits)} result(s)", file=sys.stderr)


if __name__ == "__main__":
    main()
