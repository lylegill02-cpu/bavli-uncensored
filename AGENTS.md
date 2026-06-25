# Agent notes — Bavli Uncensored

**Repo:** https://github.com/lylegill02-cpu/bavli-uncensored  
**Public site:** https://lylegill02-cpu.github.io/bavli-uncensored/

## Architecture

| Piece | Location |
|-------|----------|
| Unified corpus | `data/bavli.json` (~70 MB, not in git — rebuild or use release) |
| Search index | `data/bavli.db` or Release `bavli.db.gz` |
| Loci seed data | `data/loci.json` → `python scripts/sync_loci.py` → `data/loci_chart.json` |
| Static UI | `web/` — deployed via `.github/workflows/pages.yml` |

**Hosting is GitHub-only** (Pages + Releases + client-side sql.js). Do not load the corpus into Supabase.

## Supabase teardown (g10be-overflow)

If `bavli_*` tables exist on project `galhchvctvmtbykzzqqp`:

```bash
python scripts/clear_supabase.py   # SUPABASE_DB_URL required
```

Or apply `forge-aop/supabase/migrations/20260625120000_drop_bavli_search.sql`.

## Key scripts

- `scripts/build_bavli.py` — rebuild unified source
- `scripts/build_index.py` — SQLite search index
- `scripts/serve.py` — local FastAPI (search + loci API)
- `scripts/audit_censorship.py` — censorship audit reports
