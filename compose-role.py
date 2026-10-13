#!/usr/bin/env python3
"""Compose the Batch 4 role pages from the copy team's documents.

    python3 compose-role.py <docx-dir>            # dry run: report only
    python3 compose-role.py <docx-dir> --apply    # write content/ + pages.json

Ernest's eight Batch 4 documents (Janet, ACS Website thread, 4 September 2026)
carry the SAME ten-section contract as Batch 3, verified across all eight, so
the parser and every block device are imported from compose-industry.py rather
than copied. Only three things differ, and they are below.

⚠⚠ NOTHING IS APPLIED WITHOUT --apply, AND APPROVAL IS NOT IN. Batch 4 has been
with Chris and Dan since 4 September. This script exists so the pages can go up
within the hour of a yes; running it with --apply before that yes is the thing
it is written to make deliberate.

⚠⚠ THE TEMPLATE QUESTION IS REAL AND IT IS NOT MINE TO SETTLE. Batch 3 moved
its pages from `industry` to `content-page` because industry.html is a passive
shell. **role.html is not.** It renders four things of its own:

    hero (eyebrow, title, EXCERPT, "Build your team" button, photo)
    post-content            <- the only per-page slot
    THE THREE LEVELS        <- template component
    THE CORE DISTINCTION    <- template component
    THE ACTION              <- template CTA band

So the two obvious moves both cost something:

  role         the document's section 1 hero and section 9 closing CTA
               duplicate bands the template already draws, and the other
               seven sections have to live in one unstyled post-content group
  content-page every approved word lands and the page composes properly, but
               the page silently LOSES the core distinction table, which the
               proposal requires on the homepage and every staff page, and
               loses the three-levels component

--template content-page therefore refuses to run unless the caller has said in
the flag itself that the loss is understood and the components are being
carried. Silence is not consent for dropping a component the proposal requires.

⚠ THE LEVELS COMPONENT IS PUBLICATION-GATED INDEPENDENTLY OF ALL THIS.
role.html's own header says the three levels are Commercial 1.0's wording and
"must not publish until it is attributed". As of 2026-09-08 that register row
carries an answer with no name and no date against it. Whichever template wins,
the levels do not go live until Chris signs that row.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util

_spec = importlib.util.spec_from_file_location(
    "compose_industry",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "compose-industry.py"))
ci = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ci)

HERE = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(HERE, "content")

# The documents are named for the page, not slugged for it, so the map is
# explicit rather than derived. A derived one would silently mis-file a
# document whose title the copy team changes.
DOC_TO_SLUG = {
    "ACS - Accounting and Finance.docx": "accounting-finance",
    "ACS - Admin Assistants.docx": "admin-assistants",
    "ACS - AI and Automation Specialists.docx": "ai-automation-specialists",
    "ACS - Bookkeepers.docx": "bookkeepers",
    "ACS - Operations Assistants.docx": "operations-assistants",
    "ACS - Operations Managers.docx": "operations-managers",
    "ACS - Social Media Managers.docx": "social-media-managers",
    "ACS - Telesales.docx": "telesales",
}

SOURCE_NOTE = ("Batch 4, Ernest, via SharePoint (Janet Biag, ACS Website thread, "
               "4 September 2026). Composed by compose-role.py, all nine sections "
               "verbatim in document order. CTA targets rendered at each page's "
               "CURRENT address pending Janet and Ernest's URL pass.")


def compose_role(doc, slug, page_index):
    """Same devices as Batch 3, with the role eyebrow and the role provenance."""
    markup = ci.compose(doc, slug, SOURCE_NOTE, page_index)
    # The only wording difference: these sit under Staff you can hire, not
    # Who we help. Asserted rather than assumed - if the industry composer's
    # eyebrow ever changes, this fails loudly instead of silently shipping
    # the wrong section label onto eight pages.
    if ">Who we help<" not in markup:
        sys.exit("compose-industry's hero eyebrow is no longer 'Who we help'; "
                 "compose-role.py's substitution is stale - fix it, do not skip it.")
    return markup.replace(">Who we help<", ">Staff you can hire<")


# ---------------------------------------------------------------------------
# OPTION 2 (John, 2026-10-01): the role pages are rebuilt like the industry
# pages, on content-page, in the markup the industry pages carry TODAY (after
# the 16-28 Sep design passes: de-boxed prose, plain point lists, Q&A cards,
# accordion, no empty image slots), not compose-industry's 7 Sep output.
#
# The two components role.html used to draw are carried as TEMPLATE PARTS
# (acs/parts/role-levels.html, acs/parts/role-distinction.html): one
# definition, eight pages, so a change is one edit and not eight.
#
# The industry pages close on Janet's enquiry block, which she placed on the
# Homepage, Who We Help, Why ACS and the Industry pages "and nowhere else"
# (Slack, 16 Sep). The role pages therefore close on the site's standard
# closing band (the one on Staff), carrying the document's own closing copy
# and CTAs.
# ---------------------------------------------------------------------------
import html as _html
import re as _re

ROLE_EYEBROW = "Staff you can hire"
SITE_LABELS = {ROLE_EYEBROW, "Next", "Common questions"}
LEVELS_PART = '<!-- wp:template-part {"slug":"role-levels","tagName":"div"} /-->'
DISTINCTION_PART = '<!-- wp:template-part {"slug":"role-distinction","tagName":"div"} /-->'
# The documents end with brief tables (internal links, branding check,
# production notes) that are not copy. Section 9 stops at the first of these.
END_MARKERS = ("Internal links", "BRANDING CHECK", "Production notes")
CTA_MAP = {
    "/book-a-call": "/book-a-call/",
    "/pricing/build-your-team": "/pricing/build-your-team/",
    "/how-it-works/how-we-screen-and-hire": "/how-we-screen-and-hire/",
}
APPROVAL_NOTE = ("Batch 4, Ernest, via SharePoint (Janet Biag, ACS Website thread, 4 September 2026). "
                 "APPROVED: recorded as approved by John (Aljohn Jopson, account lead) on 1 October 2026, "
                 "decisions/log.md. Composed by compose-role.py on the content-page template (option 2, "
                 "John, 1 October 2026), all nine sections verbatim in document order. The levels and the "
                 "core distinction are carried as shared template parts.")

E = lambda t: _html.escape(t, quote=False)

GROUP = ('<!-- wp:group {%s"style": {"spacing": {"padding": {"top": "var:preset|spacing|%s", "bottom": "var:preset|spacing|%s"}}}, "layout": {"type": "constrained", "contentSize": "78rem"}} -->\n'
         '<div class="wp-block-group%s" style="padding-top:var(--wp--preset--spacing--%s);padding-bottom:var(--wp--preset--spacing--%s)">%s</div>\n<!-- /wp:group -->')
BG = {None: ("", ""), "sheet": ('"backgroundColor": "sheet", ', " has-sheet-background-color has-background"),
      "field": ('"backgroundColor": "field", ', " has-field-background-color has-background"),
      "structure": ('"backgroundColor": "structure", "textColor": "paper", ', " has-paper-color has-text-color has-structure-background-color has-background"),
      "structure-bright": ('"backgroundColor": "structure-bright", "textColor": "paper", ', " has-paper-color has-text-color has-structure-bright-background-color has-background")}
H2 = ('<!-- wp:heading {"level":2,"fontSize":"x-large","style":{"spacing":{"margin":{"top":"var:preset|spacing|30","bottom":"var:preset|spacing|40"}}}} -->\n'
      '<h2 class="wp-block-heading has-x-large-font-size" style="margin-top:var(--wp--preset--spacing--30);margin-bottom:var(--wp--preset--spacing--40)">%s</h2>\n<!-- /wp:heading -->')
EYEBROW = ('<!-- wp:paragraph {"fontFamily":"code","fontSize":"x-small","textColor":"structure-bright","style":{"typography":{"textTransform":"uppercase","letterSpacing":"0.12em"}}} -->\n'
           '<p class="has-structure-bright-color has-text-color has-code-font-family has-x-small-font-size" style="letter-spacing:0.12em;text-transform:uppercase">%s</p>\n<!-- /wp:paragraph -->')
H1 = ('<!-- wp:heading {"level":1,"fontSize":"xx-large","style":{"spacing":{"margin":{"top":"var:preset|spacing|30","bottom":"var:preset|spacing|40"}}}} -->\n'
      '<h1 class="wp-block-heading has-xx-large-font-size" style="margin-top:var(--wp--preset--spacing--30);margin-bottom:var(--wp--preset--spacing--40)">%s</h1>\n<!-- /wp:heading -->')
SEP = ('<!-- wp:separator {"backgroundColor":"ink","className":"is-style-wide","style":{"spacing":{"margin":{"top":"0","bottom":"var:preset|spacing|40"}}}} -->\n'
       '<hr class="wp-block-separator has-text-color has-ink-color has-alpha-channel-opacity has-ink-background-color has-background is-style-wide" style="margin-top:0;margin-bottom:var(--wp--preset--spacing--40)"/>\n<!-- /wp:separator -->')


def _para(text, cls="is-measure", size=None, lead=False):
    attrs = {"className": cls}
    klass = cls
    style = ""
    if size:
        attrs["fontSize"] = size
        klass += f" has-{size}-font-size"
    if lead:
        attrs["style"] = {"spacing": {"margin": {"bottom": "var:preset|spacing|40"}}}
        style = ' style="margin-bottom:var(--wp--preset--spacing--40)"'
    return (f"<!-- wp:paragraph {json.dumps(attrs, separators=(',', ':'))} -->\n"
            f'<p class="{klass}"{style}>{E(text)}</p>\n<!-- /wp:paragraph -->')


def _inner(blocks):
    return '<!-- wp:group {"layout":{"type":"default"}} -->\n<div class="wp-block-group">' + "\n".join(blocks) + '</div>\n<!-- /wp:group -->'


def _target(t):
    if t not in CTA_MAP:
        sys.exit(f"unknown CTA target in a Batch 4 document: {t!r} - add it to CTA_MAP with the page's CURRENT address")
    return CTA_MAP[t]


def _button(label, target, style):
    if style == "ink":
        return ('<!-- wp:button {"backgroundColor":"ink","textColor":"paper"} -->\n'
                f'<div class="wp-block-button"><a class="wp-block-button__link has-paper-color has-ink-background-color has-text-color has-background wp-element-button" href="{_target(target)}">{E(label)}</a></div>\n<!-- /wp:button -->')
    return ('<!-- wp:button {"className":"is-style-outline"} -->\n'
            f'<div class="wp-block-button is-style-outline"><a class="wp-block-button__link wp-element-button" href="{_target(target)}">{E(label)}</a></div>\n<!-- /wp:button -->')


def _buttons(ctas, first="ink"):
    btns = [_button(c[1], c[2], first if i == 0 else "outline") for i, c in enumerate(ctas)]
    return ('<!-- wp:buttons {"style":{"spacing":{"margin":{"top":"var:preset|spacing|40"}}}} -->\n'
            '<div class="wp-block-buttons" style="margin-top:var(--wp--preset--spacing--40)">' + "\n".join(btns) + '\n</div>\n<!-- /wp:buttons -->')


def _group(inner, bg=None, top="60", bottom="60"):
    a, k = BG[bg]
    return GROUP % (a, top, bottom, k, top, bottom, inner)


def _has_photo(slug):
    return os.path.exists(os.path.join(HERE, "acs", "assets", "img", f"janet-{slug}-1.jpg"))


def compose_content_page(doc, slug):
    S = {s["id"]: s for s in doc["sections"]}
    out = [f"<!-- Copy source: {APPROVAL_NOTE} -->"]

    # 1 hero: eyebrow, H1, lead, both CTAs; Janet's role photograph on the right
    s = S["1"]
    paras = [b[1] for b in s["blocks"] if b[0] == "p"]
    ctas = [b for b in s["blocks"] if b[0] == "cta"]
    left = "\n".join([EYEBROW % E(ROLE_EYEBROW), H1 % E(s["h1"]), SEP,
                      _inner([_para(p, size="large") for p in paras] + [_buttons(ctas)])])
    if _has_photo(slug):
        photo = ('<!-- wp:html -->\n<!-- PHOTOGRAPH janet-%s-1.jpg: Janet Biag, role set uploaded 2 Oct 2026 (replacing her 17 Sep files; first photograph for Operations Managers), photos approved (John, 1 Oct 2026). '
                 'Rendered by the data-acs-page-hero filter in functions.php. See PHOTOGRAPHY.md. -->\n'
                 '<div data-acs-page-hero hidden></div>\n<!-- /wp:html -->') % slug
        hero = ('<!-- wp:columns {"verticalAlignment": "center", "style": {"spacing": {"blockGap": {"top": "var:preset|spacing|50", "left": "var:preset|spacing|70"}}}} -->\n'
                '<div class="wp-block-columns are-vertically-aligned-center"><!-- wp:column {"verticalAlignment": "center", "width": "52%"} -->\n'
                '<div class="wp-block-column is-vertically-aligned-center" style="flex-basis:52%">' + left + '</div>\n<!-- /wp:column -->\n'
                '<!-- wp:column {"verticalAlignment": "center"} -->\n<div class="wp-block-column is-vertically-aligned-center">' + photo +
                '</div>\n<!-- /wp:column -->\n</div>\n<!-- /wp:columns -->')
    else:
        # No photograph supplied for this role: one column, no empty slot (John, 28 Sep).
        hero = left
    out.append(_group(hero, bg="sheet"))

    def listed(sec, bg, top="60", bottom="60", wide_close=False):
        s = S[sec]
        first = next(i for i, b in enumerate(s["blocks"]) if b[0] == "li")
        before = [b[1] for b in s["blocks"][:first] if b[0] == "p"]
        items = [b[1] for b in s["blocks"] if b[0] == "li"]
        after = [b[1] for b in s["blocks"][first:] if b[0] == "p"]
        inner = "\n".join([H2 % E(s["h2"]), _inner([_para(p, lead=True) for p in before]),
                           '<!-- wp:html -->\n<ul class="acs-points">' + "".join(f"<li>{E(t)}</li>" for t in items) + '</ul>\n<!-- /wp:html -->',
                           _inner([_para(p, cls="acs-close-wide" if wide_close else "is-measure") for p in after])])
        return _group(inner, bg=bg, top=top, bottom=bottom)

    # First card section: closing line spans the grid (Janet, ACS QA 2026-10-01,
    # all eight role pages, same request as the industry pages).
    out.append(listed("2", None, top="70", wide_close=True))

    s = S["3"]
    out.append(_group(H2 % E(s["h2"]) + "\n" + _inner([_para(b[1], size="medium") for b in s["blocks"] if b[0] == "p"]), bg="structure"))

    s = S["4"]
    cards, cur = [], None
    for b in s["blocks"]:
        if b[0] == "h3":
            cur = [b[1], []]; cards.append(cur)
        elif b[0] == "p" and cur:
            cur[1].append(b[1])
    qa = ('<!-- wp:html -->\n<div class="acs-qa">' + "".join(
        f'<div class="acs-qa__item"><h3>{E(t)}</h3><div>' + "".join(f"<p>{E(p)}</p>" for p in ps) + "</div></div>" for t, ps in cards)
        + "</div>\n<!-- /wp:html -->")
    out.append(_group(H2 % E(s["h2"]) + "\n" + qa, top="70"))

    out.append("<!-- CARRIED FROM role.html: the three levels (shared part) -->\n" + LEVELS_PART)

    out.append(listed("5", "field"))

    s = S["6"]
    out.append(_group(H2 % E(s["h2"]) + "\n" + _inner([_para(b[1]) for b in s["blocks"] if b[0] == "p"]), bg="sheet", top="70", bottom="70"))

    s = S["7"]
    paras = [_para(b[1]) for b in s["blocks"] if b[0] == "p"]
    ctas = [b for b in s["blocks"] if b[0] == "cta"]
    out.append(_group(H2 % E(s["h2"]) + "\n" + _inner(paras + ([_buttons(ctas, first="outline")] if ctas else [])), top="70"))

    s = S["7B"]
    out.append(_group(H2 % E(s["h2"]) + "\n" + _inner([_para(b[1]) for b in s["blocks"] if b[0] == "p"]), bg="field"))

    out.append("<!-- CARRIED FROM role.html: a managed service, not staff supply (shared part) -->\n" + DISTINCTION_PART)

    s = S["8"]
    qa, q = [], None
    for b in s["blocks"]:
        if b[0] == "h3":
            q = b[1]
        elif b[0] == "p" and q:
            qa.append((q, b[1])); q = None
    faq = ('<!-- wp:html -->\n<div class="acs-faq">\n' + "\n".join(
        f'  <details class="acs-faq__item">\n    <summary>{E(a)}</summary>\n    <p class="acs-faq__answer">{E(b)}</p>\n  </details>' for a, b in qa)
        + "\n</div>\n<!-- /wp:html -->")
    out.append(_group(H2 % E(s["h2"] or "Common questions") + "\n" + faq, top="70"))

    # 9 closing: the site's standard closing band (as on Staff), the document's own copy and CTAs
    s = S["9"]
    paras = [b[1] for b in s["blocks"] if b[0] == "p"]
    ctas = [b for b in s["blocks"] if b[0] == "cta"]
    copy = "\n".join([EYEBROW % "Next", H2 % E(s["h2"])] + [f"<!-- wp:paragraph -->\n<p>{E(p)}</p>\n<!-- /wp:paragraph -->" for p in paras])
    card = ('<!-- wp:html -->\n<div class="acs-cta-card"><div class="wp-block-buttons">'
            + "\n".join(_button(c[1], c[2], "ink" if i == 0 else "outline") for i, c in enumerate(ctas))
            + '\n</div></div>\n<!-- /wp:html -->')
    band = ('<!-- wp:columns {"className":"acs-cta-band","verticalAlignment": "center", "style": {"spacing": {"blockGap": {"top": "var:preset|spacing|50", "left": "var:preset|spacing|70"}}}} -->\n'
            '<div class="wp-block-columns acs-cta-band are-vertically-aligned-center"><!-- wp:column {"verticalAlignment": "center", "width": "58%"} -->\n'
            '<div class="wp-block-column is-vertically-aligned-center" style="flex-basis:58%">' + copy + '</div>\n<!-- /wp:column -->\n'
            '<!-- wp:column {"verticalAlignment": "center"} -->\n<div class="wp-block-column is-vertically-aligned-center">' + card +
            '</div>\n<!-- /wp:column -->\n</div>\n<!-- /wp:columns -->')
    out.append(_group(band, bg="structure-bright"))
    return "\n".join(out) + "\n"


def trim_brief(doc):
    """Section 9 ends at the first brief marker; nothing after it is copy."""
    for s in doc["sections"]:
        if s["id"] == "9":
            for i, b in enumerate(s["blocks"]):
                if b[0] == "p" and b[1].strip() in END_MARKERS:
                    s["blocks"] = s["blocks"][:i]
                    break
    return doc


def doc_strings(doc):
    out = []
    for s in doc["sections"]:
        for k in ("h1", "h2"):
            if s.get(k):
                out.append(s[k])
        for b in s["blocks"]:
            out.append(b[1])
    return out


def visible_texts(markup):
    """Text of every leaf element, comments stripped, in document order."""
    m = _re.sub(r"<!--.*?-->", "", markup, flags=_re.S)
    return [_html.unescape(t.strip()) for t in _re.findall(r">([^<>]+)<", m) if t.strip()]


def assert_verbatim(doc, markup, slug):
    want = doc_strings(doc)
    got = visible_texts(markup)
    i = 0
    for t in got:
        if i < len(want) and t == want[i]:
            i += 1
    if i != len(want):
        sys.exit(f"{slug}: document text not found verbatim and in order at: {want[i]!r}")
    allowed = set(want) | SITE_LABELS
    stray = [t for t in got if t not in allowed]
    if stray:
        sys.exit(f"{slug}: text on the page that is not in the document: {stray[:3]!r}")
    for marker in END_MARKERS + ("BRANDING CHECK", "Links to", "Breadcrumb parent"):
        if marker in got:
            sys.exit(f"{slug}: brief marker leaked onto the page: {marker!r}")
    for part in (LEVELS_PART, DISTINCTION_PART):
        if markup.count(part) != 1:
            sys.exit(f"{slug}: shared part missing or duplicated: {part}")


def main():
    a = argparse.ArgumentParser()
    a.add_argument("src", help="directory holding the eight .docx")
    a.add_argument("--apply", action="store_true",
                   help="write content/*.html and pages.json (approval must be in)")
    a.add_argument("--template", default="role",
                   choices=["role", "content-page"],
                   help="page template. content-page needs --components-carried")
    a.add_argument("--components-carried", action="store_true",
                   help="confirm the core distinction table and the three levels "
                        "have been carried into the composed page, so moving off "
                        "role.html does not drop them")
    args = a.parse_args()

    if args.template == "content-page" and not args.components_carried:
        sys.exit(
            "refusing: moving these pages to content-page drops role.html's core\n"
            "distinction table, which the proposal requires on every staff page,\n"
            "and its three-levels component. Carry them into the composed markup\n"
            "first, then pass --components-carried. See this file's header.")

    found = sorted(n for n in os.listdir(args.src) if n.endswith(".docx"))
    unknown = [n for n in found if n not in DOC_TO_SLUG]
    if unknown:
        sys.exit(f"documents with no slug mapping: {unknown}")
    missing = [n for n in DOC_TO_SLUG if n not in found]
    if missing:
        sys.exit(f"expected documents not present: {missing}")

    pages = json.load(open(os.path.join(CONTENT, "pages.json")))
    by_slug = {p["slug"]: p for p in pages}

    rows = []
    for page_index, name in enumerate(found):
        slug = DOC_TO_SLUG[name]
        if slug not in by_slug:
            sys.exit(f"no manifest entry for {slug}")
        doc = trim_brief(ci.parse(os.path.join(args.src, name)))
        if not doc["meta"] or not (50 <= len(doc["meta"]) <= 170):
            sys.exit(f"{slug}: meta description missing or outside 50-170 chars: {doc['meta']!r}")
        if args.template == "content-page":
            markup = compose_content_page(doc, slug)
            assert_verbatim(doc, markup, slug)
        else:
            markup = compose_role(doc, slug, page_index)
        words = sum(len(b[1].split()) for s in doc["sections"]
                    for b in s["blocks"] if b[0] in ("p", "li"))
        ctas = len([1 for s in doc["sections"] for b in s["blocks"] if b[0] == "cta"])
        rows.append((slug, name, words, ctas, len(markup)))
        if args.apply:
            with open(os.path.join(CONTENT, slug + ".html"), "w") as f:
                f.write(markup)
            by_slug[slug]["template"] = args.template
            by_slug[slug]["description"] = doc["meta"]

    if args.apply:
        with open(os.path.join(CONTENT, "pages.json"), "w") as f:
            json.dump(pages, f, indent=1, ensure_ascii=False)
            f.write("\n")

    verb = "wrote" if args.apply else "would write (dry run)"
    for slug, name, words, ctas, size in rows:
        print(f"  {slug:28} ~{words:5} words  {ctas} CTAs  {size:6} bytes  <- {name}")
    print(f"\n{verb} {len(rows)} pages on template '{args.template}'.")
    if not args.apply:
        print("Nothing written (dry run). Batch 4 copy approved by John, 1 October 2026.")


if __name__ == "__main__":
    main()
