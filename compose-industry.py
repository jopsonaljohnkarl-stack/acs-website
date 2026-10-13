#!/usr/bin/env python3
"""Compose the Batch 3 industry pages from the copy team's documents.

    python3 compose-industry.py <docx-dir>

Each document (Ernest, "Industry page. Batch 3", approved by Chris in writing on
the ACS Website thread, 2 September 2026) carries the same nine sections:
1 hero, 2 problem, 3 why offshore, 4 what a team member can own, 5 signs,
6 growth, 7 scoping, 7B remote and first 30 days, 8 common questions,
9 closing CTA. This script reads those sections verbatim and lays them into
the site's existing block patterns (the ones already used on Who We Help and
How It Works), one file per page under content/, on the content-page template.

Rules it enforces:
- Every word on the page is the document's. Section labels the document
  supplies only as a marker ("COMMON QUESTIONS") become the heading text.
- CTA targets are rendered at the page's CURRENT address; slug moves belong to
  Janet and Ernest's URL pass. Unknown targets stop the run.
- The manifest description becomes the document's meta description; the
  excerpt (the Who We Help card line) is untouched because it belongs to the
  Who We Help document, not this one.
"""
import html
import json
import os
import re
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(HERE, "content")

CTA_TARGETS = {
    "/book-a-call": "/book-a-call/",
    "/how-it-works/how-we-screen-and-hire": "/how-we-screen-and-hire/",
    "/pricing/build-your-team": "/pricing/build-your-team/",
}


def paragraphs(path):
    """Yield (kind, text) from the document body in order."""
    xml = zipfile.ZipFile(path).read("word/document.xml").decode()
    for p in re.findall(r"<w:p[ >].*?</w:p>", xml, flags=re.S):
        text = html.unescape("".join(re.findall(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>", p, flags=re.S))).strip()
        if not text:
            continue
        bullet = "<w:numPr>" in p or 'w:hanging="200"' in p
        yield ("bullet" if bullet else "para", text)


def parse(path):
    doc = {"meta": None, "sections": []}
    items = list(paragraphs(path))
    cur = None
    for i, (kind, text) in enumerate(items):
        if text == "Meta description":
            doc["meta"] = items[i + 1][1]
            continue
        m = re.match(r"^SECTION (\w+)\s{2,}(.+)$", text)
        if m:
            cur = {"id": m.group(1), "name": m.group(2).strip(), "h1": None, "h2": None, "blocks": []}
            doc["sections"].append(cur)
            continue
        if cur is None:
            continue
        if text.startswith("H1  "):
            cur["h1"] = text[4:].strip()
        elif text.startswith("H2  "):
            cur["h2"] = text[4:].strip()
        elif text.startswith("H3  "):
            cur["blocks"].append(("h3", text[4:].strip()))
        elif text.startswith("CTA  "):
            m = re.match(r"^CTA\s{2,}(.+?)\s{2,}links to\s{2,}(\S+)", text)
            if not m:
                sys.exit(f"unparsed CTA in {path}: {text}")
            cur["blocks"].append(("cta", m.group(1).strip(), m.group(2).strip()))
        elif kind == "bullet":
            cur["blocks"].append(("li", text))
        else:
            cur["blocks"].append(("p", text))
    ids = [s["id"] for s in doc["sections"]]
    if ids != ["1", "2", "3", "4", "5", "6", "7", "7B", "8", "9"]:
        sys.exit(f"unexpected section set in {path}: {ids}")
    return doc


def esc(t):
    return html.escape(t, quote=False)


# ---- block patterns, lifted from content/who-we-help.html and the industry template ----
EYEBROW = '<!-- wp:paragraph {"fontFamily":"code","fontSize":"x-small","textColor":"structure-bright","style":{"typography":{"textTransform":"uppercase","letterSpacing":"0.12em"}}} -->\n<p class="has-structure-bright-color has-text-color has-code-font-family has-x-small-font-size" style="letter-spacing:0.12em;text-transform:uppercase">%s</p>\n<!-- /wp:paragraph -->'
H1 = '<!-- wp:heading {"level":1,"fontSize":"xx-large","style":{"spacing":{"margin":{"top":"var:preset|spacing|30","bottom":"var:preset|spacing|40"}}}} -->\n<h1 class="wp-block-heading has-xx-large-font-size" style="margin-top:var(--wp--preset--spacing--30);margin-bottom:var(--wp--preset--spacing--40)">%s</h1>\n<!-- /wp:heading -->'
H2 = '<!-- wp:heading {"level":2,"fontSize":"x-large","style":{"spacing":{"margin":{"top":"var:preset|spacing|30","bottom":"var:preset|spacing|40"}}}} -->\n<h2 class="wp-block-heading has-x-large-font-size" style="margin-top:var(--wp--preset--spacing--30);margin-bottom:var(--wp--preset--spacing--40)">%s</h2>\n<!-- /wp:heading -->'
H2_TIGHT = '<!-- wp:heading {"level":2,"fontSize":"x-large","style":{"spacing":{"margin":{"top":"0","bottom":"var:preset|spacing|30"}}}} -->\n<h2 class="wp-block-heading has-x-large-font-size" style="margin-top:0;margin-bottom:var(--wp--preset--spacing--30)">%s</h2>\n<!-- /wp:heading -->'
H3 = '<!-- wp:heading {"level":3,"fontSize":"medium","style":{"spacing":{"margin":{"top":"0","bottom":"var:preset|spacing|20"}}}} -->\n<h3 class="wp-block-heading has-medium-font-size" style="margin-top:0;margin-bottom:var(--wp--preset--spacing--20)">%s</h3>\n<!-- /wp:heading -->'
SEP = '<!-- wp:separator {"backgroundColor":"ink","className":"is-style-wide","style":{"spacing":{"margin":{"top":"0","bottom":"var:preset|spacing|40"}}}} -->\n<hr class="wp-block-separator has-text-color has-ink-color has-alpha-channel-opacity has-ink-background-color has-background is-style-wide" style="margin-top:0;margin-bottom:var(--wp--preset--spacing--40)"/>\n<!-- /wp:separator -->'
P = '<!-- wp:paragraph {"className":"is-measure"} -->\n<p class="is-measure">%s</p>\n<!-- /wp:paragraph -->'
P_LEAD = '<!-- wp:paragraph {"className":"is-measure","style":{"spacing":{"margin":{"bottom":"var:preset|spacing|40"}}}} -->\n<p class="is-measure" style="margin-bottom:var(--wp--preset--spacing--40)">%s</p>\n<!-- /wp:paragraph -->'
P_LARGE = '<!-- wp:paragraph {"className":"is-measure","fontSize":"large"} -->\n<p class="is-measure has-large-font-size">%s</p>\n<!-- /wp:paragraph -->'
P_MED = '<!-- wp:paragraph {"fontSize":"medium"} -->\n<p class="has-medium-font-size">%s</p>\n<!-- /wp:paragraph -->'
P_PLAIN = '<!-- wp:paragraph -->\n<p>%s</p>\n<!-- /wp:paragraph -->'
POINTS = '<!-- wp:html -->\n<ul class="acs-points">%s</ul>\n<!-- /wp:html -->'
FAQ = '<!-- wp:html -->\n<div class="acs-faq">\n%s\n</div>\n<!-- /wp:html -->'
FAQ_ITEM = '  <details class="acs-faq__item">\n    <summary>%s</summary>\n    <p class="acs-faq__answer">%s</p>\n  </details>'


def group(inner, bg=None, top="60", bottom="60", text=None):
    attrs = {}
    cls = "wp-block-group"
    if bg:
        attrs["backgroundColor"] = bg
        cls += f" has-{bg}-background-color has-background"
    if text:
        attrs["textColor"] = text
        cls = cls.replace("wp-block-group", f"wp-block-group has-{text}-color has-text-color")
    attrs["style"] = {"spacing": {"padding": {"top": f"var:preset|spacing|{top}", "bottom": f"var:preset|spacing|{bottom}"}}}
    attrs["layout"] = {"type": "constrained", "contentSize": "78rem"}
    style = f"padding-top:var(--wp--preset--spacing--{top});padding-bottom:var(--wp--preset--spacing--{bottom})"
    return f'<!-- wp:group {json.dumps(attrs)} -->\n<div class="{cls}" style="{style}">{inner}</div>\n<!-- /wp:group -->'


def prose(inner):
    return '<!-- wp:group {"layout":{"type":"default"}} -->\n<div class="wp-block-group">' + inner + '</div>\n<!-- /wp:group -->'


def bordered_columns(cells, gap="60", color="ink"):
    col = ('<!-- wp:column {"style":{"border":{"top":{"color":"var:preset|color|%s","width":"2px"}},"spacing":{"padding":{"top":"var:preset|spacing|30"}}}} -->\n'
           '<div class="wp-block-column" style="border-top-color:var(--wp--preset--color--%s);border-top-width:2px;padding-top:var(--wp--preset--spacing--30)">%%s</div>\n<!-- /wp:column -->') % (color, color)
    cols = "\n".join(col % c for c in cells)
    return f'<!-- wp:columns {{"style":{{"spacing":{{"blockGap":{{"top":"var:preset|spacing|50","left":"var:preset|spacing|{gap}"}}}}}}}} -->\n<div class="wp-block-columns">{cols}\n</div>\n<!-- /wp:columns -->'


def prose_columns(cells, gap="40"):
    """Section 3's columns as plain paragraphs on the blue field.

    Janet Biag, ACS QA 2026-09-16: this section is continuous explanatory copy,
    not a list, so it takes no card. Carries .acs-prose-band, which style.css
    uses to opt the band out of the column-as-card rule, and no inline border,
    because an inline declaration would beat that opt-out.
    """
    col = '<!-- wp:column {} -->\n<div class="wp-block-column">%s</div>\n<!-- /wp:column -->'
    cols = "\n".join(col % c for c in cells)
    attrs = {"className": "acs-prose-band",
             "style": {"spacing": {"blockGap": {"top": "var:preset|spacing|50", "left": f"var:preset|spacing|{gap}"}}}}
    return (f'<!-- wp:columns {json.dumps(attrs)} -->\n'
            f'<div class="wp-block-columns acs-prose-band">{cols}\n</div>\n<!-- /wp:columns -->')


def buttons(items, top_margin=True):
    out = []
    for label, href, style in items:
        if style == "ink":
            out.append(f'<!-- wp:button {{"backgroundColor":"ink","textColor":"paper"}} -->\n<div class="wp-block-button"><a class="wp-block-button__link has-paper-color has-ink-background-color has-text-color has-background wp-element-button" href="{href}">{esc(label)}</a></div>\n<!-- /wp:button -->')
        elif style == "outline":
            out.append(f'<!-- wp:button {{"className":"is-style-outline"}} -->\n<div class="wp-block-button is-style-outline"><a class="wp-block-button__link wp-element-button" href="{href}">{esc(label)}</a></div>\n<!-- /wp:button -->')
        else:
            out.append(f'<!-- wp:button -->\n<div class="wp-block-button"><a class="wp-block-button__link wp-element-button" href="{href}">{esc(label)}</a></div>\n<!-- /wp:button -->')
    if top_margin:
        return '<!-- wp:buttons {"style":{"spacing":{"margin":{"top":"var:preset|spacing|40"}}}} -->\n<div class="wp-block-buttons" style="margin-top:var(--wp--preset--spacing--40)">' + "\n".join(out) + '\n</div>\n<!-- /wp:buttons -->'
    return '<!-- wp:buttons -->\n<div class="wp-block-buttons">' + "\n".join(out) + '\n</div>\n<!-- /wp:buttons -->'


def cta(block, style):
    label, target = block[1], block[2]
    if target not in CTA_TARGETS:
        sys.exit(f"unknown CTA target {target!r}; add it to CTA_TARGETS with its current address")
    return (label, CTA_TARGETS[target], style)


SHOTS = ["shot-9", "shot-2", "shot-6", "shot-7", "shot-8", "shot-10", "shot-11", "shot-4", "shot-5", "shot-1"]


def jpeg_size(path):
    import struct
    with open(path, "rb") as f:
        f.read(2)
        while True:
            marker, = struct.unpack(">H", f.read(2))
            length, = struct.unpack(">H", f.read(2))
            if marker in (0xFFC0, 0xFFC1, 0xFFC2):
                f.read(1); h, w = struct.unpack(">HH", f.read(4)); return w, h
            f.read(length - 2)


def shot(i, aspect=None, hero=False):
    """A photograph in a frame of its OWN ratio, so nothing is ever cropped.

    ⚠ `aspect` is ignored and kept only so existing call sites still read.
    The frame used to be hard-coded portrait (4/5, 3/4) while every supplied
    photograph but one is landscape, and .acs-shot img is `object-fit: cover`:
    the industry pages were throwing away 47-58% of every picture and slicing
    people down the middle at the frame edge. Janet Biag flagged it as "the
    crop is too obvious and looks awkward" (ACS QA, 2026-09-16) on three pages
    and the same defect was on all thirteen.

    Deriving the ratio from the file cannot crop, so it needs no per-image
    judgement. The image is kept substantial by the column split beside it
    (52/48, not 58/42), which is the other half of her note - re-cutting the
    frame alone makes the picture small, which is what she came back on.
    """
    from math import gcd
    name = SHOTS[i % len(SHOTS)]
    w, h = jpeg_size(os.path.join(HERE, "acs", "assets", "img", name + ".jpg"))
    g = gcd(w, h)
    # The hero is above the fold on every industry page: lazy-loading it costs
    # LCP and flashes an empty grey frame before it paints. Below-fold shots
    # stay lazy.
    load = 'loading="eager" fetchpriority="high"' if hero else 'loading="lazy"'
    return ('<!-- wp:html -->\n<!-- PLACEHOLDER PHOTOGRAPH: sector context. Replace before launch; the photography brief names the real shot. -->\n'
            f'<figure class="acs-shot"><div class="acs-shot__frame" style="aspect-ratio:{w // g}/{h // g}"><img src="/wp-content/themes/acs/assets/img/{name}.jpg" alt="" width="{w}" height="{h}" {load} decoding="async"></div></figure>\n<!-- /wp:html -->')


def columns(cells, widths=None, gap="70", valign=None):
    out = []
    for n, c in enumerate(cells):
        attrs = {}
        if valign: attrs["verticalAlignment"] = valign
        if widths and widths[n]: attrs["width"] = widths[n]
        style = f' style="flex-basis:{widths[n]}"' if widths and widths[n] else ""
        cls = "wp-block-column" + (" is-vertically-aligned-center" if valign == "center" else "")
        out.append(f'<!-- wp:column {json.dumps(attrs)} -->\n<div class="{cls}"{style}>{c}</div>\n<!-- /wp:column -->')
    cattrs = {"style": {"spacing": {"blockGap": {"top": "var:preset|spacing|50", "left": f"var:preset|spacing|{gap}"}}}}
    ccls = "wp-block-columns"
    if valign == "center":
        cattrs = {"verticalAlignment": "center", **cattrs}; ccls += " are-vertically-aligned-center"
    return f'<!-- wp:columns {json.dumps(cattrs)} -->\n<div class="{ccls}">' + "\n".join(out) + '\n</div>\n<!-- /wp:columns -->'


PULL = '<!-- wp:paragraph {"className":"is-measure"} -->\n<p class="is-measure">%s</p>\n<!-- /wp:paragraph -->'
# The line closing the FIRST card section spans the card grid above it, not the
# 44rem measure. Janet Biag, ACS QA 2026-10-01, on every industry page: "the
# concluding paragraph under the first card section still needs to be
# full-width, matching the card grid above it." Section 5 keeps the measure;
# her Construction comment the same night called that one clean.
CLOSE_WIDE = '<!-- wp:paragraph {"className":"acs-close-wide"} -->\n<p class="acs-close-wide">%s</p>\n<!-- /wp:paragraph -->'
KICKER = '<!-- wp:paragraph {"fontFamily":"code","fontSize":"x-small","textColor":"structure-bright","style":{"typography":{"textTransform":"uppercase","letterSpacing":"0.12em"}}} -->\n<p class="has-structure-bright-color has-text-color has-code-font-family has-x-small-font-size" style="letter-spacing:0.12em;text-transform:uppercase">Next</p>\n<!-- /wp:paragraph -->'


def split_first_sentence(text):
    m = re.match(r"^(.+?[.!?])\s+(.+)$", text)
    return (m.group(1), m.group(2)) if m else (text, "")


def compose(doc, slug, source_name, page_index=0):
    S = {s["id"]: s for s in doc["sections"]}
    out = [f"<!-- Copy source: {source_name} (Batch 3, Ernest), approved in writing by Chris Banks on the ACS Website thread, 2 September 2026. Applied 7 September 2026 by compose-industry.py, all nine sections verbatim in document order, laid into the site's card, glass, stack and pull devices (design pass the same day). CTA targets rendered at the page's CURRENT address pending Janet and Ernest's URL pass. -->"]

    # 1 hero: copy left, sector photograph right (uncovers on load)
    s = S["1"]
    paras = [b[1] for b in s["blocks"] if b[0] == "p"]
    ctas = [cta(b, "ink") for b in s["blocks"] if b[0] == "cta"]
    left = EYEBROW % "Who we help" + "\n" + H1 % esc(s["h1"]) + "\n" + SEP + "\n" + prose("\n".join(P_LARGE % esc(p) for p in paras) + ("\n" + buttons(ctas) if ctas else ""))
    out.append(group(columns([left, shot(page_index, hero=True)], widths=["52%", None], valign="center"), bg="sheet"))

    # 2 problem: intro, point cards, the closing line as a pull card
    s = S["2"]
    first_li = next(i for i, b in enumerate(s["blocks"]) if b[0] == "li")
    before = [b[1] for b in s["blocks"][:first_li] if b[0] == "p"]
    items = [b[1] for b in s["blocks"] if b[0] == "li"]
    after = [b[1] for b in s["blocks"][first_li:] if b[0] == "p"]
    inner = H2 % esc(s["h2"]) + "\n" + prose("\n".join(P_LEAD % esc(p) for p in before)) + "\n" + POINTS % "".join(f"<li>{esc(t)}</li>" for t in items) + "\n" + prose("\n".join(CLOSE_WIDE % esc(p) for p in after))
    out.append(group(inner, top="70", bottom="60"))

    # 3 why: plain paragraphs on the blue field. Authored as paper-ruled
    # columns, but the column-as-card rule in style.css turned every column on
    # a structure ground into a glass panel, so what shipped was three boxes.
    # Janet Biag, ACS QA 2026-09-16: "Remove the three cards and present the
    # content as 3 standard paragraphs, as this is continuous explanatory copy
    # rather than a list." The columns stay as layout; the card goes.
    s = S["3"]
    cells = [P_MED % esc(b[1]) for b in s["blocks"] if b[0] == "p"]
    out.append(group(H2 % esc(s["h2"]) + "\n" + prose_columns(cells, gap="40"), bg="structure", text="paper"))

    # 4 own: question-and-answer cards (title left, what it covers right)
    s = S["4"]
    cards, cur = [], None
    for b in s["blocks"]:
        if b[0] == "h3":
            cur = [b[1], []]; cards.append(cur)
        elif b[0] == "p" and cur:
            cur[1].append(b[1])
    qa = '<!-- wp:html -->\n<div class="acs-qa">' + "".join(f'<div class="acs-qa__item"><h3>{esc(t)}</h3><div>' + "".join(f"<p>{esc(p)}</p>" for p in ps) + "</div></div>" for t, ps in cards) + "</div>\n<!-- /wp:html -->"
    out.append(group(H2 % esc(s["h2"]) + "\n" + qa, top="70", bottom="60"))

    # 5 signs: field ground, point cards, closing line as a pull card
    s = S["5"]
    first_li = next(i for i, b in enumerate(s["blocks"]) if b[0] == "li")
    before = [b[1] for b in s["blocks"][:first_li] if b[0] == "p"]
    items = [b[1] for b in s["blocks"] if b[0] == "li"]
    after = [b[1] for b in s["blocks"][first_li:] if b[0] == "p"]
    inner = H2 % esc(s["h2"]) + "\n" + prose("\n".join(P_LEAD % esc(p) for p in before)) + "\n" + POINTS % "".join(f"<li>{esc(t)}</li>" for t in items) + "\n" + prose("\n".join(PULL % esc(p) for p in after))
    out.append(group(inner, bg="field"))

    # 6 grow: three pull cards side by side (the sticky stack clipped two-line openers under its fan)
    s = S["6"]
    cells = [PULL % esc(b[1]) for b in s["blocks"] if b[0] == "p"]
    out.append(group(H2 % esc(s["h2"]) + "\n" + columns(cells, gap="40"), bg="sheet", top="70", bottom="70"))

    # 7 scoped: prose and its CTA beside a second photograph
    s = S["7"]
    paras = [b[1] for b in s["blocks"] if b[0] == "p"]
    ctas = [cta(b, "outline") for b in s["blocks"] if b[0] == "cta"]
    left = H2 % esc(s["h2"]) + "\n" + prose("\n".join(P % esc(p) for p in paras) + ("\n" + buttons(ctas) if ctas else ""))
    out.append(group(columns([left, shot(page_index + 3)], widths=["52%", None], valign="center"), top="70", bottom="60"))

    # 7B remote and the first 30 days: two pull cards side by side
    s = S["7B"]
    paras = [b[1] for b in s["blocks"] if b[0] == "p"]
    cells = [PULL % esc(p) for p in paras]
    out.append(group(H2 % esc(s["h2"]) + "\n" + columns(cells, gap="50"), bg="field"))

    # 8 questions: the accordion
    s = S["8"]
    qa, q = [], None
    for b in s["blocks"]:
        if b[0] == "h3":
            q = b[1]
        elif b[0] == "p" and q:
            qa.append((q, b[1])); q = None
    heading = s["h2"] or s["name"].capitalize()
    out.append(group(H2 % esc(heading) + "\n" + FAQ % "\n".join(FAQ_ITEM % (esc(a), esc(b)) for a, b in qa), top="70", bottom="60"))

    # 9 closing: the site's closing band
    s = S["9"]
    paras = [b[1] for b in s["blocks"] if b[0] == "p"]
    ctas = [cta(b, "ink") for b in s["blocks"] if b[0] == "cta"]
    inner = KICKER + "\n" + H2 % esc(s["h2"]) + "\n" + "\n".join(P_PLAIN % esc(p) for p in paras) + ("\n" + buttons(ctas) if ctas else "")
    out.append(group(inner, bg="structure-bright", text="paper"))
    return "\n".join(out) + "\n"


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = sys.argv[1]
    manifest_path = os.path.join(CONTENT, "pages.json")
    pages = json.load(open(manifest_path))
    by_slug = {p["slug"]: p for p in pages}
    done = []
    for page_index, name in enumerate(sorted(os.listdir(src))):
        if not name.endswith(".docx"):
            continue
        slug = name[:-5]
        if slug not in by_slug:
            sys.exit(f"no manifest entry for {slug}")
        doc = parse(os.path.join(src, name))
        if not doc["meta"] or not (50 <= len(doc["meta"]) <= 170):
            sys.exit(f"{slug}: meta description missing or outside 50-170 chars: {doc['meta']!r}")
        markup = compose(doc, slug, f"{name} via SharePoint (Janet Biag, 28 Aug / 1 Sep 2026)", page_index)
        with open(os.path.join(CONTENT, slug + ".html"), "w") as f:
            f.write(markup)
        page = by_slug[slug]
        page["template"] = "content-page"
        page["description"] = doc["meta"]
        words = sum(len(b[1].split()) for s in doc["sections"] for b in s["blocks"] if b[0] in ("p", "li")) + sum(len((s["h1"] or s["h2"] or "").split()) for s in doc["sections"])
        done.append((slug, words, len([1 for s in doc["sections"] for b in s["blocks"] if b[0] == "cta"])))
    with open(manifest_path, "w") as f:
        json.dump(pages, f, indent=1, ensure_ascii=False)
        f.write("\n")
    for slug, words, ctas in done:
        print(f"{slug:28} ~{words} words, {ctas} CTAs -> content/{slug}.html (content-page)")


if __name__ == "__main__":
    main()
