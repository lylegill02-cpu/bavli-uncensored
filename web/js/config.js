/** Site config — works locally and on GitHub Pages. */
export const REPO = "lylegill02-cpu/bavli-uncensored";
export const DB_RELEASE_TAG = "v1.0.0-search";

/** Project Pages base path, e.g. /bavli-uncensored/ — empty when served from root. */
export function basePath() {
  const m = location.pathname.match(/^(\/[^/]+)\//);
  if (m && m[1] !== "/js" && location.hostname.endsWith("github.io")) {
    return m[1];
  }
  return "";
}

export function assetUrl(path) {
  const base = basePath();
  return `${base}${path.startsWith("/") ? path : `/${path}`}`;
}

export function dbDownloadUrl() {
  return `https://github.com/${REPO}/releases/download/${DB_RELEASE_TAG}/bavli.db.gz`;
}

export function lociChartUrl() {
  return assetUrl("/data/loci_chart.json");
}

export function auditWitnessDeltasUrl() {
  return assetUrl("/data/audit_witness_deltas.json");
}

/**
 * Tier 3 AI query expansion (Cloudflare Worker).
 * Deploy: workers/query-expand — then paste URL here.
 * Empty string = lexicon + fuzzy spelling only (still works).
 */
export const AI_EXPAND_URL = "";
