<?php
/**
 * Sample entries for the blog and vacancy template previews (2 Oct 2026).
 * Idempotent: finds each by slug and updates it. Every visible line says SAMPLE
 * so nobody mistakes it for copy. Delete both entries before launch.
 *
 * Also sets the post permalink to /resources/%postname%/ on this local site, so
 * articles live under Resources and never collide with page addresses at the
 * root. ⚠ The production site needs the same setting (DEPLOY note in README).
 */
update_option( 'permalink_structure', '/resources/%postname%/' );
flush_rewrite_rules();

$para = function ( $t ) { return "<!-- wp:paragraph -->\n<p>$t</p>\n<!-- /wp:paragraph -->\n"; };
$h2   = function ( $t ) { return "<!-- wp:heading -->\n<h2 class=\"wp-block-heading\">$t</h2>\n<!-- /wp:heading -->\n"; };
$list = function ( $items ) { return "<!-- wp:list -->\n<ul class=\"wp-block-list\">" . implode( '', array_map( function ( $i ) { return "<li>$i</li>"; }, $items ) ) . "</ul>\n<!-- /wp:list -->\n"; };

$samples = array(
	array(
		'post_type'    => 'vacancy',
		'post_name'    => 'sample-vacancy',
		'post_title'   => 'SAMPLE ROLE: replace with an approved vacancy',
		'post_excerpt' => 'SAMPLE: one sentence on what the role owns.',
		'post_content' => "<!-- wp:heading {\"level\":4} -->\n<h4 class=\"wp-block-heading\">Key tasks</h4>\n<!-- /wp:heading -->\n"
			. $list( array( 'SAMPLE: a key task', 'SAMPLE: another key task', 'SAMPLE: a third key task' ) )
			. "<!-- wp:heading {\"level\":4} -->\n<h4 class=\"wp-block-heading\">What we look for</h4>\n<!-- /wp:heading -->\n"
			. $list( array( 'SAMPLE: a requirement', 'SAMPLE: another requirement' ) ),
		'image'        => null,
		'terms'        => array( 'vacancy_role' => 'Telesales', 'vacancy_level' => 'Intermediate', 'vacancy_hours' => 'Full time' ),
		'apply'        => '#',
	),
	array(
		'post_type'    => 'vacancy',
		'post_name'    => 'sample-vacancy-2',
		'post_title'   => 'SAMPLE ROLE 2: replace with an approved vacancy',
		'post_excerpt' => 'SAMPLE: one sentence on what the role owns.',
		'post_content' => "<!-- wp:heading {\"level\":4} -->\n<h4 class=\"wp-block-heading\">Key tasks</h4>\n<!-- /wp:heading -->\n"
			. $list( array( 'SAMPLE: a key task', 'SAMPLE: another key task', 'SAMPLE: a third key task' ) )
			. "<!-- wp:heading {\"level\":4} -->\n<h4 class=\"wp-block-heading\">What we look for</h4>\n<!-- /wp:heading -->\n"
			. $list( array( 'SAMPLE: a requirement', 'SAMPLE: another requirement' ) ),
		'image'        => null,
		'terms'        => array( 'vacancy_role' => 'Bookkeeper', 'vacancy_level' => 'Junior', 'vacancy_hours' => 'Part time' ),
		'apply'        => '#',
	),
);

// WordPress's default "Hello world!" post would list on the blog index. Drafted, not deleted.
$hello = get_posts( array( 'post_type' => 'post', 'name' => 'hello-world', 'post_status' => 'publish', 'numberposts' => 1 ) );
if ( $hello ) {
	wp_update_post( array( 'ID' => $hello[0]->ID, 'post_status' => 'draft' ) );
	WP_CLI::log( 'drafted the default hello-world post' );
}

foreach ( $samples as $s ) {
	$found = get_posts( array( 'post_type' => $s['post_type'], 'name' => $s['post_name'], 'post_status' => array( 'publish', 'draft' ), 'numberposts' => 1 ) );
	$args  = array(
		'post_type'    => $s['post_type'],
		'post_name'    => $s['post_name'],
		'post_title'   => $s['post_title'],
		'post_excerpt' => $s['post_excerpt'],
		'post_content' => $s['post_content'],
		'post_status'  => 'publish',
	);
	if ( $found ) {
		$args['ID'] = $found[0]->ID;
		$id         = wp_update_post( $args );
	} else {
		$id = wp_insert_post( $args );
	}
	if ( $s['image'] && ! get_post_thumbnail_id( $id ) ) {
		require_once ABSPATH . 'wp-admin/includes/file.php';
		require_once ABSPATH . 'wp-admin/includes/media.php';
		require_once ABSPATH . 'wp-admin/includes/image.php';
		$tmp = wp_tempnam( $s['image'] );
		copy( get_theme_file_path( 'assets/img/' . $s['image'] ), $tmp );
		$att = media_handle_sideload( array( 'name' => $s['image'], 'tmp_name' => $tmp ), $id );
		if ( ! is_wp_error( $att ) ) {
			set_post_thumbnail( $id, $att );
		}
	}
	if ( ! empty( $s['terms'] ) ) {
		foreach ( $s['terms'] as $tax => $name ) {
			wp_set_object_terms( $id, $name, $tax );
		}
	}
	if ( isset( $s['apply'] ) ) {
		update_post_meta( $id, '_acs_apply_url', $s['apply'] ); // '#' = no provider address yet
	}
	update_post_meta( $id, '_acs_sample', 1 ); // never counts towards showing Resources or Vacancies
	WP_CLI::log( "sample {$s['post_type']} {$s['post_name']} -> #$id" );
}

/*
 * RESOURCES SAMPLES (2 Oct 2026): Janet Biag's blog design (claude.ai artifact
 * GPjeFaL4CcinbwXLsbhj9f). Twelve articles with her mockup titles and
 * summaries, so the hub, the three category pages and the article read as her
 * boards do. Only the featured guide has a body (hers, verbatim); the others
 * carry a SAMPLE line. Bylines are her placeholders. All are SAMPLE entries:
 * they list only under /template-preview/ and never make a Resources page show.
 * ⚠ Before launch: delete every post with the meta _acs_sample.
 */
$old = get_posts( array( 'post_type' => 'post', 'name' => 'sample-article', 'post_status' => 'any', 'numberposts' => 1 ) );
if ( $old ) {
	wp_delete_post( $old[0]->ID, true ); // the generic 2 Oct sample, replaced by Janet's set
	WP_CLI::log( 'deleted the old sample-article post' );
}

$cat_ids = array();
foreach ( array( 'guides' => 'Guides', 'role-suitability-checklist' => 'Role suitability checklists', 'position-descriptions' => 'Position descriptions' ) as $slug => $name ) {
	$t = term_exists( $slug, 'category' );
	if ( ! $t ) {
		$t = wp_insert_term( $name, 'category', array( 'slug' => $slug ) );
	}
	$cat_ids[ $slug ] = (int) ( is_array( $t ) ? $t['term_id'] : $t );
}

$checks  = function ( $items ) { return "<!-- wp:list {\"className\":\"acs-checks\"} -->\n<ul class=\"wp-block-list acs-checks\">" . implode( '', array_map( function ( $i ) { return "<li>$i</li>"; }, $items ) ) . "</ul>\n<!-- /wp:list -->\n"; };
$details = function ( $q, $a, $open = false ) { return '<!-- wp:details' . ( $open ? ' {"showContent":true}' : '' ) . " -->\n<details class=\"wp-block-details\"" . ( $open ? ' open' : '' ) . "><summary>$q</summary><!-- wp:paragraph -->\n<p>$a</p>\n<!-- /wp:paragraph --></details>\n<!-- /wp:details -->\n"; };
$sample_body = $para( 'SAMPLE TEXT. This article is a placeholder for the template preview. Replace it with approved copy before publishing.' );

$flagship = $para( 'Most owners do not start with a job title. They start with a task that is eating their week. This guide walks through turning that task into a role an offshore team member can own.' )
	. $h2( 'Start with the task, not the title' )
	. $para( 'Job titles are a shortcut, and they often point to the wrong role. Two businesses can both say they need an admin assistant and mean completely different work.' )
	. $para( 'Instead, write down the tasks that are actually costing you time each week. Be specific: answering calls you missed while on a job, sending quotes, chasing unpaid invoices, updating the schedule.' )
	. $h2( 'Check each task against three questions' )
	. $para( 'A task can generally be supported by an offshore team member if the answer to all three is yes.' )
	. $checks( array( 'It is done on a computer', 'It follows a process you could write down', 'It does not need someone physically on site' ) )
	. $para( 'A task that fails one of these is not automatically ruled out, but it needs a closer look on the scoping call.' )
	. "<!-- wp:group {\"className\":\"acs-tip\",\"layout\":{\"type\":\"default\"}} -->\n<div class=\"wp-block-group acs-tip\"><!-- wp:paragraph {\"className\":\"acs-tip__label\"} -->\n<p class=\"acs-tip__label\">Tip</p>\n<!-- /wp:paragraph -->\n"
	. "<!-- wp:paragraph -->\n<p>Run each task through the <a href=\"/resources/role-suitability-checklist/\">role suitability checklist</a> before your first call. It takes a few minutes and makes the call shorter.</p>\n<!-- /wp:paragraph --></div>\n<!-- /wp:group -->\n"
	. $h2( 'Decide what should stay in Australia' )
	. $para( 'Some work should stay local, usually because it sits close to the client relationship or needs judgement that should not be delegated. Separating that work early keeps the offshore role clean and the handover realistic.' )
	. $h2( 'List the systems the role will use' )
	. $para( 'Candidates are screened against the systems your business actually runs, not a generic skill set. Note every platform the role touches, such as your CRM, accounting software, job management tool or shared inbox, and what level of access each task needs.' )
	. $h2( 'Agree what good looks like' )
	. $para( 'Performance measures work best when they are set before the person starts. Most roles can be measured on three things.' )
	. "<!-- wp:list {\"ordered\":true} -->\n<ol class=\"wp-block-list\"><li><strong>Output</strong>, such as calls made, invoices processed or tickets resolved</li><li><strong>Quality</strong>, such as accuracy rates or client feedback</li><li><strong>Responsiveness</strong>, such as turnaround time on requests</li></ol>\n<!-- /wp:list -->\n"
	. $h2( 'Set the seniority and hours' )
	. $para( 'The last inputs are seniority and hours: junior, intermediate or senior, and full time or part time. Together with the role itself and any systems it must hold, these are what the pricing calculator uses to give you an indicative range.' )
	. $h2( 'Common scoping mistakes' )
	. $list( array( '<strong>Scoping too broadly.</strong> Vague scoping produces the wrong shortlist.', '<strong>Handing over judgement calls too early.</strong> Authority is best built up in stages over the first 90 days.', '<strong>Restricting system access.</strong> A restricted version of your systems slows the role down from day one.' ) )
	. $para( 'With the task list written, the three questions answered and the systems noted, the scoping call becomes a short conversation rather than a long one.' )
	. $h2( 'Frequently asked questions' )
	. $details( 'How long does the scoping call take?', 'About an hour of your time. It is a conversation about what the work actually is: the real tasks and the systems they sit in, not a job title.', true )
	. $details( 'Can I be involved in writing the role scope?', 'Yes, and it works best when you are. The scoping conversation is built around your actual workflow, not a generic template.' )
	. $details( 'What if I am not sure which role fits?', 'Tell us the task that is eating your week. On the call we will tell you which role, or combination of roles, actually solves it.' )
	. $details( 'Can the scope change after the person starts?', 'Yes. Scope adjustments based on real experience are normal, particularly during the first 90 days, and are discussed openly rather than treated as a failure of the original scoping.' )
	. $details( 'How long does it take to find someone?', 'It depends on the role and how specific the requirements are. We give a realistic estimate on the scoping call rather than a generic promise.' );

// Newest first on the pages, so each list is dated in reverse of its order here.
$articles = array(
	array( 'guides', 'sample-scope-an-offshore-role', 'How to scope an offshore role around your workflow', 'Most owners start with a task that is eating their week, not a job title. Here is how to turn that task into a role an offshore team member can own.', 'team-13.jpg', $flagship, true ),
	array( 'guides', 'sample-prepare-first-day', "What to prepare before your team member's first day", 'System access, documented processes and a narrow first task. What to have ready so week one is spent working, not waiting on logins.', 'team-05.jpg' ),
	array( 'guides', 'sample-performance-measured', 'How performance is measured once the role is live', 'Output, quality and responsiveness measures, agreed before the person starts and reported on a regular cadence.', 'team-14.jpg' ),
	array( 'guides', 'sample-freelancer-bpo-managed', 'Freelancer, BPO or managed service: matching the model to the work', 'A one off project, high volume processing and ongoing operational work each suit a different model. Here is how to tell which you have.', 'team-07.jpg' ),
	array( 'guides', 'sample-stay-in-australia', 'Which work should stay in Australia', 'Some work sits close to the client relationship or needs judgement that should not be delegated. How to tell the difference before you scope.', 'team-11.jpg' ),
	array( 'guides', 'sample-first-90-days', 'Your first 90 days with an offshore team member', 'Foundation, expansion, then ownership. What changes at 30, 60 and 90 days, and what is needed from you at each stage.', 'team-06.jpg' ),
	array( 'role-suitability-checklist', 'sample-task-suitable', 'Is this task suitable for an offshore team member?', 'Is it done on a computer? Does it follow a process you could write down? Does it need someone on site? Start here.' ),
	array( 'role-suitability-checklist', 'sample-checklist-telesales', 'Role suitability checklist: Telesales', 'Lead follow up, appointment setting and customer calls. Check whether your call workload is ready to hand over.' ),
	array( 'role-suitability-checklist', 'sample-checklist-bookkeeping', 'Role suitability checklist: Bookkeeping', 'Transaction entry, bank feed reconciliation and BAS preparation. Check what can move and what stays with your accountant.' ),
	array( 'position-descriptions', 'sample-pd-admin-assistant', 'Position description: Admin assistant', 'Email, documents and customer admin, handled consistently so nothing waits on you.' ),
	array( 'position-descriptions', 'sample-pd-operations-manager', 'Position description: Operations manager', 'Owns a workflow end to end, reports on it and handles escalations within agreed authority.' ),
	array( 'position-descriptions', 'sample-pd-social-media-manager', 'Position description: Social media manager', 'Plans, schedules, posts and reports on your core channels, to a consistent cadence.' ),
);

require_once ABSPATH . 'wp-admin/includes/file.php';
require_once ABSPATH . 'wp-admin/includes/media.php';
require_once ABSPATH . 'wp-admin/includes/image.php';
foreach ( $articles as $i => $a ) {
	list( $cat, $slug, $title, $excerpt ) = $a;
	$image = $a[4] ?? null;
	$body  = $a[5] ?? ( 'role-suitability-checklist' === $cat ? $sample_body . $checks( array( 'SAMPLE: a check', 'SAMPLE: another check', 'SAMPLE: a third check' ) ) : $sample_body );
	$found = get_posts( array( 'post_type' => 'post', 'name' => $slug, 'post_status' => 'any', 'numberposts' => 1 ) );
	$args  = array(
		'post_type'     => 'post',
		'post_name'     => $slug,
		'post_title'    => $title,
		'post_excerpt'  => $excerpt,
		'post_content'  => $body,
		'post_status'   => 'publish',
		'post_date'     => gmdate( 'Y-m-d H:i:s', strtotime( '2026-10-01 09:00:00' ) - $i * DAY_IN_SECONDS ),
		'post_category' => array( $cat_ids[ $cat ] ),
	);
	if ( $found ) {
		$args['ID'] = $found[0]->ID;
		$id         = wp_update_post( $args );
	} else {
		$id = wp_insert_post( $args );
	}
	if ( $image && ! get_post_thumbnail_id( $id ) ) {
		$tmp = wp_tempnam( $image );
		copy( get_theme_file_path( 'assets/img/' . $image ), $tmp );
		$att = media_handle_sideload( array( 'name' => $image, 'tmp_name' => $tmp ), $id );
		if ( ! is_wp_error( $att ) ) {
			set_post_thumbnail( $id, $att );
		}
	}
	update_post_meta( $id, '_acs_sample', 1 );
	update_post_meta( $id, '_acs_author', '[Author name]' );
	update_post_meta( $id, '_acs_author_role', '[Role]' );
	update_post_meta( $id, '_acs_coauthor', '[Co-author name]' );
	update_post_meta( $id, '_acs_editor', '[Editor name]' );
	if ( ! empty( $a[6] ) ) {
		update_post_meta( $id, '_acs_featured', 1 );
	} else {
		delete_post_meta( $id, '_acs_featured' );
	}
	WP_CLI::log( "sample article $slug -> #$id" );
}
