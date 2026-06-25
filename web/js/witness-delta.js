/** Render English witness-delta block for English-only readers. */

function trustLabel(level) {
  if (level === "high") return "Sefaria English: generally OK here";
  if (level === "medium") return "Sefaria English: compare carefully";
  return "Sefaria English: often follows Vilna — compare to notes below";
}

function trustClass(level) {
  if (level === "high") return "trust-high";
  if (level === "medium") return "trust-medium";
  return "trust-low";
}

export function renderWitnessDelta(loc, { compact = false } = {}) {
  const d = loc?.witness_delta;
  if (!d) return "";

  const trust = d.sefaria_trust || "medium";
  if (compact) {
    return (
      `<div class="witness-delta compact">` +
      `<p class="plain"><strong>In plain English:</strong> ${escapeHtml(d.plain_english)}</p>` +
      `<p class="trust ${trustClass(trust)}">${escapeHtml(trustLabel(trust))}</p>` +
      `</div>`
    );
  }

  return (
    `<div class="witness-delta">` +
    `<h4>What you can trust in English</h4>` +
    `<p class="plain"><strong>In plain English:</strong> ${escapeHtml(d.plain_english)}</p>` +
    `<dl>` +
    `<dt>Standard Vilna / typical English base</dt>` +
    `<dd>${escapeHtml(d.vilna_standard)}</dd>` +
    `<dt>Witness manuscripts (this build)</dt>` +
    `<dd>${escapeHtml(d.witness_reading)}</dd>` +
    `</dl>` +
    `<p class="trust ${trustClass(trust)}"><strong>${escapeHtml(trustLabel(trust))}.</strong> ${escapeHtml(d.sefaria_note || "")}</p>` +
    `</div>`
  );
}

function escapeHtml(s) {
  return String(s || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

/** Find locus row for a daf ref. */
export function locusForRef(loci, ref) {
  if (!ref || !loci?.length) return null;
  return loci.find((x) => x.ref === ref) || null;
}
