#!/usr/bin/env bash
# Fetch axe-core and serve it on 127.0.0.1:8899 for the browser harness.
#
# ⚠ axe is deliberately NOT a dependency of this theme and must never ship in
# it. An earlier note suggested copying axe.min.js into acs/ and deleting it
# afterwards; serving it from outside the theme removes the chance of the
# delete being forgotten.
set -euo pipefail
npm i axe-core --prefix /tmp/a11y --silent
lsof -ti:8899 | xargs kill -9 2>/dev/null || true
cd /tmp/a11y/node_modules/axe-core
python3 -m http.server 8899 --bind 127.0.0.1 >/dev/null 2>&1 &
sleep 1
curl -fsS -o /dev/null http://127.0.0.1:8899/axe.min.js && echo "axe served on http://127.0.0.1:8899/axe.min.js"
echo "Now paste a11y/run-in-browser.js into the console on http://localhost:8888/"
