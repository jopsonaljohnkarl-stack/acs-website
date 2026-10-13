# Fonts

**Archivo** (variable, width + weight) and **Martian Mono** (variable), both SIL
Open Font License, fetched from the Google Fonts repository 2026-08-20.

**Archivo** carries the whole site. Its **width axis is the reason it was
chosen**: clause headings run expanded, table labels run condensed, and the
document reads as one voice at both ends rather than as two families pretending
to agree. It is a workhorse with real tabular figures, which a specification
world cannot do without.

**Martian Mono** sets clause numbers, reference codes and table labels only. It
never sets a sentence.

## The build step

```
./build-fonts.sh
```

Subsets both fonts to Latin and converts them to woff2. **Both the `.ttf`
sources and the `.woff2` outputs are committed**, because the theme deploys by
copying files and a build nobody can run at deploy time is a build that gets
skipped.

| | Before | After |
|---|---|---|
| Archivo | 658,596 | **95,332** |
| Martian Mono | 148,460 | **39,252** |
| **Total** | **807 KB** | **135 KB** |

⚠ **The tooling was never missing.** The previous note here said `fonttools` was
not on this machine. It is not installed, but the reason `pip install` failed is
that macOS ships an **externally-managed Python (PEP 668)** which refuses to
install into itself. `build-fonts.sh` creates a virtualenv, which is the answer
rather than `--break-system-packages`. **A tool that refuses is not a tool that
is absent**, and the difference was worth a minute of checking.

⚠ **The axes are NOT limited.** Pinning `wdth` would save more bytes and would
take away the reason Archivo is here. `wght 100-900` and `wdth 62-125` both
survive the subset, verified by reading `fvar` out of the woff2.

⚠ **U+2713, the tick in `.acs-ticks`, is in NEITHER SOURCE FONT.** It has always
come from a system fallback. Checked against both cmaps directly, because
`document.fonts.check()` reports it as present — it tests family availability,
not glyph coverage.
