# Bavli Uncensored

One file. Full Shas. Pre-censorship readings restored where Vilna print and Christian censorship replaced **גוים** with **עובדי כוכבים**.

**Primary source:** [`data/bavli.json`](data/bavli.json) — the entire Babylonian Talmud (gemara + Rashi + Tosafot) keyed by standard refs like `Sanhedrin.43a`.

## Quick start

```bash
# Build the unified source (~2 min; downloads Sefaria export once per tractate)
python scripts/build_bavli.py --compact

# Look up any daf
python scripts/query.py Sanhedrin.43a
python scripts/query.py Sanhedrin.43a --layer gemara --json

# Search (build index once)
python scripts/build_index.py
python scripts/search.py "יֵשׁוּ"
python scripts/search.py "גוים" --tractate "Avodah Zarah" --layer rashi
python scripts/search.py "סטָדָא" --layer gemara --json

# Verify famous uncensored passages landed on the right daf
python scripts/verify_loci.py
```

## File format

```json
{
  "meta": { "edition": "bavli-uncensored-v2", "daf_count": 5499, ... },
  "index": ["Berakhot.2a", "Berakhot.2b", "..."],
  "refs": {
    "Sanhedrin.43a": {
      "seder": "Seder Nezikin",
      "tractate": "Sanhedrin",
      "daf": "43a",
      "gemara": ["…יֵשׁוּ הַנּוֹצְרִי…"],
      "rashi": ["…"],
      "tosafot": ["…"]
    }
  }
}
```

- **`index`** — canonical Daf Yomi traversal order (37 tractates)
- **`refs`** — O(1) lookup by `"Tractate.daf"`
- Layers are line arrays (same structure Sefaria uses internally)

Compact copy: `data/bavli.min.json` (no whitespace, ~15% smaller).

## Search

`bavli.json` itself is not searchable — load it for ref lookup only. For full-text search, build the SQLite index:

```bash
python scripts/build_index.py          # → data/bavli.db (~60s first time)
python scripts/search.py "יֵשׁוּ"        # Hebrew phrase search
python scripts/search.py "גוים" --tractate "Avodah Zarah" --layer rashi
python scripts/build_bavli.py --index    # rebuild source + index together
```

Each hit returns `ref`, `layer`, line number, and a text snippet. Use `--json` for programmatic use.

## What “uncensored” means here

| Layer | Source | Restoration |
|-------|--------|-------------|
| Gemara | Sefaria export (Vilna-aligned) | Sefaria already restored key passages (Sanhedrin 43a, Gittin 57a, 67a); global euphemism patches applied |
| Rashi | Sefaria Vilna Edition | **עובדי כוכבים → גוים** per Munich 95 / Bomberg |
| Tosafot | Sefaria Vilna Edition | Same |

This is **Vilna pagination + witness-based uncensoring**, not a diplomatic transcription of Munich Cod. hebr. 95. Patches are conservative string substitutions documented in `patches/`.

For maximum gemara fidelity (live Sefaria restorations), add `--api-gemara` — results are cached under `data/cache/gemara/`.

## Rebuild options

```bash
python scripts/build_bavli.py              # unified source only
python scripts/build_bavli.py --compact    # + minified copy
python scripts/build_all.py --split        # unified + legacy per-tractate files
python scripts/build_bavli.py --api-gemara # slower; refreshes gemara from API
```

## Methodology

1. **Daf alignment** — Sefaria `merged.json` has two leading slots before 2a (Tamid: long prefix before 25a). Auto-detected and cached in `data/alignments/`.
2. **Patches** — JSON rules in `patches/` from Munich 95 (1342), Bomberg Venice (1520–23), verified against [Hachi Garsinan](https://bavli.genizah.org/) (manual verification only; do not bulk-scrape).
3. **Single output** — one JSON you can load, index, and ship.

## Legal

| Component | License |
|-----------|---------|
| Scripts, patch metadata, README | [MIT](LICENSE) |
| Underlying Vilna text (via Sefaria) | Public domain |
| Munich manuscript (BSB) | Public domain — cite BSB |

## References

- [Sefaria Export](https://github.com/Sefaria/Sefaria-Export)
- [Munich Talmud (NLI)](https://www.nli.org.il/en/discover/manuscripts/hebrew-manuscripts/munich-95)
- [Instone-Brewer — Jesus’ Trial in the Uncensored Talmud](https://tyndalebulletin.org/article/29322-jesus-of-nazareth-s-trial-in-the-uncensored-talmud/)
- [Waxman — Uncensored Printings for Avodah Zarah](https://scribalerror.substack.com/p/uncensored-printings-for-avodah-zarah)
