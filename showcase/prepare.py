#!/usr/bin/env python3
"""Turn the internal WordPress crawl into an inert portfolio showcase."""
from pathlib import Path
import re

root = Path(__file__).resolve().parent / "site"
theme_images = Path(__file__).resolve().parents[1] / "acs/assets/img"

banner = """<div id="acs-showcase-banner" role="note">Portfolio showcase · Website built by John Jopson · Static preview; forms are disabled.</div>
<style>#acs-showcase-banner{position:fixed;bottom:0;left:0;right:0;z-index:2147483647;background:#142a37;color:#fff;padding:12px 20px;text-align:center;font:600 14px/1.5 Arial,sans-serif;box-shadow:0 -4px 18px #0003}body{padding-bottom:52px!important}@media(max-width:600px){#acs-showcase-banner{font-size:12px}body{padding-bottom:70px!important}}</style>"""

def photo_path(match):
    name = re.match(r"team-\d+", match.group(0).rsplit("/", 1)[-1])
    if not name:
        return match.group(0)
    photo = name.group(0) + ".jpg"
    if not (theme_images / photo).is_file():
        raise FileNotFoundError(photo)
    return "/wp-content/themes/acs/assets/img/" + photo

count = 0
for path in root.rglob("*.html"):
    html = path.read_text()
    html = re.sub(r'<div id="acs-review-banner".*?</style>', banner, html, flags=re.S)
    html = re.sub(r'/wp-content/uploads/\d{4}/\d{2}/team-\d+(?:-\d+x\d+)?\.jpg', photo_path, html)
    html = re.sub(r'<script id="acs-forms-js-before">.*?</script>', '', html, flags=re.S)
    html = re.sub(r'<script[^>]+id="acs-forms-js"[^>]*></script>', '', html)
    html = re.sub(r'<form\b([^>]*)>', r'<form\1 onsubmit="return false">', html)
    html = re.sub(r'<button\b([^>]*type="submit"[^>]*)>', r'<button\1 disabled title="Showcase preview: forms are disabled">', html)
    path.write_text(html)
    count += 1

print(f"Prepared {count} static showcase pages")
