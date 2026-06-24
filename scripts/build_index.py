#!/usr/bin/env python3
"""Build SQLite FTS index from data/bavli.json for fast Hebrew search."""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "data" / "bavli.json"
DEFAULT_DB = ROOT / "data" / "bavli.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS lines USING fts5(
  ref UNINDEXED,
  tractate UNINDEXED,
  daf UNINDEXED,
  layer UNINDEXED,
  line_no UNINDEXED,
  text,
  tokenize = 'unicode61'
);
"""


def build_index(source: Path, db_path: Path) -> dict[str, int]:
    if not source.exists():
        raise SystemExit(f"Missing {source}. Run: python scripts/build_bavli.py")

    data = json.loads(source.read_text(encoding="utf-8"))
    refs = data.get("refs", {})
    meta = data.get("meta", {})

    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.execute("DELETE FROM meta")
    conn.execute("INSERT INTO meta VALUES ('edition', ?)", (meta.get("edition", ""),))
    conn.execute("INSERT INTO meta VALUES ('source', ?)", (str(source.name),))
    conn.execute("INSERT INTO meta VALUES ('daf_count', ?)", (str(len(refs)),))

    rows: list[tuple[str, str, str, str, int, str]] = []
    for ref, entry in refs.items():
        tractate = entry.get("tractate", ref.rsplit(".", 1)[0])
        daf = entry.get("daf", ref.rsplit(".", 1)[-1])
        for layer in ("gemara", "rashi", "tosafot"):
            for i, line in enumerate(entry.get(layer, []) or [], start=1):
                if line and line.strip():
                    rows.append((ref, tractate, daf, layer, i, line.strip()))

    conn.executemany(
        "INSERT INTO lines(ref, tractate, daf, layer, line_no, text) VALUES (?,?,?,?,?,?)",
        rows,
    )
    conn.commit()
    conn.execute("INSERT INTO meta VALUES ('line_count', ?)", (str(len(rows)),))
    conn.commit()
    conn.close()

    return {"refs": len(refs), "lines": len(rows)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build search index for bavli.json")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    stats = build_index(args.source, args.output)
    size_mb = args.output.stat().st_size / (1024 * 1024)
    print(
        f"Wrote {args.output} — {stats['lines']:,} lines indexed "
        f"from {stats['refs']:,} dapim ({size_mb:.1f} MB)"
    )


if __name__ == "__main__":
    main()
