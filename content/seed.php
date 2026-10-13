<?php
/**
 * ACS site seeder.
 *
 * ⚠ THE PAGES ARE NOT THE THEME. A block theme is files and lives in git; the
 * pages, their template assignments, the navigation and the front-page setting
 * live in a database that `wp-env destroy` throws away. On 2026-08-20 the whole
 * ACS build existed in exactly one place, a local Docker volume, with nothing
 * to recreate it. This script is that missing half.
 *
 * Run it from `websites/acs`:
 *
 *   npx @wordpress/env run cli wp eval-file /var/www/html/wp-content/acs-content/seed.php
 *
 * or use the wrapper, which is shorter and gets the path right:
 *
 *   ./seed.sh
 *
 * IDEMPOTENT BY DESIGN. It matches on slug, creates what is missing and updates
 * what has drifted, and it reports every action rather than running silently.
 * Running it twice is a no-op the second time, which is the property that makes
 * it safe to run after every content change.
 *
 * ⚠ IT DOES NOT DELETE. A page removed from the manifest is left alone and
 * reported, because a seeder that deletes is a seeder nobody dares run.
 */

$root = dirname( __FILE__ );
$content_dir = $root;
$manifest_path = $content_dir . '/pages.json';

if ( ! file_exists( $manifest_path ) ) {
	WP_CLI::error( "No manifest at $manifest_path" );
}

$manifest = json_decode( file_get_contents( $manifest_path ), true );
if ( ! is_array( $manifest ) ) {
	WP_CLI::error( 'Manifest is not valid JSON' );
}

// A duplicate slug would make the lookup above ambiguous and the run destructive.
$slugs = wp_list_pluck( $manifest, 'slug' );
$dupes = array_keys( array_filter( array_count_values( $slugs ), function ( $n ) { return $n > 1; } ) );
if ( $dupes ) {
	WP_CLI::error( 'Manifest has duplicate slugs: ' . implode( ', ', $dupes ) );
}

$created = 0;
$updated = 0;
$unchanged = 0;
$front_id = 0;
$ids = array();

// Two passes, because a child cannot resolve its parent until the parent exists.
/*
 * ⚠ A RENAME IS NOT A NEW PAGE, AND THIS SCRIPT COULD NOT TELL THE DIFFERENCE.
 *
 * Pages are matched by slug. Change a slug and nothing matches, so a second
 * page is created and the first is left published at its old address. Found
 * 2026-08-24 applying Janet's clustered URL structure: three slugs changed,
 * three new pages appeared, and `/data-security-privacy/`,
 * `/who-we-help/security-facilities/` and `/staff-you-can-hire/` all still
 * returned 200 with the old copy. **On a live site that is duplicate content
 * at two addresses, with the stale one still indexed.**
 *
 * ⚠ check-site.sh cannot see this. It reads files; this lives in the database.
 * The rendered site was the only place it was visible.
 *
 * `content/redirects.json` already records every move, so it is the record of
 * what a rename was. Where the old slug still exists and the new one does not,
 * rename the existing page — same post, same ID, new address — instead of
 * leaving a duplicate behind.
 */
$redirects_file = $content_dir . '/redirects.json';
if ( file_exists( $redirects_file ) ) {
	$redirects = json_decode( file_get_contents( $redirects_file ), true );
	foreach ( (array) $redirects as $old_address => $new_address ) {
		$old_parts = array_values( array_filter( explode( '/', $old_address ) ) );
		$new_parts = array_values( array_filter( explode( '/', $new_address ) ) );
		if ( ! $old_parts || ! $new_parts ) {
			continue;
		}
		$old_slug = end( $old_parts );
		$new_slug = end( $new_parts );
		if ( $old_slug === $new_slug ) {
			continue; // only the parent moved; the slug is untouched
		}
		$old_found = get_posts( array( 'post_type' => 'page', 'name' => $old_slug, 'post_status' => array( 'publish', 'draft', 'pending', 'private', 'future' ), 'numberposts' => 1 ) );
		$new_found = get_posts( array( 'post_type' => 'page', 'name' => $new_slug, 'post_status' => array( 'publish', 'draft', 'pending', 'private', 'future' ), 'numberposts' => 1 ) );
		if ( $old_found && ! $new_found ) {
			wp_update_post( array( 'ID' => $old_found[0]->ID, 'post_name' => $new_slug ) );
			WP_CLI::log( "renamed  {$old_slug} -> {$new_slug} (#{$old_found[0]->ID}, same page)" );
		} elseif ( $old_found && $new_found ) {
			WP_CLI::warning(
				"{$old_slug} (#{$old_found[0]->ID}) and {$new_slug} (#{$new_found[0]->ID}) BOTH exist — " .
				"the rename already ran as a create, so the old page is a duplicate serving stale copy. " .
				"Decide what happens to #{$old_found[0]->ID}; this script will not delete it."
			);
		}
	}
}

foreach ( array( 'create', 'link' ) as $pass ) {
	foreach ( $manifest as $entry ) {
		$slug = $entry['slug'];
		$file = $content_dir . '/' . $slug . '.html';

		if ( ! file_exists( $file ) ) {
			WP_CLI::warning( "$slug: no content file, skipped" );
			continue;
		}

		$content = file_get_contents( $file );

		/*
		 * ⚠ NOT get_page_by_path(). It resolves a full hierarchical path, so a
		 * child page looked up by its own slug alone comes back null — and the
		 * first run of this script created a duplicate of all thirteen child
		 * pages before that was understood. Querying post_name directly is
		 * indifferent to hierarchy, which is why the manifest requires slugs to
		 * be unique across the whole site rather than only within a parent.
		 */
		/*
		 * ⚠ 'any' IS NOT ANY. WP_Query's 'any' excludes every status flagged
		 * exclude_from_search — which includes DRAFT. Found 2026-08-25, the day
		 * the first two manifest entries became drafts: the lookup stopped
		 * seeing them and the seeder re-created one duplicate per run. The
		 * statuses are now named explicitly.
		 */
		$found = get_posts( array(
			'post_type'   => 'page',
			'name'        => $slug,
			'post_status' => array( 'publish', 'draft', 'pending', 'private', 'future' ),
			'numberposts' => 1,
		) );
		$existing = $found ? $found[0] : null;

		if ( 'create' === $pass ) {
			if ( ! $existing ) {
				$id = wp_insert_post( array(
					'post_type'    => 'page',
					'post_status'  => isset( $entry['status'] ) ? $entry['status'] : 'publish',
					'post_name'    => $slug,
					'post_title'   => $entry['title'],
					'post_content' => $content,
					'post_excerpt' => isset( $entry['excerpt'] ) ? $entry['excerpt'] : '',
					'menu_order'   => isset( $entry['menu_order'] ) ? (int) $entry['menu_order'] : 0,
				), true );
				if ( is_wp_error( $id ) ) {
					WP_CLI::warning( "$slug: " . $id->get_error_message() );
					continue;
				}
				WP_CLI::log( "created  $slug (#$id)" );
				$created++;
				$existing = get_post( $id );
			}
			$ids[ $slug ] = $existing->ID;
			continue;
		}

		// Link pass: title, content, parent, order, template.
		$id = $ids[ $slug ];
		$post = get_post( $id );
		$parent_id = ( ! empty( $entry['parent'] ) && isset( $ids[ $entry['parent'] ] ) ) ? $ids[ $entry['parent'] ] : 0;
		$order = isset( $entry['menu_order'] ) ? (int) $entry['menu_order'] : 0;
		$template = isset( $entry['template'] ) ? $entry['template'] : '';

		$changes = array();
		if ( $post->post_title !== $entry['title'] ) { $changes['post_title'] = $entry['title']; }
		/*
		 * The excerpt is a SECOND per-page slot, and it exists because the role
		 * and industry templates need two: a lede in the hero and a body
		 * further down. Without it those thirteen pages differed from each
		 * other by their title and one sentence.
		 */
		$excerpt = isset( $entry['excerpt'] ) ? $entry['excerpt'] : '';
		if ( $post->post_excerpt !== $excerpt ) { $changes['post_excerpt'] = $excerpt; }
		if ( $post->post_content !== $content ) { $changes['post_content'] = $content; }
		if ( (int) $post->post_parent !== $parent_id ) { $changes['post_parent'] = $parent_id; }
		if ( (int) $post->menu_order !== $order ) { $changes['menu_order'] = $order; }
		/*
		 * A page the sitemap withdraws is DRAFTED, never deleted. `"status":
		 * "draft"` in the manifest unpublishes it and keeps the content and the
		 * ID, so the withdrawal is reversible and the seeder still never
		 * deletes. Added 2026-08-25 for the two pages the 56-page sitemap
		 * withdraws (Security & Facilities, Small Business).
		 */
		$status = isset( $entry['status'] ) ? $entry['status'] : 'publish';
		if ( $post->post_status !== $status ) { $changes['post_status'] = $status; }

		if ( $changes ) {
			$changes['ID'] = $id;
			wp_update_post( $changes );
		}

		/*
		 * The meta description is a THIRD per-page slot, and it is deliberately
		 * not the excerpt. The excerpt above is VISIBLE — the role and industry
		 * templates render it as the hero lede — so overloading it would mean
		 * one edit silently changing both the page and its search result.
		 * `functions.php` reads this meta to emit <meta name="description">,
		 * Open Graph and the JSON-LD description.
		 */
		$description = isset( $entry['description'] ) ? $entry['description'] : '';
		$current_description = (string) get_post_meta( $id, '_acs_meta_description', true );
		$description_changed = false;
		if ( $current_description !== $description ) {
			if ( '' === $description ) {
				delete_post_meta( $id, '_acs_meta_description' );
			} else {
				update_post_meta( $id, '_acs_meta_description', $description );
			}
			$description_changed = true;
		}

		$current_template = get_post_meta( $id, '_wp_page_template', true );
		$template_changed = false;
		if ( $template ) {
			if ( $current_template !== $template ) {
				update_post_meta( $id, '_wp_page_template', $template );
				$template_changed = true;
			}
		} elseif ( $current_template && 'default' !== $current_template ) {
			delete_post_meta( $id, '_wp_page_template' );
			$template_changed = true;
		}

		if ( ! empty( $entry['front'] ) ) { $front_id = $id; }

		if ( $changes || $template_changed || $description_changed ) {
			$what = array_keys( $changes );
			if ( $template_changed ) { $what[] = 'template'; }
			if ( $description_changed ) { $what[] = 'description'; }
			$what = array_values( array_diff( $what, array( 'ID' ) ) );
			WP_CLI::log( "updated  $slug (#$id): " . implode( ', ', $what ) );
			$updated++;
		} else {
			$unchanged++;
		}
	}
}

// The navigation is a post too, and it is just as easy to lose as the pages.
$nav_file = $content_dir . '/navigation.html';
if ( file_exists( $nav_file ) ) {
	$nav_content = file_get_contents( $nav_file );
	$navs = get_posts( array( 'post_type' => 'wp_navigation', 'numberposts' => -1, 'post_status' => 'any', 'title' => 'ACS main' ) );
	$nav = $navs ? $navs[0] : null;
	if ( ! $nav ) {
		$nav_id = wp_insert_post( array(
			'post_type'    => 'wp_navigation',
			'post_status'  => 'publish',
			'post_title'   => 'ACS main',
			'post_content' => $nav_content,
		) );
		WP_CLI::log( "created  navigation 'ACS main' (#$nav_id)" );
	} elseif ( $nav->post_content !== $nav_content ) {
		wp_update_post( array( 'ID' => $nav->ID, 'post_content' => $nav_content ) );
		WP_CLI::log( "updated  navigation 'ACS main' (#{$nav->ID})" );
	}

	/*
	 * The header's navigation block carries no `ref`, so it resolves the most
	 * recently published navigation menu. WordPress publishes its own titled
	 * 'Navigation' containing a bare page list the first time a ref-less block
	 * renders with none present, and if that one wins the site's menu becomes
	 * every page on the site. Removing it is the only delete this script does.
	 */
	foreach ( get_posts( array( 'post_type' => 'wp_navigation', 'numberposts' => -1, 'post_status' => 'any' ) ) as $other ) {
		if ( 'ACS main' !== $other->post_title ) {
			wp_delete_post( $other->ID, true );
			WP_CLI::log( "removed  stray navigation '{$other->post_title}' (#{$other->ID})" );
		}
	}
}

// Settings the site does not work without.
if ( $front_id ) {
	if ( 'page' !== get_option( 'show_on_front' ) || (int) get_option( 'page_on_front' ) !== $front_id ) {
		update_option( 'show_on_front', 'page' );
		update_option( 'page_on_front', $front_id );
		WP_CLI::log( "updated  front page -> #$front_id" );
	}
}

/*
 * ⚠ Load-bearing, not cosmetic. A fresh WordPress ships with plain permalinks,
 * and every internal link in this theme is written as /slug/. Without this the
 * whole site 404s on a rebuild and it looks like the theme is broken.
 */
if ( '/%postname%/' !== get_option( 'permalink_structure' ) ) {
	update_option( 'permalink_structure', '/%postname%/' );
	flush_rewrite_rules( true );
	WP_CLI::log( 'updated  permalinks -> /%postname%/' );
}

if ( get_option( 'blogname' ) !== 'All Commercial Services' ) {
	update_option( 'blogname', 'All Commercial Services' );
	WP_CLI::log( 'updated  site title' );
}

// Report pages in the database that the manifest does not know about.
$known = wp_list_pluck( $manifest, 'slug' );
foreach ( get_posts( array( 'post_type' => 'page', 'numberposts' => -1, 'post_status' => 'any' ) ) as $p ) {
	if ( ! in_array( $p->post_name, $known, true ) ) {
		WP_CLI::warning( "in database but not in the manifest: {$p->post_name} (#{$p->ID}) — not touched" );
	}
}

WP_CLI::success( "$created created, $updated updated, $unchanged unchanged" );
