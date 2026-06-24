"""Quick scan helper."""
from __future__ import annotations

import json
import re
import unicodedata
import urllib.request


def strip_marks(text: str) -> str:
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def fetch_lines(ref: str, text_type: str = "he") -> list[str]:
    url = f"https://www.sefaria.org/api/texts/{ref.replace('_', ' ').replace(' ', '%20')}?context=0"
    with urllib.request.urlopen(url, timeout=60) as resp:
        data = json.load(resp)
    key = "he" if text_type == "he" else "text"
    return data.get(key) or []


def count_in_ref(ref: str, terms: list[str], text_type: str = "he") -> dict[str, int]:
    text = strip_marks(re.sub(r"<[^>]+>", " ", " ".join(fetch_lines(ref, text_type))))
    return {t: text.count(strip_marks(t)) for t in terms}


if __name__ == "__main__":
    terms = ["עובדי כוכבים", "עובד כוכבים", "גוים", "גוי", "נכרים", "נכרי"]
    results = {}
    for n in range(2, 40):
        for side in ("a", "b"):
            ref = f"Avodah_Zarah.{n}{side}"
            c = count_in_ref(ref, terms)
            if any(c.values()):
                results[ref] = c
            ref_r = f"Rashi_on_Avodah_Zarah.{n}{side}"
            try:
                cr = count_in_ref(ref_r, terms, text_type="text")
                if any(cr.values()):
                    results[ref_r] = cr
            except Exception:
                pass
    from pathlib import Path

    out = Path(__file__).resolve().parents[1] / "data" / "reports" / "az_scan.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out} ({len(results)} refs)")
