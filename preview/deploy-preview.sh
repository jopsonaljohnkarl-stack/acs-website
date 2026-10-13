#!/usr/bin/env bash
# Rebuild the ACS internal review snapshot and deploy it to Cloudflare Pages.
#
# The site is WordPress; Cloudflare Pages is static. This crawls the running
# local WordPress into flat HTML, stamps every page with a noindex meta and the
# unapproved-content banner, and deploys it behind HTTP Basic Auth.
#
#   ./deploy-preview.sh            rebuild + deploy
#   ./deploy-preview.sh --build    rebuild only, serve locally on :8901
#
# ⚠ The password is NOT in this repo. It lives in Cloudflare as the project
#   secret REVIEW_PASSWORD and in Bitwarden. To rotate:
#     npx wrangler pages secret put REVIEW_PASSWORD --project-name acs-review-copy
set -euo pipefail
cd "$(dirname "$0")"

PROJECT=acs-review-copy
SRC=http://localhost:8888
OUT=$(mktemp -d)/acs-preview

if ! curl -sf -o /dev/null "$SRC/"; then
  echo "Local WordPress is not answering on $SRC — run 'npx @wordpress/env start' first." >&2
  exit 1
fi

mkdir -p "$OUT"
curl -s "$SRC/wp-sitemap-posts-page-1.xml" \
  | grep -o '<loc>[^<]*</loc>' | sed 's/<[^>]*>//g' > "$OUT/pages.txt"
# Blog posts and vacancies have their own sitemaps (template previews, 2 Oct 2026).
for map in wp-sitemap-posts-post-1.xml wp-sitemap-posts-vacancy-1.xml; do
  curl -s "$SRC/$map" | grep -o '<loc>[^<]*</loc>' | sed 's/<[^>]*>//g' >> "$OUT/pages.txt" || true
done
echo "pages in sitemap: $(wc -l < "$OUT/pages.txt")"

python3 snapshot.py "$OUT/assets" "$OUT/pages.txt"
cp -R functions "$OUT/functions"

if [[ "${1:-}" == "--build" ]]; then
  echo "built at $OUT/assets — serving on http://localhost:8901"
  cd "$OUT/assets" && exec python3 -m http.server 8901
fi

cd "$OUT"
npx --yes wrangler@latest pages deploy assets \
  --project-name "$PROJECT" --branch main --commit-dirty=true
