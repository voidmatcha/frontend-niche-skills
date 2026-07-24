---
name: frontend-security-baseline
description: "Use when running a trap-first client-side security pass before shipping, focused on non-obvious frontend security traps: unsafe HTML sinks, sanitizer misuse, framework raw-HTML escape hatches, Trusted Types/DOMPurify gaps, host-allowlist CSP silently fails, JWT/localStorage token theft, SameSite/CSRF edge cases, opener leaks/window.open, open-redirect string checks, npm supply-chain footguns. Client-side scope; frontend-owned server proxy/SSRF/upload relay boundaries use bff-proxy-security-contracts; payment-page/PAN/PCI DSS evidence use payment-page-client-security; native-WebView bridge inbound-origin contracts use webview-bridge-pages."
---

# Frontend security baseline

This is a **trap-first hardening pass**, not a generic security checklist. Start with the
default-looking choice that quietly fails open, then replace it with the control that makes
the unsafe operation difficult or impossible.

Use this skill when reviewing browser-rendered surfaces before release: rich text, markdown
or CMS HTML, script policy, cookie/session behavior, cross-site requests, outbound links,
redirects, build/install steps, and client-bundled secrets.

## Scope and non-goals

- Covers browser/client-side implementation and frontend-owned build configuration.
- Does not replace backend authz, server-side input validation, threat modeling, or a full
  application security review.
- For frontend-owned server routes that proxy targets, headers, bodies, or multipart
  uploads, use `bff-proxy-security-contracts`.
- For WebView page ↔ native bridge origin/message contracts, use `webview-bridge-pages`.
- For login/email-code/passkey browser-flow contracts, use `frontend-auth-flow-contracts`.

## How to use

1. Identify the feature boundary: HTML rendering, script loading, token/session storage,
   cookie-authenticated mutation, navigation, redirect, install/build, or secret exposure.
2. Pick the matching trap row below. Do **not** produce a broad baseline report when only
   one trap family is relevant.
3. Read the linked reference only for the selected trap family.
4. Recommend the narrowest control that fails closed, plus one verification probe (`rg`,
   header check, unit/e2e assertion, or CI config check).

## Default-looking traps to check first

| Trap | Why it fails open | Prefer | Details |
| --- | --- | --- | --- |
| HTML-encoding before assigning to `innerHTML` | Browser parses in HTML/URL/CSS/JS contexts differently; one wrong encoder is enough. | Safe sinks (`textContent`), DOMPurify for rich HTML, Trusted Types for sink enforcement. | [xss-and-sanitization](./references/xss-and-sanitization.md) |
| Framework escape hatches (`dangerouslySetInnerHTML`, `v-html`, `bypassSecurityTrust*`) | They bypass the framework's auto-escaping and normalize raw HTML as an app feature. | Trusted + sanitized data only; keep sanitizer last, with no post-sanitize mutation. | [xss-and-sanitization](./references/xss-and-sanitization.md) |
| Sanitizer output post-processed or re-parsed | Linkifiers, markdown passes, string replaces, DOM mutation, or another library after `sanitize()` can reintroduce dangerous markup. | Put every transform before DOMPurify; insert exact returned string/TrustedHTML into sink. | [xss-and-sanitization](./references/xss-and-sanitization.md) |
| A host allow-list used *instead of* nonce/hash + `'strict-dynamic'` | A bare host allow-list (`script-src https://cdn… 'unsafe-inline'`) with no nonce/hash + `strict-dynamic` is the bypassable kind: JSONP, compromised hosts, redirects, and broad CDNs satisfy it. (Note: `https:`/`'unsafe-inline'` placed *after* the nonce + `strict-dynamic` are an intentional, security-neutral legacy fallback CSP3 browsers ignore — not the trap.) | Strict nonce/hash CSP with `strict-dynamic`, rolled out in `Report-Only` first; keep any host/`'unsafe-inline'` tokens only as a post-`strict-dynamic` legacy fallback. | [csp-and-headers](./references/csp-and-headers.md) |
| Nonce-rewriting middleware | A string-rewriter can stamp the nonce onto attacker-injected `<script>` tags too. | Generate the nonce per response in the template/render path that owns trusted scripts. | [csp-and-headers](./references/csp-and-headers.md) |
| CSP in `<meta>` or missing framing headers | Some directives are ignored in meta; framing is often left to defaults. | Real HTTP headers: `Content-Security-Policy`, `frame-ancestors`, HSTS, SRI as applicable. | [csp-and-headers](./references/csp-and-headers.md) |
| Cross-origin SRI without `crossorigin` | The load can fail closed because a `no-cors` response cannot be integrity-checked. | Pin both `integrity` and `crossorigin="anonymous"` for cross-origin static resources. | [csp-and-headers](./references/csp-and-headers.md) |
| JWT/session/refresh token in `localStorage` | Any XSS on the origin can read and exfiltrate it. | Opaque server session or BFF pattern with `HttpOnly; Secure; SameSite` cookies. | [auth-tokens-and-csrf](./references/auth-tokens-and-csrf.md) |
| "SameSite means no CSRF" | `Lax` has edge cases, including the browser-default Lax top-level POST grace window after a cookie is set; high-risk actions still need intent proof. | SameSite plus signed anti-CSRF token from a header for sensitive cookie-auth mutations. | [auth-tokens-and-csrf](./references/auth-tokens-and-csrf.md) |
| Cookie-vs-cookie double submit | An injected/subdomain cookie can match the submitted cookie value. | Signed/HMAC double-submit tied to the session and validated from a request header. | [auth-tokens-and-csrf](./references/auth-tokens-and-csrf.md) |
| `target="_blank"` is fixed, so all popups are safe | Modern anchors may imply `noopener`; `window.open()` does not unless requested. | `rel="noopener noreferrer"` on anchors and `'noopener,noreferrer'` features for `window.open`. | [navigation-and-supply-chain](./references/navigation-and-supply-chain.md) |
| `?next=` / `returnUrl=` checked with `startsWith` or deny-lists | Parser tricks, encoded hosts, and trusted-prefix phishing bypass string checks. | Server-side URL parsing and explicit allow-list/mapping of destinations. | [navigation-and-supply-chain](./references/navigation-and-supply-chain.md) |
| `npm install` / AI-suggested package accepted by name | Lock drift, install scripts, typosquatting, and dependency confusion execute attacker code. | `npm ci`, committed lockfile, install-script policy, package provenance review. | [navigation-and-supply-chain](./references/navigation-and-supply-chain.md) |
| "It is only in the browser bundle" | Anything shipped to the browser is public, including keys, internal URLs, and source maps. | No client secrets; gate production source maps and debug routes. | [navigation-and-supply-chain](./references/navigation-and-supply-chain.md) |

## Quick probes

Use probes as starting evidence, not as proof of safety:

```sh
# Dangerous HTML/code sinks — each needs a safe sink, sanitizer, or Trusted Types path
rg -n 'innerHTML|outerHTML|insertAdjacentHTML|document\.write|\beval\(|new Function\(' src/

# Framework raw-HTML escape hatches and sanitizer policy points
rg -n 'dangerouslySetInnerHTML|v-html|\{@html|bypassSecurityTrust|DOMPurify|sanitize\(|setHTMLUnsafe|parseHTMLUnsafe' src/

# Browser-readable token storage
rg -n 'localStorage|sessionStorage' src/ | rg -i 'token|jwt|session|refresh|auth'

# Popup opener leaks and reflected redirects
rg -n 'window\.open\(' src/ | rg -v 'noopener'
rg -n 'next=|returnUrl=|redirect_uri=|returnTo=' -i src/

# CI/install looseness
rg -n 'npm install' .github/ ci/ Makefile package.json 2>/dev/null
rg -n 'ignore-scripts|audit=false' .npmrc package.json 2>/dev/null
```

## Baseline controls by family

**XSS and sanitization** — [xss-and-sanitization](./references/xss-and-sanitization.md)

1. Prefer safe sinks: `textContent`, `setAttribute` non-URL attributes, DOM APIs that
 create text nodes.
2. Treat raw HTML as exceptional. If rich HTML is required, sanitize with a maintained
 allow-list library like DOMPurify and assign only the returned value.
3. Never mutate sanitized HTML afterward; post-sanitize rewrites, linkifiers, markdown
 passes, or DOM libraries can reintroduce XSS.
4. Run `eslint-plugin-no-unsanitized`, Semgrep, or CodeQL as candidate generators
 when available; still show source → sink → exploitability before filing.
5. Avoid string-to-code APIs (`eval`, `new Function`, string timers). Use data parsing and
 function references instead.
6. Consider Trusted Types where supported to enforce that injection sinks cannot receive
 raw strings.


**CSP and headers** — [csp-and-headers](./references/csp-and-headers.md)

1. Prefer strict nonce/hash CSP with `strict-dynamic` over host allow-lists.
2. Roll CSP out in `Content-Security-Policy-Report-Only` before enforcement.
3. Set framing policy with `frame-ancestors` in an HTTP CSP header; do not rely on meta CSP.
4. Use HSTS only when HTTPS is correct for the whole host; preload is a long-lived contract.
5. Use SRI for third-party static scripts/styles when bytes are expected to be stable.

**Auth tokens and CSRF** — [auth-tokens-and-csrf](./references/auth-tokens-and-csrf.md)

1. Do not store auth tokens, refresh tokens, JWTs, session IDs, or credentials in
    `localStorage` or `sessionStorage`.
2. Prefer host-only `HttpOnly; Secure; SameSite=Strict` cookies for opaque sessions; relax
    to `Lax` only for a specific top-level navigation need.
3. CSRF defenses still matter for high-risk cookie-authenticated mutations: validate a
    signed token sent in a custom header.
4. Regenerate session IDs on login and privilege change; client-only login/logout state is
    not enough.
5. On logout, invalidate server-side first, then clear client-visible state.

**Navigation and supply chain** — [navigation-and-supply-chain](./references/navigation-and-supply-chain.md)

1. For outbound new tabs, set `rel="noopener noreferrer"`; for `window.open`, pass
    `'noopener,noreferrer'` in the feature string.
2. Validate redirects on the server with URL parsing and explicit allow-lists or route IDs.
3. Treat every new dependency as executable code: inspect provenance, scripts, package age,
    maintainers, and registry scope.
4. Use deterministic CI installs (`npm ci`) and commit lockfiles.
5. Assume browser-shipped assets are public: no secrets, production credentials, or private
    operational endpoints in client bundles.

## PR-worthiness gate

A security grep hit is only a lead. Before calling it a vulnerability, show the boundary:

1. **Source**: attacker/user/CMS/package/URL-controlled data, or a browser security boundary such
   as cookies, CSP, opener, redirect destinations, or install scripts.
2. **Sink/control**: the data reaches an executable HTML/code/navigation sink, or the protective
   browser control is absent/misapplied.
3. **Exploit or policy effect**: show the smallest payload, header behavior, redirect, storage
   exposure, or install behavior that would change security posture.
4. **Fail-closed patch**: prefer a safe sink, renderer hook, URL parser allow-list, nonce/hash CSP,
   HttpOnly cookie, or CI install policy over ad-hoc string filtering.

Be precise about modern browser behavior:

- `<a target="_blank">` is lower signal by itself because modern browsers generally apply
  implicit `noopener` for anchors. Count it as a hardening/policy consistency issue only when the
  project requires `noreferrer`, supports older WebViews/browsers, or performs fragile post-render
  HTML mutation. `window.open()` remains high signal unless it passes `noopener,noreferrer`.
- Raw HTML APIs are not automatically bugs when the input is constant, sanitized immediately before
  assignment, and not mutated afterward. The bug is the unsafe trust boundary, not the API name.
- Client-visible API keys are not secrets if they are documented public identifiers; prove privilege
  or quota impact before filing.

## Output shape

Return findings as trap-focused bullets:

- **Trap**: the default-looking unsafe choice.
- **Evidence**: file/header/config/probe that shows the risk.
- **Fix**: the fail-closed control.
- **Verification**: smallest regression check that would detect reintroduction.

## References

| File | Covers |
| --- | --- |
| [xss-and-sanitization.md](./references/xss-and-sanitization.md) | Source-to-sink XSS, safe sinks, sanitizer/allow-list misuse, Trusted Types. |
| [csp-and-headers.md](./references/csp-and-headers.md) | CSP (nonce/hash, `strict-dynamic`), `frame-ancestors`, HSTS, SRI, report-only rollout. |
| [auth-tokens-and-csrf.md](./references/auth-tokens-and-csrf.md) | Token/session storage boundaries, cookie flags, CSRF defenses, session regeneration. |
| [navigation-and-supply-chain.md](./references/navigation-and-supply-chain.md) | `noopener`/`noreferrer`, open-redirect validation, dependency provenance, public-bundle secrets. |
