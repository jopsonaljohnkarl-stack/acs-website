/*
 * Scan every launch page's rendered DOM for top-level content sections that
 * carry no visual device (card, glass panel, photo split, ruled columns,
 * pull card, accordion, etc.) — the "flat white wall of words" pattern.
 *
 * 1. ./a11y/serve-axe.sh is NOT required here (no axe dependency), but the
 *    page must be served by wp-env on :8888.
 * 2. open http://localhost:8888/ and paste this whole file into the console
 * 3. await runAll()
 *
 * ⚠ SAME IFRAME GOTCHAS AS run-in-browser.js:
 *   - sandbox the iframe (allow-same-origin allow-scripts) or a page with
 *     top-window navigation logic can hijack the visible tab with zero error
 *     output (hit once building the Day 26 flatness sweep).
 *   - content sections live under .wp-block-post-content > .wp-block-group,
 *     not directly under <main> — main > .wp-block-group finds 0 everywhere.
 *   - device-wrapped chains (acs-qa, cards, ruled columns) score as false
 *     positives unless their device markers are excluded explicitly. This
 *     scanner only flags CANDIDATES; eyeball the rendered page before
 *     touching anything (the markup scanner's job is narrowing 56 pages
 *     down to a handful, not being the final word).
 */
const DEVICE_CLASS = /\bacs-(band|byt|calc|choice|choices|compare|consent|contact-list|faq|field|form|glass|hero|included|index|levels|logo|masthead|optional|pair-glass|pair-zone|points|problem|pull|pull-up|qa|role|roles|schedule|shot|spec|split|stack|step|steps|surface-action|surface-field|surface-ink|surface-structure|tagline|ticks)\b/;

function classifySection(el) {
  const html = el.outerHTML;
  if (DEVICE_CLASS.test(html)) return { flat: false, reason: 'device-class' };
  if (el.querySelector('img, figure, svg')) return { flat: false, reason: 'media' };
  if (el.querySelector('[style*="border-top"]')) return { flat: false, reason: 'ruled-columns' };
  if (el.querySelector('.wp-block-column[style*="background"]')) return { flat: false, reason: 'panel' };
  if (el.querySelector('details, .wp-block-details')) return { flat: false, reason: 'accordion' };
  const text = (el.innerText || '').replace(/\s+/g, ' ').trim();
  if (text.length < 200) return { flat: false, reason: 'short' };
  const paraChars = Array.from(el.querySelectorAll('p'))
    .reduce((sum, p) => sum + (p.innerText || '').trim().length, 0);
  if (paraChars / Math.max(text.length, 1) < 0.55) return { flat: false, reason: 'not-prose-dominant' };
  return { flat: true, reason: `prose ${text.length} chars`, sample: text.slice(0, 90) };
}

async function scanPage(url) {
  const frame = document.createElement('iframe');
  frame.setAttribute('sandbox', 'allow-same-origin allow-scripts');
  frame.style.cssText = 'width:1280px;height:900px;position:fixed;left:-9999px;top:0;border:0';
  document.body.appendChild(frame);
  try {
    await new Promise((res, rej) => {
      frame.onload = res;
      frame.src = url + (url.includes('?') ? '&' : '?') + 'cb=' + Date.now();
      setTimeout(() => rej(new Error('timeout loading ' + url)), 20000);
    });
    const doc = frame.contentDocument;
    doc.documentElement.classList.remove('js-motion');
    doc.querySelectorAll('[data-acs-reveal]').forEach((el) => el.classList.add('is-revealed'));
    await new Promise((r) => setTimeout(r, 150));
    const root = doc.querySelector('.wp-block-post-content');
    if (!root) return { candidates: [], sections: 0, note: 'no .wp-block-post-content' };
    const sections = Array.from(root.children).filter((el) => el.classList.contains('wp-block-group'));
    const candidates = [];
    sections.forEach((el, i) => {
      const c = classifySection(el);
      if (c.flat) candidates.push({ index: i, reason: c.reason, sample: c.sample });
    });
    return { candidates, sections: sections.length };
  } finally {
    frame.remove();
  }
}

async function runAll(urls) {
  if (!urls) {
    const res = await fetch('/wp-json/wp/v2/pages?per_page=100&_fields=link');
    urls = (await res.json()).map((p) => new URL(p.link).pathname);
  }
  const results = {}, errors = {};
  for (const url of urls) {
    try { results[url] = await scanPage(url); } catch (e) { errors[url] = String(e.message || e); }
  }
  const flagged = Object.entries(results).filter(([, v]) => v.candidates && v.candidates.length);
  console.log(`${Object.keys(results).length} pages scanned, ${flagged.length} with flat-section candidates`);
  for (const [url, r] of flagged) {
    console.group(url + ` (${r.sections} sections)`);
    r.candidates.forEach((c) => console.log(`section[${c.index}] · ${c.reason} · "${c.sample}…"`));
    console.groupEnd();
  }
  if (Object.keys(errors).length) console.warn('pages that could not be tested', errors);
  return { tested: Object.keys(results).length, flagged: flagged.length, errors, results };
}
