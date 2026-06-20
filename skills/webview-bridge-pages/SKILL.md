---
name: webview-bridge-pages
description: "Use when building the web-page side of a native app WebView (in-app webview / bridge pages) — postMessage-to-native bridge, native close/back and Android hardware-back, multi-step funnel back, the first READY/auth/analytics message silently dropped on cold start (bridge global not ready → buffer + flush), blank screen after renderer death (onRenderProcessGone / webViewWebContentProcessDidTerminate), READY-vs-blank-cold-load signal, query-param render inputs and A/B variants, purchase/IAP button stuck disabled, auth/token handoff (never in query params), safe-area insets, 100vh wrong (svh/dvh), iOS input-zoom on sub-16px font, Android system-font-scale and overscroll layout breakage. Hosts: React Native, WKWebView, Android WebView, Flutter. Native-WebView bridge + inbound-origin scope; for first-render router.query/router.isReady readiness in a plain SPA see deeplink-hydration; for token storage / CSP / XSS / SameSite see frontend-security-baseline; for login/returnTo/passkey flows see frontend-auth-flow-contracts."
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
   schema → [contract-design](./references/contract-design.md)
4. Close/back ownership decided — default: native owns X button and Android back, web
   draws no close UI; layout avoids the native button area via app-passed insets
   → [contract-design](./references/contract-design.md)
5. Never permanently disable action buttons waiting for results the web can't
   observe (purchases); require an explicit native ack/result or a web-side timeout
   → [contract-design](./references/contract-design.md)
6. Loading/`READY` contract decided — required for costly-blank screens (payment,
   onboarding), skippable for low-stakes ones (document load ≠ render); paired with an
   error/timeout policy; re-sent on involuntary reload (renderer death)
   → [contract-design](./references/contract-design.md)
7. Auth/session source decided (none / shared cookie / bridge-injected — never a
   query-param token) → [contract-design](./references/contract-design.md)
8. Navigation & capabilities policy decided (external links, deep links, downloads,
   file inputs) — don't assume browser behavior
   → [contract-design](./references/contract-design.md)
9. Query parsing centralized with fallbacks for every unknown value; timestamp unit
   agreed; timers recomputed from absolute time
   → [page-implementation](./references/page-implementation.md)
10. A/B axes orthogonal (one config key → one query param); unknown variant → control
    → [contract-design](./references/contract-design.md)
11. Viewport meta set; `svh`/`dvh` instead of `vh`; insets from app params, not
    `env()` alone → [page-implementation](./references/page-implementation.md)
12. Layout verified at 130% system font scale (200% on Android 14+); keyboard +
    input-focus zoom (≥16px font) behavior decided → [page-implementation](./references/page-implementation.md)

## Transport adapter

```js
const BRIDGE_NAME = 'bridge';  // one name agreed in the contract: WKWebView handler + Android interface + Flutter channel (RN uses its own fixed global)
let queue = [];
let host = null;
let tries = 0;

function resolveHost() {
  if (window.ReactNativeWebView) return window.ReactNativeWebView;             // React Native WebView
  if (window.webkit?.messageHandlers?.[BRIDGE_NAME]) {                         // iOS WKWebView
    return window.webkit.messageHandlers[BRIDGE_NAME];
  }
  if (window[BRIDGE_NAME]?.postMessage) return window[BRIDGE_NAME];            // Android addJavascriptInterface / Flutter channel
  return null;                                                                 // plain browser, or global not injected yet
}

function flushQueue() {
  host = host || resolveHost();
  if (!host) {                          // global not injected yet — poll briefly so a lone cold-start message still drains
    if (queue.length && tries++ < 40) setTimeout(flushQueue, 50);  // ~2s cap; plain browser exhausts tries and stays a noop
    return;
  }
  for (const json of queue) host.postMessage(json);  // FIFO; queue cleared below so nothing double-sends
  queue = [];
}

function postToNative(message) {
  queue.push(JSON.stringify(message));  // single JSON string: lowest common denominator across hosts
  flushQueue();                         // drains now if the host is ready, else the poll in flushQueue drains it once it appears
}
```

The adapter sends one JSON string (WKWebView accepts any JSON-serializable body, but
RN/Android/Flutter accept strings only) and **buffers, polling briefly until the host
global appears**, so the first `READY`/auth/analytics message isn't dropped on cold
start — the global is wired at page-start but can be absent when your first message fires
(if the app exposes a `bridge-ready` event, drive `flushQueue` from it instead of the
poll). Detect the host by this **presence check, never User-Agent sniffing** (WebView
UAs are Safari-shaped and apps override them) — the same signal gates app-only UI like
hiding the close chrome. Per-host injection-timing caveats (Android
`injectedJavaScriptBeforeContentLoaded`) → [react-native](./references/react-native.md).

## References

| File | Covers |
|------|--------|
| [contract-design](./references/contract-design.md) | Message contract, close/back ownership, unobservable results, READY + error policy, auth handoff, navigation policy, A/B variants |
| [page-implementation](./references/page-implementation.md) | Query parsing on SPA hydration, timers, viewport/safe-area/keyboard/font scale |
| [react-native](./references/react-native.md) · [wkwebview](./references/wkwebview.md) · [android-webview](./references/android-webview.md) · [flutter](./references/flutter.md) | Host APIs, version caveats, quirks |

Sources are listed in each reference file.
