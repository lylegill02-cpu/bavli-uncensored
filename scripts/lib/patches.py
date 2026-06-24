"""Load and apply censorship-restoration patches."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PATCHES_DIR = ROOT / "patches"


@dataclass
class SubstitutionRule:
    id: str
    find: str
    replace: str
    enabled: bool = True
    witnesses: list[str] | None = None
    notes: str | None = None


@dataclass
class InsertionPatch:
    id: str
    tractate: str
    daf: str
    after_line: int | None
    before_anchor: str | None
    lines: list[str]
    witnesses: list[str]
    notes: str | None = None


def load_manifest() -> dict:
    return json.loads((PATCHES_DIR / "manifest.json").read_text(encoding="utf-8"))


def load_substitution_rules(path: str, tractate: str | None = None) -> list[SubstitutionRule]:
    data = json.loads((PATCHES_DIR / path).read_text(encoding="utf-8"))
    tractates = data.get("tractates")
    if tractate and tractates and tractate not in tractates and "*" not in tractates:
        return []
    rules = []
    for raw in data.get("rules", []):
        rules.append(
            SubstitutionRule(
                id=raw["id"],
                find=raw["find"],
                replace=raw["replace"],
                enabled=raw.get("enabled", True),
                witnesses=raw.get("witnesses"),
                notes=raw.get("notes"),
            )
        )
    return rules


def load_all_substitution_rules(tractate: str) -> list[SubstitutionRule]:
    manifest = load_manifest()
    rules: list[SubstitutionRule] = []
    for rel in manifest.get("patches", []):
        if not rel.startswith("substitutions/"):
            continue
        rules.extend(load_substitution_rules(rel, tractate=tractate))
    return [r for r in rules if r.enabled]


def apply_substitutions(text: str, rules: list[SubstitutionRule]) -> tuple[str, list[str]]:
    applied: list[str] = []
    out = text
    for rule in rules:
        if rule.find in out:
            count = out.count(rule.find)
            out = out.replace(rule.find, rule.replace)
            applied.append(f"{rule.id} x{count}")
    return out, applied


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


def normalize_for_compare(text: str) -> str:
    return strip_html(text).replace("\u05f3", "'").replace("\u05f4", '"')
