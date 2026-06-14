# Auth tokens & CSRF

The expensive bugs here come from a false trade-off — *'localStorage risks XSS,
cookies risk CSRF, pick your poison'* — and from defenses that look complete but
leave one gap open. The asymmetry the framing hides: a single XSS anywhere on the
origin drains **every** token out of web storage, while the CSRF exposure of a
cookie is fully solvable with known, layerable defenses. They are not equivalent.

## Keep the credential out of web storage

- Never put access tokens, refresh tokens, JWTs, or session IDs in `localStorage`
  or `sessionStorage`. Hold the session credential in an `HttpOnly; Secure;
  SameSite` cookie, or behind a Backend-for-Frontend (BFF), so JavaScript never
  has a handle to it at all.
- The trap is the "convenience" default of mainstream SPA tutorials: one XSS bug
  *anywhere on the origin* reads the whole store and exfiltrates it for offline,
  out-of-session use. OWASP: *"Do not store authentication tokens, session IDs,
  JWTs, refresh tokens, or any credential in localStorage or sessionStorage.
  These APIs are accessible to any JavaScript executing in the origin, so a single
  XSS vulnerability discloses every token. Use HttpOnly; Secure; SameSite=Strict
  cookies (preferred) or a Backend-for-Frontend (BFF) pattern."*

Paste-ready — a session cookie with every protective attribute set (the secure default
most frameworks make you opt into):

```http
Set-Cookie: session=<opaque-id>; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=3600
```

- `HttpOnly` — JS can't read it (`document.cookie`/Cookie Store blocked); blocks theft, not riding.
- `Secure` — sent over HTTPS only; **required** the moment you ever need `SameSite=None`.
- `SameSite=Strict` — not sent on any cross-site request; drop to `Lax` only if a top-level
  cross-site GET must stay logged in (and never silently rely on the browser default — see below).
- Scope with `Path` and prefer a short `Max-Age`/`Expires`; omit `Domain` to keep it host-only
  (a `Domain` cookie is also sent to sibling subdomains, widening the double-submit attack surface).

## HttpOnly stops theft, not riding

- `HttpOnly` keeps `document.cookie` / the Cookie Store API from reading the
  cookie — set it on every session cookie. But do **not** read it as "XSS can't
  touch our session."
- Under XSS the attacker doesn't need to *read* the cookie to abuse it: injected
  script can fire same-origin `fetch`/XHR that the browser silently authenticates
  with the `HttpOnly` cookie. `HttpOnly` downgrades token *theft* to in-page
  request forgery; it does not remove impact — so you must still prevent XSS.
  OWASP: *"if an XSS attack is combined with a CSRF attack, the requests sent to
  the web application will include the session cookie, as the browser always
  includes the cookies when sending requests. The HttpOnly cookie only protects
  the confidentiality of the cookie; the attacker cannot use it offline, outside
  of the context of an XSS attack."*

## SameSite: set it explicitly; defaults are not uniform

- Set `SameSite` explicitly (`Lax` or `Strict`) on auth cookies. Do not lean on
  the browser default: not every browser applies Lax-by-default, and the
  *implicit* Lax is a more permissive variant than the one you set yourself — it
  still rides top-level POSTs made within ~2 minutes of the cookie being set, a
  short cross-site window an attacker can aim at right after login. (This is Chrome's
  temporary "Lax+POST" compatibility intervention — Chromium's docs say it will be
  removed, and it is Chrome-family-specific, not a permanent cross-browser rule — so
  it only reinforces setting `SameSite` explicitly.) MDN: *"When
  Lax is applied as a default, a more permissive version is used. In this more
  permissive version, cookies are also included in POST requests, as long as they
  were set no more than two minutes before the request was made."*
- `SameSite=None` (the only value that allows cross-site delivery — cross-site
  SSO, OAuth post-back, embedded iframes) is **rejected unless `Secure` is also
  set.** MDN: *"The Secure attribute must also be set when using this value."* The
  debugging trap: a dropped cookie leaves no error in your server/app logs (the
  rejection surfaces only in the browser devtools console), so a "logged-out for
  no reason" report sends you hunting in the wrong place. And `None` disables the
  CSRF protection `Lax`/`Strict` would have given — reserve it for cookies that
  genuinely need cross-site delivery, never as a blanket "make cookies work
  everywhere" flag. For cross-site cookies that should be partitioned per
  top-level site, prefer the `Partitioned` attribute (CHIPS), which also requires
  `Secure`. MDN: *"if this is set, the Secure directive must also be set. See
  Cookies Having Independent Partitioned State (CHIPS) for more details."*

## CSRF still applies to cookie auth — on top of SameSite

- If state-changing requests authenticate via a cookie, add an anti-CSRF defense
  *in addition to* `SameSite`: a synchronizer token (stateful), a signed/HMAC
  double-submit token (stateless), and/or `Sec-Fetch-Site`/Origin checks. Use the
  framework's built-in CSRF protection rather than rolling your own.
- The common modern shortcut — *'we set `SameSite=Lax`, so we deleted the CSRF
  tokens'* — removes a still-essential layer: `SameSite` is browser-dependent and
  has known gaps (the default-Lax POST window, sibling same-site subdomains,
  client-side CSRF). OWASP: *"While Cross-Site Scripting (XSS) vulnerabilities can
  bypass CSRF protections, CSRF tokens are still essential for web applications
  that rely on cookies for authentication."*

## CSRF scope and browser-gate checks

- Treat CSRF as a **browser credential-riding** bug: a malicious site can make the
  browser send a request with ambient cookies, even though it cannot read the
  response. A `curl` request, API client, or bearer-token request that must set an
  `Authorization` header is not CSRF in this sense.
- For cookie-authenticated state changes, reject requests with unexpected or
  missing `Origin`/`Sec-Fetch-Site` signals where your browser support policy
  allows it. Maintain an explicit trusted-origin allowlist; do not infer safety
  from string prefixes.
- Reject "simple" form/content types on JSON mutation endpoints. Parse
  `Content-Type` as a media type; a naive string equality check can be bypassed
  by values such as `text/plain; application/json`.
- `SameSite=Lax`/`Strict`, Origin checks, and content-type gates are
  defense-in-depth. Keep an anti-CSRF token for high-risk cookie-authenticated
  actions instead of relying on any single browser behavior.

## Stateless CSRF: signed double-submit, validated from a header — never cookie-vs-cookie

- For a stateless defense use the **Signed (HMAC) Double-Submit Cookie** bound to
  the user's session, and validate the token from a request **header or form
  parameter only**. Never accept a match where the server reads the token back out
  of a cookie — the naive "compare cookie to body value" double-submit is
  bypassable, because an attacker on a sibling subdomain can inject the cookie.
  OWASP: *"The site must require that every transaction request from the user
  includes this random value as a custom request header or form parameter ONLY.
  Cookie validation is INSECURE."*
- For pure AJAX/API endpoints, **a custom request header is a recognized,
  token-free CSRF defense** — OWASP endorses it as a standalone control for AJAX/API
  endpoints ("No token is needed for this approach"), with two caveats: any non-AJAX
  `<form>` submission still needs a token, and the protection collapses under a
  permissive CORS config (below). It works because a custom header makes the request
  non-"simple", so the browser must preflight it, and a cross-site attacker page
  cannot get that preflight approved. OWASP: *"This
  defense relies on the CORS preflight mechanism which sends an OPTIONS request to
  verify CORS compliance with the destination server. All modern browsers
  designate requests with custom headers as \"to be preflighted\"."* (Note the
  mechanism is the CORS preflight, not the Same-Origin Policy.)
- **Caveat:** this protection collapses under a permissive CORS config. If the
  server reflects arbitrary origins (or pairs `Access-Control-Allow-Credentials:
  true` with a wide allow-list), it hands the attacker's origin preflight
  approval. OWASP: *"To allow CORS requests, but protect against CSRF, you need to
  make sure the server only allows a few select origins that you definitively
  control via the Access-Control-Allow-Origin header."*

## Bearer-header SPAs and the cookie-to-header pattern

- The load-bearing distinction for CSRF is **how the credential is sent**, not
  what it is. If your SPA sends it as an explicit `Authorization: Bearer` header
  read from JS memory, classic CSRF doesn't apply — but for a different reason than
  the custom-header trick above. A bearer token in JS memory is not an *ambient*
  credential: the browser never auto-attaches it, so an attacker-initiated
  cross-site request (a `<form>` POST, or a simple `fetch`) simply carries no
  `Authorization` header and the server sees an unauthenticated request. (No
  preflight is involved here; that mechanism is what protects the custom-header
  pattern, where the cookie *is* still auto-sent.) The trade-off: a token in JS is
  back in `localStorage`/XSS-theft territory.
- The cookie-based equivalent is the **cookie-to-header pattern**: the server sets
  a non-`HttpOnly` `XSRF-TOKEN` cookie, JS reads it and echoes it in an
  `X-XSRF-TOKEN` header. A cross-origin attacker gets the cookie auto-sent but
  cannot read it to set the matching header. OWASP: *"This approach leverages the
  fact that browsers automatically attach cookies to cross-origin requests, but
  only JavaScript running on the same origin can read values and set custom
  headers—making it possible to detect and block forged requests."*
- Two mirror-image mistakes: blanket-applying "all APIs need CSRF tokens" to a
  bearer-header SPA (wasted complexity), or assuming any token-in-JS scheme is
  CSRF-safe and then storing that token in a regular cookie the browser
  auto-attaches (re-introducing CSRF). Automatic delivery (cookie) → CSRF-exposed;
  explicit delivery (header) → not.

## Auth flow boundary

- This reference owns the security substrate: storage, cookies, SameSite, CSRF,
  Origin/content-type gates, session fixation, and logout.
- Frontend details for password forms, email-code lifecycle, passkey/WebAuthn UI,
  and auth-return navigation live in `frontend-auth-flow-contracts`. Keep only the
  security invariant here; put browser-flow behavior there.

## Session fixation: regenerate the session ID on auth

- Regenerate (rotate) the session ID at every privilege change — login above all,
  but also password change, role elevation, and any anonymous→authenticated
  transition — and destroy the old ID server-side. Never carry a pre-auth session
  ID into the authenticated session.
- The trap is the login flow that authenticates the user but keeps the session ID
  issued to the anonymous visitor: an attacker who planted or knows that pre-login
  ID (via a link, XSS, or response splitting) is now logged in as the victim.
  OWASP: *"The session ID regeneration is mandatory to prevent session fixation
  attacks, where an attacker sets the session ID on the victim user's web browser
  instead of gathering the victim's session ID, as in most of the other
  session-based attacks, and independently of using HTTP or HTTPS."*

## Logout: invalidate server-side, then clear client state

- On logout, **invalidate the session server-side** — the mandatory step. A
  client-only logout that just deletes the cookie or clears storage leaves the
  token valid on the server, so an already-exfiltrated or replayed copy keeps
  working after the user "logged out." Then clear residual client state by
  returning a `Clear-Site-Data` response header. OWASP: *"applications should
  ensure that previously stored sensitive data is removed when a session ends.
  This can be achieved by returning the Clear-Site-Data response header (for
  example, Clear-Site-Data: \"cache\", \"cookies\", \"storage\") during logout or
  session termination."*

## Find these in your codebase

Every hit is a review point, not an automatic bug:

```sh
# Credentials in web storage — the single-XSS-drains-everything pattern
rg -n '(local|session)Storage\.(set|get)Item\([^)]*(token|jwt|auth|session|refresh)' -i src/
# Cookies set without SameSite, or SameSite=None without Secure (check both lines together)
rg -n 'Set-Cookie|SameSite|setCookie|cookies\(\)\.set' -i src/ server/
```

## Sources

- OWASP — [Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
  (no credentials in web storage; HttpOnly confidentiality-only; session-ID
  regeneration; `Clear-Site-Data` on logout)
- OWASP — [Cross-Site Request Forgery Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
  (CSRF tokens still essential with cookie auth; header/form-only validation,
  cookie validation INSECURE; custom-header defense via CORS preflight + the
  permissive-CORS caveat; cookie-to-header pattern)
- MDN — [`Set-Cookie`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie)
  (`SameSite=None` requires `Secure`; default-Lax 2-minute POST window;
  `Partitioned`/CHIPS requires `Secure`)
- Pilcrow auth book — [CSRF](https://auth.pilcrowonpaper.com/csrf),
  [browser client-side storage](https://auth.pilcrowonpaper.com/browser-client-side-storage),
  [email code authentication](https://auth.pilcrowonpaper.com/email-code-authentication),
  and [passkey authentication](https://auth.pilcrowonpaper.com/passkey-authentication)
  (CSRF as browser cookie-riding, Origin/content-type gates, and auth-flow
  boundary evidence)
