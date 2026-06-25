#!/usr/bin/env python3
"""Remove Bavli corpus from Supabase (free storage after GitHub-only hosting)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

DEFAULT_PROJECT_REF = "galhchvctvmtbykzzqqp"

DROP_SQL = """
DROP FUNCTION IF EXISTS public.bavli_search(text, text, text, integer);
DROP FUNCTION IF EXISTS public.bavli_get_daf(text);
DROP TABLE IF EXISTS public.bavli_lines CASCADE;
DROP TABLE IF EXISTS public.bavli_dapim CASCADE;
DROP TABLE IF EXISTS public.bavli_meta CASCADE;
"""


def get_connection():
    try:
        import psycopg
    except ImportError:
        raise SystemExit(
            "Install psycopg: pip install 'psycopg[binary]'\n"
            "Then set SUPABASE_DB_URL from Supabase → Settings → Database → URI"
        )

    db_url = os.environ.get("SUPABASE_DB_URL") or os.environ.get("DATABASE_URL")
    if not db_url:
        raise SystemExit(
            f"Set SUPABASE_DB_URL (postgres URI for project {DEFAULT_PROJECT_REF})."
        )
    return psycopg.connect(db_url)


def clear(*, dry_run: bool = False) -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if dry_run:
                print("Would run:")
                print(DROP_SQL.strip())
                return
            cur.execute(DROP_SQL)
        conn.commit()
    finally:
        conn.close()


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description=f"Drop Bavli tables/RPCs from Supabase ({DEFAULT_PROJECT_REF})"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print SQL only",
    )
    args = parser.parse_args()

    if not args.dry_run:
        print(
            f"Removing bavli_* tables and RPCs from Supabase ({DEFAULT_PROJECT_REF})…",
            file=sys.stderr,
        )
    clear(dry_run=args.dry_run)
    if not args.dry_run:
        print("Done — Bavli corpus cleared from Supabase.")


if __name__ == "__main__":
    main()
