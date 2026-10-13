/*
 * Run axe against every launch page and report violations.
 *
 * 1. ./a11y/serve-axe.sh
 * 2. open http://localhost:8888/ and paste this whole file into the console
 * 3. await runAll()
 *
 * ⚠ TWO THINGS THIS HARNESS GETS RIGHT THAT A NAIVE ONE DOES NOT, both found
 * the hard way on 2026-08-24:
 *
 * 1. IT SETTLES THE REVEAL ANIMATION FIRST. Offscreen in an iframe the
 *    IntersectionObserver never fires, so every [data-acs-reveal] block sits at
 *    opacity 0 or mid-transition forever. axe blends partial opacity into the
 *    background and reports contrast failures that no visitor can ever see. The
 *    first run of this reported four "serious" contrast defects on the home
 *    page that were entirely an artefact of the harness, and nearly produced a
 *    fix to a colour token measuring a perfectly good 6.03:1.
 *
 * 2. IT CACHE-BUSTS. A CSS fix is invisible to a cached iframe, so a re-run
 *    after a change can confirm a defect that is already gone.
 *
 * ⚠ WHAT IT STILL CANNOT DO: text over a photograph. axe parses colour strings
 * and cannot see an image, so white text on a scrimmed photo reads as ~1.07:1.
 * Those are measured separately by compositing the image with its scrim on a
 * canvas and reading the pixels back — see DESIGN.md, "Measured, not asserted".
 * A 1.0-something ratio in these results is that artefact, not a defect.
 */
const A11Y_TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'];

async function auditPage(url) {
  const frame = document.createElement('iframe');
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
    await new Promise((r) => setTimeout(r, 250));
    await new Promise((res, rej) => {
      const s = doc.createElement('script');
      s.src = 'http://127.0.0.1:8899/axe.min.js';
      s.onload = res;
      s.onerror = () => rej(new Error('axe failed to load — is serve-axe.sh running?'));
      doc.head.appendChild(s);
      setTimeout(() => rej(new Error('timeout injecting axe')), 20000);
    });
    const result = await frame.contentWindow.axe.run(doc, { runOnly: { type: 'tag', values: A11Y_TAGS } });
    return result.violations.map((v) => ({
      id: v.id,
      impact: v.impact,
      nodes: v.nodes.length,
      help: v.help,
      sample: v.nodes.slice(0, 2).map((n) => n.target.join(' ') + ' :: ' +
        (n.failureSummary || '').split('\n').filter(Boolean).slice(-1)[0]),
    }));
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
    try { results[url] = await auditPage(url); } catch (e) { errors[url] = String(e.message || e); }
  }
  const failing = Object.entries(results).filter(([, v]) => v.length);
  console.log(`${Object.keys(results).length} pages tested, ${failing.length} with violations`);
  for (const [url, vs] of failing) {
    console.group(url);
    vs.forEach((v) => console.log(`${v.impact} · ${v.id} · ${v.nodes} node(s)`, v.sample));
    console.groupEnd();
  }
  if (Object.keys(errors).length) console.warn('pages that could not be tested', errors);
  return { tested: Object.keys(results).length, failing: failing.length, errors };
}
