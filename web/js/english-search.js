import { normalizeHebrew } from "./hebrew.js";
import { searchLines } from "./client-search.js";
import { ensureClientIndex } from "./app.js";
import { lociChartUrl, assetUrl } from "./config.js";
import { expandQueryWithAI } from "./ai-expand.js";

let lexiconCache = null;
let lociCache = null;

async function loadLexicon() {
  if (lexiconCache) return lexiconCache;
  const r = await fetch(assetUrl("/data/english_lexicon.json"));
  if (!r.ok) {
    const g = await fetch(assetUrl("/data/english_glossary.json"));
    lexiconCache = await g.json();
  } else {
    lexiconCache = await r.json();
  }
  return lexiconCache;
}

async function loadLoci() {
  if (lociCache) return lociCache;
  const r = await fetch(lociChartUrl());
  const data = await r.json();
  lociCache = data.loci || [];
  return lociCache;
}

function tokenize(query) {
  return query
    .toLowerCase()
    .replace(/[^\w\s'-]/g, " ")
    .split(/\s+/)
    .filter((w) => w.length > 1);
}

function levenshtein(a, b) {
  if (a === b) return 0;
  if (!a.length) return b.length;
  if (!b.length) return a.length;
  const row = Array.from({ length: b.length + 1 }, (_, i) => i);
  for (let i = 1; i <= a.length; i++) {
    let prev = i - 1;
    row[0] = i;
    for (let j = 1; j <= b.length; j++) {
      const cur = row[j];
      row[j] =
        a[i - 1] === b[j - 1]
          ? prev
          : 1 + Math.min(prev, row[j - 1], row[j]);
      prev = cur;
    }
  }
  return row[b.length];
}

function allAliases(termsMap) {
  const out = [];
  for (const [key, entry] of Object.entries(termsMap)) {
    out.push({ key, phrase: key, entry });
    for (const alias of entry.aliases || []) {
      out.push({ key, phrase: alias.toLowerCase(), entry });
    }
  }
  return out;
}

function matchLexicon(query, lexicon) {
  const termsMap = lexicon.terms || {};
  const words = tokenize(query);
  const q = words.join(" ");
  const hebrew = new Set();
  const matchedKeys = new Set();
  const maxDist = lexicon.fuzzy_max_distance ?? 2;
  const aliases = allAliases(termsMap);

  // Longest phrase match first (e.g. "arch angel michael")
  const sorted = [...aliases].sort((a, b) => b.phrase.length - a.phrase.length);
  for (const { key, phrase, entry } of sorted) {
    if (q.includes(phrase) || query.toLowerCase().includes(phrase)) {
      matchedKeys.add(key);
      for (const h of entry.hebrew || []) hebrew.add(h);
    }
  }

  // Single-word exact + fuzzy
  for (const word of words) {
    if (word.length < 3) continue;
    for (const { key, phrase, entry } of aliases) {
      if (phrase === word || phrase.split(/\s+/).includes(word)) {
        matchedKeys.add(key);
        for (const h of entry.hebrew || []) hebrew.add(h);
      }
    }
    if (matchedKeys.size) continue;
    for (const { key, phrase, entry } of aliases) {
      const parts = phrase.split(/\s+/);
      const target = parts.length === 1 ? phrase : parts.find((p) => p.length >= 3) || phrase;
      if (target.length >= 4 && levenshtein(word, target) <= maxDist) {
        matchedKeys.add(key);
        for (const h of entry.hebrew || []) hebrew.add(h);
      }
    }
  }

  return { hebrew: [...hebrew], matchedKeys: [...matchedKeys] };
}

function locusText(loc) {
  return [
    loc.topic?.en,
    loc.english_summary,
    loc.tradition_note,
    ...(loc.english_keywords || []),
    ...(loc.tags || []),
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
}

function scoreLocus(loc, words, fullQuery, extraKeywords = []) {
  const text = locusText(loc);
  let score = 0;
  const allWords = [...words, ...extraKeywords.map((w) => w.toLowerCase())];
  for (const w of allWords) {
    if (w.length > 2 && text.includes(w)) score += 3;
  }
  if (fullQuery.length > 3 && text.includes(fullQuery.toLowerCase())) score += 5;
  for (const kw of loc.english_keywords || []) {
    for (const w of allWords) {
      if (kw.toLowerCase().includes(w) || w.includes(kw.toLowerCase())) score += 2;
    }
  }
  return score;
}

function phraseHint(words, lexicon) {
  const set = new Set(words);
  for (const hint of lexicon.phrase_hints || []) {
    if ((hint.words || []).every((w) => set.has(w))) return hint.summary;
  }
  return null;
}

function mergeCorpusHits(hits, seen) {
  const out = [];
  for (const hit of hits) {
    const key = `${hit.ref}|${hit.layer}|${hit.line_no}`;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(hit);
  }
  return out;
}

/**
 * English search: lexicon + fuzzy spelling + optional AI expansion + loci + corpus.
 */
export async function searchEnglish(query, opts = {}) {
  const words = tokenize(query);
  if (!words.length && !query.trim()) {
    return { hint: null, featured: [], loci: [], corpus: [], hebrewTerms: [], aiUsed: false };
  }

  const lexicon = await loadLexicon();
  const loci = await loadLoci();

  let aiHint = null;
  let aiUsed = false;
  let extraKeywords = [];
  let hebrewTerms = [];

  if (opts.useAI !== false) {
    opts.onProgress?.("Understanding your question…");
    const ai = await expandQueryWithAI(query.trim());
    if (ai) {
      aiUsed = true;
      aiHint = ai.topic_summary || null;
      extraKeywords = ai.english_keywords || [];
      hebrewTerms.push(...(ai.hebrew_terms || []));
    }
  }

  const lex = matchLexicon(query, lexicon);
  hebrewTerms.push(...lex.hebrew);
  hebrewTerms = [...new Set(hebrewTerms.filter(Boolean))];

  let hint = phraseHint(words, lexicon) || aiHint;

  const scoredLoci = loci
    .map((loc) => ({
      loc,
      score: scoreLocus(loc, words, query.trim(), extraKeywords),
    }))
    .filter((x) => x.score > 0)
    .sort((a, b) => b.score - a.score);

  const featured = scoredLoci.filter((x) => x.loc.ref).slice(0, 8);

  let corpus = [];
  if (hebrewTerms.length) {
    await ensureClientIndex(opts.onProgress);
    const seen = new Set();
    const limit = opts.limit || 30;
    const perTerm = Math.max(8, Math.ceil(limit / Math.min(hebrewTerms.length, 10)));
    for (const term of hebrewTerms.slice(0, 10)) {
      const hits = searchLines(term, {
        tractate: opts.tractate || null,
        layer: opts.layer || null,
        limit: perTerm,
      });
      corpus.push(...mergeCorpusHits(hits, seen));
    }
    corpus = corpus.slice(0, limit);
  }

  if (!hint && hebrewTerms.length && !corpus.length && !featured.length) {
    hint =
      "No direct matches. Try shorter words (e.g. Michael, cow, kosher) or enable Smart search once the AI endpoint is deployed.";
  }

  return {
    hint,
    hebrewTerms,
    matchedLexicon: lex.matchedKeys,
    featured: featured.map((x) => x.loc),
    loci: scoredLoci.map((x) => x.loc),
    corpus,
    aiUsed,
  };
}

export function hasHebrew(text) {
  return /[\u0590-\u05FF]/.test(text);
}
