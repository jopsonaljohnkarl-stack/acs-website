#!/usr/bin/env python3
"""Compose the Batch 5 and Batch 6 content pages from the copy team's documents.

    python3 compose-content.py <docx-dir> [<docx-dir> ...]            dry run: parse, compose, assert, report
    python3 compose-content.py <docx-dir> [<docx-dir> ...] --dump     print the parsed structure
    python3 compose-content.py <docx-dir> [<docx-dir> ...] --apply    write content/<slug>.html and manifest descriptions

Eight documents: FAQs, Onboarding and First 90 Days, Performance and Reporting,
How Your Team Is Supported, Our Story, Results, Why ACS, Your Australian Team.
APPROVED IN WRITING BY DAN BANKS, 15 September 2026 04:14 PHT, thread
"Re: ACS Website": "approved as presented ... proceed with implementation on the
review site". CHRIS BANKS HAS NOT APPROVED. See COPY-PROVENANCE.md.

Unlike Batch 3 and 4 these documents do not share one section contract, so each
page has its own layout below (section id -> device). The layout decides only
WHERE words go. Every word comes from the document, and two assertions prove it
on the composed markup before anything is written:

  1. every heading, paragraph, bullet, table cell and CTA label in the document
     appears as the exact text of one element, in document order;
  2. every visible text node in the composed markup is either one of those
     strings or one of the declared site labels (eyebrow, "Next", the
     "Common questions" marker used as a heading - the Batch 3 precedent).

Brief metadata (word counts, keyword tables, writer notes, section markers, the
Results "Placeholder section" instruction) never reaches a page: the parser
starts at SECTION 1, and a leak check fails the run on any brief marker.
"""
import html
import importlib.util
import json
import os
import re
import struct
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(HERE, "content")

_spec = importlib.util.spec_from_file_location("ci", os.path.join(HERE, "compose-industry.py"))
ci = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ci)
esc, group, prose, columns, buttons = ci.esc, ci.group, ci.prose, ci.columns, ci.buttons

# Document CTA target -> the page's CURRENT address. Slug moves are Janet and
# Ernest's URL pass (same rule as Batches 1 and 3). Unknown targets stop the run.
CTA_TARGETS = {
    "/book-a-call": "/book-a-call/",
    "/how-it-works/how-your-team-member-is-engaged": "/how-it-works/who-employs-your-staff/",
    "/pricing/build-your-team": "/pricing/build-your-team/",
    "/staff": "/staff/",
    "/how-it-works/performance-and-reporting": "/how-it-works/performance-reporting/",
    "/why-acs/our-story": "/why-acs/our-story/",
    "/why-acs": "/why-acs/",
    "/why-acs/your-australian-team": "/your-australian-team/",
    "/why-acs/results": "/why-acs/results/",
    "/how-it-works": "/how-it-works/",
    "/how-it-works/managed-service-vs-freelancers": "/how-it-works/managed-service-vs-freelancers/",
}

DOCS = {
    "ACS - FAQs.docx": "faqs",
    "ACS - Onboarding and First 90 Days.docx": "onboarding-first-90-days",
    "ACS - Performance and Reporting.docx": "performance-reporting",
    "ACS - How Your Team Is Supported.docx": "how-your-team-is-supported",
    "ACS - Our Story.docx": "our-story",
    "ACS - Results.docx": "results",
    "ACS - Why ACS.docx": "why-acs",
    "ACS - Your Australian Team.docx": "your-australian-team",
    # Batch 2 (18 Aug 2026), supplied again by Janet Biag on Asana 16 Sep 2026 as
    # the copy these pages should carry. Their own attribution below, NOT Dan's
    # 15 September approval, which covered Batches 5 and 6 only.
    "ACS_Data_Security_and_Privacy.docx": "data-security-and-privacy",
    "ACS_What_Is_Included.docx": "what-is-included",
    "ACS_How_We_Screen_and_Hire.docx": "how-we-screen-and-hire",
    "ACS_Staff_You_Can_Hire.docx": "staff",
    # Batch 7: utility and legal pages, supplied by Janet Biag on Asana 24 Sep 2026
    # (one task per page, ACS Page Copies QA section), filed in
    # context/source-docs/acs-batch7. Applied 2 Oct 2026 on her chase that morning.
    "ACS - Book a Call.docx": "book-a-call",
    "ACS - Candidate Privacy Notice.docx": "candidate-privacy",
    "ACS - Contact.docx": "contact",
    "ACS - Cookie Policy.docx": "cookies",
    "ACS - Get a Quote.docx": "get-a-quote",
    "ACS - Pricing Disclaimer.docx": "pricing-disclaimer",
    "ACS - Privacy Policy.docx": "privacy-policy",
    "ACS - Terms of Use.docx": "terms",
    "ACS - Thank You.docx": "thank-you",
    "ACS - Work With Us.docx": "work-with-us",
}

# The header comment each composed page opens with. Batches 5 and 6 carry Dan's
# written approval; a page from another batch must say what IS on record for it
# and nothing more (approval semantics: writing a sentence is not approving it).
DAN_15_SEP = ("APPROVED IN WRITING BY DAN BANKS, 15 September 2026 04:14 PHT, thread 'Re: ACS Website' "
              "(\"approved as presented ... proceed with implementation on the review site\"). CHRIS BANKS HAS NOT APPROVED: "
              "flagged claims on this page need his signature before production (COPY-PROVENANCE.md, Batch 5 and 6). "
              "Applied 15 September 2026 by compose-content.py")
BATCH2 = ("Batch 2 document, sent to Chris and Dan for approval 25 August 2026. APPROVED BY CHRIS BANKS AND DAN BANKS "
          "per John Jopson, 16 September 2026; the approval message itself is not filed in this workspace "
          "(COPY-PROVENANCE.md). Applied to the review site on Janet Biag's Asana instruction of 16 September 2026 "
          "(\"please replace ... with the provided content\"). Applied 16 September 2026 by compose-content.py")
SOURCE_NOTES = {
    "data-security-and-privacy": BATCH2,
    "what-is-included": BATCH2,
    "how-we-screen-and-hire": BATCH2,
    "staff": BATCH2,
}

# Batch 2 documents end with writer material after the last section: an
# "Internal links" table, a "BRANDING CHECK" table and "Production notes".
# None of it is copy. Parsing stops at the first of these.
END_MARKERS = ("Internal links", "BRANDING CHECK", "Production notes")

# Writer instructions that sit INSIDE a copy section. They are not copy; they
# become an HTML comment so the instruction survives for the copy team.
COPY_TEAM_NOTES = ("Placeholder section. Replace this note",
                   # Batch 2, What Is Included: Ernest's two in-section annotations.
                   "Inclusions list matches the confirmed set exactly",
                   "Pending confirmation on the register",
                   # Batch 7 (utility and legal pages): build and legal-review
                   # instructions written inside copy sections.
                   "Calendar booking tool renders here",
                   "Registered entity name, ABN, phone and hours are placeholders",
                   "Form fields:",
                   "Response standard pending confirmation",
                   "A link or embedded application form",
                   "Live vacancy listings are phase two",
                   "This section requires particular solicitor attention")

PHOTO_NOTE = "<!-- PHOTOGRAPH %s: supplied by Janet Biag 2026-09-11 (approved set, Drive folder 1JDVoV0JKMYdYgzyWrtEdIVAwYxs0a5qq), applied 2026-09-11. Provenance and what it shows: PHOTOGRAPHY.md. -->"


# ----------------------------------------------------------------- parsing ---

def _text(fragment):
    return html.unescape("".join(re.findall(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>", fragment, flags=re.S))).strip()


def _para_kind(p):
    return "bullet" if ("<w:numPr>" in p or 'w:hanging="200"' in p) else "para"


def body_items(path):
    """Yield ('p', kind, text) and ('table', rows) in document order."""
    xml = zipfile.ZipFile(path).read("word/document.xml").decode()
    for m in re.finditer(r"<w:tbl>.*?</w:tbl>|<w:p[ >].*?</w:p>", xml, flags=re.S):
        chunk = m.group(0)
        if chunk.startswith("<w:tbl>"):
            rows = []
            for tr in re.findall(r"<w:tr[ >].*?</w:tr>", chunk, flags=re.S):
                cells = [_text(tc) for tc in re.findall(r"<w:tc>.*?</w:tc>", tr, flags=re.S)]
                rows.append(cells)
            yield ("table", rows)
        else:
            t = _text(chunk)
            if t:
                yield ("p", _para_kind(chunk), t)


def parse(path):
    doc = {"meta": None, "meta_title": None, "url": None, "header": None, "sections": []}
    cur = None
    for item in body_items(path):
        if item[0] == "table":
            if cur is None:
                for row in item[1]:
                    if len(row) >= 2 and row[0] == "Meta description":
                        doc["meta"] = row[1]
                    if len(row) >= 2 and row[0] == "Meta title":
                        doc["meta_title"] = row[1]
                    if len(row) >= 2 and row[0] == "URL":
                        doc["url"] = row[1]
                continue
            cur["blocks"].append(("table", item[1]))
            continue
        _, kind, text = item
        if text in END_MARKERS:
            break
        if doc["header"] is None and re.search(r"Batch \d", text):
            doc["header"] = text
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
            mm = re.match(r"^CTA\s{2,}(.+?)\s{2,}links to\s{2,}(\S+)$", text)
            if not mm:
                sys.exit(f"unparsed CTA in {path}: {text!r}")
            cur["blocks"].append(("cta", mm.group(1).strip(), mm.group(2).strip()))
        elif text.startswith(COPY_TEAM_NOTES):
            cur["blocks"].append(("note", text))
        elif re.match(r"^H\d\s", text):
            sys.exit(f"unrecognised heading marker in {path}: {text!r}")
        elif kind == "bullet":
            cur["blocks"].append(("li", text))
        else:
            cur["blocks"].append(("p", text))
    if not doc["sections"]:
        doc = parse_legal(path, doc)
    for s in doc["sections"]:
        if s["h1"] and s["id"] != "1":
            sys.exit(f"{path}: H1 outside section 1")
    return doc


def parse_legal(path, doc):
    """Batch 7's five legal drafts carry no SECTION markers. Their copy is the
    LEGAL DRAFT notice (kept visible: the review site must show these are not
    final) and, after "Draft content", numbered headings ("1. OVERVIEW") each
    followed by paragraphs, bullets or a table. Bracketed placeholders stay
    visible, on John's instruction of 2 Oct 2026."""
    intro = {"id": "0", "name": "LEGAL DRAFT", "h1": None, "h2": None, "blocks": []}
    doc["sections"] = [intro]
    cur, started = None, False
    for item in body_items(path):
        if item[0] == "table":
            if cur is not None:
                cur["blocks"].append(("table", item[1]))
            continue
        _, kind, text = item
        if text.startswith("LEGAL DRAFT:"):
            intro["blocks"].append(("p", text))
            continue
        if text == "Draft content":
            started = True
            continue
        if not started:
            continue
        m = re.match(r"^(\d+)\.\s+[A-Z][A-Z ,'&-]+$", text)
        if m:
            cur = {"id": m.group(1), "name": text, "h1": None, "h2": text, "blocks": []}
            doc["sections"].append(cur)
        elif cur is None:
            sys.exit(f"{path}: legal copy before the first numbered heading: {text!r}")
        elif text.startswith(COPY_TEAM_NOTES):
            cur["blocks"].append(("note", text))
        elif text.startswith("CTA  "):
            mm = re.match(r"^CTA\s{2,}(.+?)\s{2,}links to\s{2,}(\S+)$", text)
            if not mm:
                sys.exit(f"unparsed CTA in {path}: {text!r}")
            cur["blocks"].append(("cta", mm.group(1).strip(), mm.group(2).strip()))
        else:
            cur["blocks"].append(("li" if kind == "bullet" else "p", text))
    if len(doc["sections"]) < 2 or not intro["blocks"]:
        sys.exit(f"{path}: not a Batch 7 legal draft")
    return doc


def copy_strings(doc):
    """Every string the document asks to be published, in document order."""
    out = []
    for s in doc["sections"]:
        if s["h1"]:
            out.append(s["h1"])
        if s["h2"]:
            out.append(s["h2"])
        for b in s["blocks"]:
            if b[0] in ("p", "li", "h3"):
                out.append(b[1])
            elif b[0] == "cta":
                out.append(b[1])
            elif b[0] == "kvtable":
                out.extend(c for row in b[1] for c in row if c)
            elif b[0] == "table":
                # ⚠ COLUMN-MAJOR, because the device is two columns of cards and
                # that is the order a reader meets the cells in. The document's
                # table is a two-column split (who does what), not a sequence of
                # rows to be read across, so reading it down each column keeps
                # the order assertion meaningful instead of arbitrary.
                for c in range(len(b[1][0])):
                    out.extend(row[c] for row in b[1] if row[c])
    return out


# ----------------------------------------------------------------- devices ---

def jpeg_size(path):
    with open(path, "rb") as f:
        f.read(2)
        while True:
            b = f.read(1)
            while b and b != b"\xff":
                b = f.read(1)
            m = f.read(1)
            while m == b"\xff":
                m = f.read(1)
            if not m:
                return None
            if m in (b"\xc0", b"\xc1", b"\xc2", b"\xc3", b"\xc5", b"\xc6", b"\xc7", b"\xc9", b"\xca", b"\xcb", b"\xcd", b"\xce", b"\xcf"):
                f.read(3)
                h, w = struct.unpack(">HH", f.read(4))
                return w, h
            ln = struct.unpack(">H", f.read(2))[0]
            f.read(ln - 2)


def photo(name, aspect, eager=False):
    w, h = jpeg_size(os.path.join(HERE, "acs", "assets", "img", name))
    load = "eager" if eager else "lazy"
    return ("<!-- wp:html -->\n" + PHOTO_NOTE % name + "\n"
            f'<figure class="acs-shot"><div class="acs-shot__frame" style="aspect-ratio:{aspect}"><img src="/wp-content/themes/acs/assets/img/{name}" alt="" width="{w}" height="{h}" loading="{load}" decoding="async"></div></figure>\n<!-- /wp:html -->')


def cta_of(b, style):
    if b[2] not in CTA_TARGETS:
        sys.exit(f"unknown CTA target {b[2]!r}; add it to CTA_TARGETS with its current address")
    return (b[1], CTA_TARGETS[b[2]], style)


def paras(s):
    return [b[1] for b in s["blocks"] if b[0] == "p"]


def ctas(s, style):
    return [cta_of(b, style) for b in s["blocks"] if b[0] == "cta"]


def btns(s, style):
    c = ctas(s, style)
    return ("\n" + buttons(c)) if c else ""


def notes(s):
    return "".join("\n<!-- COPY TEAM NOTE, not for publication (from the document): " + esc(b[1]).replace("--", "-") + " -->" for b in s["blocks"] if b[0] == "note")


H2 = lambda s: ci.H2 % esc(s["h2"])
PULL = ci.PULL
RULED = lambda cells: ci.bordered_columns(cells, gap="40", color="paper")


def only(s, kinds):
    extra = {b[0] for b in s["blocks"]} - set(kinds)
    if extra:
        sys.exit(f"section {s['id']} ({s['name']}) carries {sorted(extra)}; its device accepts only {kinds}")


def d_hero(s, eyebrow, img=None, aspect="4/5"):
    only(s, ("p", "cta"))
    left = (ci.EYEBROW % esc(eyebrow) + "\n" if eyebrow else "") + ci.H1 % esc(s["h1"]) + "\n" + ci.SEP + "\n" + prose("\n".join(ci.P_LARGE % esc(p) for p in paras(s)) + btns(s, "ink"))
    if img:
        return group(columns([left, photo(img, aspect, eager=True)], widths=["58%", None], valign="center"), bg="sheet")
    # No photograph: Results, How Your Team Is Supported and Your Australian Team.
    # The last two documents list photographs under "Deliberately excluded", and a
    # people photograph on a "meet the team" page reads as the team it cannot show.
    return group(left, bg="sheet")


def d_points(s, bg=None, top="70", bottom="60"):
    """Lead paragraphs, point cards, closing paragraphs as a pull card."""
    only(s, ("p", "li", "cta", "note"))
    first = next(i for i, b in enumerate(s["blocks"]) if b[0] == "li")
    before = [b[1] for b in s["blocks"][:first] if b[0] == "p"]
    items = [b[1] for b in s["blocks"] if b[0] == "li"]
    after = [b[1] for b in s["blocks"][first:] if b[0] == "p"]
    inner = H2(s) + "\n"
    if before:
        inner += prose("\n".join(ci.P_LEAD % esc(p) for p in before)) + "\n"
    inner += ci.POINTS % "".join(f"<li>{esc(t)}</li>" for t in items)
    if after:
        inner += "\n" + prose("\n".join(PULL % esc(p) for p in after))
    inner += notes(s) + btns(s, "ink" if bg == "structure" else "outline")
    return group(inner, bg=bg, top=top, bottom=bottom)


def role_slugs():
    """Child pages of /staff/, keyed by a normalised title ("&" read as "and")."""
    pages = json.load(open(os.path.join(CONTENT, "pages.json")))
    norm = lambda t: re.sub(r"\s+", " ", t.lower().replace("&", "and")).strip()
    return {norm(p["title"]): p["slug"] for p in pages if p.get("parent") == "staff"}


def d_role_cards(s, bg=None):
    """The Staff directory: heading, lead paragraph, then one card per document
    bullet "Name: summary", linked to the role page whose title is Name. The
    cards replace the template's child-index block, which listed the same eight
    pages from their own summaries."""
    only(s, ("p", "li"))
    slugs = role_slugs()
    cards = []
    for b in s["blocks"]:
        if b[0] != "li":
            continue
        if ": " not in b[1]:
            sys.exit(f"section {s['id']}: role bullet without 'Name: summary' shape: {b[1]!r}")
        name, summary = b[1].split(": ", 1)
        key = re.sub(r"\s+", " ", name.lower().replace("&", "and")).strip()
        if key not in slugs:
            sys.exit(f"section {s['id']}: no role page titled {name!r} under /staff/ (have {sorted(slugs)})")
        cards.append(f'<a class="acs-index__item" href="/staff/{slugs[key]}/"><span class="acs-index__name">{esc(name)}</span><p class="acs-index__summary">{esc(summary)}</p></a>')
    inner = H2(s) + "\n" + prose("\n".join(ci.P_LEAD % esc(p) for p in paras(s))) + "\n"
    inner += '<!-- wp:html -->\n<div class="acs-index">' + "".join(cards) + "</div>\n<!-- /wp:html -->"
    return group(inner, bg=bg, top="70", bottom="60")


def d_ruled(s, lead=0):
    """Paragraphs as ruled columns on the blue field; optional lead paragraphs above."""
    only(s, ("p", "cta"))
    ps = paras(s)
    inner = H2(s) + "\n"
    if lead:
        inner += prose("\n".join(ci.P_LARGE % esc(p) for p in ps[:lead])) + "\n"
    inner += RULED([ci.P_MED % esc(p) for p in ps[lead:]]) + btns(s, "ink")
    return group(inner, bg="structure", text="paper")


def d_pulls(s, bg=None, lead=0, per_row=None, top="60", bottom="60"):
    """Paragraphs as pull cards side by side; optional lead paragraph(s) above."""
    only(s, ("p", "cta", "note"))
    ps = paras(s)
    inner = H2(s) + "\n"
    if lead:
        inner += prose("\n".join(ci.P_LEAD % esc(p) for p in ps[:lead])) + "\n"
    cards = [PULL % esc(p) for p in ps[lead:]]
    per_row = per_row or len(cards)
    rows = [cards[i:i + per_row] for i in range(0, len(cards), per_row)]
    inner += "\n".join(columns(r, gap="40") if len(r) > 1 else prose(r[0]) for r in rows)
    inner += notes(s) + btns(s, "ink" if bg == "structure" else "outline")
    return group(inner, bg=bg, top=top, bottom=bottom)


def d_split(s, img, aspect="3/4", bg=None):
    """Heading, prose and CTA beside a photograph."""
    only(s, ("p", "cta"))
    left = H2(s) + "\n" + prose("\n".join(ci.P % esc(p) for p in paras(s)) + btns(s, "outline"))
    return group(columns([left, photo(img, aspect)], widths=["58%", None], valign="center"), bg=bg, top="70", bottom="60")


def d_prose(s, bg=None):
    """Narrative prose: the first paragraph large, the rest at reading size."""
    only(s, ("p", "cta"))
    ps = paras(s)
    inner = H2(s) + "\n" + prose(ci.P_LARGE % esc(ps[0]) + "\n" + "\n".join(ci.P % esc(p) for p in ps[1:]) + btns(s, "outline"))
    return group(inner, bg=bg, top="70", bottom="60")


def d_qa(s, bg=None, tail=0):
    """Intro paragraph(s), H3 question-and-answer cards; `tail` trailing paragraphs
    of the LAST card are the section's conclusion and render as a pull card."""
    only(s, ("p", "h3"))
    intro, cards, cur = [], [], None
    for b in s["blocks"]:
        if b[0] == "h3":
            cur = [b[1], []]
            cards.append(cur)
        elif cur is None:
            intro.append(b[1])
        else:
            cur[1].append(b[1])
    closing = []
    if tail:
        closing = cards[-1][1][-tail:]
        cards[-1][1] = cards[-1][1][:-tail]
    inner = H2(s) + "\n"
    if intro:
        inner += prose("\n".join(ci.P_LEAD % esc(p) for p in intro)) + "\n"
    inner += '<!-- wp:html -->\n<div class="acs-qa">' + "".join(f'<div class="acs-qa__item"><h3>{esc(t)}</h3><div>' + "".join(f"<p>{esc(p)}</p>" for p in ps) + "</div></div>" for t, ps in cards) + "</div>\n<!-- /wp:html -->"
    if closing:
        inner += "\n" + prose("\n".join(PULL % esc(p) for p in closing))
    return group(inner, bg=bg, top="70", bottom="60")


def d_table(s, bg="field"):
    """Lead paragraph, the document's two-column table as two point-card columns, closing paragraph as a pull card."""
    only(s, ("p", "table"))
    ti = next(i for i, b in enumerate(s["blocks"]) if b[0] == "table")
    rows = s["blocks"][ti][1]
    before = [b[1] for b in s["blocks"][:ti] if b[0] == "p"]
    after = [b[1] for b in s["blocks"][ti:] if b[0] == "p"]
    head, body = rows[0], rows[1:]
    if len(head) != 2 or any(len(r) != 2 for r in body):
        sys.exit(f"section {s['id']}: expected a two-column table")
    cols = []
    for c in range(2):
        cols.append(ci.H3 % esc(head[c]) + "\n" + ci.POINTS % "".join(f"<li>{esc(r[c])}</li>" for r in body))
    inner = H2(s) + "\n" + prose("\n".join(ci.P_LEAD % esc(p) for p in before)) + "\n" + columns(cols, gap="50")
    if after:
        inner += "\n" + prose("\n".join(PULL % esc(p) for p in after))
    return group(inner, bg=bg, top="70", bottom="60")


def d_faq(s, bg=None):
    """Questions as the accordion (the theme builds FAQPage schema from it).
    A document CTA that follows an answer is kept inside that question."""
    only(s, ("p", "h3", "cta"))
    items, cur = [], None
    for b in s["blocks"]:
        if b[0] == "h3":
            cur = [b[1], [], []]
            items.append(cur)
        elif cur is None:
            sys.exit(f"section {s['id']}: content before the first question")
        elif b[0] == "p":
            cur[1].append(b[1])
        else:
            cur[2].append(cta_of(b, "link"))
    out = []
    for q, answers, links in items:
        body = "\n".join(f'    <p class="acs-faq__answer">{esc(a)}</p>' for a in answers)
        body += "".join(f'\n    <p class="acs-faq__cta"><a href="{href}">{esc(label)}</a></p>' for label, href, _ in links)
        out.append(f'  <details class="acs-faq__item">\n    <summary>{esc(q)}</summary>\n{body}\n  </details>')
    heading = s["h2"] or s["name"].capitalize()
    return group(ci.H2 % esc(heading) + "\n" + ci.FAQ % "\n".join(out), bg=bg, top="70", bottom="60")


def _wptable(rows):
    head, body = rows[0], rows[1:]
    th = "".join(f"<th>{esc(c)}</th>" for c in head)
    tb = "".join("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>" for r in body)
    return ('<!-- wp:table {"className":"acs-doc-table"} -->\n<figure class="wp-block-table acs-doc-table"><table>'
            f"<thead><tr>{th}</tr></thead><tbody>{tb}</tbody></table></figure>\n<!-- /wp:table -->")


def _seq(blocks):
    """Render blocks in document order: paragraphs, bullet runs as a list,
    buttons, tables, and writer notes as hidden comments."""
    out, run = [], []
    def flush():
        if run:
            out.append('<!-- wp:list -->\n<ul class="wp-block-list">' + "".join(f"<li>{esc(t)}</li>" for t in run) + "</ul>\n<!-- /wp:list -->")
            run.clear()
    for b in blocks:
        if b[0] == "li":
            run.append(b[1]); continue
        flush()
        if b[0] == "p":
            out.append(ci.P_PLAIN % esc(b[1]))
        elif b[0] == "cta":
            out.append(buttons([cta_of(b, "outline")]))
        elif b[0] in ("table", "kvtable"):
            out.append(_wptable(b[1]))
        elif b[0] == "note":
            out.append("<!-- COPY TEAM NOTE, not for publication (from the document): " + esc(b[1]).replace("--", "-") + " -->")
        else:
            sys.exit(f"_seq cannot render {b[0]!r}")
    flush()
    return "\n".join(out)


def d_seq(s, bg=None):
    """Batch 7 utility sections: the document's blocks in document order under
    its H2, so a CTA that sits between two paragraphs stays between them."""
    blocks = [("kvtable", b[1]) if b[0] == "table" else b for b in s["blocks"]]
    s["blocks"] = blocks
    inner = (H2(s) + "\n" if s["h2"] else "") + prose(_seq(blocks))
    return group(inner, bg=bg, top="70", bottom="60")


def d_keep(s, slug, marker):
    """A section that is a build instruction (the booking widget) over a block
    this page already carries: the writer note becomes a comment and the
    existing block is carried over unchanged, fenced so the verbatim check
    skips it. The block is Janet's enquiry design, wired to acs-lead-capture."""
    only(s, ("note", "p"))
    if paras(s):
        sys.exit(f"section {s['id']}: d_keep found copy, not just a build note")
    cur = open(os.path.join(CONTENT, slug + ".html")).read()
    m = re.search(r"<!-- KEEP:start -->.*?<!-- KEEP:end -->", cur, flags=re.S)
    if m:
        kept = m.group(0)
    else:
        i = cur.index(marker)
        a = cur.rindex("<!-- wp:group", 0, i)
        depth, j = 0, a
        for t in re.finditer(r"<!-- (/?)wp:group", cur[a:]):
            depth += -1 if t.group(1) else 1
            if depth == 0:
                j = a + t.end()
                j = cur.index("-->", j) + 3
                break
        kept = "<!-- KEEP:start -->\n" + cur[a:j] + "\n<!-- KEEP:end -->"
    return notes(s).lstrip("\n") + "\n" + kept


def d_keep_form(s, template):
    """Contact: the hard-coded `contact` template never rendered page content,
    so Batch 7's copy moves the page to content-page (2 Oct 2026). Section 3 is
    a build note over that template's enquiry form; the form is carried over
    unchanged (still presentation only, not wired) and fenced from the verbatim
    check."""
    only(s, ("note",))
    cur = open(os.path.join(CONTENT, "contact.html")).read()
    m = re.search(r"<!-- KEEP:start -->.*?<!-- KEEP:end -->", cur, flags=re.S)
    if m:  # the template was removed once the form moved here (2 Oct 2026)
        return notes(s).lstrip("\n") + "\n" + m.group(0)
    t = open(os.path.join(HERE, "acs", "templates", template + ".html")).read()
    i = t.index('<form class="acs-form"')
    form = t[i:t.index("</form>", i) + len("</form>")]
    kept = ("<!-- KEEP:start -->\n" + group('<!-- wp:html -->\n<div class="acs-enquiry__form">' + form + "</div>\n<!-- /wp:html -->", top="40", bottom="60")
            + "\n<!-- KEEP:end -->")
    return notes(s).lstrip("\n") + "\n" + kept


def d_legal(s):
    """A legal draft section inside the legal template's narrow column: heading
    and body as plain blocks, no bands (the template supplies the page)."""
    if s["id"] == "0":
        return ci.P_PLAIN % esc(s["blocks"][0][1])
    s["blocks"] = [("kvtable", b[1]) if b[0] == "table" else b for b in s["blocks"]]
    return (ci.H2 % esc(s["h2"])) + "\n" + _seq(s["blocks"])


def d_closing(s):
    """The closing band, two columns since 16 Sep 2026 (Janet's QA email: CTA
    sections should read as a B2B call to action). Copy on the left, the
    document's buttons stacked in a light card on the right, first button
    filled. No words are added: the kicker, heading, paragraphs and labels are
    the document's; the card is layout."""
    only(s, ("p", "cta"))
    left = ci.KICKER + "\n" + H2(s) + "\n" + "\n".join(ci.P_PLAIN % esc(p) for p in paras(s))
    c = ctas(s, "ink")
    if not c:
        return group(left, bg="structure-bright", text="paper")
    first = [(c[0][0], c[0][1], "ink")] + [(l, h, "outline") for l, h, _ in c[1:]]
    # Janet, Slack 16 Sep 08:59: the band should also carry a Get Pricing button
    # to the calculator so visitors reach it without the menu. Her label, site
    # level (SITE_LABELS), added only where the document does not already send
    # the reader there.
    if not any(h == CTA_TARGETS["/pricing/build-your-team"] for _, h, _ in first):
        first.append(("Get pricing", CTA_TARGETS["/pricing/build-your-team"], "outline"))
    card = ('<!-- wp:html -->\n<div class="acs-cta-card">' + buttons(first, top_margin=False)
            .replace('<!-- wp:buttons -->\n', '').replace('\n<!-- /wp:buttons -->', '') + '</div>\n<!-- /wp:html -->')
    cols = columns([left, card], widths=["58%", None], valign="center")
    # The theme renders every column on a blue band as a card. The copy column
    # here must not be one (that is the boxed look Janet asked to lose), so the
    # columns block carries a class the stylesheet uses to switch that off.
    cols = cols.replace('<!-- wp:columns {', '<!-- wp:columns {"className":"acs-cta-band",', 1)
    cols = cols.replace('<div class="wp-block-columns', '<div class="wp-block-columns acs-cta-band', 1)
    return group(cols, bg="structure-bright", text="paper")


# ----------------------------------------------------------------- layouts ---
# section id -> (device, kwargs). Photographs are the ones each page already
# carried. How Your Team Is Supported and Your Australian Team carry NONE: both
# documents list photographs under "Deliberately excluded" (a people photograph
# on "Your Australian Team" reads as the team, and none is of the team).

HOW = "How it works"
WHY = "Why ACS"

LAYOUTS = {
    "faqs": {
        "1": (d_hero, dict(eyebrow=HOW, img="team-12.jpg")),
        "2": (d_faq, {}), "3": (d_faq, dict(bg="field")), "4": (d_faq, {}),
        "5": (d_faq, dict(bg="field")), "6": (d_faq, {}),
        "7": (d_closing, {}),
    },
    "onboarding-first-90-days": {
        "1": (d_hero, dict(eyebrow=HOW, img="team-19.jpg")),
        "2": (d_points, {}),
        "3": (d_ruled, {}),
        "4": (d_points, dict(bg="field")),
        "5": (d_points, {}),
        "6": (d_points, dict(bg="field")),
        "7": (d_points, dict(bg="sheet")),
        "8": (d_faq, {}),
        "9": (d_closing, {}),
    },
    "performance-reporting": {
        "1": (d_hero, dict(eyebrow=HOW, img="team-09.jpg")),
        "2": (d_points, {}),
        "3": (d_table, dict(bg="field")),
        "4": (d_points, {}),
        "5": (d_points, dict(bg="sheet")),
        "6": (d_ruled, dict(lead=1)),
        "7": (d_faq, {}),
        "8": (d_closing, {}),
    },
    "how-your-team-is-supported": {
        "1": (d_hero, dict(eyebrow=WHY)),
        "2": (d_ruled, {}),
        "3": (d_points, {}),
        "4": (d_pulls, dict(bg="field")),
        "5": (d_pulls, dict(bg="sheet", top="70", bottom="70")),
        "6": (d_points, dict(bg="field")),
        "7": (d_faq, {}),
        "8": (d_closing, {}),
    },
    "our-story": {
        "1": (d_hero, dict(eyebrow=WHY, img="team-06.jpg", aspect="4/3")),
        "2": (d_prose, {}),
        "3": (d_split, dict(img="team-01.jpg", bg="field")),
        "4": (d_qa, dict(tail=1)),
        "5": (d_prose, dict(bg="sheet")),
        "6": (d_faq, {}),
        "7": (d_closing, {}),
    },
    "results": {
        "1": (d_hero, dict(eyebrow=WHY)),
        "2": (d_ruled, {}),
        "3": (d_pulls, {}),
        "4": (d_points, dict(bg="field")),
        "5": (d_pulls, {}),
        "5B": (d_pulls, dict(bg="sheet", top="70", bottom="70")),
        "6": (d_ruled, {}),
        "7": (d_faq, {}),
        "8": (d_closing, {}),
    },
    "why-acs": {
        "1": (d_hero, dict(eyebrow=None, img="team-01.jpg")),
        "2": (d_split, dict(img="team-06.jpg")),
        "3": (d_ruled, {}),
        "4": (d_pulls, dict(bg="field", lead=1)),
        "5": (d_pulls, {}),
        "5B": (d_ruled, {}),
        "5C": (d_pulls, dict(bg="field", lead=1, per_row=2)),
        "6": (d_closing, {}),
    },
    "your-australian-team": {
        "1": (d_hero, dict(eyebrow=WHY)),
        "2": (d_ruled, {}),
        "3": (d_qa, {}),
        "4": (d_pulls, dict(bg="field")),
        "4B": (d_pulls, dict(bg="sheet", top="70", bottom="70")),
        "5": (d_ruled, {}),
        "6": (d_faq, {}),
        "7": (d_closing, {}),
    },
    # Batch 2. team-16.jpg is the photograph this page already carried (hands
    # typing, no face), kept on a page about data handling. No eyebrow: the
    # document's own table header is "How it works", and the same words twice
    # in the first screen reads as a mistake.
    "data-security-and-privacy": {
        "1": (d_hero, dict(eyebrow=None, img="team-16.jpg")),
        "2": (d_table, dict(bg="field")),
        "3": (d_prose, {}),
        "4": (d_ruled, {}),
        "5": (d_closing, {}),
    },
    # Batch 2. team-18.jpg is the photograph the page carried; its frame is the
    # photograph's own 16/9 because the 4/5 frame cut the outer people off
    # (Janet, 16 Sep). Section 2 carries Ernest's "do not add or remove items"
    # note and section 3 his "pending confirmation on the register" note; both
    # become comments for the copy team, never copy.
    "what-is-included": {
        "1": (d_hero, dict(eyebrow=HOW, img="team-18.jpg", aspect="16/9")),
        "2": (d_points, {}),
        "3": (d_pulls, dict(bg="field")),
        "4": (d_prose, {}),
        "5": (d_closing, {}),
    },
    # Batch 2. team-13.jpg kept, frame at its own 3/2 for the same reason.
    "how-we-screen-and-hire": {
        "1": (d_hero, dict(eyebrow=HOW, img="team-13.jpg", aspect="3/2")),
        "2": (d_qa, {}),
        "3": (d_prose, {}),
        "4": (d_prose, dict(bg="field")),
        "5": (d_closing, {}),
    },
    # Batch 2. The directory: no photograph (it never had one), the eight role
    # bullets rendered as the eight cards Janet asked to keep.
    "staff": {
        "1": (d_hero, dict(eyebrow=None)),
        "2": (d_role_cards, {}),
        "3": (d_prose, {}),
        "4": (d_prose, dict(bg="field")),
        "5": (d_ruled, {}),
        "6": (d_closing, {}),
    },
}

LAYOUTS.update({
    "book-a-call": {
        "1": (d_hero, dict(eyebrow=None, img="janet-book-a-call-1.jpg")),
        "2": (d_points, {}),
        "3": (d_keep, dict(slug="book-a-call", marker='data-acs-surface="bookACall"')),
        "4": (d_seq, dict(bg="field")),
    },
    "contact": {
        "1": (d_hero, dict(eyebrow=None)),
        "2": (d_seq, {}), "3": (d_keep_form, dict(template="contact")), "4": (d_seq, dict(bg="field")),
    },
    "get-a-quote": {
        "1": (d_hero, dict(eyebrow=None, img="janet-get-a-quote-1.jpg")),
        "2": (d_seq, {}), "3": (d_seq, {}), "4": (d_seq, dict(bg="field")),
    },
    "thank-you": {
        "1": (d_hero, dict(eyebrow=None)),
        "2": (d_seq, {}), "3": (d_seq, dict(bg="field")),
    },
    "work-with-us": {
        "1": (d_hero, dict(eyebrow=None)),
        "2": (d_seq, {}), "3": (d_seq, dict(bg="field")), "4": (d_seq, {}), "5": (d_seq, dict(bg="field")),
    },
})
LEGAL_SLUGS = {"candidate-privacy", "cookies", "pricing-disclaimer", "privacy-policy", "terms"}

SITE_LABELS = {"Next", HOW, WHY, "Common questions", "Get pricing"}
# "  links to  " with the document's double spaces: an unparsed CTA line. The bare
# words are ordinary prose ("Each card links to a page", Staff, Batch 2).
LEAK_MARKERS = ["SECTION ", "H1  ", "H2  ", "H3  ", "CTA  ", "  links to  ", "Meta description", "Meta title",
                "Keyword", "Deliberately excluded", "LAUNCH STATE", "PUBLISHING NOTE", "Live copy",
                "Primary buyer", "Page goal", "Placeholder section", "Written as", "w:t", "w:p", "<w:"]


def compose(doc, slug, source):
    if slug in LEGAL_SLUGS:
        layout = {s["id"]: (d_legal, {}) for s in doc["sections"]}
    else:
        layout = LAYOUTS[slug]
    ids = [s["id"] for s in doc["sections"]]
    if ids != list(layout):
        sys.exit(f"{slug}: document sections {ids} do not match the layout {list(layout)}")
    out = [f"<!-- Copy source: {source}. {SOURCE_NOTES.get(slug, DAN_15_SEP)}, every section verbatim in document order. CTA targets rendered at the page's CURRENT address pending Janet and Ernest's URL pass. -->"]
    for s in doc["sections"]:
        fn, kw = layout[s["id"]]
        out.append(fn(s, **kw))
    return "\n".join(out) + "\n"


# -------------------------------------------------------------- assertions ---

def visible_nodes(markup):
    markup = re.sub(r"<!-- KEEP:start -->.*?<!-- KEEP:end -->", " ", markup, flags=re.S)
    live = re.sub(r"<!--.*?-->", " ", markup, flags=re.S)
    return [html.unescape(t).strip() for t in re.split(r"<[^>]+>", live) if t.strip()]


def assert_verbatim(doc, markup, slug):
    wanted = copy_strings(doc)
    nodes = visible_nodes(markup)
    # A document bullet of the form "Name: summary" may render as a card with
    # the name and the summary in two adjacent elements (the Staff directory).
    # Two adjacent nodes are read as one only when their join with ": " IS a
    # document string and neither half is one on its own, so nothing else
    # gets stitched together.
    wanted_set, merged, i = set(wanted), [], 0
    while i < len(nodes):
        if (i + 1 < len(nodes) and nodes[i] not in wanted_set
                and nodes[i] + ": " + nodes[i + 1] in wanted_set):
            merged.append(nodes[i] + ": " + nodes[i + 1])
            i += 2
        else:
            merged.append(nodes[i])
            i += 1
    nodes = merged
    # 1. every document string is the whole text of an element, in order
    pos = 0
    for w in wanted:
        try:
            pos = nodes.index(w, pos) + 1
        except ValueError:
            where = "anywhere" if w not in nodes else "in document order"
            sys.exit(f"{slug}: VERBATIM FAIL, not found {where}: {w!r}")
    # 2. nothing visible that is not the document's or a declared site label
    extra = [n for n in nodes if n not in set(wanted) | SITE_LABELS]
    if extra:
        sys.exit(f"{slug}: VERBATIM FAIL, text not in the document: {extra}")
    # counts must match exactly (no string duplicated or dropped). A site label
    # may appear on top of the document's own uses of the same words, never
    # instead of them: Batch 2's Data Security table is headed "How it works",
    # which is also the section eyebrow, and dropping every label occurrence
    # before counting made that document unpassable (found 16 Sep 2026).
    from collections import Counter
    cn, cw = Counter(nodes), Counter(wanted)
    for lab in SITE_LABELS:
        if cn[lab] >= cw[lab]:
            cn[lab] = cw[lab]
    cn, cw = +cn, +cw
    if cn != cw:
        sys.exit(f"{slug}: VERBATIM FAIL, occurrence counts differ: {(cn - cw) or ''} {(cw - cn) or ''}")
    labels = [n for n in nodes if n in SITE_LABELS]
    live = re.sub(r"<!-- KEEP:start -->.*?<!-- KEEP:end -->", " ", markup, flags=re.S)
    live = re.sub(r"<!--.*?-->", " ", live, flags=re.S)
    for marker in LEAK_MARKERS:
        if marker in live:
            sys.exit(f"{slug}: BRIEF LEAK, {marker!r} is visible markup")
    words_doc = sum(len(w.split()) for w in wanted)
    words_page = sum(len(n.split()) for n in nodes if n not in SITE_LABELS)
    return words_doc, words_page, labels


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    apply, dump = "--apply" in sys.argv, "--dump" in sys.argv
    # --only=slug[,slug]: compose just those pages. Without it every document in
    # DOCS must be present, so a later batch cannot silently re-write an earlier one.
    only = next((a[len("--only="):].split(",") for a in sys.argv[1:] if a.startswith("--only=")), None)
    docs = {n: s for n, s in DOCS.items() if not only or s in only}
    if only and len(docs) != len(only):
        sys.exit(f"--only names a slug with no document: {sorted(set(only) - set(docs.values()))}")
    if not args:
        sys.exit(__doc__)
    manifest_path = os.path.join(CONTENT, "pages.json")
    pages = json.load(open(manifest_path))
    by_slug = {p["slug"]: p for p in pages}
    found = {}
    for d in args:
        for name in sorted(os.listdir(d)):
            if name in docs:
                found[name] = os.path.join(d, name)
    missing = set(docs) - set(found)
    if missing:
        sys.exit(f"documents not found: {sorted(missing)}")
    report = []
    for name, path in sorted(found.items()):
        slug = DOCS[name]
        doc = parse(path)
        if dump:
            print("=" * 20, slug, "|", doc["header"], "|", doc["url"], "|", doc["meta_title"])
            for s in doc["sections"]:
                print(f"  [{s['id']}] {s['name']} | H1={s['h1']!r} H2={s['h2']!r}")
                for b in s["blocks"]:
                    print("     ", b[0], (b[1] if b[0] != "table" else b[1])[:110] if b[0] != "table" else b[1], *(b[2:] if b[0] == "cta" else []))
            continue
        if slug in LEGAL_SLUGS and not doc["meta"]:
            doc["meta"] = by_slug[slug]["description"]  # legal drafts carry no meta; the manifest's stands
        if not doc["meta"] or not (50 <= len(doc["meta"]) <= 170):
            sys.exit(f"{slug}: meta description missing or outside 50-170 chars ({len(doc['meta'] or '')}): {doc['meta']!r}")
        markup = compose(doc, slug, f"{name} ({doc['header']})")
        wd, wp, labels = assert_verbatim(doc, markup, slug)
        report.append((slug, wd, wp, len(doc["meta"]), labels, doc["url"], doc["meta_title"]))
        if apply:
            with open(os.path.join(CONTENT, slug + ".html"), "w") as f:
                f.write(markup)
            by_slug[slug]["description"] = doc["meta"]
    if dump:
        return
    if apply:
        with open(manifest_path, "w") as f:
            json.dump(pages, f, indent=1, ensure_ascii=False)
            f.write("\n")
    for slug, wd, wp, ml, labels, url, mt in report:
        print(f"{slug:28} doc {wd:5} words, page {wp:5} words, meta {ml} chars, site labels {labels}  (doc URL {url}; meta title not supported by theme: {mt!r})")
    print("verbatim + leak assertions: PASS on all", len(report), "pages", "(written)" if apply else "(dry run, nothing written)")


if __name__ == "__main__":
    main()
