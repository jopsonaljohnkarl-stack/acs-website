#!/usr/bin/env python3
"""Compose the two pricing pages from Janet Biag's revision documents.

    python3 compose-pricing.py            dry run: parse, compose, assert, report
    python3 compose-pricing.py --apply    write content/pricing.html, the Build
                                          Your Team template and both manifest
                                          descriptions

Documents (context/source-docs/acs-pricing-v2/):
  "Pricing v2.docx"          -> content/pricing.html          (/pricing/)
  "Build Your Team v2.docx"  -> acs/templates/build-your-team.html
                                (Pricing Page Revision 2, 21 August 2026)

APPLIED ON JOHN JOPSON'S DECISION, 1 October 2026 (decisions/log.md): the two
pricing pages go on without waiting for Chris Banks. CHRIS HAS NOT BEEN ASKED.

Same rules as compose-content.py, whose parser and assertions this reuses:
every heading, paragraph, bullet and CTA label in each document appears as the
exact text of one element, in document order, and nothing else is visible
except declared site labels. Brief tables and writer notes never reach a page.

⚠ BUILD YOUR TEAM IS A TEMPLATE, NOT A CONTENT FILE. The calculator and the
configurator are markup in acs/templates/build-your-team.html. This script
rewrites only the copy around them: the two widget blocks are lifted out of
the current template and asserted BYTE-IDENTICAL in the output, so the
calculator's fields and behaviour cannot change through this route. The one
addition is id="calculator" on the calculator's wrapper, which the document's
"Skip to the calculator" button targets.
"""
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, "context", "source-docs", "acs-pricing-v2")
CONTENT = os.path.join(HERE, "content")
TEMPLATE = os.path.join(HERE, "acs", "templates", "build-your-team.html")

_spec = importlib.util.spec_from_file_location("cc", os.path.join(HERE, "compose-content.py"))
cc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cc)
ci, esc, group, prose = cc.ci, cc.esc, cc.group, cc.prose

# Pricing v2, section 3, is followed by a writer instruction. It is not copy; it
# becomes an HTML comment so the instruction survives for the copy team.
cc.COPY_TEAM_NOTES = cc.COPY_TEAM_NOTES + ("Setup fee wording pending confirmation on the register",)

# The two targets these documents add to compose-content.py's map.
# /how-it-works/what-is-included: the page lives at root today (pages.json,
# parent ""), the same URL discrepancy already named to Janet on 16 Sep.
cc.CTA_TARGETS["/how-it-works/what-is-included"] = "/what-is-included/"
cc.CTA_TARGETS["#calculator"] = "#calculator"

PRICING_PHOTO = (
    "<!-- wp:html -->\n"
    "<!-- PHOTOGRAPH janet-pricing-1.jpg: supplied by Janet Biag, Drive folder 1JDVoV0JKMYdYgzyWrtEdIVAwYxs0a5qq, "
    "uploaded 17 Sep 2026 as \"pricing.jpg\". Web copy 1200x1500, frame at the photograph's own ratio, 100% kept. "
    "Kept from the previous version of this page on 1 Oct 2026. Used once only. See PHOTOGRAPHY.md. -->\n"
    '<figure class="acs-shot"><div class="acs-shot__frame" style="aspect-ratio:4/5"><img src="/wp-content/themes/acs/'
    'assets/img/offshoring-in-australia-pricing-1.jpg" alt="" width="1200" height="1500" loading="eager" fetchpriority="high" '
    'decoding="async"></div></figure>\n<!-- /wp:html -->'
)

SOURCE = ("Janet Biag's revision document, applied 1 October 2026 by compose-pricing.py ON JOHN JOPSON'S DECISION "
          "of 1 October 2026 (decisions/log.md). CHRIS BANKS HAS NOT BEEN ASKED. ⚠ The document promises the "
          "calculator returns an indicative range; the calculator's figures are 'review-only' (COPY-PROVENANCE.md, "
          "pricing v2). Every section verbatim in document order; CTA targets at the pages' CURRENT addresses")

PRICING_EYEBROW = "Pricing"
cc.SITE_LABELS = cc.SITE_LABELS | {PRICING_EYEBROW}


def d_prose_noted(s, bg=None):
    """d_prose that also carries the section's writer note as a comment."""
    cc.only(s, ("p", "cta", "note"))
    ps = cc.paras(s)
    inner = cc.H2(s) + "\n" + prose(ci.P_LARGE % esc(ps[0]) + "\n" + "\n".join(ci.P % esc(p) for p in ps[1:])
                                    + cc.btns(s, "outline")) + cc.notes(s)
    return group(inner, bg=bg, top="70", bottom="60")


def d_hero_photo(s):
    cc.only(s, ("p", "cta"))
    left = (ci.EYEBROW % esc(PRICING_EYEBROW) + "\n" + ci.H1 % esc(s["h1"]) + "\n" + ci.SEP + "\n"
            + prose("\n".join(ci.P_LARGE % esc(p) for p in cc.paras(s)) + cc.btns(s, "ink")))
    return group(ci.columns([left, PRICING_PHOTO], widths=["58%", None], valign="center"), bg="sheet")


PRICING_LAYOUT = {
    "1": (d_hero_photo, {}),
    "2": (cc.d_prose, {}),
    "3": (d_prose_noted, dict(bg="field")),
    "4": (cc.d_points, {}),
    "5": (cc.d_closing, {}),
}


def compose_pricing(doc):
    ids = [s["id"] for s in doc["sections"]]
    if ids != list(PRICING_LAYOUT):
        sys.exit(f"pricing: document sections {ids} do not match the layout {list(PRICING_LAYOUT)}")
    out = [f"<!-- Copy source: \"Pricing v2.docx\" (Drive 1OpJtZimNvgn_0xekPs3AwhEYvQcU-yU4). {SOURCE}. -->"]
    for s in doc["sections"]:
        fn, kw = PRICING_LAYOUT[s["id"]]
        out.append(fn(s, **kw))
    return "\n".join(out) + "\n"


# --------------------------------------------------------- build your team ---

INSERT = "[Insert Calculator]"
CALC_RE = re.compile(r'  <!-- wp:html -->\n  <div class="acs-calc-wrap"(?: id="calculator")?>.*?\n  <!-- /wp:html -->\n', re.S)
CONF_RE = re.compile(r'  <!-- wp:heading [^\n]*-->\n  <h2 [^\n]*>Build the full specification</h2>\n  <!-- /wp:heading -->\n\n'
                     r'  <!-- wp:html -->\n  <div class="acs-byt" data-acs-configurator>.*?\n  <!-- /wp:html -->\n', re.S)
CONFIG_LABEL = "Build the full specification"


def byt_doc(doc):
    """Section 2's H2 arrives with the calculator placeholder fused onto it."""
    ids = [s["id"] for s in doc["sections"]]
    if ids != ["1", "2", "3", "4", "5"]:
        sys.exit(f"build-your-team: unexpected sections {ids}")
    s2 = doc["sections"][1]
    if not (s2["h2"] or "").endswith(INSERT) or s2["blocks"]:
        sys.exit(f"build-your-team: section 2 is not 'heading + {INSERT}': {s2!r}")
    s2["h2"] = s2["h2"][: -len(INSERT)].strip()
    return doc


def h2_plain(text, top="70"):
    return (f'<!-- wp:heading {{"level":2,"style":{{"spacing":{{"margin":{{"top":"var:preset|spacing|{top}","bottom":"var:preset|spacing|30"}}}}}}}} -->\n'
            f'<h2 class="wp-block-heading" style="margin-top:var(--wp--preset--spacing--{top});margin-bottom:var(--wp--preset--spacing--30)">{esc(text)}</h2>\n'
            '<!-- /wp:heading -->')


def compose_byt(doc, current):
    calc = CALC_RE.search(current)
    conf = CONF_RE.search(current)
    if not calc or not conf:
        sys.exit("build-your-team: could not find the calculator and configurator blocks in the current template")
    calc_block, conf_block = calc.group(0), conf.group(0)
    calc_anchored = calc_block.replace('<div class="acs-calc-wrap">', '<div class="acs-calc-wrap" id="calculator">', 1)
    head = current[: current.index("<!-- wp:template-part")]
    # Idempotent: a re-run on the already-applied template keeps one COPY note.
    if "COPY: \"Build Your Team v2.docx\"" not in head:
      head = head.replace("-->\n", (
        "\n  COPY: \"Build Your Team v2.docx\" (Pricing Page Revision 2, 21 August 2026, Drive\n"
        "  1cM9R87MQCzSrljeDGg3fJ2gLMBotqVHq), applied 1 October 2026 by compose-pricing.py\n"
        "  ON JOHN JOPSON'S DECISION of 1 October 2026. CHRIS BANKS HAS NOT BEEN ASKED.\n"
        "  The calculator and configurator blocks are carried over byte for byte;\n"
        "  only id=\"calculator\" was added (the hero's \"Skip to the calculator\").\n"
        "-->\n"), 1)
    S = {s["id"]: s for s in doc["sections"]}
    s1 = S["1"]
    cc.only(s1, ("p", "cta"))
    parts = [head + '<!-- wp:template-part {"slug":"header","tagName":"header"} /-->\n',
             '<!-- wp:group {"tagName":"main","style":{"spacing":{"padding":{"top":"var:preset|spacing|60","bottom":"var:preset|spacing|80"}}},"layout":{"type":"constrained","contentSize":"78rem"}} -->',
             '<main class="wp-block-group" style="padding-top:var(--wp--preset--spacing--60);padding-bottom:var(--wp--preset--spacing--80)">',
             ci.EYEBROW % esc(PRICING_EYEBROW),
             ci.H1 % esc(s1["h1"]),
             prose("\n".join(ci.P_LARGE % esc(p) for p in cc.paras(s1)) + cc.btns(s1, "ink")),
             h2_plain(S["2"]["h2"], top="50"),
             calc_anchored.rstrip("\n"),
             conf_block.rstrip("\n")]
    for sid in ("3", "4", "5"):
        s = S[sid]
        cc.only(s, ("p", "cta"))
        parts.append(h2_plain(s["h2"]))
        parts.append(prose("\n".join(ci.P % esc(p) for p in cc.paras(s)) + cc.btns(s, "outline")))
    parts += ["</main>", "<!-- /wp:group -->", "", '<!-- wp:template-part {"slug":"footer","tagName":"footer"} /-->', ""]
    out = "\n".join(parts)
    # The widgets must survive unchanged (apart from the one anchor).
    if calc_anchored not in out + "\n" or conf_block.rstrip("\n") not in out:
        sys.exit("build-your-team: a widget block changed in composition")
    return out, calc_anchored, conf_block


def byt_copy_markup(out, calc_block, conf_block):
    """The template minus the two widgets and the head comment: what the document governs."""
    m = out.replace(calc_block.rstrip("\n"), "").replace(conf_block.rstrip("\n"), "")
    return m


def main():
    apply = "--apply" in sys.argv
    pages = json.load(open(os.path.join(CONTENT, "pages.json")))
    by_slug = {p["slug"]: p for p in pages}

    pdoc = cc.parse(os.path.join(SRC, "Pricing v2.docx"))
    pricing = compose_pricing(pdoc)
    wd, wp, labels = cc.assert_verbatim(pdoc, pricing, "pricing")
    print(f"pricing          verbatim PASS  {wd}/{wp} words doc/page  site labels {labels}")

    bdoc = byt_doc(cc.parse(os.path.join(SRC, "Build Your Team v2.docx")))
    current = open(TEMPLATE).read()
    byt, calc_block, conf_block = compose_byt(bdoc, current)
    saved = set(cc.SITE_LABELS)
    cc.SITE_LABELS = saved | {CONFIG_LABEL}
    wd2, wp2, labels2 = cc.assert_verbatim(bdoc, byt_copy_markup(byt, calc_block, conf_block), "build-your-team")
    cc.SITE_LABELS = saved
    print(f"build-your-team  verbatim PASS  {wd2}/{wp2} words doc/page  site labels {labels2}  widgets byte-identical")
    if "#calculator" not in byt or 'id="calculator"' not in byt:
        sys.exit("build-your-team: the #calculator anchor is missing")

    for slug, doc in (("pricing", pdoc), ("build-your-team", bdoc)):
        if not doc["meta"]:
            sys.exit(f"{slug}: no meta description in the document")
        print(f"{slug:16} meta: {doc['meta']}")

    if not apply:
        print("dry run; --apply to write")
        return
    open(os.path.join(CONTENT, "pricing.html"), "w").write(pricing)
    open(TEMPLATE, "w").write(byt)
    by_slug["pricing"]["description"] = pdoc["meta"]
    by_slug["build-your-team"]["description"] = bdoc["meta"]
    with open(os.path.join(CONTENT, "pages.json"), "w") as f:
        json.dump(pages, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print("applied")


if __name__ == "__main__":
    main()
