<?php
/**
 * RESOURCES (the blog): Janet Biag's design, claude.ai artifact
 * GPjeFaL4CcinbwXLsbhj9f ("ACS Resources (blog template)", sent on Slack 2 Oct
 * 2026 10:19; "resources naman, tsaka sub category and sample blog", 11:02).
 * Three boards: the Resources hub, one subcategory template used by all three
 * categories ("3 pages yan same template"), and the article.
 *
 * Every visible line below is her mockup wording, verbatim. Her placeholders
 * ([DD Month YYYY], [X] min read, [Author name]) become the real date, a
 * reading time, and the byline fields.
 *
 * Addresses: the hub is the Resources page (/resources/, template blog-index).
 * The categories are its three child pages (/resources/guides/, ...), template
 * resource-category, each tied to the WordPress category with the same slug.
 * Articles are posts at /resources/<slug>/. Each page shows itself only once it
 * has a real (non-SAMPLE) article, the same rule as Resources and Vacancies
 * (acs_has_real in functions.php).
 *
 * The templates hold markers (<div data-acs-res="...">) in core/html blocks;
 * the render_block filter at the end of this file replaces each with markup.
 *
 * Byline fields are post meta, so a writer does not need a WordPress login:
 * _acs_author, _acs_author_role, _acs_coauthor, _acs_editor. With no
 * _acs_author, the WordPress author's display name is used. _acs_featured = 1
 * puts an article in the hub's featured slot (otherwise the newest article).
 */

/* The three categories, in the hub's order. Slugs match the child pages. */
function acs_res_cats() {
	return array(
		'guides'                     => array(
			'hero'       => 'janet-guides-1.jpg',
			'name'       => 'Guides',
			'pill'       => 'Guide',
			'kind'       => 'guide',
			'hub_intro'  => 'Step by step explainers on scoping, onboarding and managing an offshore team member.',
			'page_intro' => 'Step by step explainers on scoping, onboarding and managing an offshore team member, written for Australian business owners.',
			'view_all'   => 'View all guides →',
			'read'       => 'Read →',
			'featured'   => 'Read the guide →',
			'noun'       => array( 'guide', 'guides' ),
		),
		'role-suitability-checklist' => array(
			'hero'       => 'janet-role-suitability-checklist-1.jpg',
			'name'       => 'Role suitability checklists',
			'pill'       => 'Checklist',
			'kind'       => 'check',
			'hub_intro'  => 'Quick checks to work out whether a task, or a whole role, suits an offshore team member.',
			'page_intro' => 'Quick checks to work out whether a task, or a whole role, suits an offshore team member.',
			'view_all'   => 'View all checklists →',
			'read'       => 'Open checklist →',
			'featured'   => 'Open checklist →',
			'noun'       => array( 'checklist', 'checklists' ),
		),
		'position-descriptions'      => array(
			'hero'       => 'janet-position-descriptions-1.jpg',
			'name'       => 'Position descriptions',
			'pill'       => 'Position description',
			'kind'       => 'pd',
			'hub_intro'  => 'What each role does day to day, the skills it is screened for, and the systems it usually works in.',
			'page_intro' => 'What each role does day to day, the skills it is screened for, and the systems it usually works in.',
			'view_all'   => 'View all position descriptions →',
			'read'       => 'View →',
			'featured'   => 'View →',
			'noun'       => array( 'position description', 'position descriptions' ),
		),
	);
}

/* Is this request a template preview? A page under /template-preview/, or a SAMPLE article. */
function acs_res_in_preview() {
	$o = get_queried_object();
	if ( $o instanceof WP_Post ) {
		if ( 'post' === $o->post_type ) {
			return (bool) get_post_meta( $o->ID, '_acs_sample', true );
		}
		return 'template-preview' === get_post_field( 'post_name', $o->post_parent );
	}
	return false;
}

/* Where the hub and each category live: the real pages, or their template-preview copies. */
function acs_res_url( $cat = '' ) {
	if ( acs_res_in_preview() ) {
		return $cat ? '/template-preview/preview-' . $cat . '/' : '/template-preview/blog/';
	}
	return $cat ? '/resources/' . $cat . '/' : '/resources/';
}

/* Published articles, SAMPLE ones only in a preview and never otherwise. */
function acs_res_args( $extra = array() ) {
	return array_merge(
		array(
			'post_type'      => 'post',
			'post_status'    => 'publish',
			'posts_per_page' => -1,
			'orderby'        => 'date',
			'order'          => 'DESC',
			'meta_query'     => array( array( 'key' => '_acs_sample', 'compare' => acs_res_in_preview() ? 'EXISTS' : 'NOT EXISTS' ) ),
		),
		$extra
	);
}

function acs_res_has_real( $cat ) {
	static $cache = array();
	if ( ! isset( $cache[ $cat ] ) ) {
		$q = new WP_Query(
			array(
				'post_type'      => 'post',
				'post_status'    => 'publish',
				'posts_per_page' => 1,
				'fields'         => 'ids',
				'no_found_rows'  => true,
				'category_name'  => $cat,
				'meta_query'     => array( array( 'key' => '_acs_sample', 'compare' => 'NOT EXISTS' ) ),
			)
		);
		$cache[ $cat ] = ! empty( $q->posts );
	}
	return $cache[ $cat ];
}

/* The first of an article's categories that is one of the three. */
function acs_res_cat_of( $id ) {
	$cats = acs_res_cats();
	foreach ( wp_get_post_categories( $id, array( 'fields' => 'slugs' ) ) as $slug ) {
		if ( isset( $cats[ $slug ] ) ) {
			return $slug;
		}
	}
	return 'guides';
}

function acs_res_minutes( $id ) {
	$words = str_word_count( wp_strip_all_tags( get_post_field( 'post_content', $id ) ) );
	return max( 1, (int) ceil( $words / 200 ) );
}

/* A checklist's count is the items in its checklist lists (class acs-checks). */
function acs_res_checks( $id ) {
	$n = 0;
	if ( preg_match_all( '#<ul[^>]*class="[^"]*acs-checks[^"]*"[^>]*>(.*?)</ul>#s', get_post_field( 'post_content', $id ), $m ) ) {
		foreach ( $m[1] as $list ) {
			$n += substr_count( $list, '<li' );
		}
	}
	return $n;
}

function acs_res_meta( $id ) {
	$kind = acs_res_cats()[ acs_res_cat_of( $id ) ]['kind'];
	if ( 'check' === $kind ) {
		$n = acs_res_checks( $id );
		return $n ? $n . ' ' . ( 1 === $n ? 'check' : 'checks' ) : '';
	}
	if ( 'pd' === $kind ) {
		return 'Updated ' . get_the_modified_date( 'j F Y', $id );
	}
	return get_the_date( 'j F Y', $id ) . ' · ' . acs_res_minutes( $id ) . ' min read';
}

function acs_res_icon( $kind ) {
	if ( 'check' === $kind ) {
		return '<svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="5" y="4" width="14" height="17" rx="2"></rect><path d="M9 4V3h6v1"></path><path d="m8.5 10 1.5 1.5 3-3"></path><path d="m8.5 15.5 1.5 1.5 3-3"></path><path d="M15 11h1.5M15 16.5h1.5"></path></svg>';
	}
	return '<svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"></path><path d="M14 3v5h5"></path><path d="M9 13h6M9 17h4"></path></svg>';
}

/* Guides show their photograph; checklists and position descriptions a tinted panel with an icon. */
function acs_res_thumb( $id, $kind, $size = 'large' ) {
	if ( 'guide' !== $kind ) {
		return '<div class="acs-res-thumb acs-res-thumb--' . $kind . '">' . acs_res_icon( $kind ) . '</div>';
	}
	$img = get_the_post_thumbnail( $id, $size, array( 'alt' => '', 'loading' => 'lazy', 'decoding' => 'async' ) );
	return '<div class="acs-res-thumb acs-res-thumb--guide">' . $img . '</div>';
}

function acs_res_pill( $cat ) {
	$c = acs_res_cats()[ $cat ];
	return '<span class="acs-res-pill acs-res-pill--' . $c['kind'] . '">' . esc_html( $c['pill'] ) . '</span>';
}

/* One card: thumbnail, pill, title, summary, then the meta line and the read link. */
function acs_res_card( $post ) {
	$id   = $post->ID;
	$cat  = acs_res_cat_of( $id );
	$c    = acs_res_cats()[ $cat ];
	$url  = get_permalink( $id );
	$text = strtolower( wp_strip_all_tags( get_the_title( $id ) . ' ' . get_the_excerpt( $id ) . ' ' . $c['name'] ) );
	return '<article class="acs-res-card" data-text="' . esc_attr( $text ) . '">'
		. acs_res_thumb( $id, $c['kind'] )
		. '<div class="acs-res-card__body">' . acs_res_pill( $cat )
		. '<h3 class="acs-res-card__title"><a href="' . esc_url( $url ) . '">' . esc_html( get_the_title( $id ) ) . '</a></h3>'
		. ( has_excerpt( $id ) ? '<p class="acs-res-card__summary">' . esc_html( get_the_excerpt( $id ) ) . '</p>' : '' )
		. '<div class="acs-res-card__foot"><span class="acs-res-meta">' . esc_html( acs_res_meta( $id ) ) . '</span>'
		. '<a class="acs-res-link" href="' . esc_url( $url ) . '" aria-label="' . esc_attr( wp_strip_all_tags( $c['read'] ) . ' ' . get_the_title( $id ) ) . '">' . esc_html( $c['read'] ) . '</a></div>'
		. '</div></article>';
}

function acs_res_chips( $active ) {
	$out = '<nav class="acs-res-chips" aria-label="Resource categories">'
		. '<a href="' . esc_url( acs_res_url() ) . '"' . ( '' === $active ? ' aria-current="page"' : '' ) . '>All resources</a>';
	foreach ( acs_res_cats() as $slug => $c ) {
		$out .= '<a href="' . esc_url( acs_res_url( $slug ) ) . '"' . ( $active === $slug ? ' aria-current="page"' : '' ) . '>' . esc_html( $c['name'] ) . '</a>';
	}
	return $out . '</nav>';
}

/* The closing band, the same on all three boards. */
function acs_res_cta() {
	return '<section class="acs-res-cta"><div class="acs-res-cta__inner">'
		. '<h2>Tell us the task, not the title</h2>'
		. '<p>Most owners do not start with a job title. They start with a task that is eating their week. Tell us what that is on the call and we will tell you which role, or combination of roles, actually solves it.</p>'
		. '<div class="acs-res-cta__actions"><a class="acs-res-btn acs-res-btn--light" href="/book-a-call/">Book a call →</a><a class="acs-res-btn acs-res-btn--ghost" href="/pricing/build-your-team/">Calculate your price</a></div>'
		. '</div></section>';
}

/* Janet's banner photographs (Slack 2 Oct 2026 11:49): one per Resources page, the person on the
 * right and an empty wall on the left for the heading. See PHOTOGRAPHY.md. */
function acs_res_hero_photo( $file ) {
	$path = get_theme_file_path( 'assets/img/' . $file );
	$size = file_exists( $path ) ? getimagesize( $path ) : false;
	return '<div class="acs-res-hero__bg" aria-hidden="true"><img src="/wp-content/themes/acs/assets/img/' . esc_attr( $file ) . '" alt=""' . ( $size ? ' width="' . $size[0] . '" height="' . $size[1] . '"' : '' ) . ' decoding="async" fetchpriority="high"></div>';
}

/* ---- The hub ---- */
function acs_res_hub() {
	$cats  = acs_res_cats();
	$posts = get_posts( acs_res_args() );
	$feat  = null;
	foreach ( $posts as $p ) {
		if ( get_post_meta( $p->ID, '_acs_featured', true ) ) {
			$feat = $p;
			break;
		}
	}
	if ( ! $feat && $posts ) {
		$feat = $posts[0];
	}

	$out = '<section class="acs-res-hero acs-res-hero--hub acs-res-hero--photo">' . acs_res_hero_photo( 'janet-resources-1.jpg' )
		. '<div class="acs-res-hero__inner"><span class="acs-res-eyebrow">Resources</span>'
		. '<h1>Guides and tools for planning an offshore team member</h1>'
		. '<p class="acs-res-lead">Practical guides, role suitability checklists and position descriptions for Australian businesses working out which work to hand over, and how.</p>'
		. '<form role="search" class="acs-res-search" data-acs-res-search-form><label for="acs-res-q" class="screen-reader-text">Search resources</label><input id="acs-res-q" type="search" placeholder="Search resources" data-acs-res-search><button type="submit">Search</button></form>'
		. acs_res_chips( '' ) . '</div></section>';

	$out .= '<div data-acs-res-list>';
	if ( $feat ) {
		$cat = acs_res_cat_of( $feat->ID );
		$c   = $cats[ $cat ];
		$url = get_permalink( $feat->ID );
		$out .= '<section class="acs-res-band acs-res-band--featured"><div class="acs-res-wrap">'
			. '<article class="acs-res-featured" data-text="' . esc_attr( strtolower( wp_strip_all_tags( get_the_title( $feat->ID ) . ' ' . get_the_excerpt( $feat->ID ) ) ) ) . '">'
			. '<div class="acs-res-featured__media">' . acs_res_thumb( $feat->ID, $c['kind'], 'large' ) . '</div>'
			. '<div class="acs-res-featured__body"><div class="acs-res-featured__tags">' . acs_res_pill( $cat ) . '<span class="acs-res-flag">Featured</span></div>'
			. '<h2><a href="' . esc_url( $url ) . '">' . esc_html( get_the_title( $feat->ID ) ) . '</a></h2>'
			. ( has_excerpt( $feat->ID ) ? '<p>' . esc_html( get_the_excerpt( $feat->ID ) ) . '</p>' : '' )
			. '<span class="acs-res-meta">' . esc_html( acs_res_meta( $feat->ID ) ) . '</span>'
			. '<div><a class="acs-res-btn acs-res-btn--accent" href="' . esc_url( $url ) . '">' . esc_html( $c['featured'] ) . '</a></div>'
			. '</div></article></div></section>';
	}
	$n = 0;
	foreach ( $cats as $slug => $c ) {
		$in = array_values(
			array_filter(
				$posts,
				function ( $p ) use ( $slug, $feat ) {
					return ( ! $feat || $p->ID !== $feat->ID ) && acs_res_cat_of( $p->ID ) === $slug;
				}
			)
		);
		if ( ! $in ) {
			continue;
		}
		$out .= '<section class="acs-res-band' . ( 1 === $n % 2 ? ' acs-res-band--tint' : '' ) . '" data-acs-res-section><div class="acs-res-wrap acs-res-wrap--section">'
			. '<div class="acs-res-head"><div><h2>' . esc_html( $c['name'] ) . '</h2><p>' . esc_html( $c['hub_intro'] ) . '</p></div>'
			. '<a class="acs-res-link" href="' . esc_url( acs_res_url( $slug ) ) . '">' . esc_html( $c['view_all'] ) . '</a></div>'
			. '<div class="acs-res-grid">' . implode( '', array_map( 'acs_res_card', array_slice( $in, 0, 3 ) ) ) . '</div>'
			. '</div></section>';
		++$n;
	}
	$out .= '<p class="acs-res-none" hidden data-acs-res-none>No resources match.</p></div>';
	$out .= acs_res_cta();
	/* Search filters the cards on this page in the browser, the same way the Vacancies page does. */
	$out .= '<script>(function(){var f=document.querySelector("[data-acs-res-search-form]"),i=document.querySelector("[data-acs-res-search]"),l=document.querySelector("[data-acs-res-list]");if(!f||!i||!l)return;'
		. 'function run(){var q=i.value.trim().toLowerCase(),any=false;[].forEach.call(l.querySelectorAll("[data-text]"),function(a){var hit=!q||a.dataset.text.indexOf(q)>-1;a.hidden=!hit;var s=a.closest("section");if(hit)any=true;});'
		. '[].forEach.call(l.querySelectorAll("section"),function(s){s.hidden=!!q&&!s.querySelector("[data-text]:not([hidden])");});l.querySelector("[data-acs-res-none]").hidden=any;}'
		. 'f.addEventListener("submit",function(e){e.preventDefault();run();});i.addEventListener("input",run);})();</script>';
	return $out;
}

/* ---- A category page ---- */
function acs_res_category( $cat ) {
	$cats = acs_res_cats();
	if ( ! isset( $cats[ $cat ] ) ) {
		return '';
	}
	$c     = $cats[ $cat ];
	$per   = 9;
	$paged = max( 1, (int) ( $_GET['pg'] ?? 1 ) ); // phpcs:ignore WordPress.Security.NonceVerification
	$old   = 'oldest' === ( $_GET['sort'] ?? '' ); // phpcs:ignore WordPress.Security.NonceVerification
	$q     = new WP_Query(
		acs_res_args(
			array(
				'category_name'  => $cat,
				'posts_per_page' => $per,
				'paged'          => $paged,
				'order'          => $old ? 'ASC' : 'DESC',
			)
		)
	);
	$total = (int) $q->found_posts;
	$pages = (int) $q->max_num_pages;
	$here  = strtok( $_SERVER['REQUEST_URI'] ?? acs_res_url( $cat ), '?' );

	$out = '<section class="acs-res-hero acs-res-hero--cat acs-res-hero--photo">' . acs_res_hero_photo( $c['hero'] )
		. '<div class="acs-res-hero__inner"><nav class="acs-res-crumbs" aria-label="Breadcrumb"><a href="' . esc_url( acs_res_url() ) . '">Resources</a><span aria-hidden="true">/</span><span aria-current="page">' . esc_html( $c['name'] ) . '</span></nav>'
		. '<h1>' . esc_html( $c['name'] ) . '</h1><p class="acs-res-lead">' . esc_html( $c['page_intro'] ) . '</p>'
		. acs_res_chips( $cat ) . '</div></section>';

	$out .= '<section class="acs-res-band"><div class="acs-res-wrap acs-res-wrap--list">'
		. '<div class="acs-res-toolbar"><p class="acs-res-count">Showing ' . $total . ' ' . esc_html( 1 === $total ? $c['noun'][0] : $c['noun'][1] ) . '</p>'
		. '<form method="get" action="' . esc_url( $here ) . '"><label class="acs-res-sort">Sort by <select name="sort" onchange="this.form.submit()"><option value="newest"' . ( $old ? '' : ' selected' ) . '>Newest first</option><option value="oldest"' . ( $old ? ' selected' : '' ) . '>Oldest first</option></select></label><button type="submit" class="screen-reader-text">Sort</button></form></div>'
		. '<div class="acs-res-grid">' . implode( '', array_map( 'acs_res_card', $q->posts ) ) . '</div>';
	if ( $pages > 1 ) {
		$link = function ( $p ) use ( $here, $old ) {
			$args = array();
			if ( $p > 1 ) {
				$args['pg'] = $p;
			}
			if ( $old ) {
				$args['sort'] = 'oldest';
			}
			return esc_url( add_query_arg( $args, $here ) );
		};
		$out .= '<nav class="acs-res-pager" aria-label="Pagination">'
			. ( $paged > 1 ? '<a class="acs-res-pager__step" href="' . $link( $paged - 1 ) . '">Previous</a>' : '<span class="acs-res-pager__step" aria-disabled="true">Previous</span>' );
		for ( $p = 1; $p <= $pages; $p++ ) {
			$out .= $p === $paged ? '<span class="acs-res-pager__num" aria-current="page">' . $p . '</span>' : '<a class="acs-res-pager__num" href="' . $link( $p ) . '">' . $p . '</a>';
		}
		$out .= ( $paged < $pages ? '<a class="acs-res-pager__step" href="' . $link( $paged + 1 ) . '">Next</a>' : '<span class="acs-res-pager__step" aria-disabled="true">Next</span>' ) . '</nav>';
	}
	$out .= '</div></section>' . acs_res_cta();
	return $out;
}

/* The category a page shows: its own slug, or for a preview copy its slug after "preview-". */
function acs_res_page_cat() {
	$o = get_queried_object();
	return $o instanceof WP_Post ? preg_replace( '/^preview-/', '', $o->post_name ) : '';
}

/* ---- The article ---- */
function acs_res_initials( $name ) {
	preg_match_all( '/[A-Za-z0-9]+/', $name, $m );
	$i = strtoupper( implode( '', array_map( function ( $w ) { return $w[0]; }, array_slice( $m[0], 0, 2 ) ) ) );
	return 0 === strpos( trim( $name ), '[' ) ? '[' . $i . ']' : $i;
}

function acs_res_byline( $id ) {
	$author = get_post_meta( $id, '_acs_author', true );
	if ( ! $author ) {
		$author = get_the_author_meta( 'display_name', get_post_field( 'post_author', $id ) );
	}
	return array(
		'author'   => $author,
		'role'     => get_post_meta( $id, '_acs_author_role', true ),
		'coauthor' => get_post_meta( $id, '_acs_coauthor', true ),
		'editor'   => get_post_meta( $id, '_acs_editor', true ),
	);
}

function acs_res_post_head() {
	$id  = get_the_ID();
	$cat = acs_res_cat_of( $id );
	$c   = acs_res_cats()[ $cat ];
	$b   = acs_res_byline( $id );
	return '<section class="acs-res-hero acs-res-hero--post"><div class="acs-res-hero__inner">'
		. '<nav class="acs-res-crumbs" aria-label="Breadcrumb"><a href="' . esc_url( acs_res_url() ) . '">Resources</a><span aria-hidden="true">/</span><a href="' . esc_url( acs_res_url( $cat ) ) . '">' . esc_html( $c['name'] ) . '</a></nav>'
		. acs_res_pill( $cat )
		. '<h1>' . esc_html( get_the_title( $id ) ) . '</h1>'
		. '<div class="acs-res-byline"><div class="acs-res-byline__who"><span class="acs-res-avatar acs-res-avatar--lg" aria-hidden="true">' . esc_html( acs_res_initials( $b['author'] ) ) . '</span>'
		. '<span class="acs-res-byline__names"><span class="acs-res-byline__name">' . esc_html( $b['author'] ) . '</span>' . ( $b['role'] ? '<span class="acs-res-byline__role">' . esc_html( $b['role'] ) . ', ACS</span>' : '' ) . '</span></div>'
		. '<span class="acs-res-meta">' . esc_html( acs_res_meta( $id ) ) . '</span></div>'
		. '</div></section>';
}

function acs_res_share_links( $id ) {
	$u = rawurlencode( get_permalink( $id ) );
	$t = rawurlencode( get_the_title( $id ) );
	return array(
		'facebook' => 'https://www.facebook.com/sharer/sharer.php?u=' . $u,
		'x'        => 'https://x.com/intent/post?url=' . $u . '&text=' . $t,
		'email'    => 'mailto:?subject=' . $t . '&body=' . $u,
		'linkedin' => 'https://www.linkedin.com/sharing/share-offsite/?url=' . $u,
		'reddit'   => 'https://www.reddit.com/submit?url=' . $u . '&title=' . $t,
	);
}

/* The h2 headings of an article, for "On this page" (ids are added by acs_res_heading_id). */
function acs_res_toc( $id ) {
	$items = array();
	$walk  = function ( $blocks ) use ( &$walk, &$items ) {
		foreach ( $blocks as $b ) {
			if ( 'core/heading' === $b['blockName'] && 2 === (int) ( $b['attrs']['level'] ?? 2 ) ) {
				$text = trim( wp_strip_all_tags( $b['innerHTML'] ) );
				if ( '' !== $text ) {
					$items[] = array( 'id' => $b['attrs']['anchor'] ?? sanitize_title( $text ), 'text' => $text );
				}
			}
			if ( ! empty( $b['innerBlocks'] ) ) {
				$walk( $b['innerBlocks'] );
			}
		}
	};
	$walk( parse_blocks( get_post_field( 'post_content', $id ) ) );
	return $items;
}

function acs_res_post_aside() {
	$id    = get_the_ID();
	$b     = acs_res_byline( $id );
	$s     = acs_res_share_links( $id );
	$icons = array(
		'facebook' => array( 'Share on Facebook', '<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M13.5 21v-7.5h2.5l.4-3h-2.9V8.6c0-.9.3-1.5 1.5-1.5h1.5V4.4c-.3 0-1.2-.1-2.2-.1-2.2 0-3.7 1.3-3.7 3.8v2.4H8v3h2.6V21z"></path></svg>' ),
		'x'        => array( 'Share on X', '<svg width="16" height="16" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M4 4h4.4L20 20h-4.4z"></path><path fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" d="M19.5 4 13.6 10.8M10.4 13.2 4.5 20"></path></svg>' ),
		'email'    => array( 'Share by email', '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"></rect><path d="m3 7 9 6 9-6"></path></svg>' ),
		'linkedin' => array( 'Share on LinkedIn', '<svg width="16" height="16" viewBox="0 0 24 24" aria-hidden="true"><rect fill="currentColor" x="4" y="9" width="3.2" height="11"></rect><circle fill="currentColor" cx="5.6" cy="5.6" r="1.8"></circle><path fill="currentColor" d="M10 9h3v1.6c.5-.9 1.7-1.9 3.5-1.9 3 0 3.5 2 3.5 4.6V20h-3.2v-5.8c0-1.4 0-3-1.9-3s-2.1 1.4-2.1 2.9V20H10z"></path></svg>' ),
		'reddit'   => array( 'Share on Reddit', '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><ellipse cx="12" cy="14.5" rx="7.5" ry="5.5"></ellipse><circle fill="currentColor" stroke="none" cx="9.3" cy="14" r="1.1"></circle><circle fill="currentColor" stroke="none" cx="14.7" cy="14" r="1.1"></circle><path d="M9.5 17c1.5.9 3.5.9 5 0M12 9l1-4.5 3.5 1"></path><circle cx="17.5" cy="5.5" r="1.3"></circle></svg>' ),
	);
	$share = '';
	foreach ( $icons as $k => $v ) {
		$share .= '<a href="' . esc_url( $s[ $k ] ) . '" aria-label="' . esc_attr( $v[0] ) . '"' . ( 'email' === $k ? '' : ' target="_blank" rel="noopener"' ) . '>' . $v[1] . '</a>';
	}
	$out = '<div class="acs-res-aside__sticky">'
		. '<div class="acs-res-aside__people"><div class="acs-res-aside__row acs-res-aside__share"><h2>Share</h2><div>' . $share . '</div></div>'
		. '<div class="acs-res-aside__row"><div class="acs-res-avatars" aria-hidden="true"><span class="acs-res-avatar">' . esc_html( acs_res_initials( $b['author'] ) ) . '</span>'
		. ( $b['coauthor'] ? '<span class="acs-res-avatar acs-res-avatar--2">' . esc_html( acs_res_initials( $b['coauthor'] ) ) . '</span>' : '' ) . '</div>'
		. '<p>Written by <strong>' . esc_html( $b['author'] ) . '</strong>' . ( $b['coauthor'] ? ' &amp; <strong>' . esc_html( $b['coauthor'] ) . '</strong>' : '' ) . '</p></div>'
		. ( $b['editor'] ? '<div class="acs-res-aside__row"><span class="acs-res-avatar" aria-hidden="true">' . esc_html( acs_res_initials( $b['editor'] ) ) . '</span><p>Edited by <strong>' . esc_html( $b['editor'] ) . '</strong></p></div>' : '' )
		. '</div>';
	$toc = acs_res_toc( $id );
	if ( count( $toc ) > 1 ) {
		$out .= '<nav class="acs-res-toc" aria-label="On this page"><h2>On this page</h2><ol>';
		foreach ( $toc as $t ) {
			$out .= '<li><a href="#' . esc_attr( $t['id'] ) . '">' . esc_html( $t['text'] ) . '</a></li>';
		}
		$out .= '</ol></nav>';
	}
	$out .= '<div class="acs-res-aside__cta"><h2>Want help scoping the role?</h2><p>A short call. We will tell you honestly which role fits, and if none of them do.</p><div><a class="acs-res-btn acs-res-btn--light" href="/book-a-call/">Book a call →</a></div></div>';
	return $out . '</div>';
}

function acs_res_post_share() {
	$id   = get_the_ID();
	$s    = acs_res_share_links( $id );
	$noun = acs_res_cats()[ acs_res_cat_of( $id ) ]['noun'][0];
	return '<div class="acs-res-shareline"><span>Share this ' . esc_html( $noun ) . '</span>'
		. '<button type="button" data-acs-copy="' . esc_attr( get_permalink( $id ) ) . '">Copy link</button>'
		. '<a href="' . esc_url( $s['email'] ) . '">Email</a>'
		. '<a href="' . esc_url( $s['linkedin'] ) . '" target="_blank" rel="noopener">LinkedIn</a></div>'
		. '<script>(function(){var b=document.querySelector("[data-acs-copy]");if(!b||!navigator.clipboard)return;b.addEventListener("click",function(){navigator.clipboard.writeText(b.dataset.acsCopy).then(function(){b.textContent="Link copied";setTimeout(function(){b.textContent="Copy link"},2000)})})})();</script>';
}

/* Related: the newest article from each category, as on Janet's board (a checklist, a guide, a position description). */
function acs_res_related() {
	$id   = get_the_ID();
	$pick = array();
	foreach ( array( 'role-suitability-checklist', 'guides', 'position-descriptions' ) as $cat ) {
		$p = get_posts( acs_res_args( array( 'category_name' => $cat, 'posts_per_page' => 1, 'post__not_in' => array( $id ) ) ) );
		if ( $p ) {
			$pick[] = $p[0];
		}
	}
	if ( count( $pick ) < 3 ) {
		$more = get_posts( acs_res_args( array( 'posts_per_page' => 3 - count( $pick ), 'post__not_in' => array_merge( array( $id ), wp_list_pluck( $pick, 'ID' ) ) ) ) );
		$pick = array_merge( $pick, $more );
	}
	if ( ! $pick ) {
		return '';
	}
	return '<section class="acs-res-band acs-res-band--tint"><div class="acs-res-wrap acs-res-wrap--section"><h2 class="acs-res-related__title">Related resources</h2>'
		. '<div class="acs-res-grid">' . implode( '', array_map( 'acs_res_card', $pick ) ) . '</div></div></section>';
}

/* Anchor ids on an article's h2s, so "On this page" can link to them. */
add_filter(
	'render_block_core/heading',
	function ( $html, $block ) {
		if ( ! ( is_singular( 'post' ) || is_page_template( 'legal' ) ) || 2 !== (int) ( $block['attrs']['level'] ?? 2 ) || preg_match( '/<h2[^>]*\sid=/', $html ) ) {
			return $html;
		}
		$id = sanitize_title( wp_strip_all_tags( $block['innerHTML'] ) );
		return preg_replace( '/<h2\b/', '<h2 id="' . esc_attr( $id ) . '"', $html, 1 );
	},
	10,
	2
);

/* Replace the template markers. */
add_filter(
	'render_block_core/html',
	function ( $html ) {
		if ( ! preg_match( '/<div data-acs-res="([a-z-]+)"><\/div>/', $html, $m ) ) {
			return $html;
		}
		switch ( $m[1] ) {
			case 'hub':
				return acs_res_hub();
			case 'category':
				return acs_res_category( acs_res_page_cat() );
			case 'post-head':
				return acs_res_post_head();
			case 'post-aside':
				return acs_res_post_aside();
			case 'post-share':
				return acs_res_post_share();
			case 'related':
				return acs_res_related();
			case 'cta':
				return acs_res_cta();
			case 'legal-toc':
				return acs_legal_toc();
		}
		return $html;
	}
);

/* A category page shows itself only once it has a real article: 404, and out of the sitemap, until then. */
function acs_res_gated_cat_page( $page ) {
	return $page instanceof WP_Post && 'page' === $page->post_type
		&& 'resources' === get_post_field( 'post_name', $page->post_parent )
		&& isset( acs_res_cats()[ $page->post_name ] )
		&& ! acs_res_has_real( $page->post_name );
}

add_action(
	'template_redirect',
	function () {
		if ( is_page() && acs_res_gated_cat_page( get_queried_object() ) ) {
			global $wp_query;
			$wp_query->set_404();
			status_header( 404 );
			nocache_headers();
		}
	}
);

add_filter(
	'wp_sitemaps_posts_query_args',
	function ( $args, $post_type ) {
		if ( 'page' !== $post_type ) {
			return $args;
		}
		foreach ( array_keys( acs_res_cats() ) as $slug ) {
			$page = get_page_by_path( 'resources/' . $slug );
			if ( acs_res_gated_cat_page( $page ) ) {
				$args['post__not_in'] = array_merge( $args['post__not_in'] ?? array(), array( $page->ID ) );
			}
		}
		return $args;
	},
	10,
	2
);

/*
 * WordPress's own archives duplicate the Resources pages: category archives
 * (/resources/category/guides/), author and date archives. Found by the 2 Oct
 * responsive audit, which read the category archives out of the sitemap. Each
 * is sent to the matching Resources page (which keeps its own show-itself
 * rule), and the category sitemap is dropped.
 */
add_action(
	'template_redirect',
	function () {
		if ( is_category() ) {
			$slug = get_queried_object()->slug ?? '';
			wp_safe_redirect( isset( acs_res_cats()[ $slug ] ) ? '/resources/' . $slug . '/' : '/resources/', 301 );
			exit;
		}
		if ( is_author() || is_date() || is_tag() ) {
			wp_safe_redirect( '/resources/', 301 );
			exit;
		}
	},
	1
);

add_filter(
	'wp_sitemaps_taxonomies',
	function ( $taxonomies ) {
		unset( $taxonomies['category'], $taxonomies['post_tag'] );
		return $taxonomies;
	}
);

/*
 * SAMPLE entries (articles and vacancies, meta _acs_sample) are for the template
 * previews only. Found by the 2 Oct independent check: their own pages carried no
 * noindex, and the public REST API listed them. They now say noindex, and the
 * REST API leaves them out. They stay in the sitemap because the review-site
 * build crawls it to find the preview pages. Delete them before launch.
 */
add_filter(
	'wp_robots',
	function ( $robots ) {
		if ( is_singular( array( 'post', 'vacancy' ) ) && get_post_meta( get_queried_object_id(), '_acs_sample', true ) ) {
			$robots['noindex']  = true;
			$robots['nofollow'] = true;
		}
		return $robots;
	}
);

foreach ( array( 'post', 'vacancy' ) as $acs_rest_type ) {
	add_filter(
		'rest_' . $acs_rest_type . '_query',
		function ( $args ) {
			$args['meta_query']   = $args['meta_query'] ?? array();
			$args['meta_query'][] = array( 'key' => '_acs_sample', 'compare' => 'NOT EXISTS' );
			return $args;
		}
	);
}

/* ---- Legal pages (template legal): Janet's "first version" layout ---- */
function acs_legal_toc() {
	$toc = acs_res_toc( get_the_ID() );
	if ( count( $toc ) < 2 ) {
		return '';
	}
	$out = '<div class="acs-legal__sticky"><nav class="acs-legal__toc" aria-label="On this page"><h2>On this page</h2><ol>';
	foreach ( $toc as $t ) {
		$out .= '<li><a href="#' . esc_attr( $t['id'] ) . '">' . esc_html( $t['text'] ) . '</a></li>';
	}
	$out .= '</ol></nav>';
	// Her v1 board's "Applying for a role?" box belongs to the candidate notice only. Vacancies shows itself once live.
	if ( 'candidate-privacy' === get_post_field( 'post_name', get_the_ID() ) ) {
		$out .= '<div class="acs-legal__apply"><h2>Applying for a role?</h2><p>See the roles open now, or how applications work.</p><ul>'
			. ( acs_has_real( 'vacancy' ) ? '<li><a class="acs-legal__btn acs-legal__btn--fill" href="/vacancies/">Vacancies</a></li>' : '' )
			. '<li><a class="acs-legal__btn acs-legal__btn--ghost" href="/work-with-us/">Work with us</a></li></ul></div>';
	}
	return $out . '</div>';
}

/* The legal header's eyebrow names the footer group: "Candidates" on the candidate notice (her v1 board). */
add_filter(
	'render_block_core/paragraph',
	function ( $html ) {
		if ( false !== strpos( $html, 'acs-legal__eyebrow' ) && 'candidate-privacy' === get_post_field( 'post_name', get_queried_object_id() ) ) {
			return str_replace( '>Terms and privacy<', '>Candidates<', $html );
		}
		return $html;
	}
);

/* Bracketed placeholders in a legal page's paragraphs and lists show as amber highlights, as on her board. */
foreach ( array( 'core/paragraph', 'core/list' ) as $acs_legal_block ) {
	add_filter(
		'render_block_' . $acs_legal_block,
		function ( $html ) {
			if ( ! is_page_template( 'legal' ) || false === strpos( $html, '[' ) || false !== strpos( $html, 'acs-legal__updated' ) ) {
				return $html;
			}
			return preg_replace_callback(
				'/>([^<]*)</',
				function ( $m ) {
					return '>' . preg_replace( '/\[[^\]<>]+\]/', '<mark class="acs-legal__ph">$0</mark>', $m[1] ) . '<';
				},
				$html
			);
		}
	);
}
