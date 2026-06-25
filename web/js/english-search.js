import { normalizeHebrew } from "./hebrew.js";
import { searchLines } from "./client-search.js";
import { ensureClientIndex } from "./app.js";
import { lociChartUrl, assetUrl } from "./config.js";

let glossaryCache = null;
let lociCache = null;

async function loadGlossary() {
  if (glossaryCache) return glossaryCache;
  const r = await fetch(assetUrl("/data/english_glossary.json"));
  glossaryCache = await r.json();
  return glossaryCache;
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

function scoreLocus(loc, words, fullQuery) {
  const text = locusText(loc);
  let score = 0;
  for (const w of words) {
    if (text.includes(w)) score += 3;
  }
  if (fullQuery.length > 3 && text.includes(fullQuery.toLowerCase())) score += 5;
  for (const kw of loc.english_keywords || []) {
    for (const w of words) {
      if (kw.toLowerCase() === w || kw.toLowerCase().includes(w)) score += 2;
    }
  }
  return score;
}

function expandHebrewTerms(words, glossary) {
  const terms = new Set();
  const termsMap = glossary.terms || {};

  for (const word of words) {
    for (const [key, entry] of Object.entries(termsMap)) {
      const aliases = [key, ...(entry.aliases || [])].map((a) => a.toLowerCase());
      if (aliases.some((a) => a === word || a.includes(word) || word.includes(a))) {
        for (const h of entry.hebrew || []) terms.add(h);
      }
    }
  }

  // Multi-word alias match (e.g. "ben stada")
  const q = words.join(" ");
  for (const [key, entry] of Object.entries(termsMap)) {
    for (const alias of entry.aliases || []) {
      if (q.includes(alias.toLowerCase())) {
        for (const h of entry.hebrew || []) terms.add(h);
      }
    }
  }

  return [...terms];
}

function phraseHint(words, glossary) {
  const set = new Set(words);
  for (const hint of glossary.phrase_hints || []) {
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
 * Plain-English search: loci matches (with summaries) + Hebrew corpus via glossary.
 */
export async function searchEnglish(query, opts = {}) {
  const words = tokenize(query);
  if (!words.length) return { hint: null, featured: [], loci: [], corpus: [] };

  const glossary = await loadGlossary();
  const loci = await loadLoci();
  const hint = phraseHint(words, glossary);

  const scoredLoci = loci
    .map((loc) => ({ loc, score: scoreLocus(loc, words, query.trim()) }))
    .filter((x) => x.score > 0)
    .sort((a, b) => b.score - a.score);

  const featured = scoredLoci.filter((x) => x.loc.ref).slice(0, 8);
  const hebrewTerms = expandHebrewTerms(words, glossary);

  let corpus = [];
  if (hebrewTerms.length) {
    await ensureClientIndex(opts.onProgress);
    const seen = new Set();
    for (const term of hebrewTerms.slice(0, 6)) {
      const hits = searchLines(term, {
        tractate: opts.tractate || null,
        layer: opts.layer || null,
        limit: opts.limit || 25,
      });
      corpus.push(...mergeCorpusHits(hits, seen));
    }
    corpus = corpus.slice(0, opts.limit || 30);
  }

  return {
    hint,
    hebrewTerms,
    featured: featured.map((x) => x.loc),
    loci: scoredLoci.map((x) => x.loc),
    corpus,
  };
}

export function hasHebrew(text) {
  return /[\u0590-\u05FF]/.test(text);
}
