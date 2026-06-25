#!/usr/bin/env python3
"""Systematic censorship-pattern audit over built bavli.json."""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "data" / "bavli.json"
REPORT_JSON = ROOT / "data" / "reports" / "censorship_audit.json"
REPORT_MD = ROOT / "data" / "reports" / "censorship_audit.md"

# Patterns that often indicate Christian censorship (not always — context matters)
PATTERNS: list[tuple[str, str, str]] = [
    ("ovdei_kochavim_plural", "עובדי כוכבים", "Euphemism for גוים — patch candidate"),
    ("oved_kochav_singular", "עובד כוכבים", "Euphemism for גוי — patch candidate"),
    ("akum_ascii", 'עכו"ם', "Censor acronym — patch candidate"),
    ("akum_hebrew", "עכו״ם", "Censor acronym (Hebrew quotes) — patch candidate"),
    ("nokhri_as_euphemism", "נכרי", "Sometimes original; flag for manual review"),
]

# Tractates where עובדי כוכבים may be legitimate legal terminology
LEGITIMATE_OVDEI_TRACTATES = frozenset({"Avodah Zarah"})

RESTORED_LOCI = [
    ("Sanhedrin.43a", "יֵשׁוּ", "Yeshu baraita"),
    ("Sanhedrin.67a", "סָטָדָא", "ben Stada"),
    ("Gittin.57a", "יֵשׁוּ", "Yeshu ha-Notzri"),
]


@dataclass
class Hit:
    ref: str
    tractate: str
    daf: str
    layer: str
    line_no: int
    pattern_id: str
    pattern: str
    count: int
    snippet: str
    note: str
    likely_censorship: bool


def audit(source: Path) -> dict:
    data = json.loads(source.read_text(encoding="utf-8"))
    refs = data.get("refs", {})
    hits: list[Hit] = []
    by_pattern: dict[str, int] = defaultdict(int)
    by_tractate: dict[str, int] = defaultdict(int)
    by_layer: dict[str, int] = defaultdict(int)

    for ref, entry in refs.items():
        tractate = entry.get("tractate", ref.rsplit(".", 1)[0])
        daf = entry.get("daf", ref.rsplit(".", 1)[-1])
        for layer in ("gemara", "rashi", "tosafot"):
            for i, line in enumerate(entry.get(layer, []) or [], start=1):
                if not line:
                    continue
                for pid, needle, note in PATTERNS:
                    count = line.count(needle)
                    if not count:
                        continue
                    likely = pid.startswith("ovdei") or pid.startswith("oved") or pid.startswith("akum")
                    if tractate in LEGITIMATE_OVDEI_TRACTATES and pid.startswith("ovdei"):
                        likely = layer != "gemara"  # gemara often already restored
                    hits.append(
                        Hit(
                            ref=ref,
                            tractate=tractate,
                            daf=daf,
                            layer=layer,
                            line_no=i,
                            pattern_id=pid,
                            pattern=needle,
                            count=count,
                            snippet=line[:200],
                            note=note,
                            likely_censorship=likely,
                        )
                    )
                    by_pattern[pid] += count
                    by_tractate[tractate] += count
                    by_layer[layer] += count

    loci_status = []
    for ref, needle, label in RESTORED_LOCI:
        entry = refs.get(ref, {})
        text = " ".join(entry.get("gemara", []))
        loci_status.append(
            {
                "ref": ref,
                "label": label,
                "needle": needle,
                "present": needle in text,
            }
        )

    suspicious = [h for h in hits if h.likely_censorship]
    suspicious_tractates = sorted(
        {h.tractate for h in suspicious},
        key=lambda t: sum(1 for h in suspicious if h.tractate == t),
        reverse=True,
    )

    return {
        "audited_at": datetime.now(timezone.utc).isoformat(),
        "source": str(source.name),
        "edition": data.get("meta", {}).get("edition"),
        "summary": {
            "total_hits": len(hits),
            "likely_censorship_hits": len(suspicious),
            "by_pattern": dict(by_pattern),
            "by_tractate_top10": dict(
                sorted(by_tractate.items(), key=lambda x: -x[1])[:10]
            ),
            "by_layer": dict(by_layer),
            "tractates_most_suspicious": suspicious_tractates[:15],
        },
        "restored_loci": loci_status,
        "likely_censorship": [
            {
                "ref": h.ref,
                "layer": h.layer,
                "line_no": h.line_no,
                "pattern_id": h.pattern_id,
                "pattern": h.pattern,
                "count": h.count,
                "snippet": h.snippet,
                "note": h.note,
            }
            for h in suspicious[:500]
        ],
        "all_hits_sample": [
            {
                "ref": h.ref,
                "layer": h.layer,
                "pattern_id": h.pattern_id,
                "count": h.count,
            }
            for h in hits[:200]
        ],
    }


def write_markdown(report: dict, path: Path) -> None:
    s = report["summary"]
    lines = [
        "# Bavli censorship audit",
        "",
        f"Generated: {report['audited_at']}",
        f"Source: `{report['source']}` · edition `{report.get('edition')}`",
        "",
        "## Summary",
        "",
        f"- **Total pattern matches:** {s['total_hits']}",
        f"- **Likely censorship (needs patch/review):** {s['likely_censorship_hits']}",
        "",
        "### By pattern",
        "",
    ]
    for pid, n in sorted(s["by_pattern"].items(), key=lambda x: -x[1]):
        lines.append(f"- `{pid}`: **{n}**")
    lines += ["", "### By layer", ""]
    for layer, n in s["by_layer"].items():
        lines.append(f"- {layer}: **{n}**")
    lines += ["", "### Tractates with most suspicious hits", ""]
    for t in s["tractates_most_suspicious"]:
        lines.append(f"- {t}")
    lines += ["", "## Restored loci (sanity check)", ""]
    for loc in report["restored_loci"]:
        mark = "OK" if loc["present"] else "MISSING"
        lines.append(f"- [{mark}] **{loc['ref']}** — {loc['label']}")
    lines += [
        "",
        "## Next steps",
        "",
        "1. Review `likely_censorship` entries in `censorship_audit.json`",
        "2. Verify against Munich 95 / Bomberg via [Hachi Garsinan](https://bavli.genizah.org/)",
        "3. Add substitution rules in `patches/substitutions/` for confirmed cases",
        "4. Rebuild: `python scripts/build_bavli.py --index`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit built corpus for censorship patterns")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    args = parser.parse_args()

    if not args.source.exists():
        raise SystemExit(f"Missing {args.source}")

    report = audit(args.source)
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(report, REPORT_MD)

    s = report["summary"]
    print(f"Wrote {REPORT_JSON}")
    print(f"Wrote {REPORT_MD}")
    print(
        f"Hits: {s['total_hits']} total, {s['likely_censorship_hits']} likely censorship"
    )
    for loc in report["restored_loci"]:
        print(f"  [{('OK' if loc['present'] else 'MISS')}] {loc['ref']}")


if __name__ == "__main__":
    main()
