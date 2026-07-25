---
name: iframe-embed-contracts
description: "Use when a web app embeds a third-party page or is itself shipped as an iframe/widget and the host-guest contract fails: a blank frame from frame-ancestors/X-Frame-Options, postMessage with wildcard targetOrigin or no origin/source/schema validation, the first READY/init message lost, height-resize loops or flickering scrollbars, sandbox tokens blocking forms/popups/downloads or collapsing isolation, iframe allow/Permissions-Policy blocking fullscreen/camera/microphone/payment, third-party cookie or partitioned-storage changes breaking sign-in, or listeners/observers surviving frame navigation and teardown. Browser iframe/embed scope; use webview-bridge-pages for native app WebViews, payment-page-client-security for hosted payment fields/PAN boundaries, and frontend-security-baseline for site-wide CSP/cookie/security policy."
---

# Iframe embed contracts

An iframe integration has two applications and one browser boundary. Treat the parent and guest as separate deploys with an explicit protocol: who may embed whom, which capabilities are delegated, how readiness and messages are authenticated, how size and navigation are synchronized, and what happens when storage or the frame disappears.

## Checklist

1. **Classify both sides before editing.** Record whether you own the parent, guest, or both; the exact origins in every environment; whether the frame is same-origin, cross-origin, `srcdoc`, or sandboxed to an opaque origin; and whether the guest must support more than one parent. Do not infer a cross-origin frame's health from DOM access that the same-origin policy intentionally blocks.
2. **Inspect the delivered frame policy, not only JSX.** Capture the final `<iframe>` attributes and the guest response headers. The parent controls where frames may load (`frame-src`), while the guest controls who may embed it (`frame-ancestors`, with `X-Frame-Options` only as a legacy fallback). `frame-ancestors` is HTTP-header-only and does not fall back to `default-src`; a meta CSP cannot prove the production embedding contract.
3. **Make readiness a replayable handshake.** `load` is not success: browsers fire it even when the frame's resource failed, and a guest can post READY before the parent listener attaches. Register the listener before setting `src`, let the guest emit `{type, version, instanceId}` READY, let the parent answer with bounded init/config, and keep a timeout/diagnostic state instead of a permanent spinner. If either side may reload or navigate, make READY and init idempotent.
4. **Authenticate every message in both directions.** Send with an exact `targetOrigin`; on receive, verify `event.origin`, `event.source === iframe.contentWindow` (or the expected parent window), message type/version, and payload schema before acting. An origin allowlist alone is insufficient when several frames share it. A sandboxed `srcdoc`/opaque guest reports origin `null`; if that architecture is unavoidable, bind the channel to the exact `source` plus an unguessable per-instance nonce or transferred `MessagePort`, and expose minimal capabilities rather than accepting every `null` sender.
5. **Grant the minimum sandbox and feature capabilities.** Start from a restricted `sandbox` and add only required tokens. For same-origin content, `allow-scripts` plus `allow-same-origin` lets the guest remove its sandbox, so untrusted active content belongs on a separate origin. Browser features need both layers: the response `Permissions-Policy` sets the outer ceiling and the iframe `allow` attribute may narrow/delegate within it. Test forms, popups, downloads, fullscreen, camera/microphone, clipboard, and top navigation only if the product actually needs them.
6. **Treat dynamic sizing as a bounded protocol.** A cross-origin parent cannot read guest layout. Reserve an initial box to avoid CLS, observe the guest's actual content box with `ResizeObserver`, coalesce messages to one animation frame, include an instance/sequence id, and clamp the height in the parent to sane min/max values. Do not use the guest document's viewport-bounded `scrollHeight` as the only shrink signal: after the parent grows the iframe, that value can stay pinned to the larger viewport and create a parent resize -> guest measurement feedback loop. Test growth and shrink, fonts/images/async content, hidden-to-visible transitions, and mobile widths. Use a maintained resizer library when its protocol fits rather than copying a partial snippet.
7. **Design for partitioned storage and blocked third-party cookies.** An embedded guest may not see the same cookies/storage it sees top-level. Prefer an explicit parent-to-guest session exchange with short-lived, audience-bound data over long-lived tokens in the URL. If unpartitioned cookie access is essential, the Storage Access API is permission- and user-activation-dependent; provide a top-level sign-in or recovery path and test denial.
8. **Make navigation and teardown observable.** Remove `message` listeners, `ResizeObserver`s, timers, and channels when the frame unmounts or the instance id changes. Revalidate origin/source after guest navigation. Expose guest error/timeout states to the parent, but do not treat the iframe `load` event as authoritative failure evidence.
9. **Preserve accessibility and performance contracts.** Give every meaningful frame a concise `title`; reserve dimensions; lazy-load only below-the-fold, non-critical frames; and provide an equivalent link/fallback when the embedded surface is not the only way to complete a critical task.

## Quick probes

Use matches as leads, then trace the parent and guest together:

```sh
rg -n "<iframe|createElement\\(['\"]iframe|srcDoc|srcdoc|sandbox=|allow=" src/ app/ packages/ 2>/dev/null
rg -n "postMessage|addEventListener\\(['\"]message|MessageChannel|MessagePort|event\\.origin|event\\.source" src/ app/ packages/ 2>/dev/null
rg -n 'ResizeObserver|scrollHeight|offsetHeight|frame-ancestors|X-Frame-Options|frame-src|Permissions-Policy|requestStorageAccess' . 2>/dev/null
curl -sSI https://guest.example.test/embed | rg -i 'content-security-policy|x-frame-options|permissions-policy|set-cookie|cross-origin'
```

## Boundary with sibling skills

- Use **iframe-embed-contracts** for the browser parent/guest protocol: embeddability, sandbox/`allow`, READY/init, `postMessage`, dynamic size, partitioned storage, navigation, and teardown.
- Use **webview-bridge-pages** when the host is WKWebView, Android WebView, React Native WebView, or Flutter and JavaScript is talking to native code rather than `window.parent`.
- Use **frontend-security-baseline** for site-wide CSP, XSS, cookies/tokens, cross-origin isolation, and security-header rollout; this skill consumes those policies at the embed boundary.
- Use **payment-page-client-security** when the iframe owns card fields or the question is PAN/CVV visibility, runtime payment scripts, or PCI evidence.
- Use **core-web-vitals-performance-contracts** when the primary finding is page-level CLS/LCP/INP attribution; this skill owns the iframe sizing protocol that may cause the shift.
- Use **a11y-contract-testing** for rendered role/name/focus/state assertions beyond the iframe's required accessible title and fallback route.

## PR-worthiness gate

Count a finding only when the host-guest contract is concrete and reproducible:

- a message receiver accepts the wrong origin or wrong frame source, or a sender leaks data through `targetOrigin="*"`;
- READY/init can be lost or duplicated across listener order, reload, or navigation;
- sandbox/`allow`/response policy blocks a required capability or grants an unnecessary high-risk one;
- cross-origin sizing loops, flickers, or shifts layout because the protocol is unbounded or missing;
- embedded authentication fails under partitioned/blocked third-party storage with no recovery path;
- listeners, observers, or timers survive teardown and mutate the next frame instance.

Reject weak findings: a wildcard used only to bootstrap an opaque-origin guest when `source` + nonce/port + schema are verified; a static fixed-size media frame that needs no messaging; a resizer library already validating origin and instance ids; or a same-origin internal frame whose parent intentionally owns the DOM. Minimal useful PR: one host/guest regression test covering the failing sequence plus the smallest protocol or policy change.

## Verification

Use two real origins in browser tests (different ports are different origins). Cover:

- allowed parent loads the guest; disallowed parent gets the expected policy failure;
- wrong origin, wrong `source`, unknown type/version, and malformed payload are ignored;
- early, delayed, duplicate, and post-navigation READY converge to one init state;
- content growth/shrink produces bounded stable height without a feedback loop or CLS spike;
- sandbox and `allow` grant only the required product features;
- storage denial has a visible top-level recovery path;
- unmount/navigation removes listeners, observers, timers, and stale instance messages;
- frame has an accessible `title` and a usable fallback for a critical flow.

This repository includes a live regression fixture at
[`tests/iframe-contract.bats`](./tests/iframe-contract.bats). It starts parent
and guest servers on distinct loopback ports and, when the Playwright CLI plus
its Chromium browser are installed, checks the authenticated replayable
handshake, wrong-source/origin rejection, bounded grow-and-shrink sizing,
listener teardown, accessible title, and a `frame-ancestors` rejection from a
disallowed parent origin. The Bats test skips cleanly when the Playwright CLI is
unavailable; source/audit checks still run.

## Output shape

- **Role/origins**: parent owner, guest owner, exact origins, sandbox/origin mode.
- **Contract**: embed-policy / handshake / message-auth / capability / sizing / storage / teardown.
- **Evidence**: parent and guest file/line, delivered attributes/headers, and the failing sequence.
- **Risk**: blank embed, spoofed command/data leak, broken capability, resize loop/CLS, lost auth, or stale listener.
- **Fix + verification**: smallest two-sided protocol/policy change and the browser test that covers the failure.

## Sources

- MDN, `<iframe>` — sandbox tokens, `allow`, lazy loading, same-origin rules, load/error behavior, and accessible titles: <https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/iframe>
- MDN, `Window.postMessage()` — exact `targetOrigin`, `origin`/`source` validation, payload validation, and structured cloning: <https://developer.mozilla.org/en-US/docs/Web/API/Window/postMessage>
- WHATWG HTML, cross-document messaging — normative `postMessage` and `MessageEvent` behavior: <https://html.spec.whatwg.org/multipage/web-messaging.html>
- MDN, Permissions Policy — header policy plus iframe `allow` delegation: <https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Permissions_Policy>
- MDN, CSP `frame-ancestors` — guest-controlled parent allowlist, no `default-src` fallback, HTTP-header-only: <https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/frame-ancestors>
- MDN, Storage Access API — embedded access to unpartitioned cookies and its permission/user-activation model: <https://developer.mozilla.org/en-US/docs/Web/API/Storage_Access_API>
- `ctxr-dev/skill-frontend-excellence`, Embed Patterns (MIT) — prior-art host/guest checklist covering sandboxing, messaging, sizing, storage, CSP, and accessibility: <https://github.com/ctxr-dev/skill-frontend-excellence/blob/bcdd3a5fee4723e8ec1d206a5e3bf1553afa5b53/references/embed-patterns.md>
- [Prior-art and evidence snapshot](./references/prior-art.md) — bounded public GitHub/web searches, overlapping public skills, real issue examples, and the local retention decision.
- `davidjbradshaw/iframe-resizer` — maintained cross-domain resize protocol and failure handling prior art: <https://github.com/davidjbradshaw/iframe-resizer>
- WHATWG HTML issue #555 — long-running platform gap for automatic iframe sizing: <https://github.com/whatwg/html/issues/555>
- Shopify embedded-app issue #3214 — real postMessage origin mismatch producing a blank iframe: <https://github.com/Shopify/shopify-app-js/issues/3214>
- Enketo issue #1515 — real demand for robust postMessage-based dynamic iframe sizing: <https://github.com/enketo/enketo/issues/1515>
