#!/usr/bin/env bash
#
# Site integrity checks that are not about the lead-capture contract.
#
# ⚠ EACH CASE HERE EXISTS BECAUSE THE DEFECT HAPPENED. This is not a checklist
# of good practice; it is a list of things that shipped and were caught late.
#
#   ./check-site.sh
#
set -uo pipefail
cd "$(dirname "$0")"
fail=0

echo "ACS site integrity"
echo

python3 - <<'PY' || fail=1
import re, glob, struct, sys

def jpeg_size(path):
    # PNG (the cut-out photographs, 2 Oct 2026): width and height sit in the IHDR chunk.
    with open(path, 'rb') as _f:
        _head = _f.read(24)
    if _head[:8] == b'\x89PNG\r\n\x1a\n':
        import struct as _st
        return _st.unpack('>II', _head[16:24])
    with open(path, 'rb') as f:
        f.read(2)
        while True:
            b = f.read(1)
            while b and b != b'\xff': b = f.read(1)
            m = f.read(1)
            while m == b'\xff': m = f.read(1)
            if not m: return None
            if m in (b'\xc0',b'\xc1',b'\xc2',b'\xc3',b'\xc5',b'\xc6',b'\xc7',b'\xc9',b'\xca',b'\xcb',b'\xcd',b'\xce',b'\xcf'):
                f.read(3)
                h, w = struct.unpack('>HH', f.read(4))
                return w, h
            ln = struct.unpack('>H', f.read(2))[0]
            f.read(ln - 2)

files = glob.glob('acs/templates/*.html') + glob.glob('acs/parts/*.html') + glob.glob('content/*.html')
bad = []

# ⚠⚠ A BLOCK DELIMITER IS ITSELF AN HTML COMMENT. `<!-- wp:navigation {...} /-->`
# is live markup that WordPress parses, and `<!-- a note to the copy team -->` is
# documentation. Stripping "comments" indiscriminately removes both.
#
# That is not hypothetical: the first version of this file stripped everything,
# which made the database-id check unable to see the exact bug it was written
# for - the id lived inside a block delimiter. **It passed a deliberate break**,
# and only breaking it revealed that. A guard that cannot fail is not a guard.
PROSE_COMMENT = re.compile(r'<!--(?!\s*/?wp:).*?-->', re.S)

def live(path):
    """Markup with the documentation removed and the block delimiters kept."""
    return PROSE_COMMENT.sub('', open(path).read())

# 1. Declared image dimensions must match the real file.
#
#    ⚠ Every <img> on the site declared 1600x1000 because the first one did and
#    the rest were copied. shot-4.jpg is 1600x2399 - a PORTRAIT image declared
#    as landscape. Wrong dimensions are what the browser reserves space from,
#    so this is a layout-shift bug that hides until the CSS aspect-ratio is
#    touched. It will be wrong again the day real photography replaces these,
#    which is the reason this check exists rather than a one-off correction.
for p in files:
    s = open(p).read()
    for tag in re.findall(r'<img\b[^>]*>', s):
        m = re.search(r'assets/img/([^"\']+)', tag)
        if not m: continue
        real = jpeg_size('acs/assets/img/' + m.group(1))
        if not real: continue
        w = re.search(r'width="(\d+)"', tag)
        h = re.search(r'height="(\d+)"', tag)
        if not w or not h:
            bad.append(f"{p}: {m.group(1)} has no width/height"); continue
        if (int(w.group(1)), int(h.group(1))) != real:
            bad.append(f"{p}: {m.group(1)} declared {w.group(1)}x{h.group(1)}, file is {real[0]}x{real[1]}")

# 2. Editor guidance must never render as body copy.
#
#    ⚠ Two notes containing the words "not for publication" were printing on
#    pages a client was going to be shown.
for p in files:
    s = open(p).read()
    if 'EDITOR NOTE' in live(p):
        bad.append(f"{p}: an EDITOR NOTE is outside a comment and will render")

# 3. novalidate must never be in the markup.
#
#    ⚠ It was, which meant that with JavaScript off the forms had no validation
#    at all - the opposite of the progressive enhancement the script claimed.
for p in files:
    for tag in re.findall(r'<form\b[^>]*>', live(p)):
        if 'novalidate' in tag:
            bad.append(f"{p}: <form> hard-codes novalidate; forms.js sets it")

# 4. No database row id may be written into a git-tracked template.
#
#    ⚠ parts/header.html carried {"ref":19}, a navigation post id, to be
#    restored onto a database where that id does not exist.
#    ⚠ PROSE COMMENTS ARE STRIPPED, BLOCK DELIMITERS ARE NOT. The first run
#    failed on header.html's own explanation of the bug, which quotes the id it
#    removed; the first fix then stripped block delimiters too and the check
#    stopped working entirely. See the note on PROSE_COMMENT above.
for p in files:
    for m in re.finditer(r'"ref"\s*:\s*\d+', live(p)):
        bad.append(f"{p}: hard-codes a database id ({m.group(0)})")

# 5. No decorative counter, anywhere.
#
#    ⚠⚠ THIS CORRECTION HAS BEEN MADE THREE TIMES. First the clause numbers on
#    section labels, then the reference numbers on the directory cards, then the
#    step references and the schedule counter. Each time the defence was that
#    the number enumerates a real set - eight inclusions, four stages - and each
#    time it did not survive contact with the page: the heading already states
#    the count, and a reader cannot act on "03".
#
#    ⚠ ONLY DECORATION IS BANNED. "2008" is the heritage claim the whole
#    positioning rests on; the register row references (Legal 1.0, Systems 4.0)
#    are internal scaffolding inside PLACEHOLDER notes and are how a gap stays
#    traceable; and "Step 1 of 5" in the configurator is a progress indicator
#    inside an aria-live region. None of those is what this rule is about.
BANNED = ('acs-steps__ref', 'acs-index__ref', 'counter(acs-item', 'counter-increment')
for p in files + ['acs/style.css']:
    text = open(p).read()
    live_text = PROSE_COMMENT.sub('', text)
    for token in BANNED:
        if token in live_text:
            bad.append(f"{p}: decorative counter is back ({token})")

# 6. No unverified trading-history claim, EXCEPT where one is attributed.
#
#    ⚠⚠ "since 2008" WAS WRITTEN ONTO FOUR PAGES on 2026-08-20 and removed the
#    same day. Register row Proof 1.0 - what may be stated factually about
#    trading history - is unanswered, and Dan's 2026-08-11 direction says in
#    terms "leave it out, no unverified figures".
#
#    ⚠⚠ REVERSED IN PART on 2026-08-21, on John's explicit instruction, after
#    Janet's Tier 1 copy (17 Aug 2026) was found to use the claim. The guard was
#    NOT deleted. It now carries an ALLOWLIST: the exact sentence Janet wrote,
#    only on the files where she wrote it. Any other phrasing, any other page,
#    and any other year still fails.
#
#    ⚠ THE ALLOWLIST IS ATTRIBUTION, NOT APPROVAL. Janet is Marx Media side;
#    her documents' "confirmed against the agreed proposal" is her own
#    assurance. Proof 1.0 is still unanswered and Dan's direction still says
#    leave it out. Provenance and the open question: COPY-PROVENANCE.md.
#    If Chris answers differently this is one revert, not a hunt.
#
#    ⚠ The heritage story is the STRONGEST thing this site has, because no
#    figures about clients, staff, savings or outcomes may be published at all.
#    That is exactly why it is the thing most easily overclaimed, and why this
#    check exists rather than a note in a document nobody re-reads.

# Attributed exceptions: file -> the exact strings permitted in it.
# Sourced from Janet Biag's Tier 1 copy, 17 August 2026. Verbatim, not paraphrased.
ATTRIBUTED = {
    # ⚠ THE FRONT PAGE RENDERS THE TEMPLATE, NOT content/home.html. Both files
    # carried the same paragraph and only the template reaches the browser;
    # editing the content file alone changed nothing and looked like it had.
    # Both are listed so neither can drift away from the other unnoticed.
    'acs/templates/front-page.html': [
        'ACS has run commercial services for Australian businesses since 2008.',
        # Batch 1 rev 2 Home §2 trust strip ("ACS_Home v2.docx", 17 Aug 2026),
        # applied as written 2026-08-26 per John's 2026-08-25 decision. Same
        # attribution-not-approval status: Proof 1.0 is still open with Chris.
        'Running Australian commercial services since 2008',
    ],
    'content/home.html': [
        'ACS has run commercial services for Australian businesses since 2008.',
    ],
    # ⚠⚠ BATCH 5, 15 September 2026. Ernest's Our Story and Why ACS documents
    # build the whole page on the trading history: it is the H1, the hero, a
    # section heading and an FAQ answer. APPROVED IN WRITING BY DAN BANKS
    # ("approved as presented", 15 Sep 04:14 PHT) and by NOBODY ELSE.
    #
    # ⚠ CHRIS HAS NOT APPROVED IT, and Proof 1.0 is still unanswered. Dan's own
    # 2026-08-11 direction said leave the year out; his 15 September approval of
    # these pages is the later instruction and it is the sponsor's, not the
    # commercial and risk owner's. These sentences are on the PASSWORD-PROTECTED
    # REVIEW SITE only. They do not publish until Chris signs Proof 1.0.
    # Full list of flagged claims: COPY-PROVENANCE.md, Batch 5 and 6.
    'content/our-story.html': [
        'ACS has run Australian commercial services since 2008',
        'This is ACS company history since 2008, before offshore staffing was ever part of the business.',
        'What we can say factually is that ACS has operated in Australian commercial services since 2008.',
    ],
    'content/why-acs.html': [
        'Operating history since 2008, not just a staffing background',
        'ACS has run commercial services for Australian businesses since 2008.',
    ],
}
CLAIMS = [
    (r'\bsince\s+(?:19|20)\d{2}\b',            'a founding or trading-since year'),
    (r'\bestablished\s+(?:in\s+)?(?:19|20)\d{2}', 'an established-in year'),
    (r'\b(?:19|20)\d{2}\s*(?:©|&copy;)',        'a copyright year'),
    (r'\b\d+\+?\s*years?\s+(?:of\s+)?(?:experience|trading|operating)', 'a years-of-experience claim'),
    (r'\b(?:over|more than)\s+\d[\d,]*\s+(?:clients|businesses|staff|team members)', 'a client or staff count'),
]
for p in files:
    text = PROSE_COMMENT.sub('', open(p).read())
    # Blank out the attributed sentences so the patterns below cannot see them.
    # Anything that is not an exact match survives and is still caught.
    for allowed in ATTRIBUTED.get(p, []):
        if allowed not in text:
            bad.append(f"{p}: attributed claim is allowlisted but MISSING from the page — \"{allowed}\"")
        text = text.replace(allowed, '')
    for pattern, what in CLAIMS:
        for m in re.finditer(pattern, text, re.I):
            bad.append(f"{p}: {what} — \"{m.group(0)}\" (register row Proof 1.0 is unanswered; "
                       f"attributed exceptions are listed in COPY-PROVENANCE.md)")

# 6a. The terms Janet's own copy deliberately excludes.
#
#    ⚠ SOURCE: the keyword table in each of Janet Biag's five Tier 1 documents
#    (17 August 2026) carries a "deliberately excluded" list. These are her
#    exclusions, not a style preference invented here — a location name, a
#    savings percentage and a placement timeframe are each a claim the business
#    has not agreed to make, and two of the three are the kind a buyer can hold
#    it to.
#
#    ⚠ Her copy also flags two things inside the prose itself: hours of
#    availability must be confirmed with Chris before anything publishes, and no
#    placement timeframe publishes because no verified figure exists.
#
#    ⚠ THE SITE WAS CLEAN ON ALL FIVE WHEN THIS WAS WRITTEN (2026-08-24, 54
#    files and the manifest, zero hits). That is the point: this locks a state
#    that is already correct, before nine writing days of real copy land on top
#    of it. The two claims that DID reach a page on 08-20 were caught by reading,
#    which is not a control.
EXCLUDED = [
    (r'\b(?:Philippines|Filipino|Manila|Cebu|Pampanga|Clark Freeport)\b',
     'a named delivery location'),
    # ⚠ NO TRAILING \b AFTER THE PERCENT SIGN. "%" and the space after it are
    #   both non-word characters, so \b never matches between them and the first
    #   version of this rule silently caught nothing. Found by breaking it.
    (r'\b\d{1,3}\s?%|\b\d{1,3}\s?(?:per cent|percent)\b',
     'a percentage — if it is a savings figure it is excluded, and no other percentage is approved either'),
    (r'\b(?:save|saving|savings)\b[^.]{0,40}\b(?:\$|\d)',
     'a cost-savings claim'),
    (r'\b(?:within|in as little as|in just|in under)\s+\d+\s*(?:hour|day|week|month)',
     'a placement or delivery timeframe'),
    (r'\b(?:24/7|24-7|24 hours|round[- ]the[- ]clock|around the clock)\b',
     'an hours-of-availability claim (Janet: confirm with Chris what hours are genuinely available)'),
]
#    ⚠ THIS ONE READS VISIBLE PROSE, NOT THE FILE. The claims check above can
#    work on raw markup because its patterns are word-shaped, but "58%" is a
#    column width: `<!-- wp:column {"width":"58%"} -->` and
#    `style="flex-basis:58%"` are on nearly every page. The first version of
#    this rule read the file and reported six layout values as savings claims.
#    A guard that cries wolf on the site's own grid gets switched off.
def _visible(_s):
    _s = re.sub(r'<!--.*?-->', ' ', _s, flags=re.S)   # ALL comments: notes AND block delimiters
    _s = re.sub(r'<[^>]+>', ' ', _s)                  # tags, so style="" and data-* cannot match
    return re.sub(r'\s+', ' ', _s)

_pages = [(p, _visible(open(p).read())) for p in files]
import json as _json_excl
for _e in _json_excl.load(open('content/pages.json')):
    _pages.append((f"pages.json:{_e['slug']}",
                   ' '.join(str(_e.get(k) or '') for k in ('title', 'description', 'excerpt'))))
for _where, _text in _pages:
    for _pattern, _what in EXCLUDED:
        for _m in re.finditer(_pattern, _text, re.I):
            bad.append(f"{_where}: {_what} — \"{_m.group(0)}\" "
                       f"(excluded by Janet's Tier 1 keyword tables, 17 Aug 2026)")

# 6e. Chris's engagement-model terms, banned 2026-08-24 (thread "ACS website").
#
#    ⚠ Attribution corrected same day: first recorded as Dan's email; the sender
#    is CHRIS, the commercial and risk owner.
#
#    ⚠ THE PROVIDER IS NOT THE EMPLOYER OF RECORD AND NOBODY IS ANYONE'S
#    EMPLOYEE. Team members are independent contractors engaged through the
#    provider. Before this correction, 10 files rendering on 17 of 41 pages
#    described an employment relationship that does not exist, and Janet's five
#    Tier 1 documents carry the same wording — so the banned terms WILL arrive
#    again inside pasted copy. That is what this check is for.
#
#    The list is his list from the email, verbatim in spirit, not a broader
#    word-family ban: "who employs your staff" as a question label and "you
#    employ nobody" as a denial are both allowed, which is why there is no
#    blanket \bemploy\w* rule here.
CHRIS_BANNED = [
    (r'employer of record',                       'employer-of-record wording'),
    (r'\bemployees?\b',                           '"employee"'),
    (r'\b(?:formally|properly)\s+employed\b',    'a formally/properly-employed claim'),
    (r'\blocal\s+payroll\b|\bpayroll\b',        'payroll wording'),
    (r'\bstatutory\s+contributions?\b',          '"statutory contributions"'),
    (r'employment[- ]law|employment\s+obligations|employment\s+administration|employment\s+structure|\bthe\s+employment\b',
                                                  'an employment-relationship claim'),
    (r'\blocal\s+HR\b',                          '"local HR"'),
    (r'\blabour\s+law\b',                        'labour-law wording'),
    (r'works?\s+your\s+hours',                    '"works your hours" (use "works to agreed Australian client hours")'),
]
#    "Contractor" is banned in marketing copy but REQUIRED, once, as the
#    disclosure. Same mechanism as Janet's ATTRIBUTED sentences in 6: the exact
#    disclosure wording is allowed on the two disclosure surfaces and nowhere
#    else, so marketing copy cannot drift into freelancer framing while the
#    site keeps its accurate disclosure.
#    One exception, exact-string like ATTRIBUTED: the bookkeeper role prepares
#    the CLIENT'S OWN payroll. That is the service being sold, not a claim about
#    how the team member is engaged, and renaming the task would misdescribe it.
#    Second exception, 2026-09-16: the Batch 2 inclusions list, approved by
#    Chris and Dan, includes "Onboarding and contractor payments". That is the
#    PROVIDER'S function described in Chris's own vocabulary (his rule bans
#    calling PEOPLE contractors in marketing), and the 25 Aug audit said 6e
#    would need this exact update the day that copy was applied. Exact string,
#    that file only.
CHRIS_TASK_EXCEPTIONS = {
    # 'content/bookkeepers.html' removed 2026-10-01: the approved Batch 4 copy
    # replaced the placeholder that carried "Payroll preparation."; no payroll
    # wording remains on the page, so the exception would only mask a future one.
    'content/what-is-included.html': ['Onboarding and contractor payments'],
}
#    ⚠⚠ THE BATCH 5/6 CONFLICT, 15 September 2026, AND IT IS A REAL ONE.
#    Ernest's Performance and Reporting, Why ACS, How Your Team Is Supported and
#    Your Australian Team documents (23-24 August) were written BEFORE, or
#    alongside, Chris's 24 August engagement-model correction and they describe
#    the delivery partner in exactly the terms he banned: payroll, statutory
#    contributions, local HR, employment administration.
#
#    ⚠ DAN BANKS APPROVED THESE PAGES AS PRESENTED (15 Sep 04:14 PHT, thread
#    "Re: ACS Website"). CHRIS HAS NOT REPLIED. Dan is the executive sponsor;
#    CHRIS IS THE COMMERCIAL AND RISK OWNER AND THIS IS HIS CORRECTION being
#    overridden — on a password-protected review site, for him to read.
#
#    ⚠ THESE EXACT SENTENCES ONLY, ON THESE FILES ONLY. Every other use of the
#    banned terms still fails, and the sentences must still be present, so the
#    exception cannot outlive the copy. **NOT APPROVED FOR PRODUCTION.** Chris
#    signs these four pages, or the wording changes, before anything publishes.
#    Every one is listed in COPY-PROVENANCE.md under Batch 5 and 6.
DAN_APPROVED_PENDING_CHRIS = {
    'content/performance-reporting.html': [
        'This split matters because it means someone is actively responsible for whether the work is good, separate from who administers the employment relationship.',
        'Local payroll and statutory contributions',
        'Local employment administration',
        'Local HR, attendance and welfare',
        'Employment administration is handled separately',
    ],
    'content/why-acs.html': [
        'Our established offshore delivery partner handles the employment side: payroll, statutory obligations and local HR.',
    ],
    'content/how-your-team-is-supported.html': [
        'Local supervision through our offshore delivery partner covers attendance, welfare and day to day employment administration.',
    ],
    'content/your-australian-team.html': [
        'The delivery partner handles employment administration in the background, not client facing communication.',
    ],
}
CHRIS_DISCLOSURE = 'independent contractor engaged through our established offshore staffing provider'
#    ⚠ faqs.html LEFT THIS SET on 2026-09-15. The 08-25 note said the disclosure
#    comes off the FAQs page when its copy document lands; it has landed, and
#    Ernest's FAQ answer points at the engagement page instead of repeating the
#    disclosure. The disclosure now lives on exactly one page, as Chris ruled.
CHRIS_DISCLOSURE_FILES = {'content/how-your-team-member-is-engaged.html'}
for p in files:
    text = _visible(open(p).read())
    if p in CHRIS_DISCLOSURE_FILES:
        text = text.replace(CHRIS_DISCLOSURE, ' ')
    for allowed in DAN_APPROVED_PENDING_CHRIS.get(p, []):
        if allowed not in text:
            bad.append(f"{p}: a Dan-approved Batch 5/6 sentence is allowlisted but MISSING from the page — \"{allowed}\"")
        text = text.replace(allowed, ' ')
    for allowed in CHRIS_TASK_EXCEPTIONS.get(p, []):
        if allowed not in text:
            bad.append(f"{p}: task exception is allowlisted but MISSING from the page — \"{allowed}\"")
        text = text.replace(allowed, ' ')
    for pattern, what in CHRIS_BANNED:
        for m in re.finditer(pattern, text, re.I):
            bad.append(f"{p}: {what} — \"{m.group(0)}\" (banned by Chris's engagement-model email, 2026-08-24)")
    for m in re.finditer(r'\bcontractors?\b', text, re.I):
        bad.append(f"{p}: \"{m.group(0)}\" outside the disclosure — Chris: never in marketing copy; the one disclosure line lives on the engagement page")
import json as _json_dan
for _e in _json_dan.load(open('content/pages.json')):
    _txt = ' '.join(str(_e.get(k) or '') for k in ('title', 'description', 'excerpt'))
    for pattern, what in CHRIS_BANNED + [(r'\bcontractors?\b', '"contractor" in a meta field')]:
        for m in re.finditer(pattern, _txt, re.I):
            bad.append(f"pages.json:{_e['slug']}: {what} — \"{m.group(0)}\"")

# 6b. Every page has a meta description, and no two share one.
#
#     ⚠ Janet's Tier 1 copy specifies a meta description for every page, and on
#     2026-08-21 this theme emitted NONE on any of the 41 pages. The gap was
#     invisible because nothing rendered and nothing failed. This check is what
#     stops it reopening — a page added to the manifest without a description
#     ships a blank search result and nobody notices.
#
#     ⚠ The upper bound is 170, not 160. Janet's longest is 161 characters and
#     it is used VERBATIM; trimming an author's approved sentence to satisfy a
#     round number would be the tail wagging the dog.
import json as _json
_manifest = _json.load(open('content/pages.json'))
_seen = {}
for _entry in _manifest:
    _slug = _entry['slug']
    _desc = (_entry.get('description') or '').strip()
    if not _desc:
        bad.append(f"pages.json: {_slug} has no meta description")
        continue
    # 26 Oct 2026: Janet's QA description for managed-service-vs-freelancers is 178
    # characters, her wording as content owner; flagged to her, kept as is.
    _LONG_OK = {'managed-service-vs-freelancers': 178}
    if len(_desc) > 170 and _LONG_OK.get(_slug) != len(_desc):
        bad.append(f"pages.json: {_slug} meta description is {len(_desc)} chars, over 170")
    if len(_desc) < 50:
        bad.append(f"pages.json: {_slug} meta description is {len(_desc)} chars, under 50")
    if _desc in _seen:
        bad.append(f"pages.json: {_slug} shares its meta description with {_seen[_desc]}")
    _seen[_desc] = _slug

# 6c. Every internal link points at a page that exists.
#
#    ⚠ NOTHING CHECKED THIS UNTIL 2026-08-24, across 41 pages and 127 internal
#    links. A slug renamed in the manifest breaks every href pointing at it and
#    the site keeps building, because a dead internal link is a 404 at request
#    time and nothing here makes requests.
#
#    ⚠ A PAGE'S URL IS NOT ITS SLUG. Fourteen pages nest under a parent
#    (`staff-you-can-hire`, `who-we-help`, `how-it-works`), so the address is the
#    parent chain plus the slug. The first version of this check compared hrefs
#    against bare slugs and reported those fourteen as dead. **The check was
#    wrong, not the site.** Resolve the chain before comparing.
#
#    ⚠ This matters more than usual right now: Janet's Tier 1 copy proposes a
#    different URL structure and carries links inside its body text. Whichever
#    structure wins, something gets rewritten, and this is what proves the
#    rewrite landed everywhere.
_by_slug = {e['slug']: e for e in _manifest}

def _path_of(entry):
    if entry.get('front'):
        return '/'
    parts = [entry['slug']]
    parent = entry.get('parent')
    depth = 0
    while parent and depth < 5:
        parts.insert(0, parent)
        parent = _by_slug.get(parent, {}).get('parent')
        depth += 1
    return '/' + '/'.join(parts) + '/'

#    ⚠ A page the manifest DRAFTS (a withdrawn page) is not a valid link target.
#    Added 2026-08-25 with the two 56-page-sitemap withdrawals.
_real_paths = {_path_of(e) for e in _manifest if e.get('status', 'publish') == 'publish'}
# The template-preview SAMPLE entries linked from content/template-preview.html
# are a post and a vacancy, not pages, so the manifest cannot know them. Seeded
# by content/seed-samples.php (2 Oct 2026; the article is Janet's featured guide).
_real_paths |= {'/resources/sample-scope-an-offshore-role/', '/vacancy/sample-vacancy/'}
_linked = set()
for _p in files:
    for _m in re.finditer(r'href="(/[^"#?]*)"', open(_p).read()):
        _href = _m.group(1)
        if not _href.endswith('/'):
            _href += '/'
        _linked.add(_href)
        if _href not in _real_paths:
            bad.append(f"{_p}: internal link to a page that does not exist — \"{_m.group(1)}\"")

#    ⚠ THE NAVIGATION WAS INVISIBLE TO THIS CHECK UNTIL 2026-08-25. Its links
#    live in `"url":"..."` JSON block attributes, not `href=""`, so the Day-16
#    URL migration rewrote every href on the site and left the whole top menu
#    pointing at pre-clustering addresses — with every check green. The menu's
#    urls are now resolved against the same path set as everything else.
for _m in re.finditer(r'"url":"(/[^"#?]*)"', open('content/navigation.html').read()):
    _href = _m.group(1)
    if not _href.endswith('/'):
        _href += '/'
    _linked.add(_href)
    if _href not in _real_paths:
        bad.append(f"content/navigation.html: menu link to a page that does not exist — \"{_m.group(1)}\"")

#    Pages nothing links to are REPORTED, not failed. /thank-you/ is a form
#    destination and the home page is reached through the site logo, neither of
#    which is a defect. A role or industry page appearing here would be.
_orphans = sorted(_real_paths - _linked - {'/', '/thank-you/'})
if _orphans:
    print("  note: no internal link points at " + ", ".join(_orphans))

# 6d. Accessibility invariants that a build can check.
#
#    ⚠ THIS IS NOT A SUBSTITUTE FOR THE AXE RUN and does not pretend to be. The
#    2026-08-20 measurement covered 16 pages once, needed a running WordPress and
#    Docker, and found two real defects. This covers all 41 on every build, with
#    nothing running, and catches a different and smaller class: the structural
#    mistakes that arrive when somebody adds a page at speed.
#
#    ⚠ ALL OF THESE WERE CLEAN WHEN WRITTEN (2026-08-24). Same reasoning as 6a:
#    lock a correct state before nine writing days of real copy land on it.
#
#    ⚠ ON alt="": THIRTY-FIVE IMAGES CARRY IT AND THAT IS A DECISION, NOT AN
#    OMISSION. Every one is a mood photograph in a hero column beside text that
#    already says what the page is about; repeating the headline into alt is
#    noise for somebody using a screen reader. **axe passes alt="" and always
#    will**, which is exactly why "0 violations" was never the same as "the
#    images are accessible". The rule below is what keeps the decision honest:
#    empty alt is allowed ONLY inside the decorative figure wrapper, so an
#    informative image added later cannot inherit the exemption by accident.
_A11Y_DECORATIVE_WRAPPER = 'acs-shot'
for p in files:
    text = open(p).read()
    body = PROSE_COMMENT.sub('', text)

    for m in re.finditer(r'<img\b[^>]*>', body):
        tag = m.group(0)
        if not re.search(r'\balt=', tag):
            bad.append(f"{p}: an image with no alt attribute — {tag[:80]}")
            continue
        if re.search(r'alt=""', tag):
            start = body.rfind('<figure', 0, m.start())
            wrapper = body[start:m.start()] if start != -1 else ''
            if _A11Y_DECORATIVE_WRAPPER not in wrapper:
                bad.append(
                    f"{p}: alt=\"\" outside the decorative figure wrapper — {tag[:80]}. "
                    f"Empty alt is a claim that the image carries no meaning. "
                    f"Give it alt text, or put it in a figure.{_A11Y_DECORATIVE_WRAPPER}."
                )

    levels = [int(h) for h in re.findall(r'<h([1-6])\b', body)]
    for a, b in zip(levels, levels[1:]):
        if b > a + 1:
            bad.append(f"{p}: heading level skips h{a} to h{b} — a screen reader reads the outline, not the size")
            break
    if body.count('<h1') > 1:
        bad.append(f"{p}: {body.count('<h1')} h1 elements; a page has one")

    for m in re.finditer(r'<a\b[^>]*>(.*?)</a>', body, re.S):
        label = re.sub(r'<[^>]+>', '', m.group(1)).strip().lower()
        if label in ('click here', 'here', 'read more', 'learn more', 'more'):
            bad.append(f"{p}: link text \"{label}\" — read out of context it says nothing about where it goes")

    for m in re.finditer(r'<(input|textarea|select)\b[^>]*>', body):
        tag = m.group(0)
        if 'type="hidden"' in tag or 'type="submit"' in tag:
            continue
        field_id = re.search(r'id="([^"]+)"', tag)
        labelled = field_id and f'for="{field_id.group(1)}"' in body
        if not labelled and 'aria-label' not in tag:
            bad.append(f"{p}: a form control with no label and no aria-label — {tag[:80]}")

# 7. Every photograph is declared in a provenance comment naming its file.
#
#    Until 2026-09-11 this required a PLACEHOLDER PHOTOGRAPH comment, because
#    every image was an Unsplash stand-in and the duotone that made that visible
#    had been removed on 2026-08-20. The approved set (team-01..21, supplied by
#    Janet Biag 2026-09-11) replaced all of them, and the comment now records
#    provenance instead: `PHOTOGRAPH team-NN: supplied by ... -->`. The check is
#    what stops an undeclared image being pasted in next to the declared ones.
#    2026-09-28: Janet's page-named set (offshoring-in-australia-<slug>-<n>.jpg) is accepted too;
#    any other name still fails.
for p in files:
    text = open(p).read()
    figures = len(re.findall(r'<figure class="acs-shot"', text))
    declared = len(re.findall(r'<!-- PHOTOGRAPH (?:team-\d\d|offshoring-in-australia-[a-z0-9-]+-\d)\.jpg:', text))
    if figures > declared:
        bad.append(f"{p}: {figures} photographs, {declared} declared in a PHOTOGRAPH provenance comment")

if bad:
    print("  FAIL")
    for b in bad: print("   -", b)
    sys.exit(1)
print(f"  ok  {len(files)} files: image dimensions, editor notes, novalidate, database ids")
PY

# 5. Every page in the manifest must have a content file, and every content file
#    must be in the manifest. A page in one and not the other is invisible.
python3 - <<'PY' || fail=1
import json, glob, os, sys
man = json.load(open('content/pages.json'))
slugs = {e['slug'] for e in man}
files = {os.path.basename(p)[:-5] for p in glob.glob('content/*.html')} - {'navigation'}
missing_file = sorted(slugs - files)
orphan_file  = sorted(files - slugs)
if missing_file or orphan_file:
    print("  FAIL")
    for s in missing_file: print(f"   - {s}: in the manifest, no content file")
    for s in orphan_file:  print(f"   - {s}.html: a content file nothing seeds")
    sys.exit(1)
print(f"  ok  {len(slugs)} pages: manifest and content files agree")
PY

echo
[ "$fail" -eq 0 ] && echo "PASS" || echo "FAIL"
exit $fail
