# Host reference: React Native WebView

## Contents

- [Sending (web → app)](#sending-web--app)
- [Receiving (app → web)](#receiving-app--web)
- [Loading & lifecycle](#loading--lifecycle)
- [Back button (Android)](#back-button-android)
- [Layout & text](#layout--text)
- [Security](#security)
- [Sources](#sources)

`react-native-webview` — the web page's view of it.

## Sending (web → app)

```js
window.ReactNativeWebView.postMessage(jsonString); // string only
```

- Injected **only when the app sets the `onMessage` prop** — guard for absence.
- App receives it in `onMessage` as `event.nativeEvent.data` (string → parse + validate).
- **Timing:** the global is injected at page-start, but an early synchronous send can
  still miss it — `injectedJavaScriptBeforeContentLoaded` is *not* 100% reliable on
  Android (it can run after the page's own scripts, or not at all on first launch —
  #1609). Have the page buffer messages until `window.ReactNativeWebView` exists, then
  flush; prefer the app passing startup data via `injectedJavaScriptObject` over an
  early bridge round-trip.
- **Detecting the app:** test for `window.ReactNativeWebView`, not the User-Agent — the
  app's custom `userAgent`/`applicationNameForUserAgent` is applied only to the *first*
  page request on Android and reverts to the default UA on later in-funnel navigations
  (#3703, #1971), so a UA-based gate breaks mid-flow.

## Receiving (app → web)

- App calls `injectJavaScript()` (the path shown in official docs) or
  `webViewRef.postMessage()`. For the latter, the dispatch target differs by
  platform in current source: iOS dispatches a `MessageEvent` on `window`
  (`apple/RNCWebViewImpl.m`), Android dispatches on `document`
  (`RNCWebViewManagerImpl.kt`) — a page listening only on `window` silently
  receives nothing on Android. Register the same handler on both `window` and
  `document`. Neither listener is shown in the official guide.
- Prefer not to need this at all (one-way design). If used, validate payload schema —
  and note the race: injected JS runs in whatever page is currently loaded.

## Loading & lifecycle

- `onLoadEnd` fires when the document load **succeeds or fails** — not render-complete,
  not JS-executed. Use a web-sent `READY` message for content-critical screens.
- `startInLoadingState` + `renderLoading` give a native spinner until first load;
  pair with `READY` for the swap when content is client-rendered.

## Back button (Android)

Official pattern: app wires `BackHandler.addEventListener('hardwareBackPress')` →
`webViewRef.goBack()` when `canGoBack` (the official guide tracks it via
`onLoadProgress`; `onNavigationStateChange` also exposes it). Web-side caveats:

- `goBack()` has been reported to silently no-op on some Android devices/WebView
  versions (issue #2810 — a version regression; commenters tie their cases to SPA
  `history.pushState` routing) — don't build multi-page bridge flows that depend on
  webview history.
- Single-screen bridge pages: no navigations → `canGoBack` stays false → the
  `BackHandler` returns false and the OS closes the screen natively, which is the
  desired contract (inference from the official pattern, not a documented contract).

## Layout & text

- `textZoom` prop (Android-only): Android follows system font scale unless set.
  Official docs only show pinning `textZoom={100}`; clamping instead is this skill's
  recommendation to preserve accessibility:
  `textZoom={Math.min(130, fontScale * 100)}`.
- Page meta: `viewport-fit=cover`; app may pass `statusBarHeight` as a query param.
- **White flash on rotation/load is the native layer, not the page.** In
  `react-native-webview` v14 there is no `opaque` prop — opacity is *derived* from the
  WebView `backgroundColor` alpha (`apple/RNCWebViewImpl.m` `setBackgroundColor:` —
  `alpha = CGColorGetAlpha(...); opaque = (alpha == 1.0); self.opaque =
  _webView.opaque = opaque; _webView.backgroundColor = scrollView.backgroundColor =
  bg`), and the default container background is `clearColor`. During a rotation/resize
  the native WKWebView surface repaints before the web layout catches up; a web-side
  `html`/`body` color only applies *after* that repaint, so it can't cover the
  transition frames. Fix on the native side: give the WebView an opaque dark
  `style={{ backgroundColor }}` (plus a matching backing-view color). Scope it per
  page via a prop — don't change a shared WebView wrapper's default.

## Security

- App should set `originWhitelist` (default `http://*`/`https://*`). Avoid `['*']`
  for URI-loaded pages in production — note `source={{ html }}` legitimately requires
  `['*']` per official docs. Treat all `onMessage` data as untrusted.

## Sources

- react-native-webview [Reference](https://github.com/react-native-webview/react-native-webview/blob/master/docs/Reference.md)
  and [Guide](https://github.com/react-native-webview/react-native-webview/blob/master/docs/Guide.md):
  `onMessage`/`postMessage` string contract, `injectedJavaScriptBeforeContentLoaded`,
  `injectedJavaScriptObject`, `injectJavaScript`, `onLoadEnd`, `startInLoadingState`,
  `originWhitelist`, Android `textZoom`.
- Injection timing and User-Agent behavior: issues
  [#1609](https://github.com/react-native-webview/react-native-webview/issues/1609)
  (`injectedJavaScriptBeforeContentLoaded` unreliable on Android),
  [#3703](https://github.com/react-native-webview/react-native-webview/issues/3703) /
  [#1971](https://github.com/react-native-webview/react-native-webview/issues/1971)
  (custom `userAgent` reverts on later in-funnel navigations).
- Back button and renderer lifecycle: React Native
  [`BackHandler`](https://reactnative.dev/docs/backhandler); issues
  [#2810](https://github.com/react-native-webview/react-native-webview/issues/2810)
  (`goBack()` no-op regression),
  [#2199](https://github.com/react-native-webview/react-native-webview/issues/2199)
  (iOS blank WebView after idle) /
  [#2559](https://github.com/react-native-webview/react-native-webview/issues/2559)
  (`onContentProcessDidTerminate` not firing) — iOS renderer death; Android
  `onRenderProcessGone` is covered in [android-webview](./android-webview.md).
- Surface color derived from `backgroundColor` alpha: react-native-webview
  `apple/RNCWebViewImpl.m` (`setBackgroundColor:`).
