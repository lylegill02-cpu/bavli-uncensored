/**
 * Tier 3: optional AI query expansion via Cloudflare Worker (or compatible endpoint).
 * Falls back silently to lexicon-only search when unavailable.
 */
import { AI_EXPAND_URL } from "./config.js";

/**
 * @returns {Promise<{ hebrew_terms: string[], english_keywords: string[], topic_summary: string, from_ai: boolean } | null>}
 */
export async function expandQueryWithAI(query) {
  if (!AI_EXPAND_URL) return null;

  try {
    const r = await fetch(AI_EXPAND_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
      signal: AbortSignal.timeout(25000),
    });
    if (!r.ok) return null;
    const data = await r.json();
    return {
      hebrew_terms: data.hebrew_terms || [],
      english_keywords: data.english_keywords || [],
      topic_summary: data.topic_summary || "",
      from_ai: true,
    };
  } catch {
    return null;
  }
}
