/**
 * HTTP Basic Auth in front of the whole ACS review snapshot.
 *
 * This is an internal review copy of an unreleased site: every word is
 * unapproved placeholder copy and every photograph is a stand-in. A Pages
 * preview URL is unlisted but publicly reachable, so it gets a password.
 *
 * Fails CLOSED — if REVIEW_PASSWORD is not configured, nothing is served.
 */
const REALM = 'ACS internal review';

function unauthorized(message) {
  return new Response(message, {
    status: 401,
    headers: {
      'WWW-Authenticate': `Basic realm="${REALM}", charset="UTF-8"`,
      'Content-Type': 'text/plain; charset=utf-8',
      'Cache-Control': 'no-store',
    },
  });
}

/** Length-independent compare, so the response time leaks nothing useful. */
function safeEqual(a, b) {
  const enc = new TextEncoder();
  const x = enc.encode(a);
  const y = enc.encode(b);
  let diff = x.length ^ y.length;
  for (let i = 0; i < Math.max(x.length, y.length); i++) {
    diff |= (x[i] ?? 0) ^ (y[i] ?? 0);
  }
  return diff === 0;
}

export async function onRequest(context) {
  const { request, env, next } = context;
  const expected = env.REVIEW_PASSWORD;

  if (!expected) {
    return new Response('Review access is not configured.', {
      status: 503,
      headers: { 'Cache-Control': 'no-store' },
    });
  }

  const header = request.headers.get('Authorization') || '';
  if (!header.startsWith('Basic ')) return unauthorized('Authentication required.');

  let decoded;
  try {
    decoded = atob(header.slice(6));
  } catch {
    return unauthorized('Malformed credentials.');
  }

  // Only the password is checked; any username is accepted so reviewers do not
  // have to be told two things.
  const password = decoded.slice(decoded.indexOf(':') + 1);
  if (!safeEqual(password, expected)) return unauthorized('Not authorised.');

  const response = await next();
  const out = new Response(response.body, response);
  out.headers.set('X-Robots-Tag', 'noindex, nofollow, noarchive, nosnippet');
  // Never let an edge cache hold a copy that outlives the password check.
  out.headers.set('Cache-Control', 'no-store, private');
  return out;
}
