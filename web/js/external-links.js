/** External reading — Sefaria (English) + Hachi Garsinan (manuscripts). */

export function sefariaSlug(ref) {
  if (!ref) return "";
  return ref.trim().replace(/\s+/g, "_");
}

/** Bilingual Hebrew + English on Sefaria. */
export function sefariaUrl(ref) {
  const slug = sefariaSlug(ref);
  return slug ? `https://www.sefaria.org/${encodeURIComponent(slug)}?lang=bi` : "";
}

/** English-primary view on Sefaria. */
export function sefariaEnglishUrl(ref) {
  const slug = sefariaSlug(ref);
  return slug ? `https://www.sefaria.org/${encodeURIComponent(slug)}?lang=en` : "";
}

/** Manuscript witness index (not every daf has a direct deep link). */
export function garsinanUrl() {
  return "https://bavli.genizah.org/";
}

export const EXTERNAL_NOTE =
  "This site shows witness-restored Hebrew. Sefaria adds English but often follows Vilna print — on censored loci the wording may differ (e.g. עובדי כוכבים vs גוים). Use both: English to understand, this build to see what was suppressed.";

export const EXTERNAL_NOTE_SHORT =
  "Sefaria = English (may reflect print censorship). This site = restored Hebrew.";

/**
 * @param {string} ref
 * @param {{ compact?: boolean }} opts
 */
export function externalLinksHtml(ref, opts = {}) {
  if (!ref) return "";
  const sef = sefariaUrl(ref);
  const sefEn = sefariaEnglishUrl(ref);
  const gar = garsinanUrl();
  if (opts.compact) {
    return (
      `<span class="ext-links">` +
      `<a href="${sef}" target="_blank" rel="noopener">English (Sefaria)</a>` +
      ` · <a href="${gar}" target="_blank" rel="noopener">Manuscripts</a>` +
      `</span>`
    );
  }
  return (
    `<div class="ext-panel">` +
    `<p class="ext-note">${EXTERNAL_NOTE}</p>` +
    `<p class="ext-links">` +
    `<a href="${sefEn}" target="_blank" rel="noopener">Sefaria — English</a>` +
    ` · <a href="${sef}" target="_blank" rel="noopener">Sefaria — Hebrew + English</a>` +
    ` · <a href="${gar}" target="_blank" rel="noopener">Hachi Garsinan — manuscript witnesses</a>` +
    `</p></div>`
  );
}
