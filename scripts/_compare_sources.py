"""Compare Sefaria API gemara vs export for a daf."""
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

EXPORT = "https://storage.googleapis.com/sefaria-export/json"
API = "https://www.sefaria.org/api"


def quote_path(path: str) -> str:
    return "/".join(urllib.parse.quote(p, safe="") for p in path.split("/"))


def export_daf(tractate: str, idx: int) -> str:
    path = quote_path(f"Talmud/Bavli/Seder Nezikin/{tractate}/Hebrew/merged.json")
    data = json.load(urllib.request.urlopen(f"{EXPORT}/{path}", timeout=120))
    node = data["text"][idx]
    if isinstance(node, list):
        text = " ".join(str(x) for x in node if x)
    else:
        text = str(node)
    return re.sub(r"<[^>]+>", "", text)


def api_daf(tractate: str, daf: str) -> str:
    ref = urllib.parse.quote(f"{tractate}.{daf}", safe=".")
    data = json.load(urllib.request.urlopen(f"{API}/texts/{ref}?context=0", timeout=120))
    text = re.sub(r"<[^>]+>", "", " ".join(data.get("he") or []))
    return text


def daf_label(idx: int) -> str:
    num = 2 + idx // 2
    side = "a" if idx % 2 == 0 else "b"
    return f"{num}{side}"


if __name__ == "__main__":
    lines = []
    for idx in range(80, 86):
        label = daf_label(idx)
        api = api_daf("Sanhedrin", label)
        exp = export_daf("Sanhedrin", idx)
        markers = ["ישו", "יֵשׁוּ", "הנוצרי", "מתתי", "בערב הפסח"]
        out = {
            "index": idx,
            "label": label,
            "api_markers": {m: m in api for m in markers},
            "exp_markers": {m: m in exp for m in markers},
            "api_start": api[:250],
            "exp_start": exp[:250],
        }
        lines.append(json.dumps(out, ensure_ascii=False, indent=2))
    Path(__file__).resolve().parents[1].joinpath("data/reports/sanhedrin_source_compare.json").write_text(
        "\n\n".join(lines), encoding="utf-8"
    )
    print("wrote compare file")
