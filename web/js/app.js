import { basePath, assetUrl } from "./config.js";
import { loadIndex, isLoaded } from "./client-db.js";
import * as client from "./client-search.js";

export function useClientMode() {
  return (
    location.hostname.endsWith("github.io") ||
    location.search.includes("client=1")
  );
}

export async function ensureClientIndex(onProgress) {
  if (!isLoaded()) await loadIndex(onProgress);
}

export async function apiHealth() {
  try {
    const r = await fetch(`${basePath()}/health`, { signal: AbortSignal.timeout(1500) });
    return r.ok;
  } catch {
    return false;
  }
}

export async function search(query, opts) {
  if (useClientMode() || !(await apiHealth())) {
    await ensureClientIndex(opts.onProgress);
    return client.searchLines(query, opts);
  }
  const params = new URLSearchParams({ q: query, limit: String(opts.limit || 30) });
  if (opts.tractate) params.set("tractate", opts.tractate);
  if (opts.layer) params.set("layer", opts.layer);
  const r = await fetch(`${basePath()}/search?${params}`);
  if (!r.ok) throw new Error("Search failed");
  const data = await r.json();
  return data.results || [];
}

export async function openDaf(ref) {
  if (useClientMode() || !(await apiHealth())) {
    await ensureClientIndex();
    return client.getDaf(ref);
  }
  const r = await fetch(`${basePath()}/ref/${encodeURIComponent(ref)}`);
  if (!r.ok) return null;
  return r.json();
}

export async function loadTractates() {
  if (useClientMode() || !(await apiHealth())) {
    await ensureClientIndex();
    return client.listTractates();
  }
  const r = await fetch(`${basePath()}/tractates`);
  if (!r.ok) return [];
  const data = await r.json();
  return data.tractates || [];
}

export { assetUrl };
