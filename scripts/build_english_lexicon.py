#!/usr/bin/env python3
"""Build data/english_lexicon.json from glossary + term packs."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GLOSSARY = ROOT / "data" / "english_glossary.json"
OUT = ROOT / "data" / "english_lexicon.json"

# Additional terms — add here instead of one-by-one in JS
TERM_PACK = {
    "michael": {
        "hebrew": ["מיכאל"],
        "aliases": ["archangel michael", "arch angel michael", "micheal"],
    },
    "gabriel": {"hebrew": ["גבריאל"], "aliases": ["archangel gabriel"]},
    "raphael": {"hebrew": ["רפאל"], "aliases": ["archangel raphael"]},
    "uriel": {"hebrew": ["אוריאל"], "aliases": []},
    "angel": {"hebrew": ["מלאך", "מלאכים"], "aliases": ["angels", "archangel"]},
    "melchizedek": {
        "hebrew": ["מלכי צדק"],
        "aliases": ["melchizadek", "melchisedec", "malchi tzedek"],
    },
    "abraham": {"hebrew": ["אברהם"], "aliases": ["avraham"]},
    "moses": {"hebrew": ["משה"], "aliases": ["moshe"]},
    "david": {"hebrew": ["דוד"], "aliases": ["king david"]},
    "cow": {"hebrew": ["פרה", "בקר", "שור"], "aliases": ["cows", "cattle", "ox", "bull"]},
    "dog": {"hebrew": ["כלב", "כלבים"], "aliases": ["dogs"]},
    "pig": {"hebrew": ["חזיר"], "aliases": ["pork", "swine"]},
    "kosher": {"hebrew": ["כשר", "כשרות", "טרף", "טרפה"], "aliases": ["kashrut", "kashrus", "treif"]},
    "slaughter": {"hebrew": ["שחיטה", "שוחט"], "aliases": ["shechita", "shehitah"]},
    "kilayim": {"hebrew": ["כלאים", "כלאי בהמה"], "aliases": ["mixing species", "crossbreed", "hybrid"]},
    "nevela": {"hebrew": ["נבלה"], "aliases": ["carrion", "unslaughtered"]},
    "meat": {"hebrew": ["בשר"], "aliases": ["basar"]},
    "milk": {"hebrew": ["חלב"], "aliases": ["dairy", "chalav"]},
    "eat": {"hebrew": ["אוכל", "אכילה"], "aliases": ["eating", "food", "consume"]},
    "friend": {"hebrew": ["חבר", "אוהב"], "aliases": ["friends", "companion"]},
    "shabbat": {"hebrew": ["שבת"], "aliases": ["sabbath", "shabbos"]},
    "passover": {"hebrew": ["פסח"], "aliases": ["pesach", "pesah"]},
    "temple": {"hebrew": ["מקדש", "בית המקדש"], "aliases": ["beis hamikdash", "sanctuary"]},
    "sacrifice": {"hebrew": ["זבח", "קורבן"], "aliases": ["offering", "altar", "korban"]},
    "halacha": {"hebrew": ["הלכה"], "aliases": ["halakha", "jewish law"]},
    "messiah": {"hebrew": ["משיח"], "aliases": ["mashiach", "mashiah"]},
    "soul": {"hebrew": ["נשמה", "נפש"], "aliases": ["neshama", "nefesh"]},
    "court": {"hebrew": ["בית דין", "סנהדרין"], "aliases": ["sanhedrin", "bet din"]},
    "charity": {"hebrew": ["צדקה"], "aliases": ["tzedakah", "zedakah"]},
    "solomon": {"hebrew": ["שלמה"], "aliases": ["shlomo"]},
    "adam": {"hebrew": ["אדם"], "aliases": ["first man"]},
    "eve": {"hebrew": ["חוה"], "aliases": ["chava"]},
    "noah": {"hebrew": ["נח"], "aliases": ["noach"]},
    "satan": {"hebrew": ["שטן"], "aliases": ["devil", "demon"]},
    "chicken": {"hebrew": ["תרנגול", "עוף"], "aliases": ["hen", "fowl", "bird"]},
    "sheep": {"hebrew": ["כבש", "צאן"], "aliases": ["lamb", "goat"]},
    "fish": {"hebrew": ["דג", "דגים"], "aliases": ["fishes"]},
    "blood": {"hebrew": ["דם"], "aliases": ["dam"]},
    "treif": {"hebrew": ["טרף", "טרפה"], "aliases": ["trefa", "non-kosher"]},
    "idol": {"hebrew": ["עבודה זרה", "עבודת כוכבים"], "aliases": ["idolatry", "avodah zarah"]},
    "christian": {"hebrew": ["נוצרי", "נוצרים"], "aliases": ["christians", "notzri"]},
    "prayer": {"hebrew": ["תפילה"], "aliases": ["tefillah", "davening"]},
    "torah": {"hebrew": ["תורה"], "aliases": ["scripture"]},
    "aggadah": {"hebrew": ["אגדה"], "aliases": ["legend", "story"]},
    "prophet": {"hebrew": ["נביא"], "aliases": ["prophecy", "prophets"]},
    "resurrection": {"hebrew": ["תחיית המתים"], "aliases": ["techiyat hameitim", "afterlife"]},
    "witch": {"hebrew": ["מכשף", "כשף"], "aliases": ["witchcraft"]},
    "dream": {"hebrew": ["חלום"], "aliases": ["dreams"]},
    "marriage": {"hebrew": ["קידושין", "כתובה"], "aliases": ["wedding", "divorce"]},
    "niddah": {"hebrew": ["נדה"], "aliases": ["menstruation", "family purity"]},
    "conversion": {"hebrew": ["גר"], "aliases": ["convert", "proselyte", "ger"]},
}

LATIN_IN_HEBREW = re.compile(r"[a-zA-Z]")


def clean_hebrew(terms: list[str]) -> list[str]:
    out = []
    for t in terms:
        t = t.replace("קרban", "קרban").replace("קרban", "קרban")
        if LATIN_IN_HEBREW.search(t):
            continue
        if t not in out:
            out.append(t)
    return out


def main() -> None:
    base = json.loads(GLOSSARY.read_text(encoding="utf-8")) if GLOSSARY.exists() else {}
    terms = dict(base.get("terms", {}))
    terms.update(TERM_PACK)

    for entry in terms.values():
        entry["hebrew"] = clean_hebrew(entry.get("hebrew", []))

    terms["sacrifice"]["hebrew"] = clean_hebrew(terms["sacrifice"].get("hebrew", [])) or ["זבח"]

    out = {
        "version": 2,
        "description": "English lexicon for Bavli search — terms, aliases, Hebrew mappings.",
        "terms": terms,
        "phrase_hints": base.get("phrase_hints", []),
        "fuzzy_max_distance": 2,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT} — {len(terms)} terms")


if __name__ == "__main__":
    main()
