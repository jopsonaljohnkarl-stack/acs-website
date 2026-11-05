#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
src=http://localhost:8888
curl -fsS -o /dev/null "$src/"
mkdir -p showcase
curl -fsS "$src/wp-sitemap-posts-page-1.xml" | grep -o '<loc>[^<]*' | sed 's/<loc>//' > showcase/pages.txt
for map in wp-sitemap-posts-post-1.xml wp-sitemap-posts-vacancy-1.xml; do
  curl -fsS "$src/$map" | grep -o '<loc>[^<]*' | sed 's/<loc>//' >> showcase/pages.txt || true
done
rm -rf showcase/site
python3 preview/snapshot.py showcase/site showcase/pages.txt
python3 showcase/prepare.py
