---
name: webview-bridge-pages
description: "Use when building the web-page side of a native app WebView (in-app webview / bridge pages) — postMessage-to-native bridge, native close/back and Android hardware-back, first READY/auth message can be missed on cold start (buffer + bounded flush), blank screen after renderer death, query-param render inputs and A/B variants, IAP button stuck disabled, auth/token handoff, safe-area insets and 100vh wrong (svh/dvh), paint/compositing vs hit-test separation, iOS sub-16px input-zoom. Hosts: React Native, WKWebView, Android WebView, Flutter. For first-render router.query/router.isReady readiness in a plain SPA see deeplink-hydration; for token storage / CSP / XSS / SameSite see frontend-security-baseline; for login/returnTo/passkey flows see frontend-auth-flow-contracts."
---

# Webview bridge pages (web side)

Guidance for the **web page** loaded inside a native app WebView — not the app side.
Core principle: **keep the web side dumb** — render from URL params, send one-way
messages through one transport adapter, let native own lifecycle
(open/close/back/result).

## Checklist (apply in order; details in references/)

1. Single transport adapter (below); every message one JSON string `{ type, data? }`;
   plain browser = noop; buffer sends until the host global appears, then flush; gate
   app-only UI on that global, never User-Agent
2. Message `type` constants + payload types in one module, mirrored with app handlers
   → [contract-design](./references/contract-design.md)
3. No inbound (native→web) listener unless justified; if present, validate origin +
   schema, and ignore non-string/non-JSON window messages before parsing bridge JSON
   → [contract-design](./references/contract-design.md)
4. Close/back ownership decided — default: native owns X button and Android back, web
   draws no close UI; layout avoids the native button area via app-passed insets
   → [contract-design](./references/contract-design.md)
5. Never permanently disable action buttons waiting for results the web can't
   observe (purchases); require an explicit native ack/result or a web-side timeout
   → [contract-design](./references/contract-design.md)
6. Loading/`READY` contract decided — required for costly-blank screens (payment,
   critical funnels), skippable for low-stakes ones (a brief blank is cheap); paired with an
   error/timeout policy; re-sent on involuntary reload (renderer death)
   → [contract-design](./references/contract-design.md)
7. Auth/session source decided (none / shared cookie / bridge-injected — never a
   query-param token); never start OAuth/social login inside the webview (embedded
   UAs get `403: disallowed_useragent` — bridge out to the system browser)
   → [contract-design](./references/contract-design.md)
8. Navigation & capabilities policy decided (external links, deep links, downloads,
   file inputs) — don't assume browser behavior; no `window.open`/`target="_blank"`
   (silently dropped without app-side support), and `input[type=file]` dead-taps on
   Android without app-side `onShowFileChooser`
   → [contract-design](./references/contract-design.md)
9. Query parsing centralized with fallbacks for every unknown value; timestamp unit
   agreed; timers recomputed from absolute time; back is usually a full load in
   WebViews (bfcache off/uncertain) — bind funnel/form drafts to `history.state` or
   a `sessionStorage` draft
   → [page-implementation](./references/page-implementation.md)
10. A/B axes orthogonal (one config key → one query param); unknown variant → control
    → [contract-design](./references/contract-design.md)
11. Viewport meta set; `svh`/`dvh` instead of `vh`; insets from app params, not
    `env()` alone; `<meta name="color-scheme">` declared with `prefers-color-scheme`
    styles (Android WebView can auto-invert pages that don't declare a scheme)
    → [page-implementation](./references/page-implementation.md)
12. Layout verified at 130% system font scale (200% on Android 14+); keyboard +
    input-focus zoom (≥16px font) behavior decided → [page-implementation](./references/page-implementation.md)
13. Missing/incorrect visuals split DOM/layout/hit-test/paint/compositing before
    height, padding, timeout, or repaint workarounds → [page-implementation](./references/page-implementation.md)
14. Localized copy containing intentional `\n` line breaks preserves them with
    `white-space: pre-line` — for line-breaking and long-token overflow rules
    (`overflow-wrap`, `word-break`, CJK) see cjk-text-and-input
15. Old Android failures: identify the actual WebView/Chrome engine version, then
    check syntax/API compatibility before treating it as an app or OS regression
16. Legacy fallback work must include a matrix: affected old WebView engine,
    modern Android WebView/Chrome control, and app WebView when bridge/safe-area/deeplink
    integration matters. Record device/API/WebView version, URL environment, screenshots,
    and whether Playwright only forced the fallback branch or an actual engine ran it.

## Shared primitives, not a mega-wrapper

When two or more WebView pages repeat the same host concerns, extract small
primitives instead of copying per-page fixes:

- Transport: `postToNative` (plus a framework wrapper if useful — e.g. a React
  `useBridgePost` hook) with JSON-string messages, noop in a
  plain browser, and optional bounded buffering for first `READY`-style messages.
- Root shell: app-height, safe-area variables, touch/callout defaults, full-width
  WebView root, and page-provided background/className.
- Viewport settling: resize/orientation/visualViewport listeners that only update
  CSS variables or trigger a bounded repaint.

Do not put page-specific query parsing, auth/login, store wiring, payment product
logic, A/B copy, or visual layout into a generic wrapper. If a proposed wrapper
needs many feature flags or knows the page's business terms, keep the behavior local
or extract a narrower hook/component.

## Transport adapter

```js
const BRIDGE_NAME = 'bridge';  // one name agreed in the contract: WKWebView handler + Android interface + Flutter channel (RN uses its own fixed global)
let queue = [];
let host = null;
let tries = 0;
let polling = false;  // re-entry guard: at most ONE poll chain ever live

function resolveHost() {
  if (window.ReactNativeWebView) return window.ReactNativeWebView;             // React Native WebView
  if (window.webkit?.messageHandlers?.[BRIDGE_NAME]) {                         // iOS WKWebView
    return window.webkit.messageHandlers[BRIDGE_NAME];
  }
  if (window[BRIDGE_NAME]?.postMessage) return window[BRIDGE_NAME];            // Android addJavascriptInterface / Flutter channel
  return null;                                                                 // plain browser, or global not injected yet
}

function flushQueue() {
  polling = false;                      // this invocation is the live one; a fresh poll may be re-armed below
  host = host || resolveHost();
  if (!host) {                          // global not injected yet — poll briefly so a lone cold-start message still drains
    if (queue.length && tries++ < 40) { // ~2s cap shared by ALL buffered messages, not ~2s/N — one chain only
      polling = true;
      setTimeout(flushQueue, 50);       // plain browser exhausts tries and stays a noop
    }
    return;
  }
  for (const json of queue) host.postMessage(json);  // FIFO; queue cleared below so nothing double-sends
  queue = [];
}

function postToNative(message) {
  if (!host && tries >= 40 && queue.length >= 20) queue.shift();  // poll gave up (plain browser) — cap the dead buffer instead of growing forever
  queue.push(JSON.stringify(message));  // single JSON string: lowest common denominator across hosts
  if (host || !polling) flushQueue();   // drain now if host is ready; otherwise only kick the poll if none is already live
}
```

The adapter sends one JSON string (WKWebView accepts any JSON-serializable body, but
RN/Android/Flutter accept strings only) and **buffers, polling briefly until the host
global appears**, so the first `READY`/auth/analytics message is less likely to be dropped on cold
start — the global is usually wired at page-start but can still be absent when the first message fires
(if the app exposes a `bridge-ready` event, drive `flushQueue` from it instead of the
poll). Detect the host by this **presence check, never User-Agent sniffing** (WebView
UAs are Safari-shaped and apps override them) — the same signal gates app-only UI like
hiding the close chrome. Per-host injection-timing caveats (Android
`injectedJavaScriptBeforeContentLoaded`) → [react-native](./references/react-native.md).

## Legacy Android WebView compatibility

Split legacy failures into two tracks and keep the fixes separate so modern
browsers do not inherit old-engine workarounds: a page blank *before* the JS
framework hydrates is a JavaScript syntax/runtime-API suspect; a page that
renders with wrong spacing/paint is a CSS feature/viewport/compositing suspect.
Never verify legacy support against a dev server (`next dev`/HMR or any bundler
dev mode): the framework's dev runtime and untranspiled `node_modules` ship
modern syntax your `browserslist` target does not downlevel, and Pages-Router
dev leaves the `style[data-next-hide-fouc]` `body{display:none}` guard behind in
old-WebView HMR — treat both as dev-runtime evidence, not a product regression.
Iterate layout on a modern WebView; run the engine and app-integration tiers
against a production build or deployed environment. Details (polyfill placement
via `beforeInteractive`, old-engine `postMessage` `targetOrigin`, the
`data-legacy-webview` CSS marker discipline):
[android-webview](./references/android-webview.md).

## Legacy Android WebView verification matrix

Use three tiers, and say which tiers ran. For the full evidence model and reporting
template, read [regression-testing](./references/regression-testing.md).

1. **Fast branch check:** Playwright/mobile browser same viewport, with and without the
   feature-detection marker. Good for as-is/to-be screenshots, not sufficient for
   engine compatibility.
2. **Engine check:** Android emulator or WebView Shell on the affected WebView/Chrome
   version. Capture console, screenshot, device/API/WebView version, and loaded URL.
3. **App integration check:** real app WebView when RN bridge, safe-area params,
   deep links, auth, or QA hidden menus are part of the claim.

At minimum, cover the affected old engine plus one modern Android control. If results
differ across devices, report by WebView/Chrome version first and Android OS/device
second; WebView updates can make same-OS devices behave differently.

## iOS Simulator and WKWebView evidence

Separate direct URL and app evidence. For the full evidence model and reporting
template, read [regression-testing](./references/regression-testing.md).

1. **Simulator Safari/WebKit smoke:** open the web URL in iOS Simulator Safari to check WebKit layout, viewport, and text wrapping. This does not establish app bridge, injected safe-area params, auth, or native lifecycle.
2. **App WKWebView integration:** open the installed app through a deeplink or QA route when bridge/safe-area/auth/native behavior is part of the claim. On iOS 16.4+, app-side `WKWebView.isInspectable = true` may be required for Safari Web Inspector.
3. **Physical device:** use for release candidates or issues involving payments, keyboard, notch/safe-area, GPU/compositing, or hardware-specific rendering.

When reporting iOS evidence, label it as Safari/WebKit simulator, app WKWebView simulator, or physical device.

## Android rotation / viewport settling

For Android WebView rotation or tablet/foldable resize glitches, first separate two
failure classes:

- Native surface flash/blank: WebView layer briefly paints white/blank. Native
  `backgroundColor` / container styling can hide only this class — on RN, opacity
  derives from the WebView `backgroundColor` alpha, see
  [react-native](./references/react-native.md); on raw WKWebView see
  [wkwebview](./references/wkwebview.md).
- DOM alignment drift: content keeps an old layout or visual viewport for a frame.
  Fix this in the page: avoid a narrow root combined with inner `100vw`; make the
  root track the WebView viewport and constrain inner content with `max-width`.

When DOM alignment depends on viewport dimensions, observe `window.resize`,
`orientationchange`, and `window.visualViewport.resize` when available, then re-read
viewport size after the next animation frame or a short settle delay. Do not document
page-specific CSS transforms as a general fix.

## PR-worthiness gate

Require evidence from the host tier implicated by the claim: browser-only
layout evidence cannot establish native bridge or lifecycle behavior, and an
app tap cannot establish missing paint. Capture the URL/params, host and engine version,
bridge/lifecycle sequence, and layout/paint/hit-test evidence before selecting
the smallest web-side fix.

Reject weak findings: User-Agent-only WebView detection, a desktop-browser
simulation presented as app integration proof, a native-host responsibility
rewritten into a web mega-wrapper, a one-frame blank on a low-stakes page with
no product impact, or a forced fallback branch presented as old-engine
compatibility evidence.

## Output shape

Report the host and engine, page URL/inputs, ownership boundary, exact
bridge/lifecycle/layout/paint/hit-test evidence, verification tier reached,
smallest web-side change, and any native-app test still required.

## References

| File | Covers |
|------|--------|
| [contract-design](./references/contract-design.md) | Message contract, close/back ownership, unobservable results, READY + error policy, auth handoff, navigation policy, A/B variants |
| [page-implementation](./references/page-implementation.md) | Query parsing on SPA hydration, timers, viewport/safe-area/keyboard/font scale |
| [react-native](./references/react-native.md) · [wkwebview](./references/wkwebview.md) · [android-webview](./references/android-webview.md) · [flutter](./references/flutter.md) | Host APIs, version caveats, quirks |
| [regression-testing](./references/regression-testing.md) | WebView evidence tiers, Android/iOS actual-engine workflow, reporting template |

Sources are listed in each reference file.
