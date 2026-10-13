#!/usr/bin/env python3
"""Janet's image asks on three story pages, filled from photographs nobody is using.

    python3 websites/acs/place-story-photos.py SCRATCH_JANET_DIR

2026-09-28. Her 16 Sep comments ask for images the page-named set does not cover:
  - How Your Team Is Supported: "add a relevant image on the right side" of the
    text-only hero;
  - Results: an image in the hero, and the "case studies are approved" section
    "compressed to the left ... widen the content area or add a relevant image";
  - Our Story: "a relevant image beside the text, alternating the placement
    between sections".
Filled only from photographs used NOWHERE else on the site, so nothing repeats:
her two different 17 Sep photos with no slot (faqs 2, operations-assistants 2)
and four from her approved 11 Sep set that today's changes freed (team-12,
team-14, team-15, team-19). Every frame takes the photograph's own ratio.

Our Story and Results are restored to their pre-removal state (commit
286dba7~1) so the image slots sit where the layout designed them; the slots not
filled here are removed again by remove-empty-slots.py afterwards.
"""
import os, re, subprocess, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
C = os.path.join(HERE, 'content')
IMG = os.path.join(HERE, 'acs', 'assets', 'img')
FOLDER = '1JDVoV0JKMYdYgzyWrtEdIVAwYxs0a5qq'
SLOT = re.compile(r'<!-- IMAGE SLOT, EMPTY\.[^\n]*-->\n<figure class="acs-shot acs-shot--empty">.*?</figure>', re.S)


def figure(fname, w, h, why, eager=False):
    g = __import__('math').gcd(w, h)
    load = 'loading="eager" fetchpriority="high"' if eager else 'loading="lazy"'
    return (f'<!-- PHOTOGRAPH {fname}: {why} Frame at the photograph\'s own ratio, 100% kept. '
            f'Placed 28 Sep 2026 for Janet\'s 16 Sep comment on this page. Used once only. See PHOTOGRAPHY.md. -->\n'
            f'<figure class="acs-shot"><div class="acs-shot__frame" style="aspect-ratio:{w // g}/{h // g}">'
            f'<img src="/wp-content/themes/acs/assets/img/{fname}" alt="" width="{w}" height="{h}" {load} decoding="async"></div></figure>')


def janet_copy(src, name):
    im = Image.open(src).convert('RGB').resize((1200, 1500), Image.LANCZOS)
    im.save(os.path.join(IMG, name), 'JPEG', quality=82, optimize=True, progressive=True)
    return 1200, 1500


def size(name):
    with Image.open(os.path.join(IMG, name)) as im:
        return im.size


def restore(slug):
    txt = subprocess.run(['git', 'show', f'286dba7~1:websites/acs/content/{slug}.html'],
                         cwd=HERE, capture_output=True, text=True, check=True).stdout
    open(os.path.join(C, slug + '.html'), 'w').write(txt)
    return txt


def fill(txt, n, fig):
    slots = list(SLOT.finditer(txt))
    a, b = slots[n - 1].span()
    return txt[:a] + fig + txt[b:]


def hero_columns(txt, fig):
    """Wrap the FIRST top-level group's inner blocks in the site's hero columns, image right.

    Found on 28 Sep: a regex stopped at the first `</div><!-- /wp:group -->`, which
    belongs to a group NESTED inside the hero, and produced a broken block tree.
    The span now comes from the block parser, and the result is re-parsed.
    """
    rm = __import__('importlib').import_module('remove-empty-slots'.replace('-', '_')) if False else None
    import importlib.util
    spec = importlib.util.spec_from_file_location('res', os.path.join(HERE, 'remove-empty-slots.py'))
    res = importlib.util.module_from_spec(spec); spec.loader.exec_module(res)
    hero = next(b for b in res.parse(txt).children if b.name == 'group')
    body = txt[hero.open_end:hero.close_start]
    m = re.match(r'(\s*<div class="wp-block-group[^"]*"[^>]*>)(.*)(</div>\s*)$', body, re.S)
    assert m and 'wp:columns' not in m.group(2), 'hero shape not recognised, or already has columns'
    cols = ('<!-- wp:columns {"verticalAlignment": "center", "style": {"spacing": {"blockGap": {"top": "var:preset|spacing|50", "left": "var:preset|spacing|70"}}}} -->\n'
            '<div class="wp-block-columns are-vertically-aligned-center"><!-- wp:column {"verticalAlignment": "center", "width": "52%"} -->\n'
            '<div class="wp-block-column is-vertically-aligned-center" style="flex-basis:52%">' + m.group(2) + '</div>\n'
            '<!-- /wp:column -->\n<!-- wp:column {"verticalAlignment": "center"} -->\n'
            '<div class="wp-block-column is-vertically-aligned-center"><!-- wp:html -->\n' + fig + '\n<!-- /wp:html --></div>\n'
            '<!-- /wp:column --></div>\n<!-- /wp:columns -->')
    out = txt[:hero.open_end] + m.group(1) + cols + m.group(3) + txt[hero.close_start:]
    res.parse(out)  # raises if the tree is broken
    return out


def swap_columns(txt, needle):
    import importlib.util
    spec = importlib.util.spec_from_file_location('res', os.path.join(HERE, 'remove-empty-slots.py'))
    res = importlib.util.module_from_spec(spec); spec.loader.exec_module(res)
    for b in res.walk(res.parse(txt)):
        cols = [c for c in b.children if c.name == 'column']
        if b.name == 'columns' and len(cols) == 2 and any(needle in txt[c.start:c.end] for c in cols):
            a, c = cols
            out = txt[:a.start] + txt[c.start:c.end] + txt[a.end:c.start] + txt[a.start:a.end] + txt[c.end:]
            res.parse(out)
            return out
    raise SystemExit('no two-column row holds ' + needle)


def main():
    J = sys.argv[1]
    w, h = janet_copy(os.path.join(J, 'faqs-2.jpg'), 'janet-faqs-2.jpg')
    p = os.path.join(C, 'how-your-team-is-supported.html')
    txt = subprocess.run(['git', 'show', f'HEAD:websites/acs/content/how-your-team-is-supported.html'],
                         cwd=HERE, capture_output=True, text=True, check=True).stdout
    txt = hero_columns(txt, figure('janet-faqs-2.jpg', w, h, f'supplied by Janet Biag, Drive folder {FOLDER}, uploaded 17 Sep 2026 as "faqs (2).jpg" (a different photograph from faqs.jpg).', eager=True))
    open(p, 'w').write(txt)

    w, h = janet_copy(os.path.join(J, 'operations-assistants-2.jpg'), 'janet-operations-assistants-2.jpg')
    txt = restore('results')
    txt = fill(txt, 2, figure('team-12.jpg', *size('team-12.jpg'), 'supplied by Janet Biag 11 Sep 2026 (approved set).'))
    txt = hero_columns(txt, figure('janet-operations-assistants-2.jpg', w, h, f'supplied by Janet Biag, Drive folder {FOLDER}, uploaded 17 Sep 2026 as "operations-assistants (2).jpg" (a different photograph from operations-assistants.jpg).', eager=True))
    open(os.path.join(C, 'results.html'), 'w').write(txt)

    txt = restore('our-story')
    for n, name in ((1, 'team-19.jpg'), (2, 'team-14.jpg'), (3, 'team-15.jpg')):
        # fill in order; each fill removes one slot, so the next is always slot 1
        txt = fill(txt, 1, figure(name, *size(name), 'supplied by Janet Biag 11 Sep 2026 (approved set).'))
    # Janet: "alternating the image placement between sections". The layout had
    # right, right, (no image), left; swapping sections 2 and 4 gives right,
    # left, (text), right. Shapes by text length: portraits beside the two long
    # sections, the landscape beside the shorter one.
    txt = swap_columns(txt, 'team-14.jpg')
    txt = swap_columns(txt, 'team-15.jpg')
    open(os.path.join(C, 'our-story.html'), 'w').write(txt)
    print('placed: how-your-team-is-supported hero; results hero + case-studies section; our-story three sections')


if __name__ == '__main__':
    main()
