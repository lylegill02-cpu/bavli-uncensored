"""Map Tamid export indices to Vilna daf labels."""
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from lib.sefaria import export_gemara_hebrew

API = "https://www.sefaria.org/api"


def snip(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)[:80]


def api_daf(daf: str) -> str:
    ref = urllib.parse.quote(f"Tamid.{daf}", safe=".")
    data = json.load(urllib.request.urlopen(f"{API}/texts/{ref}?context=0", timeout=120))
    return snip(" ".join(data.get("he") or []))


def export_snip(node) -> str:
    return snip(" ".join(str(x) for x in node) if isinstance(node, list) else str(node))


def main() -> None:
    data = export_gemara_hebrew("Seder Kodashim", "Tamid")
    lines = []
    for idx in range(48, 66):
        exp = export_snip(data["text"][idx])
        if not exp.strip():
            lines.append(f"export[{idx}]: EMPTY\n")
            continue
        for num in range(24, 34):
            for side in ("a", "b"):
                daf = f"{num}{side}"
                if exp[:50] == api_daf(daf)[:50]:
                    lines.append(f"export[{idx}] -> Tamid.{daf}\n")
                    break
    out = Path(__file__).resolve().parents[1] / "data/reports/tamid_map.txt"
    out.write_text("".join(lines), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
