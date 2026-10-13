#!/usr/bin/env python3
"""Static snapshot of the local ACS WordPress for internal review.

Crawls http://localhost:8888, rewrites absolute URLs to root-relative, drops
WordPress plumbing that means nothing off a live install, and stamps every page
with a noindex meta and a persistent unapproved-content banner.
"""
import os, re, sys, urllib.parse, urllib.request, collections

SRC  = "http://localhost:8888"
OUT  = sys.argv[1]
# ⚠ Derived at crawl time, not typed. The first version hardcoded "21 August
# 2026" and the 24 August redeploy shipped wearing a three-day-old date — a
# reviewer reading "snapshot of 21 August" on a page corrected on the 24th has
# been told, in the banner built to be trustworthy, that the corrections are
# not there.
import datetime
SNAPSHOT_DATE = datetime.date.today().strftime("%-d %B %Y")

BANNER = """
<div id="acs-review-banner" role="note" aria-label="Internal review notice">
  <strong>INTERNAL REVIEW COPY &mdash; NOTHING ON THIS SITE IS APPROVED.</strong>
  <span>Every word is placeholder copy. The photographs are the sets supplied by Marx Media on 11 and 17 September 2026; none shows a named ACS person, client or workplace. No pricing, legal or trading-history claim here has client sign-off. Snapshot of """ + SNAPSHOT_DATE + """.</span>
</div>
<style>
#acs-review-banner{position:fixed;left:0;right:0;bottom:0;z-index:2147483647;
  background:#1a1200;color:#ffd166;border-top:3px solid #ffb703;
  font:400 13px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;
  padding:10px 20px;display:flex;gap:12px;flex-wrap:wrap;align-items:baseline;
  box-shadow:0 -8px 24px rgba(0,0,0,.35)}
#acs-review-banner strong{color:#fff;letter-spacing:.04em;flex:1 1 auto;min-width:0}
#acs-review-banner span{color:#e8c98a;flex:1 1 320px;min-width:0}
/* Grow the dark footer rather than the body: padding on <body> shows the body's
   own light background as a band beneath the dark footer. */
footer.has-ink-background-color{padding-bottom:136px!important}
@media (max-width:700px){#acs-review-banner{font-size:12px;padding:8px 14px}
  #acs-review-banner strong,#acs-review-banner span{flex:1 1 100%}
  footer.has-ink-background-color{padding-bottom:210px!important}}
@media print{#acs-review-banner{position:static}}
</style>
"""

NOINDEX = '<meta name="robots" content="noindex,nofollow,noarchive,nosnippet">'

# WordPress plumbing that is meaningless on a static host.
DROP_LINK = re.compile(
    r'<link[^>]+(?:rel=["\'](?:alternate|EditURI|wlwmanifest|pingback|https://api\.w\.org/)["\']'
    r'|href=["\'][^"\']*(?:xmlrpc\.php|/feed/|wp-json)[^"\']*["\'])[^>]*>', re.I)
DROP_META_GEN = re.compile(r'<meta name=["\']generator["\'][^>]*>', re.I)
DROP_EMOJI_STYLE = re.compile(r'<style[^>]*id=["\']wp-emoji-styles[^>]*>.*?</style>', re.I | re.S)

seen, queue, assets = set(), collections.deque(), set()
css_refs = set()

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "acs-snapshot"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read(), r.headers.get("Content-Type", "")

def local_path(url):
    """Map an absolute source URL to a path inside OUT."""
    p = urllib.parse.urlsplit(url).path
    if p.endswith("/") or p == "":
        return os.path.join(OUT, p.strip("/"), "index.html")
    return os.path.join(OUT, p.lstrip("/"))

def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)

def rewrite(html):
    # Absolute -> root-relative, so the snapshot works on any hostname.
    html = html.replace(SRC + "/", "/").replace(SRC, "/")
    # Escaped form used inside inline JSON/JS.
    html = html.replace("http:\\/\\/localhost:8888", "")
    html = DROP_LINK.sub("", html)
    html = DROP_META_GEN.sub("", html)
    if "</head>" in html:
        html = html.replace("</head>", NOINDEX + "\n</head>", 1)
    if "</body>" in html:
        html = html.replace("</body>", BANNER + "\n</body>", 1)
    return html

pages = [l.strip() for l in open(sys.argv[2]) if l.strip()]
for u in [SRC + "/"] + pages:
    if u not in seen:
        seen.add(u); queue.append(u)

ASSET_RE = re.compile(r'(?:href|src)=["\']([^"\']+)["\']|url\(([^)]+)\)')

while queue:
    url = queue.popleft()
    try:
        body, ctype = get(url)
    except Exception as e:
        print(f"  !! {url}: {e}"); continue
    if "text/html" not in ctype:
        write(local_path(url), body)
        # ⚠ 2026-09-28: a stylesheet's own url() references were never followed,
        # so an image used ONLY from CSS (the homepage industry cards) was left out
        # of the deploy the day its last <img> use was replaced. Cloudflare then
        # answers the missing file with index.html and status 200, so the card is
        # blank and nothing errors. Follow them, and check them after the crawl.
        if urllib.parse.urlsplit(url).path.endswith(".css"):
            for m in re.finditer(r'url\(\s*["\']?([^"\')]+)["\']?\s*\)', body.decode("utf-8", "replace")):
                raw = m.group(1).strip()
                if raw.startswith(("data:", "#")):
                    continue
                a = urllib.parse.urljoin(url, raw).split("#")[0]
                if a.startswith(SRC) and a not in assets:
                    assets.add(a); queue.append(a); css_refs.add(a)
        continue
    html = body.decode("utf-8", "replace")
    for m in ASSET_RE.finditer(html):
        raw = (m.group(1) or m.group(2) or "").strip().strip('"\'')
        if not raw or raw.startswith(("#", "data:", "mailto:", "tel:", "javascript:")):
            continue
        a = urllib.parse.urljoin(url, raw)
        if not a.startswith(SRC):
            continue
        a = a.split("#")[0]
        path = urllib.parse.urlsplit(a).path
        if any(x in a for x in ("/feed", "wp-json", "xmlrpc", "oembed", "?rsd")):
            continue
        if re.search(r'\.(css|js|jpe?g|png|svg|webp|woff2?|ttf|ico|gif|avif)$', path, re.I):
            if a not in assets:
                assets.add(a); queue.append(a)
    write(local_path(url), rewrite(html).encode("utf-8"))

for extra in ("/wp-includes/js/twemoji.js", "/wp-includes/js/wp-emoji.js"):
    try:
        body, _ = get(SRC + extra)
        write(os.path.join(OUT, extra.lstrip("/")), body)
        assets.add(SRC + extra)
    except Exception as e:
        print(f"  !! {extra}: {e}")

write(os.path.join(OUT, "robots.txt"), b"User-agent: *\nDisallow: /\n")
html_count = sum(1 for r, _, fs in os.walk(OUT) for f in fs if f.endswith(".html"))
print(f"pages: {html_count}  assets: {len(assets)}")

missing = [a for a in sorted(css_refs) if not os.path.exists(local_path(a))]
print(f"stylesheet images: {len(css_refs)}, missing from the snapshot: {len(missing)}")
if missing:
    sys.exit("REFUSING TO DEPLOY - stylesheet images not captured:\n  " + "\n  ".join(missing))
