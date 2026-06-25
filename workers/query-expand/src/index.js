/**
 * Cloudflare Worker — Tier 3 English query expansion for Bavli Uncensored.
 *
 * Deploy:
 *   cd workers/query-expand
 *   npx wrangler deploy
 *
 * Then set AI_EXPAND_URL in web/js/config.js to your worker URL.
 */
export default {
  async fetch(request, env) {
    const cors = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    };

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: cors });
    }

    if (request.method !== "POST") {
      return json({ error: "POST { query: string }" }, 405, cors);
    }

    let body;
    try {
      body = await request.json();
    } catch {
      return json({ error: "Invalid JSON" }, 400, cors);
    }

    const query = String(body.query || "").trim();
    if (!query) {
      return json({ error: "query required" }, 400, cors);
    }

    const system = `You help search the Babylonian Talmud (Bavli) in Hebrew.
Given a plain-English question, return ONLY valid JSON (no markdown) with:
{
  "hebrew_terms": ["..."],     // 3-8 Hebrew words/phrases to search in the corpus (niqqud optional)
  "english_keywords": ["..."], // 3-8 English words for matching curated summaries
  "topic_summary": "..."       // 1-2 sentences: what the asker is probably looking for in the Bavli
}
Focus on names, halacha topics, and concrete Talmudic vocabulary. For animals/kashrut use Hebrew terms (e.g. cow→פרה/בקר/שור, dog→כלב, kosher→כשר/טרף).
Do not answer from general knowledge — only suggest search terms.`;

    try {
      const ai = await env.AI.run(env.QUERY_MODEL || "@cf/meta/llama-3.1-8b-instruct", {
        messages: [
          { role: "system", content: system },
          { role: "user", content: query },
        ],
        max_tokens: 512,
      });

      const text = ai?.response ?? "";
      const parsed = extractJson(text);
      if (!parsed) {
        return json({ error: "AI parse failed", raw: text.slice(0, 500) }, 502, cors);
      }

      return json(
        {
          hebrew_terms: array(parsed.hebrew_terms),
          english_keywords: array(parsed.english_keywords),
          topic_summary: String(parsed.topic_summary || ""),
        },
        200,
        cors
      );
    } catch (e) {
      return json({ error: String(e.message || e) }, 500, cors);
    }
  },
};

function array(v) {
  return Array.isArray(v) ? v.map(String).filter(Boolean) : [];
}

function extractJson(text) {
  const start = text.indexOf("{");
  const end = text.lastIndexOf("}");
  if (start === -1 || end <= start) return null;
  try {
    return JSON.parse(text.slice(start, end + 1));
  } catch {
    return null;
  }
}

function json(data, status = 200, extra = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json", ...extra },
  });
}
