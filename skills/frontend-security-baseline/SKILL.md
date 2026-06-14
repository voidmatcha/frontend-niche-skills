---
name: frontend-security-baseline
description: "Use when building or hardening the client side of a web app before it ships — rendering user/CMS HTML (XSS sinks, DOMPurify, Trusted Types), setting CSP and security headers (nonce vs host allowlist, frame-ancestors, HSTS preload, SRI), storing auth tokens and stopping CSRF (localStorage vs HttpOnly cookies, SameSite, double-submit), or handling outbound links, open redirects, and the npm supply chain. Client-side scope; for native-WebView bridge & inbound-origin contracts see webview-bridge-pages."
---

# Frontend security baseline

The expensive frontend security bugs aren't exotic — they're the **default-looking
choice that quietly fails open**: HTML-encoding into `innerHTML`, a host-allowlist CSP
that reviewers wave through, a JWT in `localStorage`. Each looks done and isn't. Core
rule: **prefer the control that makes the unsafe operation
structurally impossible** (safe sink, nonce, HttpOnly cookie, allowlist) over the one
that depends on encoding/validating your way to safety every time.

This is the client-side baseline. For the **postMessage bridge contract and inbound
(native→web) origin/schema validation**, use **webview-bridge-pages** — not repeated here.

**Start here — the traps that pass code review (verify these first):**

- **#7 `'strict-dynamic'` makes the browser ignore your host allowlist** — a long
  `script-src https://…` list kept "just in case" is dead weight, not a layer.
- **#8 nonce-rewriting middleware stamps the nonce onto attacker-injected scripts too**
  — it looks like a CSP but provides no XSS protection.
- **#10 cross-origin SRI without `crossorigin` fails *closed*** — the resource doesn't
  load at all; the integrity check only runs once both attributes are present.
- **#13 browser-default `SameSite=Lax` still rides a top-level POST for ~2 min after
  the cookie is set**, and `SameSite=None` is silently dropped without `Secure`.
- **#16 `target="_blank"` covers anchors, not `window.open()`** — the JS call needs
  explicit `'noopener,noreferrer'`.

## Checklist (lead with the trap; details in references/)

**XSS & sanitization** → [xss-and-sanitization](./references/xss-and-sanitization.md)

1. Encoding into `innerHTML` is the fragile fix — assign untrusted data to `textContent`
   (or `.value`, `createTextNode`), which is structurally inert. Pick the sink; don't
   encode your way into a dangerous one.
2. One global HTML-escaper is **not** XSS-safe — encode for the *exact* context (HTML
   body / attribute / JS string / URL / CSS); each parses differently. Quote attribute
   and JS-string values.
3. Never feed user input to `eval`, `new Function`, or string-form `setTimeout/setInterval`
   — encoding doesn't help; pass a function reference and `JSON.parse` for JSON.
4. For user-authored rich HTML, sanitize with a maintained allowlist library (OWASP
   recommends **DOMPurify**), keep it patched, and run it **last** — mutate nothing after.
5. Framework escape hatches bypass auto-escaping — React `dangerouslySetInnerHTML`, Vue
   `v-html`, Angular `bypassSecurityTrust*`: trusted+sanitized data only, built close to
   its source so every raw-HTML site is greppable.
6. Defense-in-depth: **Trusted Types** (`require-trusted-types-for 'script'`) makes the
   sinks themselves reject raw strings; roll out with `-Report-Only` first.

**CSP & security headers** → [csp-and-headers](./references/csp-and-headers.md)

7. Build CSP on a per-response **nonce/hash + `strict-dynamic`**, not host allowlists —
   allowlists are bypassable (JSONP, hosted libs, open redirects). Add `object-src 'none';
   base-uri 'none'`.
8. Generate the nonce fresh per response via a real templating engine — never middleware
   that string-replaces `<script>` (it stamps attacker-injected scripts too); never a
   static nonce.
9. Clickjacking: CSP `frame-ancestors` is the real control; `X-Frame-Options` is only a
   legacy fallback (browsers ignore XFO once `frame-ancestors` is set).
10. On a cross-origin `<script>`, SRI needs `crossorigin="anonymous"` too — without it the
    load fails closed (a `no-cors` fetch can't be integrity-checked), so add both and pin the
    third-party version. HSTS `preload` is near-irreversible: opt in only when *every*
    subdomain is HTTPS.
11. Set Referrer-Policy and cross-origin isolation (COOP/COEP/CORP) explicitly rather
    than trusting defaults — and dry-run isolation with `-Report-Only` (it breaks
    cross-origin embeds and OAuth popups).

**Auth tokens & CSRF** → [auth-tokens-and-csrf](./references/auth-tokens-and-csrf.md)

12. Tokens in `localStorage`/`sessionStorage` are read by *any* XSS on the origin — keep
    the credential in an `HttpOnly; Secure; SameSite` cookie (or a BFF). HttpOnly stops
    theft, not riding the session, so still prevent XSS.
13. Set `SameSite` explicitly (browser defaults differ; default-Lax has a ~2-min POST
    window); `SameSite=None` is dropped unless `Secure` is also set.
14. Cookie auth still needs CSRF defense *on top of* SameSite — synchronizer token
    (stateful) or signed/HMAC double-submit (stateless; validate via header/form, never
    cookie-vs-cookie). A bearer/`Authorization` header isn't auto-sent, so it sidesteps
    CSRF (back in XSS-theft territory instead).
15. Regenerate the session ID on login/privilege change (else session fixation); on
    logout, invalidate **server-side** + `Clear-Site-Data` — a client-only logout leaves
    the token valid. For login/email-code/passkey browser-flow contracts, use
    `frontend-auth-flow-contracts`.

**Navigation & supply chain** → [navigation-and-supply-chain](./references/navigation-and-supply-chain.md)

16. `target="_blank"` implies `noopener` on modern anchors, but still set
    `rel="noopener noreferrer"` (noreferrer also strips `Referer`); `window.open()` is
    **not** covered — pass `'noopener,noreferrer'`.
17. Open redirects: map a short ID server-side, or allowlist hosts with a real URL parser
    — never reflect `?next=`/`?returnUrl=` through `startsWith`/a denylist.
18. Supply chain: `npm ci` (not `install`) in CI; `ignore-scripts=true` + explicit
    allowlist; verify every new/AI-suggested package; scoped names + private-registry
    pinning against dependency confusion.
19. Nothing shipped to the browser is secret — no API keys, credentials, or hidden routes
    in client JS, and don't publish production source maps.

## References

| File | Covers |
|------|--------|
| [xss-and-sanitization](./references/xss-and-sanitization.md) | Safe vs dangerous sinks, contextual encoding, code-execution sinks, DOMPurify (allowlist + sanitize-last), React/Vue/Angular escape hatches, Trusted Types |
| [csp-and-headers](./references/csp-and-headers.md) | Strict CSP (nonce/hash + `strict-dynamic`), nonce generation, `frame-ancestors`, SRI, HSTS preload, COOP/COEP/CORP, Referrer-Policy |
| [auth-tokens-and-csrf](./references/auth-tokens-and-csrf.md) | Web storage vs HttpOnly cookies, SameSite semantics, CSRF (synchronizer / signed double-submit / custom-header, Origin/content-type gates), bearer vs cookie, session fixation & logout |
| [navigation-and-supply-chain](./references/navigation-and-supply-chain.md) | Reverse tabnabbing & `rel`/`window.open`, open-redirect allowlisting, npm lockfile/`ci`/scripts/typosquatting, secrets & source maps in the bundle |

Sources are listed in each reference file.
