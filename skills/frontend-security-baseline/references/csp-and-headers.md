# CSP & security headers

Headers are where security looks done but isn't. A host-allowlist CSP passes review and
blocks almost nothing; SRI without `crossorigin` silently breaks the load instead of
protecting it; HSTS `preload` is a one-way door. The theme: **the default-looking
configuration isn't the secure one.**

## Strict CSP, not host allowlists

- Build the policy around a **per-response nonce (or script hash) plus `'strict-dynamic'`**,
  e.g. `script-src 'nonce-{RANDOM}' 'strict-dynamic'; object-src 'none'; base-uri 'none'`.
  Do not rely on host/scheme allowlists (`script-src https://… ` or `https:`) to stop XSS.
- Paste-ready — web.dev's nonce-based strict CSP starting point (`{RANDOM}` is the
  fresh per-response nonce; add `report-uri`/`report-to` while you tune it):

  ```http
  Content-Security-Policy:
    script-src 'nonce-{RANDOM}' 'strict-dynamic';
    object-src 'none';
    base-uri 'none';
  ```

  `object-src 'none'` kills `<object>`/`<embed>` plugin vectors; `base-uri 'none'` stops an
  injected `<base>` from re-pointing every relative script URL. Add a `style-src` only if you
  also lock down styles — strict-dynamic governs scripts, not CSS.
- Most `script-src` allowlists are bypassable — JSONP endpoints, hosted library copies, and
  open redirects on an allowed domain all let an attacker load script "from" a trusted host.
  web.dev: *"how to use a CSP based on nonces or hashes to mitigate XSS, instead of the
  commonly used host-allowlist-based CSPs that often leave the page exposed to XSS because
  they can be bypassed in most configurations."*
- **`'strict-dynamic'` propagates trust** from your nonce/hash-marked script to scripts it
  loads, so you don't nonce-tag every third-party tag. In CSP3 browsers it also makes the
  browser **ignore** your host allowlist, `'self'`, and `'unsafe-inline'` in `script-src`.
  MDN: *"the trust explicitly given to a script… by accompanying it with a nonce or a hash,
  shall be propagated to all the scripts loaded by that root script. At the same time, any
  allowlist or source expressions such as 'self' or 'unsafe-inline' will be ignored."*
- The trap is a **host allow-list that *substitutes* for** nonce/hash + `'strict-dynamic'`
  (e.g. `script-src https://cdn… 'unsafe-inline'` with no nonce) — that is the bypassable
  policy. It is **not** a trap to keep `https:` and `'unsafe-inline'` *after* the nonce +
  `'strict-dynamic'` tokens: those are an intentional, security-neutral **legacy fallback**
  that modern (CSP3) engines ignore, and web.dev recommends keeping them. Pre-CSP3 engines
  (e.g. Safari <15.4) ignore `'strict-dynamic'` and fall back to the source list, so the
  fallback list is doing real work for them — flagging it as "dead weight" is a false
  positive. web.dev: *"Using `strict-dynamic` requires adding `https:` as a fallback for
  earlier versions of Safari… All browsers that support `strict-dynamic` ignore the `https:`
  fallback, so this won't reduce the strength of the policy"* and *"`https:` and `unsafe-inline`
  don't make your policy less safe. Any browser that supports `strict-dynamic` knows to ignore
  them."*

## Generating the nonce

- Generate a **fresh, unguessable, one-time-use** nonce for **every** HTTP response, and
  inject it with a real HTML templating engine. Never reuse a static nonce.
- The dangerous shortcut is middleware that rewrites all `<script>` tags to add the nonce —
  it defeats the entire purpose, because the same rewrite stamps the valid nonce onto
  attacker-injected scripts too, leaving the policy with no XSS protection. OWASP: *"Don't create a middleware that replaces all script
  tags with \"script nonce=...\" because attacker-injected scripts will then get the nonces
  as well. You need an actual HTML templating engine to use nonces."* (OWASP describes nonces
  as *"unique one-time-use random values that you generate for each HTTP response."*)

## Strict CSP in Next.js (App Router)

The framework-specific trap: a strict nonce CSP only works if the nonce is generated
**per request** and the page is **dynamically rendered** — a statically-generated page has
no request to attach a fresh nonce to. Next.js: *"To use a nonce, your page must be
dynamically rendered. This is because Next.js applies nonces during server-side rendering"* —
so reading the nonce opts the route out of static generation (and out of PPR).

Generate the nonce in the proxy/middleware, put it on **both** the outgoing CSP header and a
custom request header, then read it back in a Server Component:

```ts
// proxy.ts  (Next.js 16; on 13–15 use middleware.ts / `export function middleware` —
//            same signature. `proxy` runs on the Node.js runtime; keep `middleware`
//            if you need the Edge runtime.)
import { NextRequest, NextResponse } from 'next/server';

export function proxy(request: NextRequest) {
  const nonce = Buffer.from(crypto.randomUUID()).toString('base64');
  // 'self' here is the security-neutral legacy fallback (ignored by CSP3 browsers once
  // 'strict-dynamic' takes effect); nonce + 'strict-dynamic' are what actually enforce.
  const csp = `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'; object-src 'none'; base-uri 'none';`;

  const requestHeaders = new Headers(request.headers);
  requestHeaders.set('x-nonce', nonce);                       // so Server Components can read it
  requestHeaders.set('Content-Security-Policy', csp);

  const response = NextResponse.next({ request: { headers: requestHeaders } });
  response.headers.set('Content-Security-Policy', csp);       // the header the browser enforces
  return response;
}
```

```tsx
// app/page.tsx — reading the nonce forces dynamic rendering (intended)
import { headers } from 'next/headers';
import Script from 'next/script';

export default async function Page() {
  const nonce = (await headers()).get('x-nonce') ?? undefined;
  return <Script src="https://example.com/widget.js" nonce={nonce} strategy="afterInteractive" />;
}
```

Next.js auto-propagates the nonce to its own framework scripts and to any `<Script nonce={…}>`,
so you don't tag every tag by hand. Set the nonce on the **request** header (for SSR) *and* the
**response** header (for the browser) — omitting the request copy is the silent failure mode.

## Clickjacking: `frame-ancestors`

- Control framing with the CSP **`frame-ancestors`** directive (`frame-ancestors 'none'`, or
  `'self' https://trusted.example`) as the primary defense; keep `X-Frame-Options` only as a
  fallback for legacy browsers, and keep the two equivalent.
- Shipping only `X-Frame-Options`, or setting it to conflict with `frame-ancestors`, gives
  inconsistent protection: MDN: *"The frame-ancestors directive is a replacement for
  X-Frame-Options. By setting X-Frame-Options as well as frame-ancestors, you can prevent
  embedding in browsers that don't support frame-ancestors."* (Don't try per-origin framing
  via `X-Frame-Options: ALLOW-FROM` — MDN's `X-Frame-Options` reference calls it *"an obsolete
  directive. Modern browsers that encounter response headers with this directive will ignore
  the header completely."* Use `frame-ancestors` for per-origin allow-listing.)

## Subresource Integrity (SRI)

- On third-party `<script>`/`<link rel=stylesheet>`, add **both** an `integrity` hash
  (`sha256/384/512`) **and** `crossorigin="anonymous"`, and pin a specific immutable version
  (regenerate the hash on every bump).
- The non-obvious trap on a **cross-origin** resource: `integrity` without `crossorigin`
  **fails closed**, not open. The fetch defaults to `no-cors` mode, which can't be
  integrity-validated, so the browser refuses the request — the resource doesn't load at all.
  MDN: *"browsers will not allow no-cors requests to use subresource integrity, so a request
  like this will always fail"* — hence *"you must include the crossorigin attribute in your
  markup."* The CDN must also send `Access-Control-Allow-Origin`. So the mistake breaks the
  page visibly (it does not silently ship unverified script), but your integrity protection
  isn't actually doing anything until both attributes are present. Consider an
  `Integrity-Policy` header to require integrity metadata on all subresources.

## HSTS and preload

- Send `Strict-Transport-Security` over HTTPS only. Before submitting to the preload list,
  set `max-age` to at least one year and include `includeSubDomains` and `preload`, e.g.
  `max-age=63072000; includeSubDomains; preload`. MDN: *"When using preload, the max-age
  directive must be at least 31536000 (1 year), and the includeSubDomains directive must be
  present."*
- Preload is **near-irreversible**: submitting via [hstspreload.org](https://hstspreload.org/)
  while any subdomain (often internal or legacy) still serves HTTP forces HTTPS for every
  subdomain in the browser's built-in list and hard-breaks those hosts for months. Confirm
  every subdomain is HTTPS first.

## Cross-origin isolation & Referrer-Policy

- To use `SharedArrayBuffer`, high-resolution timers, or `measureUserAgentSpecificMemory()`,
  send **both** `Cross-Origin-Embedder-Policy: require-corp` and `Cross-Origin-Opener-Policy:
  same-origin`, and have every cross-origin subresource opt in via CORS or
  `Cross-Origin-Resource-Policy`. web.dev: *"To opt in to a cross-origin isolated state, you
  need to send the following HTTP headers on the main document: `Cross-Origin-Embedder-Policy:
  require-corp` / `Cross-Origin-Opener-Policy: same-origin`."* Roll out with the `-Report-Only`
  variants first — `COEP` blocks every cross-origin image/script/iframe lacking CORP and `COOP`
  nulls `window.opener`, breaking OAuth/payment popups.
- Set **`Referrer-Policy: strict-origin-when-cross-origin`** (or stricter) explicitly rather
  than trusting the default. MDN: *"This is the default policy if no policy is specified… (see
  spec revision November 2020). Previously the default was no-referrer-when-downgrade"* — older
  middleware and inconsistent browsers can still leak full path+query (and any token in the URL)
  cross-origin.

## Find these in your codebase

Header config rarely lives in `src/`, so point these at where you set headers (middleware,
server config, `next.config.js`, CDN rules) — every hit is a review point, not a verdict:

```sh
# A CSP that names hosts but never a nonce/hash or strict-dynamic is the bypassable kind
rg -n 'Content-Security-Policy' . | rg -vi 'nonce|strict-dynamic|sha256-'
# Cross-origin <script integrity=…> missing crossorigin → fails closed (won't load at all)
rg -n 'integrity=' src/ public/ | rg -v 'crossorigin'
# Markup-rewriting nonce middleware (the anti-pattern) vs a real template-injected nonce
rg -n 'replace\(.*<script|nonce' . -i
```

## Sources

- web.dev — [Mitigate XSS with a strict CSP](https://web.dev/articles/strict-csp)
  (nonce/hash over bypassable host allowlists; `https:`/`'unsafe-inline'` after `strict-dynamic`
  are a security-neutral fallback for Safari <15.4 and other pre-CSP3 browsers)
- Next.js — [Content Security Policy](https://nextjs.org/docs/app/guides/content-security-policy)
  (per-request nonce in middleware/`proxy`; nonce requires dynamic rendering; `x-nonce` handoff)
- MDN — [`Content-Security-Policy: script-src`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/script-src)
  (`'strict-dynamic'` propagation; allowlist/`'self'`/`'unsafe-inline'` ignored)
- OWASP — [Content Security Policy Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html)
  (per-response nonce via templating engine; no script-tag-rewriting middleware)
- MDN — [Clickjacking](https://developer.mozilla.org/en-US/docs/Web/Security/Attacks/Clickjacking)
  (`frame-ancestors` replaces `X-Frame-Options`)
  · [`X-Frame-Options`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/X-Frame-Options)
  (`ALLOW-FROM` is an obsolete directive modern browsers ignore)
- MDN — [Subresource Integrity](https://developer.mozilla.org/en-US/docs/Web/Security/Subresource_Integrity)
  · [SRI defenses](https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Subresource_Integrity)
  (CORS required; a `no-cors` cross-origin subresource can't be integrity-checked, so the load fails)
- MDN — [`Strict-Transport-Security`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Strict-Transport-Security)
  · [hstspreload.org](https://hstspreload.org/) (preload `max-age`/`includeSubDomains`; irreversibility)
- web.dev — [Cross-origin isolation (COOP/COEP)](https://web.dev/articles/coop-coep)
- MDN — [`Referrer-Policy`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Referrer-Policy)
  (default changed Nov 2020)
