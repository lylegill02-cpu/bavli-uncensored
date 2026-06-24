"""Find alignment between export array index and Sefaria daf refs."""
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
    return re.sub(r"<[^>]+>", "", text)[:120]


def api_daf(daf: str) -> str:
    ref = urllib.parse.quote(f"Sanhedrin.{daf}", safe=".")
    data = json.load(urllib.request.urlopen(f"{API}/texts/{ref}?context=0", timeout=120))
    return snip(" ".join(data.get("he") or []))


def main() -> None:
    data = export_gemara_hebrew("Seder Nezikin", "Sanhedrin")
    lines = [f"export length: {len(data['text'])}\n"]
    for idx in range(min(10, len(data["text"]))):
        node = data["text"][idx]
        exp = snip(" ".join(str(x) for x in node) if isinstance(node, list) else str(node))
        for daf_num in range(2, 6):
            for side in ("a", "b"):
                daf = f"{daf_num}{side}"
                api = api_daf(daf)
                if exp[:80] == api[:80]:
                    lines.append(f"export[{idx}] == API Sanhedrin.{daf}\n")
    # brute force find API ref for export 82
    node = data["text"][82]
    exp = snip(" ".join(str(x) for x in node) if isinstance(node, list) else str(node))
    lines.append(f"\nexport[82] start: {exp}\n")
    for num in range(2, 50):
        for side in ("a", "b"):
            daf = f"{num}{side}"
            api = api_daf(daf)
            if exp[:80] == api[:80]:
                lines.append(f"export[82] matches Sanhedrin.{daf}\n")
    out = Path(__file__).resolve().parents[1] / "data/reports/align.txt"
    out.write_text("".join(lines), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
