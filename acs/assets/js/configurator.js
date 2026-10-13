/**
 * Build Your Team.
 *
 * The configurator replaced a cost calculator, because Dan ruled out published
 * pricing and a calculator that returns no number is a contact form. The point
 * is to move the conversation from price to scope: the buyer specifies what
 * they need and sees exactly that specification take shape.
 *
 * ⚠ THE SPECIFICATION PANEL IS THE WHOLE IDEA. Every answer writes a ruled line
 * into a document on screen. A visitor finishes holding a spec, not a progress
 * bar, and that is what makes this feel like configuring rather than filling in
 * a long form.
 *
 * ⚠ NO FIGURE APPEARS AT ANY STEP. Not a range, not a "from", not a saving.
 * First of the four site-wide bans and the reason this tool exists.
 *
 * ⚠ THIS MIRRORS automations/acs-lead-capture. That package owns the field
 * contract, the validation and the consent rule, and it has its own tests. The
 * two are kept honest by a drift guard in that package which reads THIS FILE
 * and fails when the steps or field ids disagree. Change one, change both.
 *
 * SUBMITS THROUGH assets/js/forms.js (2026-10-13), which defines the shared
 * sender, the endpoint and the thank-you and error wording. No sender or no
 * endpoint: the old placeholder "received" panel shows and nothing is sent.
 *
 * ⚠ THE INTAKE REFUSES THIS ONE TODAY, BY DESIGN. Consent is sent exactly as
 * shown, and the consent label below has no privacy link, so `policyUrl` is
 * `''` and the intake says no. Do not invent a URL to make it pass; the label
 * gets its link when the wording is approved (register row Legal 1.0).
 */
( function () {
	'use strict';

	var STEPS = [
		{
			id: 'role',
			title: 'Which role do you need?',
			help: '',
			fields: [ {
				id: 'role',
				label: 'Role',
				type: 'choice',
				required: true,
				options: [ 'Bookkeeper', 'Admin Assistant', 'Operations Assistant', 'Telesales', 'Accounting & Finance', 'Operations Manager', 'Social Media Manager', 'AI & Automation Specialist' ]
			} ]
		},
		{
			id: 'level',
			title: 'What level of experience?',
			help: 'Described by what the person owns rather than by price.',
			fields: [ {
				id: 'seniority',
				label: 'Level',
				type: 'choice',
				required: true,
				options: [ 'Junior', 'Intermediate', 'Senior', 'Not sure yet' ],
				notes: {
					'Junior': 'Executes defined tasks within an established process.',
					'Intermediate': 'Owns a workflow end to end. Handles exceptions without escalating them.',
					'Senior': 'Owns outcomes and may coordinate others.',
					'Not sure yet': 'We will recommend a level against what you describe.'
				}
			} ]
		},
		{
			id: 'shape',
			title: 'How would they work?',
			help: 'Full time is the standard engagement. Part time is available on selected roles, by discussion.',
			fields: [
				{ id: 'engagementType', label: 'Engagement', type: 'choice', required: true, options: [ 'Full time', 'Part time, by discussion', 'Not sure yet' ] },
				{ id: 'hoursTimezone', label: 'Hours and time zone', type: 'text', required: true, placeholder: 'e.g. 8am to 4pm AEST' }
			]
		},
		{
			id: 'systems',
			title: 'Which systems would they work in?',
			help: 'Optional, and worth the moment it takes. It is what shapes the shortlist.',
			fields: [ { id: 'keySystems', label: 'Systems', type: 'textarea', required: false, placeholder: 'e.g. Xero, ServiceM8, Outlook' } ]
		},
		{
			id: 'contact',
			title: 'Where should we send it?',
			help: 'Pricing is provided on application, based on the position and level required.',
			fields: [
				{ id: 'fullName', label: 'Your name', type: 'text', required: true },
				{ id: 'workEmail', label: 'Work email', type: 'email', required: true },
				{ id: 'businessName', label: 'Business name', type: 'text', required: true },
				{ id: 'budgetRange', label: 'Rough monthly budget', type: 'text', required: false, optionalNote: 'optional' }
			]
		}
	];

	var root = document.querySelector( '[data-acs-configurator]' );
	if ( ! root ) {
		return;
	}

	var answers = {};
	var index = 0;

	var stepEl = root.querySelector( '[data-acs-step]' );
	var specEl = root.querySelector( '[data-acs-spec]' );
	var progressEl = root.querySelector( '[data-acs-progress]' );
	var backEl = root.querySelector( '[data-acs-back]' );
	var nextEl = root.querySelector( '[data-acs-next]' );

	function el( tag, cls, text ) {
		var node = document.createElement( tag );
		if ( cls ) { node.className = cls; }
		if ( text !== undefined ) { node.textContent = text; }
		return node;
	}

	/** Only this step's own required answers. A configurator that refuses step
	 *  one because of an email three steps away is one nobody finishes. */
	function canAdvance() {
		return STEPS[ index ].fields.every( function ( f ) {
			return ! f.required || ( answers[ f.id ] || '' ).trim() !== '';
		} );
	}

	function renderSpec() {
		specEl.innerHTML = '';
		var any = false;

		STEPS.forEach( function ( step ) {
			step.fields.forEach( function ( f ) {
				var value = ( answers[ f.id ] || '' ).trim();
				if ( ! value ) { return; }
				any = true;
				var row = el( 'div', 'acs-spec__row' );
				row.appendChild( el( 'span', 'acs-spec__key', f.label ) );
				row.appendChild( el( 'span', 'acs-spec__value', value ) );
				specEl.appendChild( row );
			} );
		} );

		if ( ! any ) {
			specEl.appendChild( el( 'p', 'acs-spec__empty', 'Your specification appears here as you answer.' ) );
		}
	}

	function renderStep() {
		var step = STEPS[ index ];
		stepEl.innerHTML = '';

		stepEl.appendChild( el( 'h2', 'acs-step__title', step.title ) );
		if ( step.help ) {
			stepEl.appendChild( el( 'p', 'acs-step__help', step.help ) );
		}

		step.fields.forEach( function ( f ) {
			var wrap = el( 'div', 'acs-field' );
			// So refuse() can find the field that is missing an answer.
			wrap.setAttribute( 'data-acs-field', f.id );
			var id = 'acs-byt-' + f.id;

			if ( f.type === 'choice' ) {
				var legend = el( 'span', 'acs-field__label', f.label );
				wrap.appendChild( legend );
				var list = el( 'div', 'acs-choices' );
				f.options.forEach( function ( opt ) {
					var btn = el( 'button', 'acs-choice' );
					btn.type = 'button';
					btn.setAttribute( 'aria-pressed', answers[ f.id ] === opt ? 'true' : 'false' );
					if ( answers[ f.id ] === opt ) { btn.classList.add( 'is-chosen' ); }
					btn.appendChild( el( 'span', 'acs-choice__name', opt ) );
					if ( f.notes && f.notes[ opt ] ) {
						btn.appendChild( el( 'span', 'acs-choice__note', f.notes[ opt ] ) );
					}
					btn.addEventListener( 'click', function () {
						answers[ f.id ] = opt;
						clearRefusal();
						renderStep();
						renderSpec();
						updateControls();
					} );
					list.appendChild( btn );
				} );
				wrap.appendChild( list );
			} else {
				var label = el( 'label', 'acs-field__label', f.label + ( f.optionalNote ? ' ' : '' ) );
				if ( f.optionalNote ) {
					label.appendChild( el( 'span', 'acs-optional', f.optionalNote ) );
				}
				label.setAttribute( 'for', id );
				wrap.appendChild( label );

				var input = document.createElement( f.type === 'textarea' ? 'textarea' : 'input' );
				input.id = id;
				input.name = f.id;
				if ( f.type !== 'textarea' ) { input.type = f.type === 'email' ? 'email' : 'text'; }
				if ( f.placeholder ) { input.placeholder = f.placeholder; }
				input.value = answers[ f.id ] || '';
				input.addEventListener( 'input', function () {
					answers[ f.id ] = input.value;
					if ( input.value.trim() !== '' ) { clearRefusal(); }
					renderSpec();
					updateControls();
				} );
				wrap.appendChild( input );
			}

			stepEl.appendChild( wrap );
		} );

		if ( index === STEPS.length - 1 ) {
			var consent = el( 'div', 'acs-consent' );
			var box = document.createElement( 'input' );
			box.type = 'checkbox';
			box.id = 'acs-byt-consent';
			box.checked = answers.consent === 'yes';
			box.addEventListener( 'change', function () {
				answers.consent = box.checked ? 'yes' : '';
				if ( box.checked ) { clearRefusal(); }
				updateControls();
			} );
			var p = el( 'p' );
			// The site's standard consent line, as on the other 33 forms. Approved for
			// this form by Janet Biag, #team-powepuff 2026-10-13 09:46 PHT.
			var lab = el( 'label', null, 'I agree to the ACS ' );
			lab.setAttribute( 'for', 'acs-byt-consent' );
			var policy = el( 'a', null, 'Privacy Policy' );
			policy.setAttribute( 'href', '/privacy-policy/' );
			lab.appendChild( policy );
			var star = el( 'span', null, '*' );
			star.setAttribute( 'aria-hidden', 'true' );
			lab.appendChild( star );
			p.appendChild( lab );
			consent.appendChild( box );
			consent.appendChild( p );
			stepEl.appendChild( consent );
		}

		var first = stepEl.querySelector( 'button, input, textarea' );
		if ( first && index > 0 ) { first.focus(); }
	}

	/*
	 * ⚠ THE CONTINUE BUTTON IS NO LONGER DISABLED, 2026-08-20, and that is the
	 * accessibility fix rather than a relaxation.
	 *
	 * It used to be `nextEl.disabled = ! canAdvance() || ...`. A disabled button
	 * is removed from the tab order, so a visitor using a keyboard or a screen
	 * reader could not reach the one control that would have told them what was
	 * wrong — and it gave no reason to anybody else either. It simply sat there
	 * dead, most damagingly on the last step, where the thing standing in the
	 * way is a consent box the visitor has not noticed.
	 *
	 * ⚠ THE CONSENT WALL IS UNCHANGED. There is still no path to submit without
	 * it, matching the contract in acs-lead-capture. What changed is that the
	 * refusal now says so.
	 */
	function clearRefusal() {
		var marked = stepEl.querySelectorAll( '[aria-invalid="true"]' );
		Array.prototype.forEach.call( marked, function ( node ) {
			node.removeAttribute( 'aria-invalid' );
		} );
		var notes = stepEl.querySelectorAll( '.acs-field__error, .acs-consent__error' );
		Array.prototype.forEach.call( notes, function ( node ) {
			node.parentNode.removeChild( node );
		} );
		var flagged = stepEl.querySelectorAll( '.is-invalid' );
		Array.prototype.forEach.call( flagged, function ( node ) {
			node.classList.remove( 'is-invalid' );
		} );
	}

	/*
	 * ⚠ The classes below are the ones assets/js/forms.js also writes, and they
	 * are declared once in style.css under FORM ERROR STATES. Two scripts write
	 * them because this configurator is not a <form> and shares no submit event
	 * with one; the CSS is the shared contract, and changing a class name means
	 * changing it in three places.
	 */
	function refuse() {
		clearRefusal();

		var last = index === STEPS.length - 1;
		var firstBad = null;

		STEPS[ index ].fields.forEach( function ( f ) {
			if ( ! f.required || ( answers[ f.id ] || '' ).trim() !== '' ) {
				return;
			}
			var wrap = stepEl.querySelector( '[data-acs-field="' + f.id + '"]' );
			if ( ! wrap ) { return; }
			wrap.classList.add( 'is-invalid' );
			var control = wrap.querySelector( 'input, textarea' ) || wrap.querySelector( '.acs-choice' );
			if ( control ) {
				control.setAttribute( 'aria-invalid', 'true' );
				if ( ! firstBad ) { firstBad = control; }
			}
			var note = el( 'p', 'acs-field__error', f.type === 'choice' ? 'Choose one of these.' : 'This one is needed.' );
			wrap.appendChild( note );
		} );

		if ( last && answers.consent !== 'yes' ) {
			var consentWrap = stepEl.querySelector( '.acs-consent' );
			if ( consentWrap ) {
				consentWrap.classList.add( 'is-invalid' );
				var box = consentWrap.querySelector( 'input[type="checkbox"]' );
				if ( box ) {
					box.setAttribute( 'aria-invalid', 'true' );
					if ( ! firstBad ) { firstBad = box; }
				}
				consentWrap.appendChild(
					el( 'p', 'acs-consent__error', 'You need to agree to this before we can contact you.' )
				);
			}
		}

		if ( firstBad ) { firstBad.focus(); }
	}

	function updateControls() {
		var last = index === STEPS.length - 1;
		progressEl.textContent = 'Step ' + ( index + 1 ) + ' of ' + STEPS.length;
		backEl.disabled = index === 0;
		nextEl.textContent = last ? 'Send specification' : 'Continue';
	}

	backEl.addEventListener( 'click', function () {
		if ( index > 0 ) { index--; renderStep(); updateControls(); }
	} );

	nextEl.addEventListener( 'click', function () {
		var last = index === STEPS.length - 1;

		if ( ! canAdvance() || ( last && answers.consent !== 'yes' ) ) {
			refuse();
			return;
		}

		if ( ! last ) {
			index++;
			renderStep();
			updateControls();
			return;
		}
		submit();
	} );

	var sending = false;

	/** The answers the intake knows: every step's field, never the consent flag. */
	function answersToSend() {
		var out = {};
		STEPS.forEach( function ( step ) {
			step.fields.forEach( function ( f ) {
				var value = ( answers[ f.id ] || '' ).trim();
				if ( value ) { out[ f.id ] = value; }
			} );
		} );
		return out;
	}

	function showSent( message ) {
		var sent = root.querySelector( '[data-acs-sent]' );
		if ( message ) {
			sent.innerHTML = '';
			var thanks = el( 'p', 'acs-form__thanks', message );
			thanks.setAttribute( 'role', 'status' );
			thanks.setAttribute( 'tabindex', '-1' );
			sent.appendChild( thanks );
		}
		sent.hidden = false;
		root.querySelector( '[data-acs-live]' ).hidden = true;
		if ( message ) { sent.firstChild.focus(); }
	}

	function submit() {
		var shared = window.acsForms;
		if ( 'function' !== typeof window.acsSubmitEnquiry || ! shared || ! shared.canSend() ) {
			showSent( '' );
			return;
		}
		if ( sending ) { return; }
		sending = true;
		nextEl.disabled = true;
		var old = stepEl.querySelector( '.acs-form__send-error' );
		if ( old ) { old.parentNode.removeChild( old ); }

		var box = stepEl.querySelector( '#acs-byt-consent' );
		var label = stepEl.querySelector( 'label[for="acs-byt-consent"]' );

		window.acsSubmitEnquiry(
			'buildYourTeam',
			answersToSend(),
			shared.consentFrom( label, box ? box.checked : answers.consent === 'yes' )
		).then( function ( result ) {
			sending = false;
			nextEl.disabled = false;
			if ( result.ok ) {
				showSent( shared.THANKS_MESSAGE );
				return;
			}
			// Answers stay in `answers`; the visitor can press send again.
			var note = el( 'p', 'acs-form__send-error', shared.ERROR_MESSAGE );
			note.setAttribute( 'role', 'alert' );
			stepEl.appendChild( note );
		} );
	}

	/**
	 * ⚠ Pre-fill bridge from the cost calculator (assets/js/calculator.js),
	 * added 2026-08-27 with Chris's calculator amendment. "Get a custom
	 * quote" up the page carries the chosen role and level down into this
	 * configurator so the visitor never retypes them. Values are accepted
	 * only if they are real options — the calculator and this file declare
	 * the same lists, and the drift guard in acs-lead-capture keeps them
	 * agreeing. The consent wall and every validation rule are untouched:
	 * this writes answers, it never advances past a step.
	 */
	document.addEventListener( 'acs:byt-prefill', function ( event ) {
		var detail = ( event && event.detail ) || {};
		var roleField = STEPS[ 0 ].fields[ 0 ];
		var levelField = STEPS[ 1 ].fields[ 0 ];
		if ( roleField.options.indexOf( detail.role ) !== -1 ) {
			answers[ roleField.id ] = detail.role;
		}
		if ( levelField.options.indexOf( detail.seniority ) !== -1 ) {
			answers[ levelField.id ] = detail.seniority;
		}
		renderStep();
		renderSpec();
		updateControls();
	} );

	renderStep();
	renderSpec();
	updateControls();
} )();
