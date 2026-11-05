/**
 * Build Your Team — cost estimation calculator. PLACEHOLDER STRUCTURE.
 *
 * Requested by Chris Banks 2026-08-27 ("ACS Website" thread) as an amendment
 * to the page: compare role options and estimated costs, then book a call or
 * request a custom quote. His reference (Offshore 24/7's calculator) was
 * supplied for general functionality only — this is an original build.
 *
 * ⚠ FIGURES ARE REVIEW-ONLY (state 'review-only', since 2026-09-03). Chris
 * Banks supplied one AUD range per role by email that day and, the same day,
 * said to work off the range for the three levels with A$2,600 as the floor.
 * The figures render on the gated review site under a review note. Public
 * clearance ('approved') still needs a name and date on the register's pricing
 * rows, an approved Australian comparison source, the inclusions line and the
 * disclaimer sign-off. The drift guard in automations/acs-lead-capture pins
 * the state and every figure to his emails; change either there first.
 *
 * ⚠ ROLES ARE DECLARED TWICE — here and in configurator.js. The drift guard
 * (automations/acs-lead-capture/test/calculator-drift.test.ts) reads BOTH
 * shipped files and fails when they disagree. Change one, change both.
 *
 * 2026-11-05: THE LEVEL SELECTOR IS GONE. Dan, through Chris (Slack DM 11:08
 * PHT): remove Junior, Intermediate and Senior; the calculator shows the job
 * title and the expected cost only. Each role now carries the one AUD range
 * Chris supplied on 3 Sep 2026, unchanged; the per-level split (bottom,
 * midpoint, top) is no longer rendered anywhere. The configurator below keeps
 * its own level step; it belongs to the enquiry contract.
 *
 * ⚠ AUD ONLY, decided by John 2026-08-27: the buyers are Australian
 * businesses paying in AUD. No currency toggle, no exchange-rate feed.
 *
 * Each PRICING cell is a number or { min, max }; the render handles both,
 * applies the floor, and scales by team size. Any figure change updates the
 * drift guard IN THE SAME CHANGE. Flip to 'approved' only when the public
 * gates above are all met.
 */
( function () {
	'use strict';

	var ROLES = [ 'Bookkeeper', 'Admin Assistant', 'Operations Assistant', 'Telesales', 'Accounting & Finance', 'Operations Manager', 'Social Media Manager', 'AI & Automation Specialist' ];


	var TEAM_MAX = 10; // Structural cap only; Chris's maximum replaces it.

	/**
	 * PRICING_STATE:
	 *   'pending-approval'  no figure anywhere (the 2026-08-27 placeholder).
	 *   'review-only'       the figures Chris Banks supplied on 2026-09-03 render
	 *                       on the password-gated review site, under a review
	 *                       note. This is NOT public clearance.
	 *   'approved'          public clearance: a name and date against the
	 *                       register's pricing rows, the comparison source
	 *                       approved, inclusions and disclaimer signed. Not reached.
	 * The drift guard pins the state and every figure to the source email.
	 */
	// 2026-10-27: 'approved' on John Jopson's instruction (14:05 PHT, "flip it"),
	// after the public site was found serving the figures in 'review-only'.
	// The register's pricing rows, the comparison source and the inclusions and
	// disclaimer sign-off listed above were NOT obtained first; the figures are
	// Chris Banks's 3 Sep 2026 ranges unchanged. Recorded in LOG.md and
	// decisions/log.md the same day.
	var PRICING_STATE = 'approved';

	/**
	 * Monthly client price per role, AUD. Source: Chris Banks's email of
	 * 2026-09-03 11:36 AEST ("ACS Website" thread), one range per role, and
	 * his reply at 13:35 PHT the same day: every role has a minimum of
	 * A$2,600 regardless. From 2026-11-05 the range is shown as he wrote it
	 * (no level split). The agent salaries in his first email are NOT here
	 * and never will be.
	 */
	var PRICE_FLOOR = 2600;

	var PRICING = {
		'Admin Assistant': { min: 2600, max: 2600 },
		'Telesales': { min: 2600, max: 2840 },
		'Bookkeeper': { min: 2600, max: 2600 },
		'Operations Assistant': { min: 2600, max: 2840 },
		'Social Media Manager': { min: 2600, max: 2637 },
		'Accounting & Finance': { min: 2600, max: 4868 },
		'Operations Manager': { min: 2637, max: 4057 },
		'AI & Automation Specialist': { min: 2600, max: 4057 }
	};

	var root = document.querySelector( '[data-acs-calculator]' );
	if ( ! root ) {
		return;
	}

	var state = { role: null, team: 1 };

	var roleEl = root.querySelector( '[data-acs-calc-roles]' );
	var teamEl = root.querySelector( '[data-acs-calc-team]' );
	var lessEl = root.querySelector( '[data-acs-calc-less]' );
	var moreEl = root.querySelector( '[data-acs-calc-more]' );
	var panelEl = root.querySelector( '[data-acs-calc-panel]' );
	var quoteEl = root.querySelector( '[data-acs-calc-quote]' );
	var monthlyEl = root.querySelector( '[data-acs-calc-monthly]' );
	var hourlyEl = root.querySelector( '[data-acs-calc-hourly]' );
	var compareEl = root.querySelector( '[data-acs-calc-compare]' );

	function el( tag, cls, text ) {
		var node = document.createElement( tag );
		if ( cls ) { node.className = cls; }
		if ( text !== undefined ) { node.textContent = text; }
		return node;
	}

	function renderRoles() {
		roleEl.innerHTML = '';
		var prompt = document.createElement( 'option' );
		prompt.value = '';
		prompt.textContent = 'Choose a role';
		roleEl.appendChild( prompt );
		ROLES.forEach( function ( role ) {
			var opt = document.createElement( 'option' );
			opt.value = role;
			opt.textContent = role;
			if ( state.role === role ) { opt.selected = true; }
			roleEl.appendChild( opt );
		} );
		roleEl.addEventListener( 'change', function () {
			state.role = roleEl.value || null;
			renderPanel();
		} );
	}

	function renderTeam() {
		teamEl.textContent = String( state.team );
		lessEl.disabled = state.team <= 1;
		moreEl.disabled = state.team >= TEAM_MAX;
	}

	function aud( n ) {
		return 'A$' + n.toLocaleString( 'en-AU' );
	}

	/** A cell is null, a number, or { min, max }. Scaled by team size. */
	function figureText( cell, team ) {
		if ( cell === null || cell === undefined ) { return null; }
		var lo = Math.max( PRICE_FLOOR, typeof cell === 'number' ? cell : cell.min ) * team;
		var hi = Math.max( PRICE_FLOOR, typeof cell === 'number' ? cell : cell.max ) * team;
		return lo === hi ? aud( lo ) : aud( lo ) + '\u2013' + aud( hi );
	}

	/** One stat slot. A slot shows a figure ONLY when the state allows it and
	 *  a figure exists for that slot; otherwise it names its state honestly.
	 *  Hourly and comparison slots pass null until their own sources land
	 *  (included hours; an approved Australian comparison). */
	function renderSlot( node, pendingText, figure, unit, hideWhenEmpty ) {
		var stat = node.closest ? node.closest( '.acs-calc__stat' ) : null;
		node.innerHTML = '';
		if ( PRICING_STATE === 'pending-approval' || figure === null || figure === undefined ) {
			// 2026-10-27: a slot with no source yet (hourly rate, local comparison)
			// is hidden on the public site rather than explaining itself. The
			// pending sentences were written for the review copy and read as
			// internal notes to a visitor. The lead slot always shows.
			if ( hideWhenEmpty && stat ) { stat.hidden = true; return; }
			if ( stat ) { stat.hidden = false; }
			node.appendChild( el( 'p', 'acs-calc__pending', pendingText ) );
			return;
		}
		if ( stat ) { stat.hidden = false; }
		node.appendChild( el( 'p', 'acs-calc__figure', figure ) );
		if ( unit ) { node.appendChild( el( 'p', 'acs-calc__unit', unit ) ); }
	}

	function renderPanel() {
		var chosen = !! state.role;
		var cell = chosen ? PRICING[ state.role ] : null;
		var monthly = figureText( cell, state.team );
		var unit = state.team === 1 ? 'per month' : 'per month for ' + state.team + ' team members';
		renderSlot( monthlyEl, chosen ? 'Pricing for this role is with the business for approval.' : 'Choose a role to see the estimate.', monthly, unit );
		renderSlot( hourlyEl, 'Follows the monthly figure once the included hours are confirmed.', null, undefined, true );
		renderSlot( compareEl, 'Awaiting an approved Australian comparison source.', null, undefined, true );

		panelEl.innerHTML = '';
		if ( PRICING_STATE === 'review-only' ) {
			panelEl.appendChild( el( 'p', 'acs-calc__review-note', 'Review copy. Junior, Intermediate and Senior are the bottom, midpoint and top of the range the business supplied on 3 September 2026. Not for publication.' ) );
		}
		var rows = el( 'div', 'acs-calc__summary' );
		[
			[ 'Role', state.role || 'Choose a role' ],
			[ 'Team size', String( state.team ) ]
		].forEach( function ( pair ) {
			var row = el( 'div', 'acs-spec__row' );
			row.appendChild( el( 'span', 'acs-spec__key', pair[ 0 ] ) );
			row.appendChild( el( 'span', 'acs-spec__value', pair[ 1 ] ) );
			rows.appendChild( row );
		} );
		panelEl.appendChild( rows );

		quoteEl.disabled = ! state.role;
	}

	lessEl.addEventListener( 'click', function () {
		if ( state.team > 1 ) { state.team--; renderTeam(); renderPanel(); }
	} );
	moreEl.addEventListener( 'click', function () {
		if ( state.team < TEAM_MAX ) { state.team++; renderTeam(); renderPanel(); }
	} );

	/**
	 * "Get a custom quote" carries the chosen role into the configurator
	 * below, so nothing is retyped. The configurator owns the enquiry
	 * contract (fields, consent); this only pre-fills and scrolls. Since
	 * 2026-11-05 no level is sent (there is none to send); the configurator
	 * ignores a missing seniority.
	 */
	quoteEl.addEventListener( 'click', function () {
		document.dispatchEvent( new CustomEvent( 'acs:byt-prefill', {
			detail: { role: state.role }
		} ) );
		var target = document.querySelector( '[data-acs-configurator]' );
		if ( target ) {
			target.scrollIntoView( { behavior: 'smooth', block: 'start' } );
		}
	} );

	renderRoles();
	renderTeam();
	renderPanel();
} )();
