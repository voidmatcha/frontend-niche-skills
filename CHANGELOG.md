# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `frontend-auth-flow-contracts` skill — frontend authentication flows as a
  browser/backend contract: login/signup/password-reset, email verification &
  one-time-code entry, passkeys/WebAuthn UI, auth callbacks & `returnTo` redirects,
  autofill/`autocomplete` hints, account-enumeration-safe errors, and fresh verification
  before sensitive actions. Ships `references/browser-auth-contracts.md` and a Codex
  per-skill interface manifest (`agents/openai.yaml`). Registered in the Claude
  `plugin.json` skills list, both keyword arrays, and the README skill table.
  Cross-references the boundary with `frontend-security-baseline` (token storage,
  cookies, SameSite, CSRF, open-redirect primitives), `deeplink-hydration` (router
  readiness / `returnTo` plumbing), and `a11y-contract-testing` (generic role/name/focus).
- `datetime-correctness` skill — dates/times that stay correct across timezones, DST
  transitions, and server-vs-client environments: UTC/epoch storage, the date-only
  `new Date("2026-06-14")` parsed as UTC (off-by-one in negative-offset zones),
  `<input type="datetime-local">` floating values with no zone, DST gaps/overlaps and
  zone-aware arithmetic, pinning `Intl.DateTimeFormat`'s `timeZone`, and the Temporal
  type model. Ships `references/storage-and-math.md` and `references/display-and-input.md`.
  Invariant-first (Temporal presented as the tool that encodes the distinctions). Bounded
  against `i18n-copy-and-layout` (locale display formatting) and `ssr-hydration-mismatch`
  (in-render `Date` / zone-dependent text divergence). All claims verified against MDN,
  TC39 Temporal, ECMA-402, and RFC 3339; a verification pass corrected the
  `Temporal.PlainDate.from` strictness claim and a fall-back DST example before release.
- `ssr-hydration-mismatch` skill — server-rendered HTML diverging from the client's first
  render ("Hydration failed" / "text content did not match"), which makes the framework
  discard the server tree and re-render on the client. Covers the trigger taxonomy
  (non-determinism: `Date.now()`/`Math.random()`/`typeof window`/locale/timezone; invalid
  HTML nesting), the fixes (two-pass `useEffect`, `useSyncExternalStore`, no-SSR dynamic
  import), and containment/diagnosis (`Suspense` blast radius, `suppressHydrationWarning`'s
  one-level limit, the React 18 recoverable-error model that hides in production, finding the
  diverging node). React/Next as the worked example with Vue/Nuxt, Svelte/SvelteKit, and
  Astro notes. Ships `references/triggers-and-containment.md`. Bounded against
  `deeplink-hydration` (router/query-param readiness) and `datetime-correctness`
  (zone-dependent text is one trigger). Verified against react.dev, the React 18 server-errors
  RFC, and Next.js/Vue/Astro docs; a verification pass corrected the dev-vs-prod
  `onRecoverableError` framing before release.

### Changed

- `frontend-security-baseline` — usability pass on the already-verified content (no
  factual claims changed):
  - Added a **"Start here — the traps that pass code review"** callout to `SKILL.md`,
    surfacing the five highest-value traps (strict-dynamic voiding the host allowlist,
    nonce-rewriting middleware, cross-origin SRI failing *closed*, the default-Lax 2-minute
    POST window / `SameSite=None` needing `Secure`, and `window.open` not being covered by
    `target="_blank"`) above the flat checklist.
  - Added paste-ready snippets to the core references: a narrow DOMPurify allowlist config
    (`references/xss-and-sanitization.md`), a fully-attributed `Set-Cookie` line
    (`references/auth-tokens-and-csrf.md`), and web.dev's nonce-based strict CSP header block
    (`references/csp-and-headers.md`).
  - Added a **"Strict CSP in Next.js (App Router)"** section to `references/csp-and-headers.md`
    with the per-request nonce middleware/`proxy` snippet (request + response `Content-Security-Policy`
    header, `x-nonce` handoff) and the Server Component reader, noting the Next.js 16
    `middleware`→`proxy` file rename. Verified against the official Next.js CSP guide.
  - Added a **"Find these in your codebase"** grep/ripgrep recipe block to each of the four
    references — high-signal detection one-liners for the anti-patterns each file documents
    (dangerous sinks & escape hatches, host-allowlist CSP / `integrity` without `crossorigin`,
    tokens in web storage / `SameSite`, `window.open` without `noopener` / reflected redirects /
    loose installs), framed as "every hit is a review point, not an automatic bug."
- `webview-bridge-pages` — strengthened the bridge security boundary in
  `references/contract-design.md` with verified real-world citations: Tauri remote-origin
  iframes reaching IPC without allow-listing ([CVE-2024-35222](https://nvd.nist.gov/vuln/detail/CVE-2024-35222)),
  Joplin note-content XSS escalating to RCE via Electron `nodeIntegration`
  ([CVE-2018-1000534](https://nvd.nist.gov/vuln/detail/CVE-2018-1000534)), and the
  cross-host `canGoBack()`-after-interaction quirk (tauri #13957) added to the existing
  WebView-history caveat. All three confirmed against NVD / the upstream issue.

### Fixed

- Factual-accuracy corrections from a sources re-verification pass (no guidance
  reversed; each change reconfirmed against the official source):
  - `frontend-security-baseline/references/xss-and-sanitization.md` — Trusted Types no
    longer scoped "Chromium-only" (now Baseline 2026: Chrome/Edge 83+, Safari 26+,
    Firefox 148+); the `data:` claim qualified — DOMPurify allows `data:` on
    data-URI-safe tags (`DATA_URI_TAGS`) by default rather than stripping it wholesale.
  - `frontend-security-baseline/references/auth-tokens-and-csrf.md` — the ~2-minute
    `SameSite=Lax` POST window labeled as Chrome's temporary "Lax+POST" intervention
    (Chromium docs say it will be removed), not a permanent cross-browser rule; the
    custom-header CSRF defense reframed to match OWASP (a recognized standalone control
    for AJAX/API endpoints, not merely a token supplement).
  - `frontend-security-baseline/references/csp-and-headers.md` — Next.js example leads
    with the v16 canonical `proxy.ts` / `export function proxy` (Node.js runtime), noting
    `middleware` remains for Next.js 13–15 and the Edge runtime.
  - `frontend-security-baseline/references/navigation-and-supply-chain.md` — ua-parser-js
    parenthetical corrected to the ~4-hour account-hijack + loose-resolution mechanism
    (a strict `npm ci` against a reviewed lockfile would have protected), not a
    lockfile mismatch.
  - `webview-bridge-pages/references/contract-design.md` — CVE-2024-35222 v2 fix
    corrected to `2.0.0-beta.20` (per GHSA-57fm-592m-34r7; the NVD description's
    `beta.19` is still an affected version).
  - `i18n-copy-and-layout/references/copy.md` — re-attributed the reorderable-placeholder
    example to the OpenStack I18n guide (not a W3C example) and added the source link.
  - `frontend-auth-flow-contracts/references/browser-auth-contracts.md` — Unicode
    normalization removed from the "do not mutate the credential" prohibition (NIST
    SP 800-63B: the verifier SHOULD apply NFC before hashing).

## [0.4.0] - 2026-06-11

### Added

- `frontend-security-baseline` skill — the client-side security baseline for the
  expensive default-looking choices that quietly fail open: HTML-encoding into
  `innerHTML` instead of choosing a safe sink, host-allowlist CSPs that pass review
  but block almost nothing, JWTs in `localStorage`, and SRI without `crossorigin`.
  A 19-item checklist over four areas — XSS & sanitization (safe sinks, contextual
  encoding, code-execution sinks, DOMPurify, React/Vue/Angular escape hatches,
  Trusted Types), CSP & security headers (nonce/hash + `strict-dynamic`,
  `frame-ancestors`, SRI, HSTS preload, COOP/COEP/CORP, Referrer-Policy), auth
  tokens & CSRF (web storage vs HttpOnly cookies, SameSite semantics, signed
  double-submit / custom-header via CORS preflight, bearer vs cookie, session
  fixation & logout), and navigation & supply chain (reverse tabnabbing &
  `window.open`, open-redirect allow-listing, `npm ci`/`ignore-scripts`/dependency
  confusion, secrets & source maps in the bundle).
- `frontend-security-baseline` ships a compact `SKILL.md` checklist plus four
  references (`references/xss-and-sanitization.md`, `references/csp-and-headers.md`,
  `references/auth-tokens-and-csrf.md`, `references/navigation-and-supply-chain.md`),
  matching the collection's two-tier structure.
- Cross-reference to `webview-bridge-pages` marking the boundary (client-side
  baseline here; postMessage bridge contract & inbound native→web origin/schema
  validation there — not duplicated).

### Notes

- All factual claims verified verbatim against official sources (OWASP Cheat Sheets
  & WSTG, MDN, web.dev, react.dev, vuejs.org, angular.dev, cure53/DOMPurify) before
  release. Every cited quote was re-confirmed verbatim against a freshly fetched copy
  of its source page, and a 26-section adversarial audit (each finding confirmed by an
  independent second verifier) checked the surrounding guidance for overstatement or
  misattribution beyond what each quote supports. Eight sections were corrected to
  their source-backed core — notably reframing SRI-without-`crossorigin` as failing
  *closed* (the load is refused) rather than open, and correcting the reason
  bearer-token SPAs sidestep CSRF (the token is never an ambient credential, distinct
  from the custom-header/CORS-preflight mechanism).

## [0.3.0] - 2026-06-11

### Added

- `i18n-copy-and-layout` skill — the cross-locale copy/layout/format layer (distinct
  from `cjk-text-and-input`'s glyph-rendering/IME scope): text expansion breaking
  layout (W3C/IBM expansion table, compound nouns, taller scripts), CLDR's six plural
  categories and `Intl.PluralRules`/ICU `plural` instead of `count === 1`, no string
  concatenation for sentences (full-sentence templates + named placeholders, ICU
  `select` for gender), `Intl.NumberFormat`/`DateTimeFormat` for locale-specific
  separators/grouping/currency (ISO 4217), and RTL via `lang`≠`dir` markup plus CSS
  logical properties.
- `i18n-copy-and-layout` ships a compact checklist `SKILL.md` plus references
  (`references/copy.md` — plurals/sentences/`Intl` formatting; `references/layout.md` —
  expansion/RTL/`lang`·`dir`), matching `webview-bridge-pages`' two-tier structure.
- Cross-references between `cjk-text-and-input` and `i18n-copy-and-layout` marking the
  boundary (East-Asian glyph/IME vs. cross-locale copy/format).

### Notes

- All factual claims verified against official sources (W3C Internationalization,
  Unicode CLDR, ICU User Guide, ECMA-402, MDN) before release.

## [0.2.0] - 2026-06-11

### Added

- `a11y-contract-testing` skill — accessibility semantics as testable contracts:
  dialog role/name requirements (WCAG 4.1.2, ARIA APG), role+name queries,
  sentinel specs, decorative-wrapper `role="presentation"` rules.
- `cjk-text-and-input` skill — CJK line breaking (`word-break: keep-all`,
  `line-break`, UAX #14), IME composition events (`isComposing`, legacy keyCode 229,
  Enter-during-composition guard), controlled-input composition pitfalls,
  grapheme-safe counting (`Intl.Segmenter`, NFC normalization).
- `deeplink-hydration` skill — deep links surviving SPA/SSR hydration:
  `router.isReady` gating, `window.location` as client-side source of truth,
  auth-bounce `returnTo`, direct-navigation e2e rule.

### Changed

- Renamed the collection from `webview-skills` to **`frontend-niche-skills`** —
  the scope is the long tail of frontend topics, not just webviews. Plugin and
  marketplace manifests updated (plugin `frontend-niche-skills` ships all skills;
  install command changed).

## [0.1.0] - 2026-06-10

### Added

- `webview-bridge-pages` skill: 12-item checklist plus a universal transport adapter
  for web pages running inside native app WebViews (React Native WebView, WKWebView,
  Android WebView, Flutter `webview_flutter`).
- `references/contract-design.md` — message contract, close/back ownership,
  actions with unobservable results (purchases), READY loading signal paired with an
  error/timeout policy, auth & session handoff, navigation & capabilities policy,
  A/B variants via query params.
- `references/page-implementation.md` — query parsing on SPA hydration, absolute-time
  timers, viewport/safe-area/keyboard/font-scale layout rules.
- Host references: `react-native.md`, `wkwebview.md`, `android-webview.md`,
  `flutter.md` (bridge APIs, version caveats, quirks).
- README curation of related bridge libraries, engineering write-ups, and
  compatibility references (all links live-verified 2026-06).
- Claude Code plugin packaging (`.claude-plugin/plugin.json`, `marketplace.json`),
  Apache-2.0 license, security policy.

### Notes

- All factual claims verified against official sources before release (93 claims
  checked; corrections incorporated). Community-sourced claims are labeled as such
  in the text.
- Incorporates an external Codex CLI review (auth/navigation/error-contract topics,
  framework-neutral adapter snippet, source-wording accuracy).

[Unreleased]: https://github.com/voidmatcha/frontend-niche-skills/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/voidmatcha/frontend-niche-skills/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/voidmatcha/frontend-niche-skills/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/voidmatcha/frontend-niche-skills/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/voidmatcha/frontend-niche-skills/releases/tag/v0.1.0
