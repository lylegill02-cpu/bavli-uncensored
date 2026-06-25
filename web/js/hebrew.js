const STRIP_RE = /[\u0591-\u05af\u05bd\u05bf\u05c1-\u05c2\u05c4-\u05c7]/g;
const FINAL_MAP = { "\u05da": "\u05db", "\u05dd": "\u05de", "\u05df": "\u05e0", "\u05e3": "\u05e4", "\u05e5": "\u05e6" };

export function normalizeHebrew(text) {
  if (!text) return "";
  let out = text.replace(STRIP_RE, "");
  out = out.replace(/[\u05da\u05dd\u05df\u05e3\u05e5]/g, (c) => FINAL_MAP[c] || c);
  out = out.replace(/\u05f3/g, "'").replace(/\u05f4/g, '"');
  out = out.replace(/\s+/g, " ").trim();
  return out;
}

export function likeEscape(s) {
  return s.replace(/\\/g, "\\\\").replace(/%/g, "\\%").replace(/_/g, "\\_");
}
