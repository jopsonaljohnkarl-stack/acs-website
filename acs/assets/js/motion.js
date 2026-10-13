/**
 * The motion system.
 *
 * ⚠⚠ EVERYTHING HERE IS AN ENHANCEMENT AND NOTHING HERE IS LOAD-BEARING. The
 * stylesheet hides nothing until this script has added `js-motion` to <html>,
 * so a blocked, failed or errored script leaves a complete readable page. That
 * property is the reason the class is added FIRST, before anything is marked.
 * A scroll animation that can blank a page is worse than no scroll animation.
 *
 * ⚠ IT IS APPLIED BY ATTRIBUTE, NOT WIRED PER SECTION. Marketing writes 41
 * pages into the block editor over nine writing days; motion tied to specific
 * section structures would mean page 42 needs a developer. Everything below
 * keys off `data-acs-*` attributes or off classes the theme already emits, so
 * a new page gets the same motion by being built the same way.
 *
 * ⚠ NO LIBRARY. GSAP and Motion are both larger than this whole theme's CSS,
 * and every effect here is an IntersectionObserver plus a CSS transition. The
 * site carries a Core Web Vitals commitment.
 *
 * ⚠ REDUCED MOTION IS HANDLED IN CSS, NOT HERE. The observers still run and
 * still add `is-revealed`; the stylesheet decides that the revealed state
 * arrives as a plain fade with no travel and no stagger. A visitor who asked
 * for less movement gets the same page, not a different one.
 */
( function () {
	'use strict';

	if ( ! ( 'IntersectionObserver' in window ) ) {
		return;
	}

	var root = document.documentElement;
	var main = document.querySelector( 'main' );

	root.classList.add( 'js-motion' );

	/**
	 * Take the transition off once it has played.
	 *
	 * ⚠ A reveal that can play twice will play at the wrong moment. The first
	 * version left the transition attached forever, so a repaint over the
	 * element - a cursor arriving was enough - could restart it. `is-settled`
	 * removes the transition, and the hidden state is already written as
	 * `:not(.is-revealed)`, so after this nothing matches the element at all.
	 */
	function settle( el ) {
		window.setTimeout( function () {
			el.classList.add( 'is-settled' );
			/*
			 * ⚠ THE CHILDREN SETTLE WITH THEIR SECTION (2026-08-31). Staggered
			 * children kept their entrance transition attached forever, which
			 * overrode any component transition on the same element (the
			 * five-step cards' hover reveal never animated because of it).
			 * 1400ms covers the longest child delay plus its duration, so by
			 * now every child has finished arriving.
			 */
			var kids = el.querySelectorAll( '[data-acs-stagger]' );
			for ( var k = 0; k < kids.length; k++ ) {
				kids[ k ].classList.add( 'is-settled' );
			}
		}, 1400 );
	}

	/* ---------------------------------------------------------------------
	 * 1. SECTION REVEAL, and the stagger inside it.
	 *
	 * The section fades and rises. Its children then arrive in sequence,
	 * because the order of a set of cards or steps IS information and showing
	 * them in order is the one thing a stagger is actually for.
	 * ------------------------------------------------------------------- */

	// What counts as a staggering group inside a revealed section.
	/*
	 * ⚠⚠ EVERY COMPONENT BUILT ON 2026-08-21 WAS MISSING FROM THIS LIST and so
	 * had no scroll reveal at all - the role cards, the split columns and the
	 * eight inclusions all simply appeared. Nothing failed and nothing logged;
	 * a stagger that was never asked for looks exactly like a stagger that is
	 * switched off. **A new grid does not get the site's motion by existing; it
	 * gets it by being named here.**
	 *
	 * ⚠ `.acs-stack` is deliberately NOT in this list. Its items are
	 * `position: sticky`, and a stagger that hands them a `translateY` is
	 * fighting the property that does the work. The stack has its own motion.
	 */
	var GROUPS = '.acs-index, .acs-points, .acs-steps, .acs-qa, .acs-levels, ' +
		'.acs-roles, .acs-split, .acs-included__grid, .wp-block-columns';

	function markChildren( section ) {
		var groups = section.querySelectorAll( GROUPS );
		for ( var g = 0; g < groups.length; g++ ) {
			var kids = groups[ g ].children;
			for ( var k = 0; k < kids.length; k++ ) {
				kids[ k ].setAttribute( 'data-acs-stagger', '' );
				/*
				 * ⚠ Capped at 7. An index of eight role cards with a linear
				 * delay would make the last one arrive most of a second after
				 * the first, and a visitor who has already started reading it
				 * watches it fade in underneath them.
				 */
				kids[ k ].style.setProperty( '--acs-i', Math.min( k, 7 ) );
			}
		}
	}

	if ( main ) {
		var host = main.querySelector( ':scope > .wp-block-post-content' ) || main;
		var sections = host.querySelectorAll( ':scope > .wp-block-group' );

		for ( var i = 0; i < sections.length; i++ ) {
			sections[ i ].setAttribute( 'data-acs-reveal', '' );
			markChildren( sections[ i ] );
		}

		if ( sections.length ) {
			/*
			 * Above the fold, so it is shown immediately: a visitor must never
			 * land on a blank first screen while a fade catches up.
			 *
			 * ⚠ AND IT MUST SETTLE TOO. The first version only settled the
			 * elements the observer handled, which left the transition attached
			 * to exactly the ones a cursor reaches first - the hero section and
			 * the hero image. That is the half of the bug that survived the
			 * first fix.
			 */
			sections[ 0 ].classList.add( 'is-revealed' );
			settle( sections[ 0 ] );

			var sectionObserver = new IntersectionObserver(
				function ( entries ) {
					entries.forEach( function ( entry ) {
						if ( ! entry.isIntersecting ) {
							return;
						}
						/*
						 * ⚠ EVERYTHING ABOVE IT REVEALS TOO. An
						 * IntersectionObserver only fires for elements that
						 * actually intersect, so a jump - an in-page anchor, a
						 * restored scroll position, End on the keyboard -
						 * leaves every section it skipped invisible for the
						 * rest of the visit. The reader scrolls back up into
						 * blank space.
						 *
						 * Anything above the one being revealed has been passed
						 * already, so it is shown without ceremony.
						 */
						var idx = Array.prototype.indexOf.call( sections, entry.target );
						for ( var b = 0; b <= idx; b++ ) {
							if ( ! sections[ b ].classList.contains( 'is-revealed' ) ) {
								sections[ b ].classList.add( 'is-revealed' );
								sectionObserver.unobserve( sections[ b ] );
								settle( sections[ b ] );
							}
						}
						entry.target.classList.add( 'is-revealed' );
						sectionObserver.unobserve( entry.target );
						settle( entry.target );
					} );
				},
				/*
				 * A POSITIVE bottom margin, so a section starts revealing
				 * before it enters view. The first attempt used -12%, which
				 * meant a fast scroll could land on a section still at zero
				 * opacity: the reader arrives before the fade does.
				 */
				{ rootMargin: '0px 0px 18% 0px', threshold: 0 }
			);

			for ( var j = 1; j < sections.length; j++ ) {
				sectionObserver.observe( sections[ j ] );
			}
		}
	}

	/* ---------------------------------------------------------------------
	 * 2. THE MASTHEAD COMPACTS ONCE THE PAGE HAS MOVED.
	 *
	 * A sentinel at the very top of the document, rather than a scroll
	 * listener. `window.addEventListener('scroll')` runs on every frame, is
	 * not batched, and is the single most common cause of a janky page.
	 * ------------------------------------------------------------------- */

	var header = document.querySelector( 'header.wp-block-group' );
	if ( header ) {
		var sentinel = document.createElement( 'div' );
		sentinel.setAttribute( 'data-acs-sentinel', '' );
		sentinel.setAttribute( 'aria-hidden', 'true' );
		/*
		 * ⚠ Zero height AND zero margin. Once the sentinel moved out to
		 * `.wp-site-blocks` it became that container's first child, which
		 * handed the header `margin-block-start: 24px` from core's
		 * `:where(.wp-site-blocks) > *` rule - the header had been the
		 * first child and exempt. The bar sat 24px down the page with a
		 * strip of ground above it.
		 */
		sentinel.style.cssText = 'height:0;margin:0;padding:0;border:0';
		/*
		 * ⚠⚠ THE SENTINEL MUST SIT OUTSIDE WHATEVER IS STICKY. Corrected
		 * 2026-08-21, the same hour the sticky moved.
		 *
		 * It used to be inserted before `header.wp-block-group`, which was
		 * correct while that element was the sticky one. The sticky moved up
		 * to the template-part wrapper - because a sticky element can only
		 * stick inside its parent's box - and the sentinel went sticky with
		 * it. Pinned at `top: 0`, it never stops intersecting, so
		 * `is-scrolled` never fires: the bar stayed full height and the
		 * tagline never hid.
		 *
		 * ⚠ The bar was visibly persistent at that point, which is exactly
		 * what made this easy to miss. **Fixing where an element sticks moves
		 * everything measured against it.**
		 */
		var stickyAnchor =
			header.closest( 'header.wp-block-template-part' ) || header;
		stickyAnchor.parentNode.insertBefore( sentinel, stickyAnchor );

		new IntersectionObserver(
			function ( entries ) {
				root.classList.toggle( 'is-scrolled', ! entries[ 0 ].isIntersecting );
			},
			{ threshold: 0 }
		).observe( sentinel );
	}

	/* ---------------------------------------------------------------------
	 * 3. THE TREATED PHOTOGRAPHS UNCOVER.
	 *
	 * ⚠ The image is not faded, it is UNCOVERED - a wipe from the bottom edge.
	 * A fade on a duotoned placeholder reads as a loading state, which is the
	 * one thing these must not look like while a real shoot is unarranged.
	 * ------------------------------------------------------------------- */

	var frames = document.querySelectorAll( '.acs-shot__frame' );
	if ( frames.length ) {
		var frameObserver = new IntersectionObserver(
			function ( entries ) {
				entries.forEach( function ( entry ) {
					if ( ! entry.isIntersecting ) {
						return;
					}
					entry.target.classList.add( 'is-uncovered' );
					frameObserver.unobserve( entry.target );
					settle( entry.target );
					// Same jump hazard as the sections above.
					for ( var q = 0; q < frames.length; q++ ) {
						if ( frames[ q ] === entry.target ) { break; }
						if ( ! frames[ q ].classList.contains( 'is-uncovered' ) ) {
							frames[ q ].classList.add( 'is-uncovered' );
							frameObserver.unobserve( frames[ q ] );
							settle( frames[ q ] );
						}
					}
				} );
			},
			{ rootMargin: '0px 0px 12% 0px', threshold: 0 }
		);
		for ( var f = 0; f < frames.length; f++ ) {
			frames[ f ].setAttribute( 'data-acs-uncover', '' );
			// Above the fold uncovers immediately, same reasoning as section 1.
			if ( frames[ f ].getBoundingClientRect().top < window.innerHeight * 0.9 ) {
				frames[ f ].classList.add( 'is-uncovered' );
				settle( frames[ f ] );
			} else {
				frameObserver.observe( frames[ f ] );
			}
		}
	}

	/* ---------------------------------------------------------------------
	 * 3b. FAQ ANSWERS ARRIVE A WORD AT A TIME.
	 *
	 * ⚠ The spans are created here and nowhere else. The stylesheet gives them
	 * no hidden state of their own, so if this never runs the answers are just
	 * text - which is what they are in the markup.
	 *
	 * ⚠ Words, not letters: ten answers at this length is ~300 spans instead of
	 * ~1,800, and at reading distance they look the same.
	 * ------------------------------------------------------------------- */

	var answers = document.querySelectorAll( '.acs-faq__answer' );
	for ( var a = 0; a < answers.length; a++ ) {
		var words = answers[ a ].textContent.split( /(\s+)/ );
		var frag = document.createDocumentFragment();
		var n = 0;
		for ( var w = 0; w < words.length; w++ ) {
			if ( words[ w ] === '' ) { continue; }
			var span = document.createElement( 'span' );
			span.className = 'acs-faq__w';
			span.textContent = words[ w ];
			// ⚠ Capped, for the same reason the card stagger is: a long answer
			// would otherwise still be arriving after the reader finished it.
			span.style.setProperty( '--acs-w', Math.min( n, 34 ) );
			if ( /\S/.test( words[ w ] ) ) { n++; }
			frag.appendChild( span );
		}
		answers[ a ].textContent = '';
		answers[ a ].appendChild( frag );
	}

	/* ---------------------------------------------------------------------
	 * 4. THE BACKSTOP.
	 *
	 * ⚠ AN IMAGE THAT NEVER ARRIVES IS WORSE THAN ONE THAT ARRIVES LATE. The
	 * jump handling above covers everything a reader scrolls past, but an
	 * observer that never fires for any reason at all - a browser quirk, a
	 * layout that puts an element permanently outside the root - would leave
	 * something clipped for the whole visit. After four seconds, anything
	 * still hidden is simply shown.
	 *
	 * It costs one timeout and it makes "the content is always visible" true
	 * rather than nearly true.
	 * ------------------------------------------------------------------- */
	window.setTimeout( function () {
		var stuck = document.querySelectorAll(
			'[data-acs-reveal]:not(.is-revealed), [data-acs-uncover]:not(.is-uncovered)'
		);
		for ( var s = 0; s < stuck.length; s++ ) {
			stuck[ s ].classList.add(
				stuck[ s ].hasAttribute( 'data-acs-reveal' ) ? 'is-revealed' : 'is-uncovered'
			);
			settle( stuck[ s ] );
		}
	}, 4000 );
} )();
