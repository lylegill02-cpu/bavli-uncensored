"""Verify export header offset (indices before 2a) across tractates."""
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from lib.sefaria import export_gemara_hebrew

API = "https://www.sefaria.org/api"
TRACTATES = json.loads(
    (Path(__file__).resolve().parents[1] / "data/tractates.json").read_text(encoding="utf-8")
)


def snip(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)[:100]


def api_start(tractate: str) -> str:
    ref = urllib.parse.quote(f"{tractate}.2a", safe=".")
    data = json.load(urllib.request.urlopen(f"{API}/texts/{ref}?context=0", timeout=120))
    return snip(" ".join(data.get("he") or []))


def find_offset(tractate: str, seder: str) -> int | None:
    data = export_gemara_hebrew(seder, tractate)
    target = api_start(tractate)
    for idx in range(min(6, len(data["text"]))):
        node = data["text"][idx]
        exp = snip(" ".join(str(x) for x in node) if isinstance(node, list) else str(node))
        if exp[:80] == target[:80]:
            return idx
    return None


def main() -> None:
    lines = []
    for tractate, seder in sorted(TRACTATES.items()):
        try:
            off = find_offset(tractate, seder)
            lines.append(f"{tractate}: offset={off}, export_len={len(export_gemara_hebrew(seder, tractate)['text'])}")
        except Exception as e:
            lines.append(f"{tractate}: ERROR {e}")
    out = Path(__file__).resolve().parents[1] / "data/reports/export_offsets.txt"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
