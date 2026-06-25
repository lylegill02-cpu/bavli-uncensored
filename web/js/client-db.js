import { dbDownloadUrl } from "./config.js";

let db = null;
let SQL = null;

export function isLoaded() {
  return !!db;
}

export async function loadIndex(onProgress) {
  if (db) return db;

  onProgress?.("Loading sql.js…");
  const initSqlJs = (await import("https://cdn.jsdelivr.net/npm/sql.js@1.10.3/dist/sql-wasm.js")).default;
  SQL = await initSqlJs({
    locateFile: (file) => `https://cdn.jsdelivr.net/npm/sql.js@1.10.3/dist/${file}`,
  });

  onProgress?.("Downloading search index (~53 MB, once per session)…");
  const url = dbDownloadUrl();
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`Failed to download index: ${resp.status}`);

  const total = Number(resp.headers.get("content-length") || 0);
  const reader = resp.body.getReader();
  const chunks = [];
  let received = 0;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
    received += value.length;
    if (total && onProgress) {
      onProgress(`Downloading… ${Math.round((received / total) * 100)}%`);
    }
  }
  const gz = new Uint8Array(received);
  let offset = 0;
  for (const c of chunks) {
    gz.set(c, offset);
    offset += c.length;
  }

  onProgress?.("Decompressing…");
  const ds = new DecompressionStream("gzip");
  const decompressed = await new Response(new Blob([gz]).stream().pipeThrough(ds)).arrayBuffer();

  onProgress?.("Ready.");
  db = new SQL.Database(new Uint8Array(decompressed));
  return db;
}

export function getDb() {
  if (!db) throw new Error("Index not loaded");
  return db;
}
