#!/usr/bin/env python3
"""Place Janet Biag's 17 September photographs into their page slots.

    python3 websites/acs/apply-janet-photos.py SOURCE_DIR [--apply]

SOURCE_DIR holds the Drive originals renamed `<page-slug>-<n>.jpg` (Drive's
"<slug>.jpg" is n=1, "<slug> (2).jpg" is n=2, and so on). Without --apply it
prints the plan and writes nothing.

Why this exists (2026-09-28): Janet uploaded 51 named photographs to the ACS
Drive folder `1JDVoV0JKMYdYgzyWrtEdIVAwYxs0a5qq` on 17 Sep 07:05 PHT, the
morning after the image system put 48 slots on placeholders waiting for them.
Nobody downloaded them. She reposted the link on Asana "Final photography"
on 24 Sep. They sat unused for eleven days.

⚠ Most "(2)" files are NOT second photographs. 16 of the 19 "(2)/(3)" files are
the SAME photograph as that page's first file, cropped square (checked by eye on
a contact sheet, 28 Sep). Placing both would repeat one image on one page. They
are excluded from SOURCE_DIR before running; only three are different pictures
(faqs 2, operations-assistants 2, who-employs-your-staff 2).

Placement:
  - photo n goes into the n-th image slot on its page, in document order;
  - the frame takes the PHOTOGRAPH's own ratio, so nothing is cropped (John,
    16 Sep: vertical, not cropped or sliced);
  - a photo whose page has fewer slots than n is HELD and reported, never
    given a layout nobody asked for;
  - photo 1 replaces whatever is in slot 1, including an older stock image,
    because she made it for that page. Slot 1 loads eagerly; the rest lazily.

Web copies: 4:5 at 1200x1500, 1:1 at 1200x1200, progressive JPEG q82, named
`janet-<slug>-<n>.jpg` so the page a file belongs to is readable from the name.
"""
import os, re, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, 'acs', 'assets', 'img')
CONTENT = os.path.join(HERE, 'content')
FOLDER = '1JDVoV0JKMYdYgzyWrtEdIVAwYxs0a5qq'

# The comment line immediately before a figure (IMAGE SLOT or PHOTOGRAPH), then the figure.
SLOT = re.compile(r'(<!-- (?:IMAGE SLOT|PHOTOGRAPH)[^\n]*?-->\n)?(<figure class="acs-shot[^"]*">.*?</figure>)', re.S)


def web_copy(src, dest):
    im = Image.open(src).convert('RGB')
    w, h = im.size
    size = (1200, 1500) if h * 4 == w * 5 else (1200, 1200) if w == h else None
    if size is None:
        sys.exit(f'{src}: {w}x{h} is neither 4:5 nor 1:1; place it by hand')
    im.resize(size, Image.LANCZOS).save(dest, 'JPEG', quality=82, optimize=True, progressive=True)
    return size


def figure(fname, size, eager):
    w, h = size
    ratio = '4/5' if h > w else '1/1'
    load = 'loading="eager" fetchpriority="high"' if eager else 'loading="lazy"'
    return (f'<figure class="acs-shot"><div class="acs-shot__frame" style="aspect-ratio:{ratio}">'
            f'<img src="/wp-content/themes/acs/assets/img/{fname}" alt="" width="{w}" height="{h}" '
            f'{load} decoding="async"></div></figure>')


def main():
    src_dir, apply = sys.argv[1], '--apply' in sys.argv
    photos = {}
    for f in sorted(os.listdir(src_dir)):
        m = re.fullmatch(r'(.+)-(\d)\.jpg', f)
        if m:
            photos.setdefault(m.group(1), []).append((int(m.group(2)), f))
    placed, held = [], []
    for slug, items in sorted(photos.items()):
        path = os.path.join(CONTENT, slug + '.html')
        if not os.path.exists(path):
            held += [(slug, n, 'no content file') for n, _ in items]; continue
        text = open(path).read()
        slots = list(SLOT.finditer(text))
        edits = []
        for n, f in sorted(items):
            if n > len(slots):
                held.append((slug, n, f'page has {len(slots)} slot(s)')); continue
            fname = f'janet-{slug}-{n}.jpg'
            size = web_copy(os.path.join(src_dir, f), os.path.join(IMG, fname)) if apply else None
            if not apply:
                with Image.open(os.path.join(src_dir, f)) as im:
                    size = (1200, 1500) if im.size[1] > im.size[0] else (1200, 1200)
            was = 'placeholder' if 'acs-shot--empty' in slots[n - 1].group(2) else 'stock photo'
            orig = f'{slug}.jpg' if n == 1 else f'{slug} ({n}).jpg'
            note = (f'<!-- PHOTOGRAPH {fname}: supplied by Janet Biag, Drive folder {FOLDER}, '
                    f'uploaded 17 Sep 2026 as "{orig}". Web copy {size[0]}x{size[1]}, frame at the '
                    f'photograph\'s own ratio, 100% kept. Replaced a {was} on 28 Sep 2026. '
                    f'Used once only. See PHOTOGRAPHY.md. -->\n')
            edits.append((slots[n - 1].span(), note + figure(fname, size, n == 1)))
            placed.append((slug, n, was, size))
        for (a, b), new in sorted(edits, reverse=True):
            text = text[:a] + new + text[b:]
        if apply and edits:
            open(path, 'w').write(text)
    for p in placed:
        print(f'PLACE  {p[0]:32} photo {p[1]} -> slot {p[1]} ({p[2]}), {p[3][0]}x{p[3][1]}')
    for h in held:
        print(f'HOLD   {h[0]:32} photo {h[1]}: {h[2]}')
    print(f'{len(placed)} placed, {len(held)} held' + ('' if apply else '  (dry run, nothing written)'))


if __name__ == '__main__':
    main()
