#!/usr/bin/env python3
"""Publish bavli.db (+ optional bavli.json) as a GitHub Release asset."""
from __future__ import annotations

import argparse
import gzip
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bavli.db"
JSON = ROOT / "data" / "bavli.json"
DIST = ROOT / "dist"


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=ROOT)


def gzip_file(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(src, "rb") as f_in, gzip.open(dest, "wb", compresslevel=6) as f_out:
        shutil.copyfileobj(f_in, f_out)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create GitHub release with search index")
    parser.add_argument("tag", help='Release tag, e.g. "v1.0.0"')
    parser.add_argument(
        "--include-json",
        action="store_true",
        help="Also attach bavli.min.json.gz (large)",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not DB.exists():
        raise SystemExit("Missing data/bavli.db — run: python scripts/build_index.py")

    DIST.mkdir(exist_ok=True)
    db_gz = DIST / "bavli.db.gz"
    gzip_file(DB, db_gz)
    db_mb = db_gz.stat().st_size / (1024 * 1024)
    print(f"Compressed index: {db_gz} ({db_mb:.1f} MB)")

    assets = [db_gz]
    if args.include_json:
        mini = ROOT / "data" / "bavli.min.json"
        src = mini if mini.exists() else JSON
        json_gz = DIST / "bavli.min.json.gz"
        gzip_file(src, json_gz)
        assets.append(json_gz)
        print(f"Compressed corpus: {json_gz} ({json_gz.stat().st_size / 1024 / 1024:.1f} MB)")

    notes = (
        f"Prebuilt search index for Bavli Uncensored.\n\n"
        f"Download `bavli.db.gz`, then:\n"
        f"```bash\n"
        f"gunzip -k bavli.db.gz   # or: python -c \"import gzip,shutil; ...\"\n"
        f"mv bavli.db data/bavli.db\n"
        f"python scripts/serve.py\n"
        f"```\n"
    )

    if args.dry_run:
        print("Dry run — would create release", args.tag, "with", [a.name for a in assets])
        return

    run(
        [
            "gh",
            "release",
            "create",
            args.tag,
            "--title",
            f"Bavli Uncensored {args.tag}",
            "--notes",
            notes,
        ]
        + [str(a) for a in assets]
    )
    print(f"Release {args.tag} published.")


if __name__ == "__main__":
    main()
