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
- Renderer death: WebContent can be killed under memory pressure
  (`webViewWebContentProcessDidTerminate`; native typically reloads). The page
  comes back with all JS state lost — re-derive from query params and re-send
  `READY` on every load; full recovery contract → [contract-design](./contract-design.md).

## Media

- iPhone WKWebView media defaults differ from Safari: `allowsInlineMediaPlayback`
  defaults to **false** on iPhone (`<video>` without `playsinline` hijacks into the
  fullscreen player) and `mediaTypesRequiringUserActionForPlayback` blocks autoplay.
  Web-side rule: always set `playsinline` (+ `muted` for autoplay intent); don't ship
  controls-less autoplay video unless the app-side config is agreed in the contract.

## Layout

- `env(safe-area-inset-*)` **works natively** in WKWebView with
  `viewport-fit=cover` — but if the same page also runs on Android WebView, don't
  rely on it alone; take app-passed insets as the canonical source.
- Keyboard: iOS overlays by default; visual viewport shrinks, layout viewport doesn't.
- Surface color on rotation/scroll-bounce: `WKWebView` is opaque with a white
  background by default. Set `isOpaque = false`, `backgroundColor`, and (iOS 15+)
  `underPageBackgroundColor` to control the color shown while the surface repaints —
  a web `html`/`body` color only takes effect after the web layout repaints. (In
  `react-native-webview` this is driven by the RN `backgroundColor` prop — see
  [react-native](./react-native.md).)

## Sources

- Apple Developer: [`WKWebView`](https://developer.apple.com/documentation/webkit/wkwebview),
  [`WKUserContentController`](https://developer.apple.com/documentation/webkit/wkusercontentcontroller)
  (`add(_:name:)` / `add(_:contentWorld:name:)`),
  [`WKScriptMessageHandlerWithReply`](https://developer.apple.com/documentation/webkit/wkscriptmessagehandlerwithreply)
  (reply handler; the JS `postMessage` Promise behavior is per WebKit source/release notes),
  [`WKNavigationDelegate`](https://developer.apple.com/documentation/webkit/wknavigationdelegate)
  (`didFinish` = navigation complete, not render), and
  [`underPageBackgroundColor`](https://developer.apple.com/documentation/webkit/wkwebview/underpagebackgroundcolor)
  / `isOpaque` for surface color while the layer repaints.
- `env(safe-area-inset-*)` with `viewport-fit=cover`, keyboard visual-viewport
  behavior, and iOS input-zoom anchors → [page-implementation](./page-implementation.md) Sources.
- Media defaults: [`allowsInlineMediaPlayback`](https://developer.apple.com/documentation/webkit/wkwebviewconfiguration/allowsinlinemediaplayback)
  (false on iPhone), `mediaTypesRequiringUserActionForPlayback`; WebKit blog
  ["New &lt;video&gt; Policies for iOS"](https://webkit.org/blog/6784/new-video-policies-for-ios/).
