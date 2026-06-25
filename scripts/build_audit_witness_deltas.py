#!/usr/bin/env python3
"""Build English witness-delta notes for censorship_audit likely_censorship hits."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "data" / "reports" / "censorship_audit.json"
OUT = ROOT / "data" / "audit_witness_deltas.json"

# Hebrew cues → plain-English topic (first match wins)
TOPIC_RULES: list[tuple[list[str], str, str]] = [
    (
        ["מינין", "מין"],
        "sectarians (minim)",
        "Rashi/Tosafot discuss sectarians in a halachic or polemical context; Vilna hides the term behind the censor acronym akum.",
    ),
    (
        ["שמע", "וקראת", "קריאת"],
        "Shema and prayer law",
        "Commentary on Shema or prayer readings — the legal point concerns who may read what; akum replaces Rashi’s direct word for gentiles or sectarians.",
    ),
    (
        ["עירוב", "חצר", "רשות", "מבוי"],
        "eruv and shared courtyards",
        "Eruv law: whether a gentile neighbor’s courtyard affects carrying on Shabbat. Halacha turns on ‘gentile’ residency — not idol-worship as such.",
    ),
    (
        ["גזל", "גזיל", "פרוטה", "השבון", "בן נח"],
        "theft and restitution",
        "Monetary law: theft from or by gentiles, Noahide rules, and whether restitution applies. The sugya is civil law; akum is a vocabulary swap only.",
    ),
    (
        ["ברכ", "מברכ"],
        "blessings",
        "Which blessings apply to gentile-owned objects or events — ritual law, not a polemic about Christianity.",
    ),
    (
        ["עבוד", "מרקוליס", "כוכב"],
        "idolatry references",
        "Commentary touching idol-worship or pagan practice. Even here Vilna often used akum where witnesses still read goyim in generic gentile references.",
    ),
    (
        ["קבר", "טמא", "אהל", "מת"],
        "ritual impurity and burial",
        "Impurity rules for gentile dwellings, corpses, or lands — purity law vocabulary censored to akum.",
    ),
    (
        ["מלכ", "פרע"],
        "gentile rulers",
        "Rules involving gentile kings or rulers (tax, oaths, capital cases) — political/legal context, not theological creed.",
    ),
    (
        ["כותי", "צדוק"],
        "Samaritans or Sadducees",
        "Compares Samaritans, Sadducees, or related groups to gentiles — classification dispute; akum obscures Rashi’s original gentile term.",
    ),
    (
        ["נהרג", "מיתות", "דינ"],
        "capital jurisdiction",
        "Who falls under which court or death penalty — procedural law about gentiles vs Israel.",
    ),
    (
        ["שנאה", "נקמה", "קבלו את התורה"],
        "gentiles and Torah acceptance",
        "Aggadic or legal rhetoric about gentiles not accepting Torah — polemical tone in commentary; censored vocabulary.",
    ),
    (
        ["גר ", "גרי", "תושב"],
        "converts and resident strangers",
        "Ger / resident-alien status vs gentile — who has which obligations.",
    ),
    (
        ["שבת", "מוקצ"],
        "Shabbat practice",
        "Shabbat restrictions involving gentile agents or property — technical Shabbat law.",
    ),
    (
        ["מעשר", "תרומ"],
        "tithes and priestly gifts",
        "Tithes, terumah, or temple-era gifts in gentile-related cases.",
    ),
    (
        ["עדים", "עדות"],
        "testimony",
        "Witness rules when gentiles testify or when testimony concerns gentile parties.",
    ),
    (
        ["מכיר", "מקח", "ממכר"],
        "sales and contracts",
        "Sale, acquisition, or contract law involving gentile counterparties.",
    ),
    (
        ["ריבית", "הלואה"],
        "loans and interest",
        "Interest and loan law where a gentile is party to the transaction.",
    ),
    (
        ["שפיכות דמים"],
        "bloodshed suspicion",
        "Whether gentiles are suspected of violence — affects eruv and partnership rulings.",
    ),
]

DEFAULT_TOPIC = (
    "commentary vocabulary",
    "A routine Rashi/Tosafot gloss where Vilna prints the censor acronym akum instead of the plain word for gentiles that early manuscripts preserve.",
)

SEFARIA_NOTE = (
    "Sefaria commentary English usually follows Vilna — expect ‘idol-worshippers’ or transliterated akum, "
    "not ‘gentiles’. Compare this build’s restored wording on the full daf."
)


def slug_ref(ref: str) -> str:
    return ref.lower().replace(".", "-").replace(" ", "-")


def hit_id(ref: str, layer: str, line_no: int) -> str:
    return f"{slug_ref(ref)}-{layer}-{line_no}"


def infer_topic(snippet: str) -> tuple[str, str]:
    for needles, label, explanation in TOPIC_RULES:
        if any(n in snippet for n in needles):
            return label, explanation
    return DEFAULT_TOPIC


def first_clause(snippet: str, max_len: int = 120) -> str:
    s = re.sub(r"\s+", " ", snippet.strip())
    if len(s) <= max_len:
        return s
    cut = s[:max_len]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut + "…"


def build_delta(hit: dict) -> dict:
    ref = hit["ref"]
    layer = hit["layer"]
    line_no = hit["line_no"]
    snippet = hit.get("snippet") or ""
    tractate = ref.rsplit(".", 1)[0]
    topic_label, topic_explanation = infer_topic(snippet)
    layer_name = "Rashi" if layer == "rashi" else "Tosafot"

    vilna = (
        f"Vilna {layer_name} on {ref} (line {line_no}) prints עכו\"ם — "
        f"the Christian-era acronym for ‘idol-worshippers’ — where pre-censor witnesses had a direct gentile term."
    )
    witness = (
        f"Manuscript {layer_name} for this gloss typically reads גוים (gentiles) or, in sectarian contexts, מין; "
        f"not the opaque acronym. Topic: {topic_label} ({tractate})."
    )
    plain = (
        f"{topic_explanation} "
        f"Open the daf for Hebrew; you do not need to read it to know this is a censorship swap, not a new halachic category. "
        f"Context cue: “{first_clause(snippet)}”"
    )

    return {
        "vilna_standard": vilna,
        "witness_reading": witness,
        "plain_english": plain,
        "sefaria_trust": "low",
        "sefaria_note": SEFARIA_NOTE,
    }


def main() -> None:
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    hits = audit.get("likely_censorship") or []
    entries = []
    by_ref: dict[str, list[str]] = {}

    for hit in hits:
        hid = hit_id(hit["ref"], hit["layer"], hit["line_no"])
        entry = {
            "id": hid,
            "ref": hit["ref"],
            "layer": hit["layer"],
            "line_no": hit["line_no"],
            "pattern_id": hit.get("pattern_id"),
            "count": hit.get("count", 1),
            "snippet": hit.get("snippet", ""),
            "witness_delta": build_delta(hit),
        }
        entries.append(entry)
        by_ref.setdefault(hit["ref"], []).append(hid)

    out = {
        "schema_version": 1,
        "source": "data/reports/censorship_audit.json",
        "pattern": "akum commentary censorship",
        "generated_from": audit.get("audited_at"),
        "count": len(entries),
        "hits": entries,
        "by_ref": by_ref,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT} ({len(entries)} hits, {len(by_ref)} refs)")


if __name__ == "__main__":
    main()
