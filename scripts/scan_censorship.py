"""Scan Sefaria Bavli for known censorship indicators."""
from __future__ import annotations

import json
import re
import unicodedata
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "reports" / "censorship_scan.json"

KNOWN_GAPS = [
    ("Sanhedrin.67a", ["ישו", "בן פנדרא", "סטada", "סטada"]),
    ("Gittin.57a", ["ישו", "בן פנדרא", "הונסר", "בGehinnom"]),
    ("Shabbat.104b", ["סטada", "פנדרא", "בן פנדרא", "מiriam"]),
    ("Sanhedrin.107b", ["ישו", "הנוצרי", "פרחיה"]),
    ("Sotah.47a", ["ישו", "הנוצרי", "פרחיה"]),
]

TRACTATES_OVDei_CHECK = [
    "Avodah_Zarah",
]


def strip_marks(text: str) -> str:
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def fetch_he(ref: str) -> str:
    url = f"https://www.sefaria.org/api/texts/{ref.replace('_', ' ').replace(' ', '%20')}?context=0"
    with urllib.request.urlopen(url, timeout=60) as resp:
        data = json.load(resp)
    lines = data.get("he") or []
    return strip_marks(re.sub(r"<[^>]+>", " ", " ".join(lines)))


def count_terms(text: str, terms: list[str]) -> dict[str, int]:
    return {term: text.count(strip_marks(term)) for term in terms}


def scan_tractate_ovdei(tractate: str, max_daf: int = 80) -> dict:
    """Rough scan: count עובדי כוכבים vs גoyim across dapim."""
    ovdei = goyim = 0
    hits = []
    for n in range(2, max_daf + 1):
        for side in ("a", "b"):
            ref = f"{tractate}.{n}{side}"
            try:
                text = fetch_he(ref)
            except Exception:
                continue
            o = text.count("עובדי כוכבים") + text.count("עובד כוכבים")
            g = text.count("גוים") + text.count("גוי")
            if o or g:
                hits.append({"ref": ref, "ovdei": o, "goyim": g})
            ovdei += o
            goyim += g
    return {"tractate": tractate, "ovdei_total": ovdei, "goyim_total": goyim, "daf_hits": hits}


def main() -> None:
    report = {"known_gaps": {}, "tractates": {}}
    for ref, terms in KNOWN_GAPS:
        text = fetch_he(ref)
        report["known_gaps"][ref] = {
            "terms": count_terms(text, terms),
            "sample": text[:400],
        }
    for tractate in TRACTATES_OVDei_CHECK:
        report["tractates"][tractate] = scan_tractate_ovdei(tractate, max_daf=30)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
