#!/usr/bin/env bash
#
# Measure the site's prose for the patterns that make writing read as machine-
# generated. Reports; it does not fail a build.
#
# ⚠ WHY THIS IS A SCRIPT AND NOT A ONE-OFF EDIT. The 41 launch pages are written
# by Marketing over nine writing days, not by whoever built the theme. A tidy-up
# of today's placeholder copy is worth very little; a number the copy team can
# run against their own drafts is worth something. Run it on the real copy.
#
#   ./check-copy.sh            all pages
#   ./check-copy.sh home       one page
#
# Thresholds are per 1,000 words and they are judgement, not law. They came from
# measuring this site's own placeholder copy on 2026-08-20 and deciding which
# numbers were embarrassing.
#
set -uo pipefail
cd "$(dirname "$0")"
python3 - "${1:-}" <<'PY'
import re, glob, sys, statistics

only = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else None

def prose(p):
    s = open(p).read()
    s = re.sub(r'<!--.*?-->', ' ', s, flags=re.S)   # block delimiters and notes
    # ⚠ CLOSING BLOCK TAGS BECOME FULL STOPS, NOT SPACES. Stripping every tag
    # to a space concatenates separate <li> items and headings into one fake
    # sentence, so "Recruitment</li><li>Onboarding</li><li>Reporting" read as
    # the three-item list "A, B and C" — 2026-08-24, roughly a third of the
    # site's 64 reported triples were list markup, and the sentence-length
    # stats were counting paragraphs that do not exist. A tool that over-counts
    # gets ignored, which is worse than no tool.
    s = re.sub(r'</(?:li|p|h[1-6]|td|th|figcaption|summary)>', '. ', s)
    s = re.sub(r'<[^>]+>', ' ', s)
    s = re.sub(r'&[a-z]+;', ' ', s)
    s = re.sub(r'\.\s*\.', '.', s)                 # "….  ." from already-punctuated items
    return re.sub(r'\s+', ' ', s).strip()

files = sorted(glob.glob('content/*.html') + glob.glob('acs/templates/*.html') + glob.glob('acs/parts/*.html'))
if only:
    files = [f for f in files if only in f]
    if not files: print(f"no file matching '{only}'"); sys.exit(1)

text = ' '.join(prose(f) for f in files)
words = len(text.split())
if not words: print("no prose"); sys.exit(0)

# per-1k-word ceilings
CHECKS = [
  ('binary contrast "rather than"', r'\brather than\b',                                    2.0,
   'State the positive. "We recruit to your specification" beats "rather than a shortlist".'),
  ('three-item list "A, B and C"',  r'\b\w+[\w\s]{2,25}, [\w\s]{2,25} and [\w\s]{2,25}\b',  4.0,
   'Two items beat three. The rule of three is the single loudest tell.'),
  ('narrator voice (nobody/everybody)', r'\b(?:nobody|anybody|everybody)\b',                2.0,
   'Put the reader in the room. "You" beats "nobody".'),
  ('"which is the/what/why"',       r'\bwhich is (?:the|what|why|where|how)\b',             1.0,
   'A trailing clause explaining the sentence you just wrote. Cut it or start a new sentence.'),
  ('"exactly that/what/why"',       r'\bexactly (?:that|what|why)\b',                       0.8,
   'Emphasis crutch.'),
  ('em dash',                        r'—',                                                  1.5,
   'Use a full stop or a colon.'),
  ('"it is not X, it is Y"',        r'\b(?:is|are|it is)\s+not\s+[^.,;]{3,40},?\s+(?:it is|but|rather)\b', 0.5,
   'State Y.'),
  ('"the whole point/reason"',      r'\bthe whole (?:point|reason|thing|argument)\b',       0.4, 'Pull-quote voice.'),
  ('"precisely/crucially/notably"', r'\b(?:precisely|crucially|notably|importantly)\b',     0.4, 'Adverb doing vague work.'),
]

print(f"ACS copy: {words} words across {len(files)} files\n")
print(f"  {'pattern':34} {'n':>4} {'/1k':>6} {'max':>6}")
over = []
for name, pat, ceiling, advice in CHECKS:
    n = len(re.findall(pat, text, re.I))
    rate = n / words * 1000
    flag = '  OVER' if rate > ceiling else ''
    print(f"  {name:34} {n:>4} {rate:>6.1f} {ceiling:>6.1f}{flag}")
    if rate > ceiling: over.append((name, advice))

# ⚠ PROSE SENTENCES ONLY. Splitting block tags into sentences (above) turns
# every list item and heading into a "sentence", and list items are SUPPOSED
# to be parallel — counting them tripled the metronome number with runs that
# are good writing, not monotony. Under eight words is list-and-heading
# territory; the rhythm complaint is about paragraphs.
sents = [s for s in re.split(r'(?<=[.!?]) +', text) if s.strip()]
lens = [len(s.split()) for s in sents if len(s.split()) >= 8]
runs = sum(1 for i in range(len(lens)-2) if abs(lens[i]-lens[i+1]) < 3 and abs(lens[i+1]-lens[i+2]) < 3)
print(f"\n  sentence length mean {statistics.mean(lens):.1f}, stdev {statistics.pstdev(lens):.1f}")
print(f"  runs of three near-equal sentences: {runs}   (metronome)")

if over:
    print("\n  what to do:")
    for name, advice in over: print(f"   - {name}: {advice}")
else:
    print("\n  nothing over the ceilings.")
PY
