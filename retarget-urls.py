#!/usr/bin/env python3
"""
Move pages to different URLs, everywhere, in one pass.

    ./retarget-urls.py url-map.json              # dry run, prints every change
    ./retarget-urls.py url-map.json --apply      # writes it

⚠ WHY THIS EXISTS. Janet's Tier 1 copy proposes a clustered URL structure
(`/how-it-works/who-employs-your-staff`) where the build is mostly flat
(`/who-employs-your-staff`). Of the fourteen addresses her documents name, four
match what is built, and **her copy carries those links inside its body text**,
so whichever structure is settled, the other set has to be rewritten. That
decision is with her. This is the machinery that makes it a command rather than
a day, whichever way it goes — and it is deliberately built BEFORE the answer,
because after two more tiers land it is a bigger job.

⚠ A PAGE'S URL IS NOT ITS SLUG. Fourteen pages nest under a parent, so the
address is the parent chain plus the slug. This script works in addresses and
derives slug and parent from them, which is the direction that cannot silently
produce a page at an address nobody asked for.

⚠ IT REFUSES RATHER THAN IMPROVISES. A target whose parent page does not exist
is an error naming the page to create, not a parent invented on the fly. The one
thing worse than a manual URL migration is one that half-happened.

Map format — current address to new address, trailing slashes required:

    {
      "/who-employs-your-staff/": "/how-it-works/who-employs-your-staff/",
      "/build-your-team/":        "/pricing/build-your-team/"
    }
"""
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, 'content/pages.json')
CONTENT = os.path.join(HERE, 'content')
FILE_GLOBS = ('content', 'acs/templates', 'acs/parts')


def page_files():
    out = []
    for d in FILE_GLOBS:
        full = os.path.join(HERE, d)
        for name in sorted(os.listdir(full)):
            if name.endswith('.html'):
                out.append(os.path.join(full, name))
    return out


def address_of(entry, by_slug):
    """The real URL of a page: its parent chain, then its slug."""
    if entry.get('front'):
        return '/'
    parts = [entry['slug']]
    parent = entry.get('parent')
    depth = 0
    while parent and depth < 5:
        parts.insert(0, parent)
        parent = by_slug.get(parent, {}).get('parent')
        depth += 1
    return '/' + '/'.join(parts) + '/'


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    map_path, apply = sys.argv[1], '--apply' in sys.argv
    url_map = json.load(open(map_path))
    pages = json.load(open(MANIFEST))
    by_slug = {e['slug']: e for e in pages}
    current = {address_of(e, by_slug): e for e in pages}

    # --- validation, all of it before anything is written -------------------
    errors = []
    for old, new in url_map.items():
        if not (old.startswith('/') and old.endswith('/')):
            errors.append(f"{old}: addresses must start and end with /")
        if not (new.startswith('/') and new.endswith('/')):
            errors.append(f"{new}: addresses must start and end with /")
        if old not in current:
            errors.append(f"{old}: no page lives at this address")
        if old == '/' or new == '/':
            errors.append("the front page cannot be moved by this script")

    # Where every page ends up once the map is applied.
    after = {}
    for addr, entry in current.items():
        after[url_map.get(addr, addr)] = entry
    if len(after) != len(current):
        seen = {}
        for addr, entry in current.items():
            dest = url_map.get(addr, addr)
            seen.setdefault(dest, []).append(entry['slug'])
        for dest, slugs in seen.items():
            if len(slugs) > 1:
                errors.append(f"{dest}: {' and '.join(slugs)} would both live here")

    # Every target's parent must be a page that exists after the move.
    for new in url_map.values():
        segments = [s for s in new.split('/') if s]
        if len(segments) > 1:
            parent_addr = '/' + '/'.join(segments[:-1]) + '/'
            if parent_addr not in after:
                errors.append(
                    f"{new}: needs a page at {parent_addr} and there is none. "
                    f"Create it first, or add it to the map."
                )
        if len(segments) > 3:
            errors.append(f"{new}: more than three levels deep, which the theme does not template")

    # ⚠ FOUND BY USING IT, 2026-08-24. Janet's structure renames
    # `staff-you-can-hire` to `staff`, and every child page stores its parent by
    # SLUG. Move the parent without moving the children and eight pages keep a
    # parent field pointing at a slug that no longer exists — no error, no
    # failure, just eight pages at an address nobody serves. The map must be
    # complete, and this is what says so out loud instead of half-applying.
    slugs_after = set()
    for addr in after:
        slugs_after.add([s for s in addr.split('/') if s][-1] if addr != '/' else '')
    for addr, entry in current.items():
        if addr in url_map:
            continue
        parent = entry.get('parent')
        if parent and parent not in slugs_after:
            errors.append(
                f"{addr}: its parent \"{parent}\" is being moved or renamed and this page is not in "
                f"the map, so it would be left pointing at a slug that no longer exists. "
                f"Add it to the map."
            )

    if errors:
        print("REFUSED — nothing written:")
        for e in errors:
            print("  -", e)
        return 1

    # --- what changes -------------------------------------------------------
    manifest_changes, link_changes, file_renames = [], [], []
    for old, new in url_map.items():
        entry = current[old]
        segments = [s for s in new.split('/') if s]
        new_slug = segments[-1]
        new_parent = segments[-2] if len(segments) > 1 else ''
        if entry['slug'] != new_slug or entry.get('parent', '') != new_parent:
            manifest_changes.append((entry['slug'], new_slug, entry.get('parent', ''), new_parent))
        if entry['slug'] != new_slug:
            file_renames.append((f"content/{entry['slug']}.html", f"content/{new_slug}.html"))

    for path in page_files():
        text = open(path).read()
        for old, new in url_map.items():
            for variant in (old, old.rstrip('/')):
                pattern = 'href="%s"' % variant
                if pattern in text:
                    link_changes.append((os.path.relpath(path, HERE), variant, new, text.count(pattern)))

    print(f"{'APPLYING' if apply else 'DRY RUN'} — {len(url_map)} page(s) in the map\n")
    print(f"manifest: {len(manifest_changes)} entr(ies) change slug or parent")
    for old_slug, new_slug, old_parent, new_parent in manifest_changes:
        print(f"  - {old_slug} (parent {old_parent or 'none'}) -> {new_slug} (parent {new_parent or 'none'})")
    print(f"content files: {len(file_renames)} rename(s)")
    for a, b in file_renames:
        print(f"  - {a} -> {b}")
    total_links = sum(c for *_, c in link_changes)
    print(f"internal links: {total_links} in {len({c[0] for c in link_changes})} file(s)")
    for f, old, new, count in link_changes:
        print(f"  - {f}: {count} x {old} -> {new}")

    if not apply:
        print("\nNothing written. Re-run with --apply, then ./check-site.sh")
        return 0

    # --- write --------------------------------------------------------------
    for old, new in url_map.items():
        entry = current[old]
        segments = [s for s in new.split('/') if s]
        old_slug = entry['slug']
        entry['slug'] = segments[-1]
        entry['parent'] = segments[-2] if len(segments) > 1 else ''
        old_file = os.path.join(CONTENT, f"{old_slug}.html")
        new_file = os.path.join(CONTENT, f"{entry['slug']}.html")
        if old_file != new_file and os.path.exists(old_file):
            shutil.move(old_file, new_file)

    json.dump(pages, open(MANIFEST, 'w'), indent=2)
    open(MANIFEST, 'a').write('\n')

    for path in page_files():
        text = original = open(path).read()
        for old, new in url_map.items():
            text = text.replace('href="%s"' % old, 'href="%s"' % new)
            text = text.replace('href="%s"' % old.rstrip('/'), 'href="%s"' % new)
        if text != original:
            open(path, 'w').write(text)

    # The redirect list is the half a rewrite cannot do for you: every old
    # address that has been indexed, shared or printed still has to resolve.
    redirects = os.path.join(HERE, 'content/redirects.json')
    existing = json.load(open(redirects)) if os.path.exists(redirects) else {}
    existing.update(url_map)
    json.dump(existing, open(redirects, 'w'), indent=2)
    open(redirects, 'a').write('\n')

    print(f"\nWritten. {len(existing)} redirect(s) recorded in content/redirects.json.")
    print("⚠ Those are a RECORD, not a working redirect — the live server has to serve them.")
    print("Now run ./check-site.sh, then ./seed.sh")
    return 0


if __name__ == '__main__':
    sys.exit(main())
