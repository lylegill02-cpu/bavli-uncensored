# Query expand worker

Turns plain-English questions into Hebrew search terms for the Bavli Uncensored site.

## Deploy (Cloudflare — free tier works)

```bash
cd workers/query-expand
npm install -g wrangler   # or npx wrangler
wrangler login
wrangler deploy
```

Copy the worker URL (e.g. `https://bavli-query-expand.your-subdomain.workers.dev`).

## Connect to the site

Edit `web/js/config.js`:

```javascript
export const AI_EXPAND_URL = "https://bavli-query-expand.your-subdomain.workers.dev";
```

Push to GitHub — English search will call the worker first, then search the full Bavli.

## Without the worker

Search still works via **english_lexicon.json** (~75+ terms, fuzzy spelling). The worker adds natural-language questions like *"is it ok to eat a cow that was friends with a dog?"*

## Test locally

```bash
curl -X POST https://YOUR-WORKER.workers.dev \
  -H "Content-Type: application/json" \
  -d '{"query":"arch angel Michael"}'
```
