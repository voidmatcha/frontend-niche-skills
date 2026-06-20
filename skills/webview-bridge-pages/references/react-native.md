# Host reference: React Native WebView

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
  `webViewRef.postMessage()`. For the latter, the page listens via
  `window.addEventListener('message', ...)` — community-documented, not in the
  official guide; historically some Android versions dispatched on `document` instead.
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
  desired contract (inference from the official pattern, not a documented guarantee).

## Layout & text

- `textZoom` prop (Android-only): Android follows system font scale unless set.
  Official docs only show pinning `textZoom={100}`; clamping instead is this skill's
  recommendation to preserve accessibility:
  `textZoom={Math.min(130, fontScale * 100)}`.
- Page meta: `viewport-fit=cover`; app may pass `statusBarHeight` as a query param.

## Security

- App should set `originWhitelist` (default `http://*`/`https://*`). Avoid `['*']`
  for URI-loaded pages in production — note `source={{ html }}` legitimately requires
  `['*']` per official docs. Treat all `onMessage` data as untrusted.
