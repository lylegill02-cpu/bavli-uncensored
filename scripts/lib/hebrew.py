"""Hebrew text normalization for search (strip niqqud, unify final letters)."""
from __future__ import annotations

import re
import unicodedata

# Final → medial forms (so יֵשׁוּ and ישו match)
_FINALS = str.maketrans("ךםןףץ", "כמנפצ")

# Niqqud, cantillation, trope marks in Hebrew block
_STRIP_RE = re.compile(
    r"[\u0591-\u05af\u05bd\u05bf\u05c1-\u05c2\u05c4-\u05c7]"
)


def normalize_hebrew(text: str) -> str:
    """Normalize for substring search: no vowels/trop, unified finals, clean space."""
    if not text:
        return ""
    out = _STRIP_RE.sub("", text)
    out = out.translate(_FINALS)
    out = out.replace("\u05f3", "'").replace("\u05f4", '"')
    out = unicodedata.normalize("NFC", out)
    out = re.sub(r"\s+", " ", out).strip()
    return out


def query_variants(query: str) -> list[str]:
    """Return normalized query plus original for dual matching."""
    norm = normalize_hebrew(query)
    variants = []
    for v in (norm, query.strip()):
        if v and v not in variants:
            variants.append(v)
    return variants
