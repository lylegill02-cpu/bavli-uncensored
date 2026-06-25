import { normalizeHebrew, likeEscape } from "./hebrew.js";
import { getDb } from "./client-db.js";

function snippet(text, query, width = 160) {
  const normText = normalizeHebrew(text);
  const normQ = normalizeHebrew(query);
  let pos = text.indexOf(query);
  if (pos === -1) pos = normText.indexOf(normQ);
  if (pos === -1) return text.slice(0, width);
  const start = Math.max(0, pos - Math.floor(width / 3));
  const end = Math.min(text.length, pos + query.length + Math.floor(width / 2));
  let out = text.slice(start, end);
  if (start > 0) out = "…" + out;
  if (end < text.length) out = out + "…";
  return out;
}

export function searchLines(query, { tractate = null, layer = null, limit = 30 } = {}) {
  const conn = getDb();
  const normQ = likeEscape(normalizeHebrew(query));
  let sql = `
    SELECT ref, tractate, daf, layer, line_no, text
    FROM lines
    WHERE text_norm LIKE '%' || ? ESCAPE '\\'
  `;
  const params = [normQ];
  if (tractate) {
    sql += " AND tractate = ?";
    params.push(tractate);
  }
  if (layer) {
    sql += " AND layer = ?";
    params.push(layer);
  }
  sql += " ORDER BY ref, line_no LIMIT ?";
  params.push(limit);

  const stmt = conn.prepare(sql);
  stmt.bind(params);
  const hits = [];
  while (stmt.step()) {
    const row = stmt.getAsObject();
    hits.push({ ...row, snippet: snippet(row.text, query) });
  }
  stmt.free();
  return hits;
}

export function getDaf(ref) {
  const conn = getDb();
  const stmt = conn.prepare(`
    SELECT layer, line_no, text FROM lines
    WHERE ref = ?
    ORDER BY
      CASE layer WHEN 'gemara' THEN 1 WHEN 'rashi' THEN 2 WHEN 'tosafot' THEN 3 ELSE 4 END,
      line_no
  `);
  stmt.bind([ref]);
  const out = { ref, gemara: [], rashi: [], tosafot: [] };
  while (stmt.step()) {
    const row = stmt.getAsObject();
    const bucket = out[row.layer];
    if (bucket) bucket.push(row.text);
  }
  stmt.free();
  if (!out.gemara.length && !out.rashi.length && !out.tosafot.length) return null;
  return out;
}

export function listTractates() {
  const conn = getDb();
  const res = conn.exec("SELECT DISTINCT tractate FROM lines ORDER BY tractate");
  if (!res.length) return [];
  return res[0].values.map(([t]) => ({ tractate: t }));
}
