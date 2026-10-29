/**
 * Form validation, as a progressive enhancement.
 *
 * ⚠ `novalidate` IS SET FROM HERE, NEVER IN THE MARKUP. That is the whole
 * safety property of this file. If the script fails to load, is blocked, or
 * throws, the form keeps the browser's own `required` handling and still cannot
 * be submitted empty. A `novalidate` attribute written into the template would
 * turn a broken script into a form with no validation at all.
 *
 * ⚠ THIS IS NOT THE CONTRACT. The field list, which fields are required, which
 * surface they belong to and the consent rule all live in
 * `automations/acs-lead-capture`, with tests. What is here is presentation: it
 * reads the constraints already on the elements and shows them. It does not
 * decide them, and it must never grow a field list of its own.
 *
 * SENDING (2026-10-13, automations/acs-lead-capture/DESIGN-DELTA-2026-10-13-wire-forms.md).
 * Once the browser checks pass, the form posts JSON to the intake named in
 * `window.acsIntake.url` (set in functions.php). No URL, no send: the form keeps
 * its old behaviour. The thank-you shows ONLY on `{ ok: true }`, which the intake
 * returns only after the store write.
 *
 * ⚠ CONSENT IS SENT EXACTLY AS SHOWN. The statement is the label's text and the
 * policy URL is the label's own link. A label with no link sends `''` and the
 * intake refuses it. That is deliberate: never invent a URL the visitor did not see.
 */
( function () {
	'use strict';

	/*
	 * --- First-touch attribution. A port of attributionFrom and
	 * parseAttribution in automations/acs-lead-capture/src/attribution.ts; read
	 * that file for why each rule exists. A parity test there runs both on the
	 * same cases, so change one, change both.
	 *
	 * It runs BEFORE the no-forms return below, on every page: the visitor may
	 * land with campaign tags on one page and submit on another.
	 */
	var ATTRIBUTION_QUERY_KEYS = [
		[ 'utm_source', 'utmSource' ],
		[ 'utm_medium', 'utmMedium' ],
		[ 'utm_campaign', 'utmCampaign' ],
		[ 'utm_term', 'utmTerm' ],
		[ 'utm_content', 'utmContent' ],
		[ 'gclid', 'gclid' ],
		[ 'fbclid', 'fbclid' ]
	];
	var ATTRIBUTION_FIELDS = ATTRIBUTION_QUERY_KEYS.map( function ( pair ) { return pair[ 1 ]; } )
		.concat( [ 'landingHost', 'landingPath', 'referrerOrigin' ] );
	// Over-long is DROPPED, not truncated. A cut value reads as data and matches nothing.
	var MAX_ATTRIBUTION_LENGTH = 256;
	var FIRST_TOUCH_KEY = 'acs-first-touch';

	function clean( value ) {
		if ( 'string' !== typeof value ) {
			return undefined;
		}
		var trimmed = value.trim();
		if ( '' === trimmed || trimmed.length > MAX_ATTRIBUTION_LENGTH ) {
			return undefined;
		}
		return trimmed;
	}

	function originOf( referrer ) {
		if ( null === referrer || 'string' !== typeof referrer || '' === referrer.trim() ) {
			return undefined;
		}
		try {
			var origin = new URL( referrer ).origin;
			return 'null' === origin ? undefined : clean( origin );
		} catch ( e ) {
			return undefined;
		}
	}

	/** Named keys only; the rest of the URL is parsed and discarded. Never throws. */
	function attributionFrom( input ) {
		var out = {};
		var landing = null;
		if ( input && null !== input.href && undefined !== input.href ) {
			try {
				landing = new URL( input.href );
			} catch ( e ) {
				landing = null;
			}
		}
		if ( landing ) {
			ATTRIBUTION_QUERY_KEYS.forEach( function ( pair ) {
				var value = clean( landing.searchParams.get( pair[ 0 ] ) );
				if ( undefined !== value ) {
					out[ pair[ 1 ] ] = value;
				}
			} );
			var host = clean( landing.hostname );
			if ( undefined !== host ) {
				out.landingHost = host;
			}
			var path = clean( landing.pathname );
			if ( undefined !== path ) {
				out.landingPath = path;
			}
		}
		var referrerOrigin = originOf( input ? input.referrer : null );
		if ( undefined !== referrerOrigin && ( ! landing || referrerOrigin !== landing.origin ) ) {
			out.referrerOrigin = referrerOrigin;
		}
		return out;
	}

	/** Storage is writable by anything on the page: known keys, strings, same cap. */
	function parseAttribution( value ) {
		if ( 'object' !== typeof value || null === value || Array.isArray( value ) ) {
			return undefined;
		}
		var out = {};
		ATTRIBUTION_FIELDS.forEach( function ( field ) {
			var cleaned = clean( value[ field ] );
			if ( undefined !== cleaned ) {
				out[ field ] = cleaned;
			}
		} );
		return out;
	}

	function readAttribution() {
		var href = null;
		var referrer = null;
		try { href = window.location.href; } catch ( e ) { href = null; }
		try { referrer = document.referrer; } catch ( e ) { referrer = null; }
		return attributionFrom( { href: href, referrer: referrer } );
	}

	/** First touch wins: written once per visit, never overwritten. */
	function rememberFirstTouch() {
		try {
			var storage = window.sessionStorage;
			if ( null === storage.getItem( FIRST_TOUCH_KEY ) ) {
				storage.setItem( FIRST_TOUCH_KEY, JSON.stringify( readAttribution() ) );
			}
		} catch ( e ) {
			// Private window, blocked storage: the submit falls back to this page.
		}
	}

	function firstTouch() {
		try {
			var raw = window.sessionStorage.getItem( FIRST_TOUCH_KEY );
			if ( null !== raw ) {
				var parsed = parseAttribution( JSON.parse( raw ) );
				if ( parsed ) {
					return parsed;
				}
			}
		} catch ( e ) {
			// Fall through to the current page.
		}
		return readAttribution();
	}

	rememberFirstTouch();

	/*
	 * --- The sender, shared with assets/js/configurator.js, which is not a
	 * <form>. Defined before the no-forms return so the Build Your Team page,
	 * which has only the configurator, still gets it.
	 */

	// APPROVED: Janet Biag, #team-powepuff 2026-10-13 09:46 PHT ("sige keri lang").
	var THANKS_MESSAGE = 'Thanks, we have your enquiry. Someone from All Commercial Services will be in touch.';
	// APPROVED: Janet Biag, #team-powepuff 2026-10-13 09:46 PHT ("sige keri lang").
	var ERROR_MESSAGE = 'Sorry, that did not go through. Please check your connection and try again.';
	// A hung request must not leave the submit button disabled for good.
	var SEND_TIMEOUT_MS = 20000;

	function intakeUrl() {
		var config = window.acsIntake;
		return config && 'string' === typeof config.url && '' !== config.url ? config.url : '';
	}

	/**
	 * The consent record, read off the label the visitor actually saw. Text
	 * marked aria-hidden (the required asterisk) is decoration, not wording.
	 */
	function consentFrom( label, granted ) {
		if ( ! label ) {
			return { granted: !! granted, statement: '', policyUrl: '' };
		}
		var copy = label.cloneNode( true );
		Array.prototype.forEach.call( copy.querySelectorAll( '[aria-hidden="true"]' ), function ( node ) {
			node.parentNode.removeChild( node );
		} );
		var link = label.querySelector( 'a[href]' );
		return {
			granted: !! granted,
			statement: copy.textContent.replace( /\s+/g, ' ' ).trim(),
			// `.href` on an anchor is already absolute.
			policyUrl: link ? link.href : ''
		};
	}

	/** Resolves { ok, issues }. Never rejects: every failure is { ok: false }. */
	function submitEnquiry( surface, answers, consent ) {
		var url = intakeUrl();
		if ( ! url || 'function' !== typeof window.fetch ) {
			return Promise.resolve( { ok: false, issues: [ 'not-configured' ] } );
		}
		var request = window.fetch( url, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify( {
				surface: surface,
				answers: answers,
				consent: consent,
				attribution: firstTouch()
			} )
		} ).then( function ( response ) {
			return response.json();
		} ).then( function ( body ) {
			return body && true === body.ok
				? { ok: true, issues: [] }
				: { ok: false, issues: ( body && body.issues ) || [] };
		} );
		var timeout = new Promise( function ( resolve ) {
			setTimeout( function () { resolve( { ok: false, issues: [ 'timeout' ] } ); }, SEND_TIMEOUT_MS );
		} );
		return Promise.race( [ request, timeout ] ).catch( function () {
			return { ok: false, issues: [ 'network' ] };
		} );
	}

	window.acsSubmitEnquiry = submitEnquiry;
	window.acsForms = {
		attributionFrom: attributionFrom,
		consentFrom: consentFrom,
		canSend: function () { return '' !== intakeUrl(); },
		THANKS_MESSAGE: THANKS_MESSAGE,
		ERROR_MESSAGE: ERROR_MESSAGE
	};

	var forms = document.querySelectorAll( '.acs-form' );
	if ( ! forms.length ) {
		return;
	}

	/**
	 * The message a control gets when it fails.
	 *
	 * ⚠ Deliberately not the browser's `validationMessage`. That string is set
	 * by the browser vendor, changes with locale in ways nobody here controls,
	 * and on a <select> in some browsers reads "Please select an item in the
	 * list" for a control this design calls a schedule row.
	 *
	 * ⚠ Every string below is an UNAPPROVED VISIBLE STRING, same as every other
	 * string in this theme. Australian English.
	 */
	function messageFor( control ) {
		if ( control.validity.valueMissing ) {
			if ( 'checkbox' === control.type ) {
				return 'You need to agree to this before we can contact you.';
			}
			if ( 'SELECT' === control.tagName ) {
				return 'Choose one of these.';
			}
			return 'This one is needed.';
		}
		if ( control.validity.typeMismatch && 'email' === control.type ) {
			return 'That does not look like an email address we could reply to.';
		}
		if ( control.validity.typeMismatch && 'tel' === control.type ) {
			return 'That does not look like a phone number.';
		}
		if ( control.validity.tooLong ) {
			return 'That is longer than this field accepts.';
		}
		return 'Check this one.';
	}

	/*
	 * ⚠ TRUNCATED, because the consent label is a sentence. The summary listed
	 * it in full on the first run and the link ran to three lines of legal
	 * wording where every other link was two words. Cutting at a word boundary
	 * keeps the list scannable, which is the only thing the list is for.
	 */
	function labelFor( control ) {
		var label = control.id ? document.querySelector( 'label[for="' + control.id + '"]' ) : null;
		if ( ! label ) {
			return 'This field';
		}
		var text = label.textContent.trim().replace( /\s+/g, ' ' );
		if ( text.length <= 44 ) {
			return text;
		}
		var cut = text.slice( 0, 44 );
		var space = cut.lastIndexOf( ' ' );
		return ( space > 20 ? cut.slice( 0, space ) : cut ) + '…';
	}

	function clearField( control ) {
		control.removeAttribute( 'aria-invalid' );
		var field = control.closest( '.acs-field, .acs-consent' );
		if ( ! field ) {
			return;
		}
		field.classList.remove( 'is-invalid' );
		var existing = field.querySelector( '.acs-field__error, .acs-consent__error' );
		if ( existing ) {
			// The control may point at a description it no longer has.
			var described = ( control.getAttribute( 'aria-describedby' ) || '' )
				.split( ' ' )
				.filter( function ( id ) { return id && id !== existing.id; } )
				.join( ' ' );
			if ( described ) {
				control.setAttribute( 'aria-describedby', described );
			} else {
				control.removeAttribute( 'aria-describedby' );
			}
			existing.parentNode.removeChild( existing );
		}
	}

	function markField( control, message ) {
		var field = control.closest( '.acs-field, .acs-consent' );
		if ( ! field ) {
			return;
		}
		clearField( control );

		var isConsent = field.classList.contains( 'acs-consent' );
		var note = document.createElement( 'p' );
		note.className = isConsent ? 'acs-consent__error' : 'acs-field__error';
		note.id = ( control.id || 'acs-field' ) + '-error';
		note.textContent = message;

		field.appendChild( note );
		field.classList.add( 'is-invalid' );
		control.setAttribute( 'aria-invalid', 'true' );

		var described = ( control.getAttribute( 'aria-describedby' ) || '' ).split( ' ' ).filter( Boolean );
		described.push( note.id );
		control.setAttribute( 'aria-describedby', described.join( ' ' ) );
	}

	function summarise( form, failures ) {
		var existing = form.querySelector( '.acs-form__summary' );
		if ( existing ) {
			existing.parentNode.removeChild( existing );
		}
		if ( ! failures.length ) {
			return;
		}

		var summary = document.createElement( 'div' );
		summary.className = 'acs-form__summary';
		/*
		 * role="alert" rather than a heading a visitor has to find. A person
		 * using a screen reader has just pressed submit and heard nothing;
		 * this is the only thing that tells them why.
		 */
		summary.setAttribute( 'role', 'alert' );

		var intro = document.createElement( 'p' );
		intro.textContent = 1 === failures.length
			? 'One thing needs fixing before this can be sent.'
			: failures.length + ' things need fixing before this can be sent.';
		summary.appendChild( intro );

		var list = document.createElement( 'ul' );
		failures.forEach( function ( control ) {
			var item = document.createElement( 'li' );
			var link = document.createElement( 'a' );
			link.href = '#' + control.id;
			link.textContent = labelFor( control );
			link.addEventListener( 'click', function ( event ) {
				event.preventDefault();
				control.focus();
			} );
			item.appendChild( link );
			list.appendChild( item );
		} );
		summary.appendChild( list );

		var submit = form.querySelector( '[type="submit"]' );
		var anchor = submit ? submit.closest( 'div' ) : null;
		if ( anchor && anchor.parentNode === form ) {
			form.insertBefore( summary, anchor );
		} else {
			form.appendChild( summary );
		}
	}

	Array.prototype.forEach.call( forms, function ( form ) {
		form.setAttribute( 'novalidate', 'novalidate' );

		var controls = form.querySelectorAll( 'input, select, textarea' );

		Array.prototype.forEach.call( controls, function ( control ) {
			/*
			 * Clear on the next interaction, not on every keystroke while the
			 * field is still empty. Re-running validity on `input` would make
			 * a message flicker away on the first character and back on the
			 * last deletion, which reads as the form arguing with the visitor.
			 */
			var clearOn = ( 'checkbox' === control.type || 'SELECT' === control.tagName ) ? 'change' : 'input';
			control.addEventListener( clearOn, function () {
				if ( control.checkValidity() ) {
					clearField( control );
				}
			} );
		} );

		form.addEventListener( 'submit', function ( event ) {
			var failures = [];

			Array.prototype.forEach.call( controls, function ( control ) {
				if ( control.disabled || 'hidden' === control.type ) {
					return;
				}
				if ( control.checkValidity() ) {
					clearField( control );
					return;
				}
				markField( control, messageFor( control ) );
				failures.push( control );
			} );

			summarise( form, failures );

			if ( failures.length ) {
				event.preventDefault();
				/*
				 * Focus the first failure rather than the summary. The summary
				 * announces itself through role="alert"; moving focus into the
				 * field is what lets the visitor start typing immediately.
				 */
				failures[ 0 ].focus();
				return;
			}

			// No endpoint configured: leave the form to behave as it always has.
			if ( ! intakeUrl() || ! form.getAttribute( 'data-acs-surface' ) ) {
				return;
			}
			event.preventDefault();
			send( form, controls );
		} );
	} );

	/** Named controls except consent; empty values and unticked boxes skipped. */
	function answersFrom( controls ) {
		var answers = {};
		Array.prototype.forEach.call( controls, function ( control ) {
			if ( ! control.name || 'consent' === control.name || control.disabled ) {
				return;
			}
			if ( ( 'radio' === control.type || 'checkbox' === control.type ) && ! control.checked ) {
				return;
			}
			if ( 'submit' === control.type || 'button' === control.type ) {
				return;
			}
			var value = ( control.value || '' ).trim();
			if ( '' !== value ) {
				answers[ control.name ] = value;
			}
		} );
		return answers;
	}

	function clearSendError( form ) {
		var existing = form.querySelector( '.acs-form__send-error' );
		if ( existing ) {
			existing.parentNode.removeChild( existing );
		}
	}

	function send( form, controls ) {
		if ( form.getAttribute( 'data-acs-sending' ) ) {
			return;
		}
		clearSendError( form );

		var box = form.querySelector( 'input[name="consent"]' );
		var label = box && box.id ? form.querySelector( 'label[for="' + box.id + '"]' ) : null;
		var submit = form.querySelector( '[type="submit"]' );

		form.setAttribute( 'data-acs-sending', 'true' );
		if ( submit ) {
			submit.disabled = true;
		}

		submitEnquiry(
			form.getAttribute( 'data-acs-surface' ),
			answersFrom( controls ),
			consentFrom( label, box ? box.checked : false )
		).then( function ( result ) {
			form.removeAttribute( 'data-acs-sending' );

			if ( result.ok ) {
				while ( form.firstChild ) {
					form.removeChild( form.firstChild );
				}
				var thanks = document.createElement( 'p' );
				thanks.className = 'acs-form__thanks';
				thanks.setAttribute( 'role', 'status' );
				thanks.setAttribute( 'tabindex', '-1' );
				thanks.textContent = THANKS_MESSAGE;
				form.appendChild( thanks );
				thanks.focus();
				return;
			}

			// Keep the form and everything the visitor typed; say so, let them retry.
			if ( submit ) {
				submit.disabled = false;
			}
			var note = document.createElement( 'p' );
			note.className = 'acs-form__send-error';
			note.setAttribute( 'role', 'alert' );
			note.textContent = ERROR_MESSAGE;
			var anchor = submit ? submit.closest( 'div, p' ) : null;
			if ( anchor && anchor.parentNode === form ) {
				form.insertBefore( note, anchor );
			} else {
				form.appendChild( note );
			}
		} );
	}
} )();
