#!/usr/bin/env python3
"""Search the Bavli full-text index (local SQLite or Supabase)."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.hebrew import normalize_hebrew  # noqa: E402
from lib.search_api import DEFAULT_DB, search_lines  # noqa: E402


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
            "Set SUPABASE_URL and SUPABASE_ANON_KEY for --supabase search."
        )

    norm_q = normalize_hebrew(query)
    rpc_url = f"{url}/rest/v1/rpc/bavli_search"
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
    parser.add_argument("--supabase", action="store_true")
    parser.add_argument("--tractate", help='Limit to tractate, e.g. "Sanhedrin"')
    parser.add_argument(
        "--layer",
        choices=("gemara", "rashi", "tosafot"),
    )
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--regex", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.supabase:
        hits = search_supabase(
            args.query,
            tractate=args.tractate,
            layer=args.layer,
            limit=args.limit,
        )
    else:
        hits = search_lines(
            args.query,
            db_path=args.db,
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
        ctx = hit.get("snippet") or hit["text"]
        sys.stdout.buffer.write(
            (
                f"{hit['ref']} [{hit['layer']}:{hit['line_no']}]\n"
                f"  {ctx}\n\n"
            ).encode("utf-8")
        )

    print(f"{len(hits)} result(s)", file=sys.stderr)


if __name__ == "__main__":
    main()
