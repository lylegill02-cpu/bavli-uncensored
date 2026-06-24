#!/usr/bin/env python3
"""Build all tractates defined in build_tractate.TRACTATE_META."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "scripts" / "build_tractate.py"

# Import meta without package install
sys.path.insert(0, str(ROOT / "scripts"))
from build_tractate import TRACTATE_META  # noqa: E402


def main() -> None:
    for name in TRACTATE_META:
        print(f"=== {name} ===")
        subprocess.run(
            [sys.executable, str(BUILD), name],
            check=True,
            cwd=ROOT,
        )


if __name__ == "__main__":
    main()
