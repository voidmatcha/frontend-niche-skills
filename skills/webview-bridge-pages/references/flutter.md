# Host reference: Flutter webview_flutter

`webview_flutter` — the web page's view of it.

## Sending (web → app)

App registers a JavaScript channel (`addJavaScriptChannel('ChannelName', ...)`);
the page then calls:

```js
window.ChannelName.postMessage(jsonString); // string only
```

- The official example calls `ChannelName.postMessage(...)` (no `window.` prefix);
  the `window.` form works on both platforms and is what the transport adapter uses.
- On Android this is implemented with `addJavascriptInterface` under the hood
  (a `@JavascriptInterface postMessage(String)` method) — so the same security
  caveats apply: injected into frames, no origin control, treat as untrusted natively.
- On iOS it registers a `WKUserContentController` script message handler, plus an
  injected at-document-start alias `window.<name> = webkit.messageHandlers.<name>`
  so the same `window.<name>.postMessage(...)` call shape works.
- Channel name is part of the contract — agree on one generic name (e.g. `NativeBridge`)
  so the universal transport adapter works unchanged.
- **Timing:** `webview_flutter` registers the channel at document-start (Android
  `addJavascriptInterface`, iOS a document-start `WKUserScript`), so `window.ChannelName`
  is normally present before your scripts run — but if the host adds the channel late or
  under a different name, an early `window.ChannelName.postMessage` hits `undefined`. The
  adapter's buffer-until-`window.ChannelName`-exists guard covers that race.

## Receiving (app → web)

- App calls `runJavaScript()` / `runJavaScriptReturningResult()`.
- Same guidance: prefer one-way; validate anything inbound.

## Loading & lifecycle

- `NavigationDelegate.onPageFinished` — official docs say only "invoked when a page
  has finished loading"; it maps to the platform load callbacks
  (`WebViewClient.onPageFinished` / `didFinish`), so it is **not** a render/hydration
  signal. Use a web-sent `READY` message for content-critical screens.
- `onWebResourceError` catches load failures, but not broken-but-200 JS bundles —
  another reason `READY` + timeout is the robust pattern.

## Back button

- Flutter apps typically intercept the system back (`PopScope`) and decide between
  `controller.goBack()` and closing the route — same rule as other hosts: single-screen
  bridge pages should not depend on webview history; native closes.

## Layout

- On Android, `webview_flutter` renders through the system Android WebView, so the
  notes in [android-webview.md](./android-webview.md) apply (viewport meta, the
  `env(safe-area-inset-*)` support timeline, `textZoom`/font scale). Take insets from
  app-passed params.
