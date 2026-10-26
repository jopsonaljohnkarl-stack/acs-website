#!/usr/bin/env python3
"""Remove every empty image slot, and unwrap the text column it leaves behind.

    python3 websites/acs/remove-empty-slots.py [--apply]

John, 2026-09-28: "remove the empty slots". 103 "Image here" placeholders sat on
39 pages of the review site; Janet supplied one photograph per page, not five.
Her own layout rule (16 Sep) asks for a single-column reading flow with a
controlled measure OR text beside an image, so a text-only section is within it.

Also removes, on ROLE pages only, the content slot holding `janet-<slug>-1.jpg`:
the role template's hero now renders that photograph (functions.php, 28 Sep),
so leaving it lower down would show it twice.

It works on the block comment tree, not on regexes over divs:
  - the slot is the `wp:html` block holding the figure;
  - if that block is the only thing in its `wp:column`, the column goes;
  - if the `wp:columns` then has one column left, the columns wrapper AND that
    column's own <div> are dropped and its inner blocks stand on their own,
    so the text does not sit at 52% of an empty row.
Without --apply it prints what it would do and writes nothing. Re-running is
safe: a page with no empty slot is left byte-identical.
"""
import glob, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROLE_PAGES = {'bookkeepers', 'admin-assistants', 'operations-assistants', 'telesales', 'accounting-finance',
              'operations-managers', 'social-media-managers', 'ai-automation-specialists'}
TOKEN = re.compile(r'<!-- (/?)wp:([a-z0-9/-]+)(.*?)(/?)-->', re.S)


class Block:
    def __init__(self, name, start, open_end):
        self.name, self.start, self.open_end = name, start, open_end
        self.close_start = self.end = None
        self.children, self.parent = [], None


def parse(text):
    root = Block('root', 0, 0); root.end = len(text); stack = [root]
    for m in TOKEN.finditer(text):
        closing, name, selfclose = m.group(1), m.group(2), m.group(4)
        if closing:
            b = stack.pop()
            if b.name != name:
                raise ValueError(f'mismatched block: opened {b.name}, closed {name} at {m.start()}')
            b.close_start, b.end = m.start(), m.end()
        else:
            b = Block(name, m.start(), m.end()); b.parent = stack[-1]; stack[-1].children.append(b)
            if selfclose:
                b.close_start = b.end = m.end()
            else:
                stack.append(b)
    if len(stack) != 1:
        raise ValueError('unclosed block ' + stack[-1].name)
    return root


def walk(b):
    for c in b.children:
        yield c; yield from walk(c)


def inner_of_column(text, col):
    """The column's inner blocks, without its own <div ...> and </div>."""
    body = text[col.open_end:col.close_start]
    body = re.sub(r'^\s*<div class="wp-block-column[^"]*"[^>]*>', '', body, count=1)
    body = re.sub(r'</div>\s*$', '', body, count=1)
    return body.strip('\n')


def plan(text, extra_photo=None):
    """Return a list of (start, end, replacement) edits, outermost first."""
    root = parse(text)
    edits = []
    for b in walk(root):
        if b.name != 'html':
            continue
        chunk = text[b.open_end:b.close_start]
        target = 'acs-shot--empty' in chunk or (extra_photo and f'assets/img/{extra_photo}' in chunk)
        if not target:
            continue
        col = b.parent
        if col.name == 'column' and len(col.children) == 1:
            cols = col.parent
            rest = [c for c in cols.children if c is not col]
            if cols.name == 'columns' and len(rest) == 1 and rest[0].name == 'column':
                edits.append((cols.start, cols.end, inner_of_column(text, rest[0])))
            else:
                edits.append((col.start, col.end, ''))
        else:
            edits.append((b.start, b.end, ''))
    # Two slots in one columns wrapper would both claim it; keep one edit per span.
    seen, out = set(), []
    for e in sorted(edits, key=lambda e: (e[0], -e[1])):
        if any(e[0] >= s and e[1] <= t for s, t in seen):
            continue
        seen.add((e[0], e[1])); out.append(e)
    return out


def main():
    apply = '--apply' in sys.argv
    files = sorted(glob.glob(os.path.join(HERE, 'content', '*.html')) + glob.glob(os.path.join(HERE, 'acs', 'templates', '*.html')))
    total = 0
    for path in files:
        text = open(path).read()
        slug = os.path.basename(path)[:-5]
        extra = f'acs-{slug}-1.jpg' if slug in ROLE_PAGES else None
        edits = plan(text, extra)
        if not edits:
            continue
        for s, e, rep in sorted(edits, reverse=True):
            text = text[:s] + rep + text[e:]
        parse(text)  # the result must still be a well-formed block tree
        left = text.count('acs-shot--empty')
        total += len(edits)
        print(f'{os.path.relpath(path, HERE):48} {len(edits)} removed, {left} empty left')
        if apply:
            open(path, 'w').write(text)
    print(f'{total} removals' + ('' if apply else '  (dry run, nothing written)'))


if __name__ == '__main__':
    main()
