#!/usr/bin/env python3
"""Load bavli.json into Supabase (g10be-overflow / forge-aop project)."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.hebrew import normalize_hebrew  # noqa: E402

DEFAULT_SOURCE = ROOT / "data" / "bavli.json"
BATCH = 500

# Second Supabase project: g10be-overflow
DEFAULT_PROJECT_REF = "galhchvctvmtbykzzqqp"


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
            f"Set SUPABASE_DB_URL (postgres URI for project {DEFAULT_PROJECT_REF}).\n"
            "Supabase dashboard → Settings → Database → Connection string → URI"
        )
    return psycopg.connect(db_url)


def load(source: Path, *, truncate: bool = True) -> dict[str, int]:
    data = json.loads(source.read_text(encoding="utf-8"))
    refs = data.get("refs", {})
    meta = data.get("meta", {})

    daf_rows = []
    line_rows = []
    for ref, entry in refs.items():
        daf_rows.append(
            (
                ref,
                entry.get("tractate", ref.rsplit(".", 1)[0]),
                entry.get("daf", ref.rsplit(".", 1)[-1]),
                entry.get("seder", ""),
                json.dumps(entry.get("gemara") or [], ensure_ascii=False),
                json.dumps(entry.get("rashi") or [], ensure_ascii=False),
                json.dumps(entry.get("tosafot") or [], ensure_ascii=False),
            )
        )
        tractate = entry.get("tractate", ref.rsplit(".", 1)[0])
        daf = entry.get("daf", ref.rsplit(".", 1)[-1])
        for layer in ("gemara", "rashi", "tosafot"):
            for i, line in enumerate(entry.get(layer, []) or [], start=1):
                if line and line.strip():
                    text = line.strip()
                    line_rows.append(
                        (ref, tractate, daf, layer, i, text, normalize_hebrew(text))
                    )

    conn = get_connection()
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            if truncate:
                cur.execute("TRUNCATE public.bavli_lines, public.bavli_dapim, public.bavli_meta CASCADE")

            cur.executemany(
                """INSERT INTO public.bavli_dapim
                   (ref, tractate, daf, seder, gemara, rashi, tosafot)
                   VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb)
                   ON CONFLICT (ref) DO UPDATE SET
                     gemara = EXCLUDED.gemara,
                     rashi = EXCLUDED.rashi,
                     tosafot = EXCLUDED.tosafot""",
                daf_rows,
            )

            for i in range(0, len(line_rows), BATCH):
                batch = line_rows[i : i + BATCH]
                cur.executemany(
                    """INSERT INTO public.bavli_lines
                       (ref, tractate, daf, layer, line_no, text, text_norm)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    batch,
                )
                print(f"  lines {i + len(batch):,}/{len(line_rows):,}", file=sys.stderr)

            cur.execute("DELETE FROM public.bavli_meta")
            cur.executemany(
                "INSERT INTO public.bavli_meta (key, value) VALUES (%s, %s)",
                [
                    ("edition", meta.get("edition", "")),
                    ("daf_count", str(len(daf_rows))),
                    ("line_count", str(len(line_rows))),
                    ("source", source.name),
                ],
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return {"dapim": len(daf_rows), "lines": len(line_rows)}


def main() -> None:
    parser = argparse.ArgumentParser(
        description=f"Load Bavli into Supabase ({DEFAULT_PROJECT_REF})"
    )
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument(
        "--no-truncate",
        action="store_true",
        help="Append instead of replacing existing rows",
    )
    args = parser.parse_args()

    if not args.source.exists():
        raise SystemExit(f"Missing {args.source}. Run: python scripts/build_bavli.py")

    print(f"Loading {args.source} → Supabase ({DEFAULT_PROJECT_REF})…", file=sys.stderr)
    stats = load(args.source, truncate=not args.no_truncate)
    print(f"Done — {stats['dapim']:,} dapim, {stats['lines']:,} searchable lines")


if __name__ == "__main__":
    main()
