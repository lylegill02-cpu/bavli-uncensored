# Bavli censorship audit

Generated: 2026-06-25T03:34:44.717003+00:00
Source: `bavli.json` · edition `bavli-uncensored-v2`

## Summary

- **Total pattern matches:** 751
- **Likely censorship (needs patch/review):** 100

### By pattern

- `nokhri_as_euphemism`: **1301**
- `akum_ascii`: **227**
- `akum_hebrew`: **1**

### By layer

- rashi: **652**
- tosafot: **877**

### Tractates with most suspicious hits

- Eruvin
- Bava Metzia
- Sanhedrin
- Bava Batra
- Shabbat
- Bava Kamma
- Berakhot
- Pesachim
- Zevachim
- Yevamot
- Taanit
- Sukkah
- Gittin
- Ketubot
- Rosh Hashanah

## Restored loci (sanity check)

- [OK] **Sanhedrin.43a** — Yeshu baraita
- [OK] **Sanhedrin.67a** — ben Stada
- [OK] **Gittin.57a** — Yeshu ha-Notzri

## Next steps

1. Review `likely_censorship` entries in `censorship_audit.json`
2. Verify against Munich 95 / Bomberg via [Hachi Garsinan](https://bavli.genizah.org/)
3. Add substitution rules in `patches/substitutions/` for confirmed cases
4. Rebuild: `python scripts/build_bavli.py --index`
