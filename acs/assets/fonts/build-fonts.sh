#!/usr/bin/env bash
#
# Subset the two variable fonts to Latin and convert them to woff2.
#
# ⚠ THIS IS A BUILD STEP, NOT A ONE-OFF. The .ttf sources stay in the repo and
# the .woff2 files are generated from them, so re-running this after a font
# update is the whole procedure. Both source and output are committed: the
# theme is deployed by copying files, and a build nobody can run at deploy time
# is a build that will be skipped.
#
# ⚠ IT CREATES ITS OWN VIRTUALENV. macOS ships an externally-managed Python
# (PEP 668) that refuses `pip install`, which is why the previous note in this
# folder said the tooling "is not on this machine". It was not missing, it was
# refused, and a venv is the answer rather than --break-system-packages.
#
#   ./build-fonts.sh
#
set -euo pipefail
cd "$(dirname "$0")"

VENV="${TMPDIR:-/tmp}/acs-fontenv"
if [ ! -x "$VENV/bin/pyftsubset" ]; then
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install --quiet fonttools brotli
fi

# The Google Fonts `latin` range.
#
# ⚠ U+2713 IS LISTED AND IS STILL NOT IN THE OUTPUT, because NEITHER SOURCE
# FONT CONTAINS IT. Checked against both .ttf cmaps, not inferred. The tick in
# .acs-ticks has therefore always rendered from a system fallback and always
# will unless the character is replaced or a third font is added - and a third
# font is not happening for one glyph. Listing it here is harmless and keeps the
# intent visible; believing it is preserved would not be.
#
# ⚠ `document.fonts.check()` REPORTS THE TICK AS PRESENT. It is checking family
# availability, not glyph coverage, and it returns true for characters the font
# does not have. Read the cmap, not the browser.
#
# ⚠ U+26A0 is absent from both sources too, which is convenient: it appears only
# in PLACEHOLDER strings that must not survive to launch.
UNICODES="U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+2074,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+2713,U+FEFF,U+FFFD"

for src in Archivo-Variable.ttf MartianMono-Variable.ttf; do
  out="${src%.ttf}.woff2"
  "$VENV/bin/pyftsubset" "$src" \
    --output-file="$out" \
    --flavor=woff2 \
    --layout-features='*' \
    --unicodes="$UNICODES" \
    --name-IDs='*' \
    --notdef-outline \
    --drop-tables+=DSIG
  # ⚠ Axes are NOT limited. Archivo was chosen for its width axis - headings run
  # expanded, table labels condensed - so pinning wdth to save bytes would take
  # the reason it is here.
  printf '%-28s %8s -> %8s\n' "$src" "$(wc -c < "$src")" "$(wc -c < "$out")"
done
