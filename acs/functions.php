<?php
/**
 * ACS theme.
 *
 * Deliberately small. A block theme's design lives in theme.json; this file
 * exists for the two things theme.json cannot do.
 */

declare( strict_types = 1 );

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/*
 * Where the site's forms post. Configuration, not code, so the review site and
 * the launched site can differ without editing JavaScript; define it in
 * wp-config.php to override. assets/js/forms.js reads it as window.acsIntake.url
 * and sends nothing when it is empty. See
 * automations/acs-lead-capture/DESIGN-DELTA-2026-10-13-wire-forms.md.
 */
if ( ! defined( 'ACS_INTAKE_URL' ) ) {
	define( 'ACS_INTAKE_URL', 'https://teamsignal.app.n8n.cloud/webhook/acs-enquiry-intake' );
}

/**
 * The direction contract, printed as the first child of <body>.
 *
 * It ships in the emitted markup on purpose. A contract that lives only in a
 * source comment is one nobody can audit against the built page, and this is
 * the page's own record of what it committed to.
 */
add_action(
	'wp_body_open',
	static function (): void {
		echo "<!--\n"
			. "SEED: acs2026 · direction · persuade · assigned index 6 of 7\n"
			. "THESIS: ACS sells a specified role with a named party accountable for it. This surface is the specification itself, not a brochure about one. It refuses the offshore-staffing arrangement every competitor ships: a savings figure, a world map, a smiling headset.\n"
			. "OWN-WORLD: The Australian commercial tender document. Cool paper ground, blue-biased neutrals, structure carried in ACS blue at region scale, ACS red reserved for the single action on any page. Archivo with its expanded axis for clause headings, Martian Mono for clause numbers and reference codes. Two faces, no third. Hierarchy from rules, case and indentation.\n"
			. "STORY: A short-staffed Australian operator arrives unsure who would actually be responsible. They read a specification, see the responsibility split before anything else, and leave having written one.\n"
			. "FIRST VIEWPORT: Positioning set as clause 1.0, supporting line beneath a rule, then immediately the two-column responsibility table. Red primary action at the foot of that table, never floating in a hero.\n"
			. "FORM: Specification and Schedule. Candidate 6 of the grounded list, assigned by the roll.\n"
			. "FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, and DESIGN.md\n"
			. "-->\n";
	},
	0
);

/**
 * Editor assets and the block styles the templates rely on.
 *
 * ⚠ The stylesheet stays thin by design. Anything that lands in it is
 * something theme.json genuinely cannot express; a long file here means the
 * design is fighting the platform.
 */
add_action(
	'wp_enqueue_scripts',
	static function (): void {
		wp_enqueue_style(
			'acs',
			get_stylesheet_uri(),
			array(),
			(string) filemtime( get_stylesheet_directory() . '/style.css' )
		);

		// Deferred, and the stylesheet hides nothing until it runs. See
		// assets/js/reveal.js for why that order is not optional.
		if ( is_page_template( 'build-your-team' ) || is_page( 'build-your-team' ) ) {
			wp_enqueue_script(
				'acs-configurator',
				get_stylesheet_directory_uri() . '/assets/js/configurator.js',
				// After forms.js, which defines the shared sender it submits through.
				array( 'acs-forms' ),
				(string) filemtime( get_stylesheet_directory() . '/assets/js/configurator.js' ),
				array( 'strategy' => 'defer', 'in_footer' => true )
			);
			// The cost calculator (Chris's 2026-08-27 amendment). Placeholder
			// structure: renders no figure until approved pricing exists.
			wp_enqueue_script(
				'acs-calculator',
				get_stylesheet_directory_uri() . '/assets/js/calculator.js',
				array(),
				(string) filemtime( get_stylesheet_directory() . '/assets/js/calculator.js' ),
				array( 'strategy' => 'defer', 'in_footer' => true )
			);
		}

		/*
		 * ⚠ Loaded on every page rather than only where a form is today. The
		 * copy team can drop the contact pattern onto any of the 41 pages, and
		 * a validation script that is only present on two of them fails
		 * silently on the third. It exits immediately when there is no form.
		 */
		wp_enqueue_script(
			'acs-forms',
			get_stylesheet_directory_uri() . '/assets/js/forms.js',
			array(),
			(string) filemtime( get_stylesheet_directory() . '/assets/js/forms.js' ),
			array( 'strategy' => 'defer', 'in_footer' => true )
		);
		wp_add_inline_script(
			'acs-forms',
			'window.acsIntake = ' . wp_json_encode( array( 'url' => ACS_INTAKE_URL ) ) . ';',
			'before'
		);

		/*
		 * ⚠ REPLACES assets/js/reveal.js, which did section fades only. The
		 * motion system supersedes it: same guarantee that content is visible
		 * without JavaScript, more moments, all applied by attribute so a page
		 * the copy team builds next month gets them for free.
		 */
		wp_enqueue_script(
			'acs-motion',
			get_stylesheet_directory_uri() . '/assets/js/motion.js',
			array(),
			(string) filemtime( get_stylesheet_directory() . '/assets/js/motion.js' ),
			array( 'strategy' => 'defer', 'in_footer' => true )
		);
	}
);

add_action(
	'after_setup_theme',
	static function (): void {
		add_theme_support( 'wp-block-styles' );
		add_theme_support( 'responsive-embeds' );
		// No custom editor font sizes, colours or spacing: the copy team writes
		// 46 pages into this theme, and open arbitrary-value pickers guarantee a
		// page that stops matching the others with nobody finding it until launch.
		add_theme_support( 'disable-custom-colors' );
		add_theme_support( 'disable-custom-font-sizes' );
	}
);

/**
 * The child index block.
 *
 * A directory page lists the pages beneath it. Core's Query Loop can filter by
 * a fixed parent id, which is useless in a TEMPLATE: one template serves both
 * directories, so a hard-coded parent makes Who We Help list the roles. Without
 * this block the directory listed every page on the site, Sample Page included.
 *
 * ⚠ The proposal singles the directories out: "The two directories set the
 * template for the sixteen pages beneath them." Getting the card right here is
 * what thirteen other pages inherit.
 *
 * The card front is a complete summary rather than a link: reference, name, and
 * the line that says what it is. A visitor should be able to choose without
 * opening anything.
 */
add_action(
	'init',
	static function (): void {
		register_block_type(
			'acs/child-index',
			array(
				'api_version'     => 3,
				'title'           => 'Child index',
				'category'        => 'theme',
				'render_callback' => 'acs_render_child_index',
				'supports'        => array( 'align' => array( 'wide', 'full' ) ),
			)
		);
	}
);

/**
 * @param array<string,mixed> $attributes Block attributes.
 */
function acs_render_child_index( array $attributes = array() ): string {
	$parent = get_the_ID();
	if ( ! $parent ) {
		return '';
	}

	$children = get_pages(
		array(
			'child_of'    => $parent,
			'parent'      => $parent,
			'sort_column' => 'menu_order,post_title',
			'post_status' => 'publish',
		)
	);

	$wrapper = get_block_wrapper_attributes( array( 'class' => 'acs-index' ) );

	if ( empty( $children ) ) {
		// Says what to do about it. An empty grid with no explanation reads as a
		// broken page to whoever is building the site out.
		return sprintf(
			'<div %s><p class="acs-index--empty">%s</p></div>',
			get_block_wrapper_attributes( array( 'class' => 'acs-index--empty' ) ),
			esc_html__( 'No pages sit beneath this one yet. Set this page as the parent on its child pages and they appear here.', 'acs' )
		);
	}

	$items = '';

	/*
	 * ⚠ NO REFERENCE NUMBER ON A DIRECTORY CARD, 2026-08-20. The cards used to
	 * open with 01..08. Caught by John, and it is the same correction he made
	 * that morning about clause numbers in section labels: a number earns its
	 * place where it enumerates a real set or a real order, and a grid of roles
	 * is neither. Nothing ranks Bookkeepers above Telesales, the heading above
	 * already says how many there are, and a visitor cannot act on "07".
	 *
	 * Numbering survives where the count is genuinely information: the eight
	 * inclusions on What Is Included, and the four stages, which are a sequence.
	 */
	foreach ( $children as $child ) {
		$summary = has_excerpt( $child ) ? get_the_excerpt( $child ) : wp_trim_words( wp_strip_all_tags( $child->post_content ), 22 );

		$items .= sprintf(
			'<a class="acs-index__item" href="%1$s"><span class="acs-index__name">%2$s</span><p class="acs-index__summary">%3$s</p></a>',
			esc_url( (string) get_permalink( $child ) ),
			esc_html( get_the_title( $child ) ),
			esc_html( $summary )
		);
	}

	return sprintf( '<div %1$s>%2$s</div>', $wrapper, $items );
}

/**
 * Head metadata: description, Open Graph, and structured data.
 *
 * ⚠ WHY THIS EXISTS. Janet's Tier 1 copy (17 August 2026) specifies a meta
 * title AND a meta description for every page, and marks up six questions on
 * `Who Employs Your Staff` as FAQ schema. On 2026-08-21 this theme emitted
 * NONE of that — no description, no Open Graph, no JSON-LD, on any of the 41
 * pages. Block themes do not provide it and nothing else here was going to.
 * Checked on rendered pages, not inferred. See
 * `context/audits/2026-08-21-janet-tier1-copy-vs-built-site.md`.
 *
 * ⚠ THE DESCRIPTION HAS ITS OWN FIELD, DELIBERATELY NOT THE EXCERPT. The
 * excerpt is already a VISIBLE slot — the role and industry templates render it
 * as the hero lede. Overloading it would mean one edit silently changing two
 * unrelated things. `_acs_meta_description` is a separate post meta, fed by the
 * `description` key in `content/pages.json`.
 */

/**
 * The page's meta description, or an empty string.
 *
 * Empty is a real answer, not a failure to be papered over: `check-site.sh`
 * fails the build when a page has none, which is a louder signal than silently
 * falling back to the first paragraph of placeholder copy.
 */
function acs_meta_description( ?WP_Post $post = null ): string {
	$post = $post ?? get_post();
	if ( ! $post instanceof WP_Post ) {
		return '';
	}
	$description = get_post_meta( $post->ID, '_acs_meta_description', true );

	return is_string( $description ) ? trim( $description ) : '';
}

/**
 * Question and answer pairs, read from the page's own `<details>` markup.
 *
 * ⚠ DRIVEN BY THE RENDERED ACCORDION, NEVER BY A SEPARATE LIST. FAQ schema that
 * does not match the visible questions is exactly the kind of drift this repo
 * keeps finding: two records of the same thing, diverging quietly. If the
 * accordion changes, this changes with it or it emits nothing.
 */
function acs_faq_pairs( WP_Post $post ): array {
	if ( false === strpos( $post->post_content, 'acs-faq__item' ) ) {
		return array();
	}

	$pairs = array();
	if ( ! preg_match_all( '#<details class="acs-faq__item">(.*?)</details>#s', $post->post_content, $items ) ) {
		return array();
	}

	foreach ( $items[1] as $item ) {
		if ( ! preg_match( '#<summary[^>]*>(.*?)</summary>#s', $item, $question ) ) {
			continue;
		}
		$answer = preg_replace( '#<summary[^>]*>.*?</summary>#s', '', $item );
		$answer = wp_strip_all_tags( (string) $answer );
		$answer = trim( preg_replace( '/\s+/', ' ', $answer ) ?? '' );
		$text   = trim( wp_strip_all_tags( $question[1] ) );

		if ( '' === $text || '' === $answer ) {
			continue;
		}
		$pairs[] = array( 'question' => $text, 'answer' => $answer );
	}

	return $pairs;
}

/**
 * Ancestors of the current page, nearest last, for the breadcrumb trail.
 */
function acs_breadcrumb_trail( WP_Post $post ): array {
	$trail = array();
	foreach ( array_reverse( get_post_ancestors( $post ) ) as $ancestor_id ) {
		$trail[] = array(
			'name' => get_the_title( $ancestor_id ),
			'url'  => get_permalink( $ancestor_id ),
		);
	}
	$trail[] = array( 'name' => get_the_title( $post ), 'url' => get_permalink( $post ) );

	return $trail;
}

/**
 * Print one JSON-LD block.
 */
function acs_print_json_ld( array $graph ): void {
	$json = wp_json_encode( $graph, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE );
	if ( false === $json ) {
		return;
	}
	echo "<script type=\"application/ld+json\">{$json}</script>\n";
}

add_action(
	'wp_head',
	static function (): void {
		if ( ! is_singular() ) {
			return;
		}
		$post = get_post();
		if ( ! $post instanceof WP_Post ) {
			return;
		}

		$description = acs_meta_description( $post );
		$title       = wp_get_document_title();
		$url         = get_permalink( $post );
		$site        = get_bloginfo( 'name' );

		if ( '' !== $description ) {
			printf( "<meta name=\"description\" content=\"%s\">\n", esc_attr( $description ) );
			printf( "<meta property=\"og:description\" content=\"%s\">\n", esc_attr( $description ) );
			printf( "<meta name=\"twitter:description\" content=\"%s\">\n", esc_attr( $description ) );
		}

		printf( "<meta property=\"og:type\" content=\"website\">\n" );
		printf( "<meta property=\"og:site_name\" content=\"%s\">\n", esc_attr( $site ) );
		printf( "<meta property=\"og:locale\" content=\"en_AU\">\n" );
		printf( "<meta property=\"og:title\" content=\"%s\">\n", esc_attr( $title ) );
		printf( "<meta property=\"og:url\" content=\"%s\">\n", esc_url( $url ) );
		printf( "<meta name=\"twitter:card\" content=\"summary\">\n" );
		printf( "<meta name=\"twitter:title\" content=\"%s\">\n", esc_attr( $title ) );

		/*
		 * ⚠ NO og:image, ON PURPOSE. Every photograph on this site is an
		 * Unsplash stand-in showing no ACS person, client or workplace
		 * (`PHOTOGRAPHY.md`). An og:image is the picture that represents the
		 * business everywhere the page is shared, and a placeholder promoted to
		 * that role is the same mistake as the duotone coming off: a stand-in
		 * quietly reading as a final choice. It goes in when a real asset does.
		 */

		$graph = array();

		if ( is_front_page() ) {
			/*
			 * ⚠ NO foundingDate, EVEN THOUGH THE PROSE CARRIES A TRADING YEAR.
			 * Schema is a machine-readable factual assertion and a stronger
			 * claim than a sentence. Register row Proof 1.0 — what may be
			 * stated about trading history — is unanswered. The prose exception
			 * is recorded and attributed in `COPY-PROVENANCE.md`; it does not
			 * extend to structured data.
			 */
			$graph[] = array(
				'@context'    => 'https://schema.org',
				'@type'       => 'Organization',
				'name'        => $site,
				'url'         => home_url( '/' ),
				'description' => $description,
			);
			$graph[] = array(
				'@context' => 'https://schema.org',
				'@type'    => 'WebSite',
				'name'     => $site,
				'url'      => home_url( '/' ),
			);
		}

		$trail = acs_breadcrumb_trail( $post );
		if ( count( $trail ) > 1 ) {
			$items = array();
			foreach ( $trail as $position => $crumb ) {
				$items[] = array(
					'@type'    => 'ListItem',
					'position' => $position + 1,
					'name'     => $crumb['name'],
					'item'     => $crumb['url'],
				);
			}
			$graph[] = array(
				'@context'        => 'https://schema.org',
				'@type'           => 'BreadcrumbList',
				'itemListElement' => $items,
			);
		}

		$faqs = acs_faq_pairs( $post );
		if ( ! empty( $faqs ) ) {
			$entities = array();
			foreach ( $faqs as $faq ) {
				$entities[] = array(
					'@type'          => 'Question',
					'name'           => $faq['question'],
					'acceptedAnswer' => array(
						'@type' => 'Answer',
						'text'  => $faq['answer'],
					),
				);
			}
			$graph[] = array(
				'@context'   => 'https://schema.org',
				'@type'      => 'FAQPage',
				'mainEntity' => $entities,
			);
		}

		foreach ( $graph as $block ) {
			acs_print_json_ld( $block );
		}
	},
	1
);

/**
 * Per-page hero photograph for the shared ROLE and INDUSTRY templates.
 *
 * Added 2026-09-28. Both templates draw their hero from the template file, so
 * every page on them showed the same empty "Role banner" / "Industry banner"
 * placeholder, while Janet Biag's photograph for that page (supplied 17 Sep)
 * could only go into a slot further down. The template now carries a marker,
 * and this renders the page's own photograph in its place:
 * `assets/img/janet-<page-slug>-1.jpg`, 4:5 at its real size, if that file exists.
 * If it does not, the marker renders NOTHING: no placeholder, by John's
 * decision of 28 Sep to remove every empty image slot.
 */
add_filter(
	'render_block',
	function ( $content, $block ) {
		if ( 'core/html' !== ( $block['blockName'] ?? '' ) || false === strpos( $content, 'data-acs-page-hero' ) ) {
			return $content;
		}
		$slug = get_post_field( 'post_name', get_queried_object_id() );
		$file = 'janet-' . sanitize_file_name( $slug ) . '-1.jpg';
		if ( ! $slug || ! file_exists( get_theme_file_path( 'assets/img/' . $file ) ) ) {
			return '';
		}
		$src = esc_url( get_theme_file_uri( 'assets/img/' . $file ) );
		// Real dimensions: the 17 Sep set is 1200x1500, the 2 Oct role set 1080x1350.
		$size = getimagesize( get_theme_file_path( 'assets/img/' . $file ) );
		$w    = $size ? (int) $size[0] : 1200;
		$h    = $size ? (int) $size[1] : 1500;
		return '<figure class="acs-shot"><div class="acs-shot__frame" style="aspect-ratio:4/5">'
			. '<img src="' . $src . '" alt="" width="' . $w . '" height="' . $h . '" loading="eager" fetchpriority="high" decoding="async">'
			. '</div></figure>';
	},
	10,
	2
);

/*
 * VACANCIES as their own entry type (2 Oct 2026, Janet: build the template now,
 * show it when there are roles). Listed by the `vacancies-index` page template,
 * shown by `single-vacancy.html`. Addresses are /vacancy/<role>/ so they never
 * collide with the Vacancies page itself.
 */
add_action(
	'init',
	function () {
		register_post_type(
			'vacancy',
			array(
				'labels'       => array(
					'name'          => 'Vacancies',
					'singular_name' => 'Vacancy',
					'add_new_item'  => 'Add new vacancy',
				),
				'public'       => true,
				'show_in_rest' => true,
				'has_archive'  => false,
				'menu_icon'    => 'dashicons-id',
				'rewrite'      => array( 'slug' => 'vacancy', 'with_front' => false ), // not under the /resources/ post prefix
				'supports'     => array( 'title', 'editor', 'excerpt', 'revisions' ),
			)
		);
	}
);

/*
 * RESOURCES AND VACANCIES SHOW THEMSELVES (Janet, Slack 2 Oct 2026: "nakahide
 * siya kasi wala pa laman, tapos if meron na, matic na siya dapat lalabas").
 * While there is no published article (post) or no published vacancy, the page
 * answers 404, its menu or footer link is not printed, and it is left out of
 * the sitemap. The first real entry brings all three back with nothing to
 * switch on.
 *
 * Template-preview SAMPLE entries carry the meta `_acs_sample` and never count,
 * and they never list on the real pages; only /template-preview/ shows them.
 */
function acs_has_real( $post_type ) {
	static $cache = array();
	if ( ! isset( $cache[ $post_type ] ) ) {
		$q = new WP_Query(
			array(
				'post_type'      => $post_type,
				'post_status'    => 'publish',
				'posts_per_page' => 1,
				'fields'         => 'ids',
				'no_found_rows'  => true,
				'meta_query'     => array( array( 'key' => '_acs_sample', 'compare' => 'NOT EXISTS' ) ),
			)
		);
		$cache[ $post_type ] = ! empty( $q->posts );
	}
	return $cache[ $post_type ];
}

function acs_gated_pages() {
	return array( 'resources' => 'post', 'vacancies' => 'vacancy' );
}

add_action(
	'template_redirect',
	function () {
		foreach ( acs_gated_pages() as $slug => $type ) {
			if ( is_page( $slug ) && ! acs_has_real( $type ) ) {
				global $wp_query;
				$wp_query->set_404();
				status_header( 404 );
				nocache_headers();
				return;
			}
		}
	}
);

add_filter(
	'render_block',
	function ( $content, $block ) {
		$name = $block['blockName'] ?? '';
		if ( in_array( $name, array( 'core/navigation-link', 'core/navigation-submenu' ), true ) ) {
			$url = untrailingslashit( $block['attrs']['url'] ?? '' );
			foreach ( acs_gated_pages() as $slug => $type ) {
				if ( '/' . $slug === $url && ! acs_has_real( $type ) ) {
					return '';
				}
			}
		}
		if ( false !== strpos( $content, 'data-acs-show-if=' ) ) {
			$content = preg_replace_callback(
				'#<li data-acs-show-if="([a-z]+)">.*?</li>\s*#s',
				function ( $m ) {
					return acs_has_real( $m[1] ) ? str_replace( ' data-acs-show-if="' . $m[1] . '"', '', $m[0] ) : '';
				},
				$content
			);
		}
		return $content;
	},
	10,
	2
);

add_filter(
	'wp_sitemaps_posts_query_args',
	function ( $args, $post_type ) {
		if ( 'page' !== $post_type ) {
			return $args;
		}
		foreach ( acs_gated_pages() as $slug => $type ) {
			$page = get_page_by_path( $slug );
			if ( $page && ! acs_has_real( $type ) ) {
				$args['post__not_in'] = array_merge( $args['post__not_in'] ?? array(), array( $page->ID ) );
			}
		}
		return $args;
	},
	10,
	2
);

// SAMPLE entries list only under /template-preview/, never on the real pages.
add_filter(
	'query_loop_block_query_vars',
	function ( $query ) {
		$page = get_queried_object();
		$in_preview = $page instanceof WP_Post && ( 'template-preview' === get_post_field( 'post_name', $page->post_parent ) );
		$query['meta_query']   = $query['meta_query'] ?? array();
		$query['meta_query'][] = array( 'key' => '_acs_sample', 'compare' => $in_preview ? 'EXISTS' : 'NOT EXISTS' );
		return $query;
	}
);

/*
 * VACANCIES PAGE (now v2, the careers hub, Janet 2 Oct 09:56; see vacancies-index.html). Originally layout 1 of Janet's mockup ("Vacancies, with listings",
 * claude.ai artifact D5jThSYNNGR4oCdJFTkaap, 2 Oct 2026; chosen by John the
 * same day). Each role carries a role type, a seniority and hours as
 * taxonomies (the page filters on them) and an apply address in the meta
 * `_acs_apply_url`. Both mockup layouts send Apply to the staffing provider,
 * whose address is not confirmed, so each role holds its own. With no address
 * the button opens the role page instead.
 */
add_action(
	'init',
	function () {
		$tax = array(
			'vacancy_role'  => array( 'Role', 'Roles' ),
			'vacancy_level' => array( 'Seniority', 'Seniority' ),
			'vacancy_hours' => array( 'Hours', 'Hours' ),
		);
		foreach ( $tax as $slug => $names ) {
			register_taxonomy(
				$slug,
				'vacancy',
				array(
					'labels'            => array( 'name' => $names[1], 'singular_name' => $names[0] ),
					'public'            => false,
					'show_ui'           => true,
					'show_in_rest'      => true,
					'show_admin_column' => true,
					'hierarchical'      => true,
				)
			);
		}
		register_post_meta(
			'vacancy',
			'_acs_apply_url',
			array(
				'type'          => 'string',
				'single'        => true,
				'show_in_rest'  => true,
				'auth_callback' => function () { return current_user_can( 'edit_posts' ); },
			)
		);
	},
	11
);

/* The fixed option lists, in the mockup's order. Terms are created on demand. */
function acs_vacancy_options() {
	return array(
		'vacancy_role'  => array( 'Telesales', 'Operations Assistant', 'Operations Manager', 'Accounting And Finance', 'Bookkeeper', 'Admin Assistant', 'AI And Automation Specialist', 'Social Media Manager' ),
		'vacancy_level' => array( 'Junior', 'Intermediate', 'Senior' ),
		'vacancy_hours' => array( 'Full time', 'Part time' ),
	);
}

function acs_vacancy_terms( $id, $tax ) {
	$t = get_the_terms( $id, $tax );
	return ( $t && ! is_wp_error( $t ) ) ? wp_list_pluck( $t, 'name' ) : array();
}

function acs_role_icon( $role ) {
	$icons = array(
		'Telesales' => '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 14v-2a8 8 0 0 1 16 0v2"></path><rect x="3" y="14" width="4" height="6" rx="1.5"></rect><rect x="17" y="14" width="4" height="6" rx="1.5"></rect><path d="M19 20a3 3 0 0 1-3 2h-3"></path></svg>',
		'Operations Assistant' => '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2"></rect><path d="M3 10h18M8 3v4M16 3v4"></path><path d="M8 14h3v3H8z"></path></svg>',
		'Operations Manager' => '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="3" width="6" height="6" rx="1"></rect><rect x="15" y="15" width="6" height="6" rx="1"></rect><rect x="15" y="3" width="6" height="6" rx="1"></rect><path d="M9 6h6M18 9v6"></path></svg>',
		'Accounting And Finance' => '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="5" y="3" width="14" height="18" rx="2"></rect><path d="M8 7h8"></path><path d="M8 12h.01M12 12h.01M16 12h.01M8 16h.01M12 16h.01M16 16h.01"></path></svg>',
		'Bookkeeper' => '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z"></path><path d="M4 21a2 2 0 0 1 2-2h13v2"></path><path d="M9 8h6M9 12h4"></path></svg>',
		'Admin Assistant' => '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"></rect><path d="m3 7 9 6 9-6"></path></svg>',
		'AI And Automation Specialist' => '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="7" y="7" width="10" height="10" rx="1.5"></rect><path d="M10 3v4M14 3v4M10 17v4M14 17v4M3 10h4M3 14h4M17 10h4M17 14h4"></path></svg>',
		'Social Media Manager' => '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 5h16v11H9l-5 4z"></path><path d="M8 9h8M8 12h5"></path></svg>',
	);
	return $icons[ $role ] ?? '';
}

/* One v2 card: role icon and posted date, tags, title, summary, where, apply. */
function acs_vacancy_card( $post ) {
	$id    = $post->ID;
	$role  = acs_vacancy_terms( $id, 'vacancy_role' );
	$level = acs_vacancy_terms( $id, 'vacancy_level' );
	$hours = acs_vacancy_terms( $id, 'vacancy_hours' );
	$apply = get_post_meta( $id, '_acs_apply_url', true );
	$href  = $apply ? $apply : get_permalink( $id );
	$label = $apply ? 'Apply for this role' : 'View role';
	$text  = strtolower( wp_strip_all_tags( get_the_title( $id ) . ' ' . get_the_excerpt( $id ) . ' ' . $post->post_content . ' ' . implode( ' ', $role ) ) );
	$tags  = '';
	foreach ( array_merge( $level, $hours ) as $t ) {
		$tags .= '<span class="acs-vac__tag">' . esc_html( $t ) . '</span>';
	}
	return '<article class="acs-vac" data-role="' . esc_attr( implode( '|', $role ) ) . '" data-text="' . esc_attr( $text ) . '">'
		. '<div class="acs-vac__top"><span class="acs-vac__icon">' . acs_role_icon( $role[0] ?? '' ) . '</span>'
		. '<span class="acs-vac__date">Posted ' . esc_html( get_the_date( 'j F Y', $id ) ) . '</span></div>'
		. '<div class="acs-vac__tags">' . $tags . '</div>'
		. '<h3 class="acs-vac__title"><a href="' . esc_url( get_permalink( $id ) ) . '">' . esc_html( get_the_title( $id ) ) . '</a></h3>'
		. ( has_excerpt( $id ) ? '<p class="acs-vac__summary">' . esc_html( get_the_excerpt( $id ) ) . '</p>' : '' )
		. '<p class="acs-vac__where">Remote, to agreed Australian client hours</p>'
		. '<a class="wp-element-button acs-vac__apply" href="' . esc_url( $href ) . '">' . esc_html( $label ) . '</a>'
		. '</article>';
}

add_filter(
	'render_block',
	function ( $content, $block ) {
		if ( 'core/html' !== ( $block['blockName'] ?? '' ) ) {
			return $content;
		}
		/* The staffing provider's address (Upload your CV, Register your interest). */
		if ( false !== strpos( $content, 'data-acs-provider-link' ) ) {
			$url     = get_option( 'acs_provider_url', '' );
			$content = str_replace( 'data-acs-provider-link href="#"', 'data-acs-provider-link href="' . esc_url( $url ? $url : '#' ) . '"' . ( $url ? ' target="_blank" rel="noopener"' : '' ), $content );
		}
		if ( false === strpos( $content, 'data-acs-vacancies' ) ) {
			return $content;
		}
		$page       = get_queried_object();
		$in_preview = $page instanceof WP_Post && 'template-preview' === get_post_field( 'post_name', $page->post_parent );
		$posts      = get_posts(
			array(
				'post_type'   => 'vacancy',
				'post_status' => 'publish',
				'numberposts' => -1,
				'orderby'     => 'date',
				'order'       => 'DESC',
				'meta_query'  => array( array( 'key' => '_acs_sample', 'compare' => $in_preview ? 'EXISTS' : 'NOT EXISTS' ) ),
			)
		);
		$cards = implode( '', array_map( 'acs_vacancy_card', $posts ) );
		return '<div class="acs-vac-list" id="vacancies" data-acs-vac-list>'
			. '<div class="acs-vac-list__head"><h2 class="wp-block-heading">Latest vacancies</h2>'
			. '<p class="acs-vac-list__active" hidden data-acs-vac-active><span data-acs-vac-active-label></span> <button type="button" class="acs-vac-list__clear" data-acs-vac-clear>Show all roles</button></p></div>'
			. '<div class="acs-vac-grid">' . $cards . '</div>'
			. '<p class="acs-vac-list__none" hidden data-acs-vac-none>No roles match.</p>'
			. '<p class="acs-vac-list__more" hidden data-acs-vac-more-wrap><button type="button" class="wp-element-button is-style-outline" data-acs-vac-more>View all vacancies</button></p>'
			. '</div>'
			. '<script>(function(){var l=document.querySelector("[data-acs-vac-list]");if(!l)return;var c=[].slice.call(l.querySelectorAll(".acs-vac")),LIM=6,all=false,role="",q="";'
			. 'var act=l.querySelector("[data-acs-vac-active]"),lab=l.querySelector("[data-acs-vac-active-label]"),none=l.querySelector("[data-acs-vac-none]"),mw=l.querySelector("[data-acs-vac-more-wrap]");'
			. 'function run(){var m=c.filter(function(a){return(!role||(a.dataset.role||"").split("|").indexOf(role)>-1)&&(!q||(a.dataset.text||"").indexOf(q)>-1)});var show=(all||role||q)?m:m.slice(0,LIM);'
			. 'c.forEach(function(a){a.hidden=show.indexOf(a)<0});none.hidden=m.length>0;mw.hidden=!(m.length>show.length);act.hidden=!(role||q);'
			. 'lab.textContent="Showing "+m.length+(m.length===1?" role":" roles")+(role?" for "+role:"")+(q?" matching “"+q+"”":"")}'
			. 'l.querySelector("[data-acs-vac-more]").addEventListener("click",function(){all=true;run()});'
			. 'l.querySelector("[data-acs-vac-clear]").addEventListener("click",function(){role="";q="";var i=document.querySelector("[data-acs-vac-search]");if(i)i.value="";run()});'
			. '[].forEach.call(document.querySelectorAll("[data-acs-role-tile]"),function(t){t.addEventListener("click",function(){role=t.getAttribute("data-acs-role-tile");q="";run();l.scrollIntoView({behavior:"smooth"})})});'
			. 'var f=document.querySelector("[data-acs-vac-search-form]");if(f)f.addEventListener("submit",function(e){e.preventDefault();q=(f.querySelector("[data-acs-vac-search]").value||"").trim().toLowerCase();role="";run();l.scrollIntoView({behavior:"smooth"})});run()})();</script>';
	},
	10,
	2
);

/* The role page's own Apply button, same rule as the card. */
add_filter(
	'render_block',
	function ( $content, $block ) {
		if ( 'core/html' !== ( $block['blockName'] ?? '' ) || false === strpos( $content, 'data-acs-vacancy-apply' ) ) {
			return $content;
		}
		$id    = get_queried_object_id();
		$apply = get_post_meta( $id, '_acs_apply_url', true );
		$tags  = '';
		foreach ( array_merge( acs_vacancy_terms( $id, 'vacancy_level' ), acs_vacancy_terms( $id, 'vacancy_hours' ) ) as $t ) {
			$tags .= '<span class="acs-vac__tag">' . esc_html( $t ) . '</span>';
		}
		return '<div class="acs-vac__tags acs-vac__tags--page">' . $tags . '</div>'
			. ( $apply ? '<p class="acs-vac__page-apply"><a class="wp-element-button acs-vac__apply" href="' . esc_url( $apply ) . '">Apply for this role</a></p>' : '' );
	},
	10,
	2
);

// Resources (the blog): Janet's hub, category and article layouts, 2 Oct 2026.
require_once get_theme_file_path( 'resources.php' );

/*
 * Editor notes never reach the public page source (22 Oct 2026, pre-launch).
 * Templates, parts and page content carry prose HTML comments for the build
 * team (approval records, names, internal channels). Block delimiters are
 * parsed away before this runs, so what is left in rendered HTML is only those
 * notes; they are stripped here. Conditional comments ("<!--[if") are kept.
 */
add_filter(
	'render_block',
	function ( $html ) {
		if ( ! is_string( $html ) || false === strpos( $html, '<!--' ) ) {
			return $html;
		}
		return preg_replace( '/<!--(?!\s*\[if).*?-->/s', '', $html );
	},
	PHP_INT_MAX
);
