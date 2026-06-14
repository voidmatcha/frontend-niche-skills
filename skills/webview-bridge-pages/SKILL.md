---
name: webview-bridge-pages
description: "Use when building the web-page side of a native app WebView (in-app webview / bridge pages) — bridge messaging, native close/back, READY loading signals, query-param variants, auth handoff, safe-area/viewport/font-scale layout. Hosts: React Native, WKWebView, Android WebView, Flutter."
---

# Webview bridge pages (web side)

Guidance for the **web page** loaded inside a native app WebView — not the app side.
Core principle: **keep the web side dumb** — render from URL params, send one-way
messages through one transport adapter, let native own lifecycle
(open/close/back/result).

## Checklist (apply in order; details in references/)

1. Single transport adapter (below); every message one JSON string `{ type, data? }`;
   plain browser = noop
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
6. Loading/`READY` contract decided — or consciously skipped (document load ≠ render);
   paired with an error/timeout policy
   → [contract-design](./references/contract-design.md)
7. Auth/session source decided (none / cookies / bridge-injected / header) — no tokens
   in query params → [contract-design](./references/contract-design.md)
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
12. Layout verified at 130% system font scale (200% on Android 14+); keyboard
    behavior decided → [page-implementation](./references/page-implementation.md)

## Transport adapter

```js
function postToNative(message) {
  const json = JSON.stringify(message);
  if (window.ReactNativeWebView) {                       // React Native WebView
    return window.ReactNativeWebView.postMessage(json);
  }
  if (window.webkit?.messageHandlers?.bridge) {          // iOS WKWebView (handler name agreed with app)
    return window.webkit.messageHandlers.bridge.postMessage(json);
  }
  if (window.NativeBridge?.postMessage) {                // Android addJavascriptInterface / Flutter channel
    return window.NativeBridge.postMessage(json);
  }
  // No native host (plain browser): intentionally a noop.
  // Add debug logging behind your framework's own dev flag if useful.
}
```

Always send a single JSON string — the lowest common denominator (WKWebView accepts
any JSON-serializable body; RN/Android/Flutter accept strings only). The injected
global only exists when the app registers a handler.

## References

| File | Covers |
|------|--------|
| [contract-design](./references/contract-design.md) | Message contract, close/back ownership, unobservable results, READY + error policy, auth handoff, navigation policy, A/B variants |
| [page-implementation](./references/page-implementation.md) | Query parsing on SPA hydration, timers, viewport/safe-area/keyboard/font scale |
| [react-native](./references/react-native.md) · [wkwebview](./references/wkwebview.md) · [android-webview](./references/android-webview.md) · [flutter](./references/flutter.md) | Host APIs, version caveats, quirks |

Sources are listed in each reference file.
