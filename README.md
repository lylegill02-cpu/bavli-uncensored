# Bavli Uncensored

Open, machine-readable **Babylonian Talmud (Bavli)** text with **Christian censorship restorations** applied on top of the public [Sefaria export](https://github.com/Sefaria/Sefaria-Export).

Vilna pagination is preserved. Each daf includes **gemara**, **Rashi**, and **Tosafot** where available.

## Why this exists

Standard digital Bavli (including Sefaria) is mostly Vilna-shaped. That is good for Daf Yomi, but:

- **Rashi and Tosafot** often still read **עובדי כוכבים** where Munich 95 and Bomberg have **גוים** / **נכרים** (especially *Avodah Zarah*).
- Some **gemara** passages were censored in print; Sefaria has already restored several (e.g. Sanhedrin 43a, Gittin 57a, Sanhedrin 67a), but commentary layers lag behind.

This repo is a **transparent patch pipeline**: base text + documented restorations + rebuild scripts.

## Quick start

```bash
# One tractate (downloads from Sefaria export; no API key)
python scripts/build_tractate.py "Avodah Zarah"

# Test run (first 20 dapim)
python scripts/build_tractate.py "Avodah Zarah" --max-daf 20

# Scan for censorship-term patterns (research)
python scripts/scan_censorship.py
```

Output: `data/output/<Tractate>.json`

### Example record (`2a`)

```json
{
  "gemara": ["…לפני אידיהן של גוים…"],
  "rashi": ["…לפני אידיהן של גוים…"],
  "tosafot": ["…"],
  "patches_applied": ["rashi:ovdei_kochavim_plural x3"]
}
```

## Methodology

1. **Base gemara** — Sefaria export `merged.json` (Vilna, often already uncensored in the main column).
2. **Base Rashi/Tosafot** — Sefaria export `Vilna Edition.json` (from Hebrew Wikisource; censored euphemisms remain).
3. **Patches** — JSON rules in `patches/` derived from manuscript/early-print witnesses:
   - Munich Cod. hebr. 95 (1342) — [BSB digitization](http://daten.digitale-sammlungen.de/bsb00003409/images)
   - Bomberg Venice (1520–1523)
   - Scholarly comparisons via [Hachi Garsinan](https://bavli.genizah.org/) (use for verification; do not scrape their database into this repo)

Default substitution (commentary + gemara where needed):

| Censored (Vilna) | Restored | Witnesses |
|------------------|----------|-----------|
| עובדי כוכבים | גוים | Munich, Bomberg |
| עובד כוכבים | גוי | Munich, Bomberg |

**Not** a diplomatic edition of Munich — it is **Vilna layout + selective uncensoring** with patch metadata on every daf.

## Included tractates

All **37 Bavli tractates** in `data/tractates.json` are supported. Run:

```bash
python scripts/build_all.py
```

Built JSON lands in `data/output/<Tractate>.json`. Re-run a single tractate with `build_tractate.py`.

### Export alignment (important)

Sefaria `merged.json` arrays are **not** index-zero = 2a. Most tractates have **two leading slots** before 2a; **Tamid** has a long empty prefix before 25a. The builder auto-detects this (`scripts/lib/daf.py`, cached in `data/alignments/`) so daf labels match Vilna pagination — e.g. Sanhedrin **43a** correctly includes the Yeshu baraita.

Verify famous uncensored loci after a build:

```bash
python scripts/verify_loci.py
```

## Legal / licensing

| Component | License / terms |
|-----------|-----------------|
| This repo (scripts, patch JSON, README) | [MIT](LICENSE) |
| Underlying Vilna text (via Sefaria/Wikisource) | Public domain |
| Munich manuscript images | Public domain (cite BSB) |
| Hachi Garsinan transcriptions | **Do not bulk-copy** — use for manual verification only |

Do not use Steinsaltz English from Sefaria in derivative works without respecting their CC BY-NC terms.

## Limitations (v1)

- Patch rules are **conservative substitutions**, not full critical apparatus.
- Some censored passages need **insertion patches** (see `patches/insertions/`) — many are already present in Sefaria gemara; more can be added with citations.
- Full Shas build = run per tractate (~37 tractates); CI can batch this.

## Publish to GitHub

```bash
cd bavli-uncensored
git add .
git commit -m "Initial uncensored Bavli patch pipeline and Avodah Zarah sample"
gh repo create bavli-uncensored --public --source=. --push
```

Or create an empty repo on GitHub and:

```bash
git remote add origin https://github.com/YOUR_USER/bavli-uncensored.git
git push -u origin main
```

## References

- [Sefaria Export](https://github.com/Sefaria/Sefaria-Export)
- [Munich Talmud (NLI)](https://www.nli.org.il/en/discover/manuscripts/hebrew-manuscripts/munich-95)
- [Instone-Brewer, Jesus’ Trial in the Uncensored Talmud](https://tyndalebulletin.org/article/29322-jesus-of-nazareth-s-trial-in-the-uncensored-talmud/)
- [Marvin, Hachi Garsinan guide](https://trmarvin.org/hachi-garsinan/)
- [Waxman, Uncensored Printings for Avodah Zarah](https://scribalerror.substack.com/p/uncensored-printings-for-avodah-zarah)
