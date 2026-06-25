#!/usr/bin/env python3
"""Search the Bavli full-text index (local SQLite or Supabase)."""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.hebrew import normalize_hebrew, query_variants  # noqa: E402

DEFAULT_DB = ROOT / "data" / "bavli.db"


def snippet(text: str, query: str, width: int = 120) -> str:
    """Return a short context window around the first match."""
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


def search_local(
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
    return [dict(r) for r in rows]


def search_supabase(
    query: str,
    *,
    tractate: str | None = None,
    layer: str | None = None,
    limit: int = 20,
) -> list[dict]:
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise SystemExit(
            "Set SUPABASE_URL and SUPABASE_ANON_KEY (or SUPABASE_SERVICE_ROLE_KEY) "
            "for --supabase search."
        )

    rpc_url = f"{url}/rest/v1/rpc/bavli_search"
    norm_q = normalize_hebrew(query)
    body = json.dumps(
        {
            "q": norm_q,
            "p_tractate": tractate,
            "p_layer": layer,
            "p_limit": limit,
        }
    ).encode("utf-8")
    req = Request(
        rpc_url,
        data=body,
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Search unified Bavli text")
    parser.add_argument("query", help="Hebrew search term or phrase")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--supabase", action="store_true", help="Search g10be-overflow via RPC")
    parser.add_argument("--tractate", help='Limit to tractate, e.g. "Sanhedrin"')
    parser.add_argument(
        "--layer",
        choices=("gemara", "rashi", "tosafot"),
        help="Limit to one layer",
    )
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--regex", action="store_true", help="Treat query as regex (local only)")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    if args.supabase:
        hits = search_supabase(
            args.query,
            tractate=args.tractate,
            layer=args.layer,
            limit=args.limit,
        )
    else:
        hits = search_local(
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
