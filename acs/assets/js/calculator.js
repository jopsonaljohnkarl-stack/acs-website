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
 * ⚠ ROLES AND LEVELS ARE DECLARED TWICE — here and in configurator.js. The
 * drift guard (automations/acs-lead-capture/test/calculator-drift.test.ts)
 * reads BOTH shipped files and fails when they disagree. Change one, change
 * both.
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

	/** Scope descriptions, matching the configurator. Whether the calculator
	 *  shows these, year bands, or both is Chris's open design decision. */
	var LEVELS = [
		{ id: 'Junior', note: 'Executes defined tasks within an established process.' },
		{ id: 'Intermediate', note: 'Owns a workflow end to end. Handles exceptions without escalating them.' },
		{ id: 'Senior', note: 'Owns outcomes and may coordinate others.' }
	];

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
	var PRICING_STATE = 'review-only';

	/**
	 * Monthly client price per role per level, AUD. Source: Chris Banks's email
	 * of 2026-09-03 11:36 AEST ("ACS Website" thread) gave one range per role;
	 * his reply at 13:35 PHT the same day said to work off that range for
	 * Junior, Intermediate and Senior, and that every role has a minimum of
	 * A$2,600 regardless. So: Junior is the bottom of the range, Senior the
	 * top, Intermediate the midpoint rounded to the dollar (half up). The
	 * agent salaries in his first email are NOT here and never will be.
	 */
	var PRICE_FLOOR = 2600;

	var PRICING = {
		'Admin Assistant': { 'Junior': 2600, 'Intermediate': 2600, 'Senior': 2600 },
		'Telesales': { 'Junior': 2600, 'Intermediate': 2720, 'Senior': 2840 },
		'Bookkeeper': { 'Junior': 2600, 'Intermediate': 2600, 'Senior': 2600 },
		'Operations Assistant': { 'Junior': 2600, 'Intermediate': 2720, 'Senior': 2840 },
		'Social Media Manager': { 'Junior': 2600, 'Intermediate': 2619, 'Senior': 2637 },
		'Accounting & Finance': { 'Junior': 2600, 'Intermediate': 3734, 'Senior': 4868 },
		'Operations Manager': { 'Junior': 2637, 'Intermediate': 3347, 'Senior': 4057 },
		'AI & Automation Specialist': { 'Junior': 2600, 'Intermediate': 3329, 'Senior': 4057 }
	};

	var root = document.querySelector( '[data-acs-calculator]' );
	if ( ! root ) {
		return;
	}

	var state = { role: null, level: null, team: 1 };

	var roleEl = root.querySelector( '[data-acs-calc-roles]' );
	var levelEl = root.querySelector( '[data-acs-calc-levels]' );
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

	function renderLevels() {
		levelEl.innerHTML = '';
		LEVELS.forEach( function ( lvl ) {
			var btn = el( 'button', 'acs-choice' );
			btn.type = 'button';
			btn.setAttribute( 'aria-pressed', state.level === lvl.id ? 'true' : 'false' );
			if ( state.level === lvl.id ) { btn.classList.add( 'is-chosen' ); }
			btn.appendChild( el( 'span', 'acs-choice__name', lvl.id ) );
			btn.appendChild( el( 'span', 'acs-choice__note', lvl.note ) );
			btn.addEventListener( 'click', function () {
				state.level = lvl.id;
				renderLevels();
				renderPanel();
			} );
			levelEl.appendChild( btn );
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
	function renderSlot( node, pendingText, figure, unit ) {
		node.innerHTML = '';
		if ( PRICING_STATE === 'pending-approval' || figure === null || figure === undefined ) {
			node.appendChild( el( 'p', 'acs-calc__pending', pendingText ) );
			return;
		}
		node.appendChild( el( 'p', 'acs-calc__figure', figure ) );
		if ( unit ) { node.appendChild( el( 'p', 'acs-calc__unit', unit ) ); }
	}

	function renderPanel() {
		var chosen = state.role && state.level;
		var cell = chosen ? PRICING[ state.role ][ state.level ] : null;
		var monthly = figureText( cell, state.team );
		var unit = state.team === 1 ? 'per month' : 'per month for ' + state.team + ' team members';
		renderSlot( monthlyEl, chosen ? 'Pricing for this role is with the business for approval.' : 'Choose a role and a level to see the estimate.', monthly, unit );
		renderSlot( hourlyEl, 'Follows the monthly figure once the included hours are confirmed.', null );
		renderSlot( compareEl, 'Awaiting an approved Australian comparison source.', null );

		panelEl.innerHTML = '';
		if ( PRICING_STATE === 'review-only' ) {
			panelEl.appendChild( el( 'p', 'acs-calc__review-note', 'Review copy. Junior, Intermediate and Senior are the bottom, midpoint and top of the range the business supplied on 3 September 2026. Not for publication.' ) );
		}
		var rows = el( 'div', 'acs-calc__summary' );
		[
			[ 'Role', state.role || 'Choose a role' ],
			[ 'Level', state.level || 'Choose a level' ],
			[ 'Team size', String( state.team ) ]
		].forEach( function ( pair ) {
			var row = el( 'div', 'acs-spec__row' );
			row.appendChild( el( 'span', 'acs-spec__key', pair[ 0 ] ) );
			row.appendChild( el( 'span', 'acs-spec__value', pair[ 1 ] ) );
			rows.appendChild( row );
		} );
		panelEl.appendChild( rows );

		quoteEl.disabled = ! ( state.role && state.level );
	}

	lessEl.addEventListener( 'click', function () {
		if ( state.team > 1 ) { state.team--; renderTeam(); renderPanel(); }
	} );
	moreEl.addEventListener( 'click', function () {
		if ( state.team < TEAM_MAX ) { state.team++; renderTeam(); renderPanel(); }
	} );

	/**
	 * "Get a custom quote" carries the visitor's selections into the
	 * configurator below, so nothing is retyped. The configurator owns the
	 * enquiry contract (fields, consent); this only pre-fills and scrolls.
	 */
	quoteEl.addEventListener( 'click', function () {
		document.dispatchEvent( new CustomEvent( 'acs:byt-prefill', {
			detail: { role: state.role, seniority: state.level }
		} ) );
		var target = document.querySelector( '[data-acs-configurator]' );
		if ( target ) {
			target.scrollIntoView( { behavior: 'smooth', block: 'start' } );
		}
	} );

	renderRoles();
	renderLevels();
	renderTeam();
	renderPanel();
} )();
