#!/usr/bin/env bash
#
# Launch checks against a RUNNING site, over HTTP. Read-only: GET and HEAD only,
# no logins, no form posts.
#
#   ./check-prod.sh https://allcommercialservices.com.au
#   ./check-prod.sh http://localhost:8888                # proves the script on the local site
#   ./check-prod.sh BASE_URL --pending=410               # if Dan picks 410 for the cleaning-era rows
#
# check-site.sh is the static check of the files in this folder and takes no
# URL; this is its counterpart for the deployed site. Run both (PRODUCTION-MOVE.md §3).
#
# Sections (each prints ok / FAIL / SKIP; exit 1 if anything FAILs):
#   1. every REDIRECTS.md row: old URL -> expected status and target
#      (parsed by htaccess-redirects.py, so generated and tested rules agree)
#   2. https + certificate, http:// and www. redirect to the canonical host
#      (SKIP on localhost / an IP / an http:// base)
#   3. robots.txt allows crawling and names the sitemap
#   4. the sitemap exists, lists only this host, and no SAMPLE / template-preview
#   5. every page in the sitemap: 200, no noindex, and none of: SAMPLE, LEGAL DRAFT,
#      the review banner, unresolved [Confirm ...] / "to be confirmed" notes,
#      localhost / 127.0.0.1 (the localhost scan SKIPs when the base is localhost)
#   6. /template-preview/ is gone
#
set -uo pipefail
cd "$(dirname "$0")"
[ -n "${1:-}" ] || { sed -n '6,9p' "$0"; exit 2; }
exec python3 - "$@" <<'PY'
import importlib.util, re, ssl, sys, urllib.error, urllib.parse, urllib.request

args = [a for a in sys.argv[1:] if not a.startswith("--")]
pending = "410" if "--pending=410" in sys.argv else "301"
BASE = args[0].rstrip("/")
u = urllib.parse.urlsplit(BASE)
HOST = u.hostname
LOCAL = HOST in ("localhost", "127.0.0.1") or re.fullmatch(r"[\d.]+", HOST or "") is not None

spec = importlib.util.spec_from_file_location("hr", "htaccess-redirects.py")
hr = importlib.util.module_from_spec(spec); spec.loader.exec_module(hr)

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k): return None
opener = urllib.request.build_opener(NoRedirect)
UA = {"User-Agent": "acs-check-prod/1"}

def fetch(url, method="GET"):
    """(status, location, body) without following redirects. Raises only on network errors."""
    req = urllib.request.Request(url, headers=UA, method=method)
    try:
        r = opener.open(req, timeout=20)
        return r.status, r.headers.get("Location"), r.read().decode("utf-8", "replace") if method == "GET" else ""
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace") if method == "GET" else ""
        return e.code, e.headers.get("Location"), body

fails = 0
def report(ok, msg, skip=False):
    global fails
    tag = "SKIP" if skip else ("ok  " if ok else "FAIL")
    if not ok and not skip: fails += 1
    print(f"  {tag}  {msg}")

def same_target(loc, target):
    if loc is None: return False
    p = urllib.parse.urlsplit(urllib.parse.urljoin(BASE + "/", loc))
    return p.netloc == u.netloc and (p.path or "/") == target and not p.query

print(f"ACS production checks against {BASE}\n")

# 1. Redirect map
print("1. REDIRECTS.md")
for src, status, target, is_pending in hr.expectations(hr.parse(), pending):
    url = BASE + ("/" + src if src.startswith("?") else src)
    try:
        code, loc, _ = fetch(url, "GET")
    except Exception as e:
        report(False, f"{src}: {e}"); continue
    if status == 301 and src == target:
        report(code == 200, f"{src} -> {code} (same URL on the same domain: expect 200)"); continue
    note = "  [pending Dan: 301 to Home or 410]" if is_pending else ""
    if status == 410:
        report(code == 410, f"{src} -> {code} (expect 410){note}")
    else:
        ok = code == status and same_target(loc, target)
        report(ok, f"{src} -> {code} {loc or ''} (expect {status} {target}){note}")
code, _, _ = fetch(BASE + "/acs-check-prod-unknown-path/")
report(code == 404, f"unknown path -> {code} (expect 404, never a catch-all redirect)")

# 2. HTTPS and canonical host
print("\n2. HTTPS and canonical host")
if LOCAL or u.scheme != "https":
    report(True, "base is local or not https; certificate and canonicalisation not testable here", skip=True)
else:
    try:
        code, _, _ = fetch(BASE + "/", "HEAD")
        report(code == 200, f"https://{HOST}/ -> {code} with a certificate Python trusts")
    except ssl.SSLError as e:
        report(False, f"certificate: {e}")
    except Exception as e:
        report(False, f"https://{HOST}/: {e}")
    for variant in (f"http://{HOST}/", f"https://www.{HOST}/", f"http://www.{HOST}/"):
        try:
            code, loc, _ = fetch(variant, "HEAD")
            report(code == 301 and loc in (f"https://{HOST}/", f"https://{HOST}"), f"{variant} -> {code} {loc or ''} (expect 301 https://{HOST}/)")
        except Exception as e:
            report(False, f"{variant}: {e}")

# 3. robots.txt
print("\n3. robots.txt")
code, _, robots = fetch(BASE + "/robots.txt")
report(code == 200, f"robots.txt -> {code}")
blocked = re.search(r"^\s*Disallow:\s*/\s*$", robots, re.M)
report(not blocked, "does not Disallow: / (search visibility is on)" if not blocked else "Disallow: / present: Settings > Reading still discourages search engines")
sm = re.search(r"^\s*Sitemap:\s*(\S+)", robots, re.M | re.I)
report(bool(sm) and urllib.parse.urlsplit(sm.group(1)).netloc == u.netloc,
       f"Sitemap line: {sm.group(1) if sm else 'missing'}")

# 4. Sitemap
print("\n4. sitemap")
pages, seen, queue = [], set(), [BASE + "/wp-sitemap.xml"]
while queue:
    sm_url = queue.pop(0)
    if sm_url in seen: continue
    seen.add(sm_url)
    code, _, xml = fetch(sm_url)
    if code != 200:
        report(False, f"{sm_url} -> {code}"); continue
    locs = re.findall(r"<loc>([^<]+)</loc>", xml)
    if "<sitemapindex" in xml: queue += locs
    else: pages += locs
report(bool(pages), f"wp-sitemap.xml lists {len(pages)} URLs across {len(seen)} files")
foreign = [p for p in pages if urllib.parse.urlsplit(p).netloc != u.netloc]
report(not foreign, f"every URL is on {u.netloc}" + (f" (not: {foreign[:3]})" if foreign else ""))
bad = [p for p in pages if re.search(r"template-preview|/sample-|/blog/|/vacancies-list/|/hello-world/", p)]
report(not bad, "no SAMPLE or template-preview URLs" + (f" (found {len(bad)}: {bad[:4]})" if bad else ""))

# 5. Published pages
print("\n5. published pages")
PATTERNS = [
    ("SAMPLE", r"\bSAMPLE\b"),
    ("LEGAL DRAFT", r"LEGAL DRAFT"),
    ("review banner", r"acs-review-banner|INTERNAL REVIEW COPY"),
    ("[Confirm ...] / to-be-confirmed note", r"\[(?:Confirm|Solicitor to confirm)[^\]]*\]|to be confirmed\]"),
    ("legal date placeholder", r"\[DD Month YYYY\]"),
    ("noindex", r"<meta[^>]+name=['\"]robots['\"][^>]+noindex"),
]
if not LOCAL:
    PATTERNS.append(("localhost", r"localhost|127\.0\.0\.1"))
hits = {name: [] for name, _ in PATTERNS}
non200 = []
for p in pages:
    code, _, html = fetch(p)
    if code != 200: non200.append(f"{p} {code}"); continue
    for name, pat in PATTERNS:
        n = len(re.findall(pat, html))
        if n: hits[name].append(f"{urllib.parse.urlsplit(p).path} ({n})")
report(not non200, f"{len(pages) - len(non200)}/{len(pages)} sitemap pages return 200" + (f"; not: {non200[:4]}" if non200 else ""))
for name, found in hits.items():
    report(not found, f"no {name}" if not found else f"{name} on {len(found)} page(s): {', '.join(found[:6])}{' ...' if len(found) > 6 else ''}")
if LOCAL:
    report(True, "localhost scan (base is localhost)", skip=True)

# 6. Template preview removed
print("\n6. template preview")
code, _, _ = fetch(BASE + "/template-preview/")
report(code in (404, 410), f"/template-preview/ -> {code} (expect 404)")

print("\nPASS" if fails == 0 else f"\nFAIL ({fails})")
sys.exit(1 if fails else 0)
PY
