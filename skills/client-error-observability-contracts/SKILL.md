---
name: client-error-observability-contracts
description: "Use when frontend error capture or monitoring misbehaves: production reports only Script error, event-handler or async failures bypass framework boundaries, unhandled rejections vanish, minified stacks cannot be symbolicated, one bug fragments into many issues, or PII/tokens/card data leave the browser. Covers global capture wiring, cross-origin stack access, source-map upload versus public shipping, grouping/fingerprinting, and pre-send scrubbing. Use frontend-security-baseline for source-map exposure policy, ssr-hydration-mismatch for recoverable hydration errors, and payment-page-client-security for PAN/CVV logging boundaries."
---

# Client error observability contracts

Global capture handlers and framework error hooks catch different, non-overlapping error surfaces; the observability contract is wiring all of them, keeping stacks readable in production without shipping original source, grouping errors so one bug is one issue, and scrubbing PII before the payload leaves the browser. The goal is not a monitoring-vendor tutorial — it is to make sure no class of error silently disappears and no sensitive data silently ships.

## Boundary with sibling skills

- Use **client-error-observability-contracts** for the capture wiring itself:
  `window.onerror`/`error` + `unhandledrejection` listeners, `crossorigin`/CORS
  for readable cross-origin stacks, source-map upload-vs-ship, grouping/fingerprint
  config, and `beforeSend`/scrubber PII redaction.
- Use **frontend-security-baseline** for the *policy* around a public source map as
  an info leak and for do-not-ship-secrets — this skill owns the capture side, not
  the security ruling.
- Use **ssr-hydration-mismatch** when the reported error is a recoverable React
  hydration mismatch (minified #418/#425, no server-vs-client diff).
- Use **payment-page-client-security** for the rule that PAN/CVV must never be
  logged or serialized into an error payload.

## Core rule

Capture every escape path (sync throw, rejected promise, framework-caught error),
attribute it (readable stack without deploying source), group it deterministically,
and scrub it — before deciding it is "reported."

## Review checklist

1. **Wire both global handlers — they are disjoint.** A synchronous throw fires
   `window.onerror`/`error`; a rejected promise with no `.catch` fires
   `unhandledrejection` and *not* `error`. Wiring only one drops a whole class of
   failures. Resource-load errors (`<img>`/`<script>` 404) do not bubble to
   `window.onerror` — capture them with `addEventListener('error', fn, true)`.
2. **Framework hooks and global handlers cover different surfaces — keep both.**
   React error boundaries (`getDerivedStateFromError`/`componentDidCatch`) catch only
   render, lifecycle, and constructor errors — **not** event handlers,
   `setTimeout`/`requestAnimationFrame`/async callbacks, SSR, or errors in the
   boundary itself. Vue's `app.config.errorHandler`/`onErrorCaptured` covers more
   (render, watchers, lifecycle, event handlers, and promise chains *returned* from
   those), but a throw in a bare timer or a detached (non-returned) promise still
   escapes to the global handlers in both. So an event-handler or async error that
   "vanishes" needs a global handler or a local `try/catch`, not a bigger boundary.
3. **Kill the "Script error." blackout.** A cross-origin script (CDN bundle,
   error-SDK loader) reports to `onerror` as the opaque string `"Script error."`
   with no message/line/column/stack unless the `<script>` has
   `crossorigin="anonymous"` **and** the asset server returns a matching
   `Access-Control-Allow-Origin`. Both are required — the attribute alone does
   nothing; a restrictive `Cross-Origin-Resource-Policy` can also block the fetch.
4. **Ship readable stacks without shipping source.** Minified bundles produce
   unreadable stacks. Upload source maps to the monitoring backend at build time
   (modern SDKs — Sentry and similar — match them via Debug IDs) rather than deploying `.map` files beside
   the bundle — a public `.map`, or a live `//# sourceMappingURL=` pointing at one,
   hands your original source to anyone. Emit hidden source maps and delete the
   `.map` from the deploy artifact after upload.
5. **Make grouping deterministic.** Per-request data in the message (ids, URLs,
   timestamps) fragments one bug into thousands of issues; an over-generic message
   merges distinct bugs into one. Set an explicit grouping key (`fingerprint` in
   Sentry-style SDKs; other reporters expose equivalents — e.g. error
   type/code plus `{{ default }}`) for known-noisy errors and keep dynamic values in
   structured context, out of the message.
6. **Scrub PII in the SDK, before send.** Payloads pull in more than the stack:
   request URLs/query strings, breadcrumbs (logged statements, prior network), user
   context, and framework state can carry emails, tokens, auth cookies, or card data.
   Redact in a `beforeSend`/scrubber hook client-side (server-side scrubbing is a
   backstop, not the boundary), keep `sendDefaultPii` off unless justified, and
   never place PAN/CVV or secrets where the reporter can serialize them.
7. **Turn framework-caught errors into signal.** React 18 `onRecoverableError` and
   React 19 `onUncaughtError`/`onCaughtError` (options on `createRoot`/`hydrateRoot`)
   route framework-handled errors to your reporter; without them a recovered error is
   logged only as a minified React code with no diff and is easy to miss.

## Defect patterns

| Smell | Risk | Better direction |
| --- | --- | --- |
| Only `window.onerror` wired, no `unhandledrejection` | Rejected promises with no `.catch` are never reported | Add an `unhandledrejection` listener too; the two are disjoint |
| Error boundary added to "catch" an `onClick`/async crash | Boundaries never see event-handler or timer/promise errors | `try/catch` in the handler (store in state); rely on global handlers for detached async |
| Cross-origin script, no `crossorigin` + ACAO | Every error from it is an opaque `"Script error."` | `crossorigin="anonymous"` on the tag **and** `Access-Control-Allow-Origin` from the asset host |
| `.map` files deployed next to the bundle | Original source is publicly downloadable | Upload maps to the backend; hidden source maps + delete `.map` from the deploy |
| Error message embeds request id / URL / timestamp | One bug fragments into thousands of issues | Explicit `fingerprint`; move dynamic values to context |
| No `beforeSend` scrub; `sendDefaultPii` on | Emails/tokens/PAN leave in the payload | Redact in `beforeSend` before send; keep PAN out entirely |

## Quick probes

Use these as leads, not proof; inspect the wiring and deploy artifact before filing:

```sh
# Global capture wiring — expect BOTH error and unhandledrejection
rg -n "\.onerror|addEventListener\(['\"]error|addEventListener\(['\"]unhandledrejection" src/ app/ 2>/dev/null

# Cross-origin script tags missing crossorigin (the "Script error." blackout)
rg -n "<script[^>]+src=" src/ app/ public/ index.html 2>/dev/null | rg -v crossorigin

# Source maps that may ship to production
rg -n "sourceMappingURL|devtool|hidden-source-map|filesToDeleteAfterUpload" . 2>/dev/null
find dist build out -name '*.map' 2>/dev/null

# Reporter init, grouping, and scrub hooks
rg -n "Sentry\.init|captureException|beforeSend|fingerprint|sendDefaultPii|onRecoverableError|onUncaughtError" src/ app/ 2>/dev/null
```

## PR-worthiness gate

Raw grep hits are noisy. Count a finding only when a capture or data-safety contract
actually breaks:

- **Dropped class**: `unhandledrejection` (or capture-phase resource errors) unwired,
  or an async/event-handler error routed to a boundary that cannot catch it — and
  that surface exists in the app.
- **Blackout**: a cross-origin script on the error path with no `crossorigin` + ACAO,
  so its errors arrive as unattributable `"Script error."`.
- **Info leak**: a `.map` deployed publicly, or a live `sourceMappingURL` pointing at
  one.
- **Grouping**: dynamic data in the message that provably fragments or merges issues.
- **PII**: a real sensitive field (email, token, cookie, PAN) reaches the reporter
  with no scrub.

Reject weak findings:

- A single global handler in an app with no promises/async — confirm the missing
  surface exists; `crossorigin` absent on a **same-origin** script (no blackout).
- A reporter that already scrubs by default, has `sendDefaultPii` off, and a
  `beforeSend`; or hidden source maps uploaded and deleted from the deploy (the
  positive control, not a leak); or `fingerprint` left default when messages are
  already stable.

Minimal useful PR: add the missing global listener (or move an async throw out of a
boundary into `try/catch` + a global handler), add `crossorigin` + ACAO to the
failing script, delete the `.map` from the deploy and upload instead, add a
`fingerprint` for the noisy error, or add a `beforeSend` redaction — plus a probe/test
that the class is now captured and the payload is scrubbed.

## Output shape

Return compact findings:

- **Capture contract**: which surface (sync `error` / `unhandledrejection` /
  resource / framework hook) is covered or missing.
- **Evidence**: file/line, or the opaque `"Script error."`, minified stack, or public
  `.map` path.
- **Risk**: dropped error class, unattributable cross-origin error, source/PII
  exposure, or grouping distortion.
- **Fix**: smallest wiring/config/scrub change.
- **Follow-up**: `frontend-security-baseline` (map/secret policy),
  `ssr-hydration-mismatch` (recoverable hydration error), or
  `payment-page-client-security` (PAN) if it crosses that boundary.

## Sources

- MDN [Window: error event](https://developer.mozilla.org/en-US/docs/Web/API/Window/error_event) — `onerror`'s five-argument signature, resource errors not bubbling, and cross-origin `"Script error."` sanitization.
- MDN [Window: unhandledrejection event](https://developer.mozilla.org/en-US/docs/Web/API/Window/unhandledrejection_event) — fires for rejected promises the sync `error` event does not cover.
- MDN [crossorigin attribute](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/crossorigin) and [Access-Control-Allow-Origin](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Access-Control-Allow-Origin) — the two coordinated pieces that restore readable cross-origin errors.
- React [Component](https://react.dev/reference/react/Component) (`componentDidCatch`/`getDerivedStateFromError`, what boundaries do *not* catch) and [createRoot](https://react.dev/reference/react-dom/client/createRoot) (`onUncaughtError`/`onCaughtError`/`onRecoverableError`).
- Vue [Application API](https://vuejs.org/api/application.html) (`app.config.errorHandler`) and [Composition API lifecycle](https://vuejs.org/api/composition-api-lifecycle.html) (`onErrorCaptured`) — the surfaces Vue does and does not track.
- Sentry [Upload source maps](https://docs.sentry.io/product/sentry-basics/integrate-frontend/upload-source-maps/) (hidden maps + delete-after-upload), [Fingerprint rules](https://docs.sentry.io/concepts/data-management/event-grouping/fingerprint-rules/) / [Issue grouping](https://docs.sentry.io/concepts/data-management/event-grouping/), and [Scrubbing sensitive data](https://docs.sentry.io/platforms/javascript/data-management/sensitive-data/) (`beforeSend`, `sendDefaultPii`).
