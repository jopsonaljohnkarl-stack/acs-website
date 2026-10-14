#!/usr/bin/env bash
#
# Build the PRODUCTION database dump from the LOCAL WordPress (wp-env, :8888).
# Runs against the local site only. It never connects to any host.
#
#   ./build-prod-db.sh https://allcommercialservices.com.au            # dry run (default)
#   ./build-prod-db.sh https://allcommercialservices.com.au --apply    # write the dump
#
# What --apply does, in order:
#   1. backs up the local database (.prod-build/local-backup-<ts>.sql)
#   2. deletes every post carrying meta _acs_sample (SAMPLE articles and
#      vacancies) and the attachments hanging off them
#   3. deletes the /template-preview/ page and every page under it
#   4. deletes revisions, transients, the default hello-world draft and its
#      comment (old draft copy, local cache, WordPress cruft)
#   5. permalinks -> /resources/%postname%/, rewrite flush
#   6. blog_public = 0  (search visibility OFF; turned on at cutover, not before)
#   7. search-replace http://localhost:8888 -> the URL given (plain, JSON-escaped
#      and scheme-less forms; serialized data handled by WP-CLI)
#   8. exports .prod-build/acs-prod-<ts>.sql WITHOUT wp_users / wp_usermeta
#   9. checks the dump: no localhost, no _acs_sample, no template-preview
#  10. RESTORES the local database from step 1 (also on any failure), so the
#      local site and the review preview are left exactly as they were
#
# ⚠ WHY wp_users AND wp_usermeta ARE LEFT OUT. The local admin is wp-env's
# default login. Importing it would put a known-password administrator on the
# public site. Production keeps the administrator created by its own install
# (DEPLOY-CPANEL.md step 4), which is user ID 1 on a fresh install, so post
# authorship still resolves.
#
# ⚠ The production table prefix must be the same as the local one (printed in
# the dry run). If the cPanel installer picks a random prefix, the import
# creates a second set of tables and the site keeps reading the empty ones.
#
# .prod-build/ is gitignored. The dump holds the site's content only (no users,
# no passwords), but it is still not for the repo.
#
set -euo pipefail
cd "$(dirname "$0")"

LOCAL_URL="http://localhost:8888"
CONTAINER_DIR="/var/www/html/wp-content/acs-content/.prod-build"   # = ./content/.prod-build on this machine
HOST_STAGE="content/.prod-build"
OUT_DIR=".prod-build"

URL="${1:-}"
MODE="${2:---dry-run}"

usage() { sed -n '3,6p' "$0"; exit 2; }
[ -n "$URL" ] || usage
case "$MODE" in --apply|--dry-run) ;; *) usage ;; esac
if ! [[ "$URL" =~ ^https://[a-z0-9.-]+\.[a-z]{2,}$ ]]; then
  echo "URL must be https://host with no path and no trailing slash, got: $URL" >&2
  exit 2
fi

mkdir -p "$OUT_DIR" "$HOST_STAGE"
LOG="$OUT_DIR/build.log"
: > "$LOG"
wpc() { npx @wordpress/env run cli wp "$@" 2>>"$LOG"; }

curl -s -o /dev/null -m 5 "$LOCAL_URL/" || { echo "Local WordPress is not answering on $LOCAL_URL. Start it: npx @wordpress/env start" >&2; exit 1; }

# The selection, shared by the dry run and the real run, so what is reported
# is exactly what gets deleted.
SELECT_PHP='
$sample = get_posts( array( "post_type" => "any", "post_status" => "any", "numberposts" => -1, "meta_key" => "_acs_sample", "fields" => "ids" ) );
$vac    = get_posts( array( "post_type" => "vacancy", "post_status" => "any", "numberposts" => -1, "meta_key" => "_acs_sample", "fields" => "ids" ) );
$sample = array_values( array_unique( array_merge( $sample, $vac ) ) );
$preview = array();
$root = get_page_by_path( "template-preview", OBJECT, "page" );
if ( $root ) {
	$preview[] = $root->ID;
	foreach ( get_pages( array( "child_of" => $root->ID, "post_status" => "publish,draft,private,pending" ) ) as $c ) { $preview[] = $c->ID; }
}
// WordPress default cruft: the "Hello world!" post (kept as a draft locally) and its comment.
$cruft = get_posts( array( "post_type" => "post", "name" => "hello-world", "post_status" => "any", "numberposts" => -1, "fields" => "ids" ) );
$comments = get_comments( array( "fields" => "ids", "status" => "all" ) );
$doomed = array_merge( $sample, $preview, $cruft );
$att = array();
foreach ( get_posts( array( "post_type" => "attachment", "post_status" => "any", "numberposts" => -1 ) ) as $a ) {
	if ( in_array( $a->post_parent, $doomed, true ) ) { $att[] = $a->ID; continue; }
	// Orphaned sample images (parent 0) that no surviving post uses as a thumbnail.
	if ( 0 === (int) $a->post_parent ) {
		global $wpdb;
		$used = (int) $wpdb->get_var( $wpdb->prepare( "SELECT COUNT(*) FROM {$wpdb->postmeta} WHERE meta_key = %s AND meta_value = %d", "_thumbnail_id", $a->ID ) );
		if ( 0 === $used ) { $att[] = $a->ID; }
	}
}
'

if [ "$MODE" = "--dry-run" ]; then
  echo "DRY RUN (nothing is changed; add --apply to build the dump)"
  echo
  echo "  local site     $LOCAL_URL"
  echo "  target URL     $URL"
  echo "  table prefix   $(wpc db prefix)   <- production must use the same prefix"
  echo "  WordPress      $(wpc core version)"
  echo "  theme          $(wpc option get stylesheet)"
  echo "  permalinks now $(wpc option get permalink_structure)   -> /resources/%postname%/"
  echo "  blog_public    $(wpc option get blog_public)   -> 0"
  echo
  wpc eval "$SELECT_PHP"'
echo "  would delete:\n";
echo "    " . count( $sample ) . " SAMPLE posts/vacancies (_acs_sample)\n";
foreach ( $sample as $i ) { echo "      #$i " . get_post_type( $i ) . " " . get_post_field( "post_name", $i ) . "\n"; }
echo "    " . count( $preview ) . " template-preview pages\n";
foreach ( $preview as $i ) { echo "      #$i " . get_page_uri( $i ) . "\n"; }
echo "    " . count( $att ) . " attachments (sample images)\n";
echo "    " . count( $cruft ) . " hello-world post, " . count( $comments ) . " comments\n";
echo "    " . wp_count_posts( "revision" )->inherit . " revisions\n";
echo "  would keep " . ( wp_count_posts( "page" )->publish - count( $preview ) ) . " published pages\n";
'
  exit 0
fi

TS="$(date +%Y%m%d-%H%M%S)"
BACKUP="local-backup-$TS.sql"
DUMP="acs-prod-$TS.sql"
PREFIX="$(wpc db prefix)"

echo "1. backing up the local database"
wpc db export "$CONTAINER_DIR/$BACKUP" >/dev/null
mv "$HOST_STAGE/$BACKUP" "$OUT_DIR/$BACKUP"

restore() {
  local rc=$?
  echo "10. restoring the local database from $OUT_DIR/$BACKUP"
  cp "$OUT_DIR/$BACKUP" "$HOST_STAGE/$BACKUP"
  if wpc db import "$CONTAINER_DIR/$BACKUP" >/dev/null; then
    wpc rewrite flush >/dev/null || true
    rm -f "$HOST_STAGE/$BACKUP"
    echo "    restored. Local site is as it was."
  else
    echo "    ⚠ RESTORE FAILED. Restore by hand: npx @wordpress/env run cli wp db import $CONTAINER_DIR/$BACKUP  (copy the backup into content/.prod-build first), or re-run ./seed.sh" >&2
    rc=1
  fi
  rmdir "$HOST_STAGE" 2>/dev/null || true
  exit $rc
}
trap restore EXIT

echo "2-4. deleting SAMPLE content, template previews, revisions, transients"
wpc eval "$SELECT_PHP"'
foreach ( $att as $i )    { wp_delete_attachment( $i, true ); }
foreach ( $sample as $i ) { wp_delete_post( $i, true ); }
foreach ( array_reverse( $preview ) as $i ) { wp_delete_post( $i, true ); }
foreach ( $cruft as $i )  { wp_delete_post( $i, true ); }
foreach ( $comments as $i ) { wp_delete_comment( $i, true ); }
global $wpdb;
$rev = $wpdb->get_col( "SELECT ID FROM {$wpdb->posts} WHERE post_type = \"revision\"" );
foreach ( $rev as $i ) { wp_delete_post_revision( $i ); }
echo "    deleted " . count( $sample ) . " SAMPLE, " . count( $preview ) . " template-preview, " . count( $att ) . " attachments, " . count( $cruft ) . " hello-world, " . count( $comments ) . " comments, " . count( $rev ) . " revisions\n";
'
wpc transient delete --all >/dev/null

echo "5. permalinks"
wpc option update permalink_structure '/resources/%postname%/' >/dev/null
wpc rewrite flush >/dev/null

echo "6. search visibility off"
wpc option update blog_public 0 >/dev/null

echo "7. search-replace $LOCAL_URL -> $URL"
HOSTONLY="${URL#https://}"
for pair in \
  "$LOCAL_URL|$URL" \
  "http:\\/\\/localhost:8888|https:\\/\\/$HOSTONLY" \
  "//localhost:8888|//$HOSTONLY" \
  "localhost:8888|$HOSTONLY"; do
  from="${pair%%|*}"; to="${pair#*|}"
  n="$(wpc search-replace "$from" "$to" --all-tables-with-prefix --skip-tables="${PREFIX}users,${PREFIX}usermeta" --precise --format=count)"
  echo "    $from -> $to : $n"
done

echo "8. exporting (without ${PREFIX}users, ${PREFIX}usermeta)"
wpc db export "$CONTAINER_DIR/$DUMP" --exclude_tables="${PREFIX}users,${PREFIX}usermeta" >/dev/null
mv "$HOST_STAGE/$DUMP" "$OUT_DIR/$DUMP"

echo "9. checking the dump"
bad=0
for pat in 'localhost' '127\.0\.0\.1' '_acs_sample' 'template-preview' "CREATE TABLE \`${PREFIX}users\`"; do
  n="$(grep -c -E "$pat" "$OUT_DIR/$DUMP" || true)"
  if [ "$n" != "0" ]; then echo "    FAIL  '$pat' found on $n line(s)"; bad=1; else echo "    ok    no '$pat'"; fi
done
n="$(grep -c "INSERT INTO \`${PREFIX}comments\`" "$OUT_DIR/$DUMP" || true)"; [ "$n" = "0" ] && echo "    ok    no comments" || { echo "    FAIL  comments in the dump"; bad=1; }
grep -q "'blog_public','0'" "$OUT_DIR/$DUMP" && echo "    ok    blog_public = 0" || { echo "    FAIL  blog_public is not 0 in the dump"; bad=1; }
grep -q "'permalink_structure','/resources/%postname%/'" "$OUT_DIR/$DUMP" && echo "    ok    permalinks /resources/%postname%/" || { echo "    FAIL  permalink_structure not set"; bad=1; }
grep -q "'siteurl','$URL'" "$OUT_DIR/$DUMP" && echo "    ok    siteurl = $URL" || { echo "    FAIL  siteurl is not $URL"; bad=1; }

echo
echo "   dump: $(pwd)/$OUT_DIR/$DUMP ($(du -h "$OUT_DIR/$DUMP" | cut -f1))"
echo "   table prefix: $PREFIX   (production must match)"
[ "$bad" -eq 0 ] || { echo "   ⚠ DUMP FAILED ITS CHECKS. Do not import it."; exit 1; }
