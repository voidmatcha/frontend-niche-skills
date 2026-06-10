# Host reference: iOS WKWebView

`WKWebView` + `WKUserContentController` — the web page's view of it.

## Sending (web → app)

```js
window.webkit.messageHandlers.<name>.postMessage(body);
```

- `<name>` is whatever the app registered on `WKUserContentController` —
  `add(_:name:)` / `add(_:contentWorld:name:)` for plain handlers,
  `addScriptMessageHandler(_:contentWorld:name:)` for reply-capable ones.
  Agree on the name in the contract.
- Unlike other hosts, `body` may be any JSON-serializable value (bridged to
  NSNumber/NSString/NSDate/NSArray/NSDictionary/NSNull). For cross-host contracts
  still send a JSON **string**.
- The handler function is injected into **all frames** for the given content world.
- Guard for absence: `window.webkit?.messageHandlers?.<name>` is undefined in plain
  browsers and when the app didn't register the handler.

## Request/reply (iOS 14+)

`WKScriptMessageHandlerWithReply` makes `postMessage(...)` return a **Promise** that
resolves with the native reply (or rejects with an error message). Apple's doc page
describes only the native `replyHandler` side; the JS Promise behavior is per the
WebKit source/release notes. Useful when iOS is the only host; avoid in cross-host
contracts (RN/Android/Flutter have no equivalent in the same call shape).

## Receiving (app → web)

- App calls `evaluateJavaScript` or injects `WKUserScript`s
  (`addUserScript`, timing: at-document-start/end).
- Same guidance: prefer one-way; validate anything inbound.

## Loading & lifecycle

- `WKNavigationDelegate.didFinish` = navigation complete, not render/hydration
  complete. Use a web-sent `READY` message for content-critical screens.
- `allowsBackForwardNavigationGestures` enables edge-swipe history navigation —
  irrelevant for single-screen bridge pages (history stays empty).

## Layout

- `env(safe-area-inset-*)` **works natively** in WKWebView with
  `viewport-fit=cover` — but if the same page also runs on Android WebView, don't
  rely on it alone; take app-passed insets as the canonical source.
- Keyboard: iOS overlays by default; visual viewport shrinks, layout viewport doesn't.
