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
- **Timing:** the global is injected at page-start, but an early synchronous send can still miss it — `injectedJavaScriptBeforeContentLoaded` is *not* 100% reliable on Android (it can run after the page's own scripts; some reports say not at all, or only on first launch — #1609, closed unfixed; checked 2026-09-24). Have the page buffer messages until `window.ReactNativeWebView` exists, then flush; prefer the app passing startup data via `injectedJavaScriptObject` over an early bridge round-trip.
- **Detecting the app:** test for `window.ReactNativeWebView`, not the User-Agent — the app's custom `userAgent`/`applicationNameForUserAgent` has been reported to apply only to the *first* page request on Android and revert to the default UA on later in-funnel navigations (#3703, reproduced only in Android production APK/AAB builds; #1971, `applicationNameForUserAgent`), so a UA-based gate can break mid-flow.

## Receiving (app → web)

- App calls `injectJavaScript()` (the path shown in official docs) or `webViewRef.postMessage()`. For the latter, the dispatch target differs by platform in the pinned source: iOS dispatches a `MessageEvent` on `window` (`apple/RNCWebViewImpl.m`), Android dispatches on `document` (`RNCWebViewManager.kt`) — a page listening only on `window` silently receives nothing on Android. Register the same handler on both `window` and `document`. Neither listener is shown in the official guide.
- Prefer not to need this at all (one-way design). If used, validate payload schema — and note the race: injected JS runs in whatever page is currently loaded.

## Loading & lifecycle

- `onLoadEnd` fires when the document load **succeeds or fails** — not render-complete, not JS-executed. Use a web-sent `READY` message for content-critical screens.
- `startInLoadingState` + `renderLoading` give a native spinner until first load; pair with `READY` for the swap when content is client-rendered.

## Back button (Android)

Official pattern: app wires `BackHandler.addEventListener('hardwareBackPress')` → `webViewRef.goBack()` when `canGoBack` (the official guide tracks it via `onLoadProgress`; `onNavigationStateChange` also exposes it). Web-side caveats:

- `goBack()` has been reported to silently no-op on some Android devices/WebView versions (issue #2810 — a version regression; commenters tie their cases to SPA `history.pushState` routing) — don't build multi-page bridge flows that depend on webview history.
- Single-screen bridge pages: no navigations → `canGoBack` stays false → the `BackHandler` returns false and the OS closes the screen natively, which is the desired contract (inference from the official pattern, not a documented contract).

## Layout & text

- `textZoom` prop (Android-only): Android follows system font scale unless set. Official docs only show pinning `textZoom={100}`. Pinning or capping is an app-owned accessibility trade-off, not a default: aim for a layout that tolerates the full system range (up to 200% on Android 14+). If the app does cap, derive the cap from the layout's verified tolerance, get an accessibility review, and record it in the contract — don't hard-code a low ceiling such as 130.
- Page meta: `viewport-fit=cover`; app may pass `statusBarHeight` as a query param.
- **White flash on rotation/load is the native layer, not the page.** At the pinned `react-native-webview` v16.0.0 source there is no `opaque` prop — opacity is *derived* from the WebView `backgroundColor` alpha (`apple/RNCWebViewImpl.m` `setBackgroundColor:` computes `alpha` with `CGColorGetAlpha`, sets `opaque` to `alpha == 1.0` on both the container and the WKWebView, then applies the color to `_webView.scrollView` and `_webView`), and the default container background is `clearColor`. During a rotation/resize the native WKWebView surface repaints before the web layout catches up; a web-side `html`/`body` color only applies *after* that repaint, so it can't cover the transition frames. Fix on the native side: give the WebView an opaque dark `style={{ backgroundColor }}` (plus a matching backing-view color). Scope it per page via a prop — don't change a shared WebView wrapper's default.

## Security

- App should set `originWhitelist` (default `http://*`/`https://*`). Avoid `['*']` for URI-loaded pages in production — note `source={{ html }}` legitimately requires `['*']` per official docs. Treat all `onMessage` data as untrusted.

## Sources

- react-native-webview [Reference](https://github.com/react-native-webview/react-native-webview/blob/d65a961080dad3e82d33370ad6e8d90e973fcbd3/docs/Reference.md) and [Guide](https://github.com/react-native-webview/react-native-webview/blob/d65a961080dad3e82d33370ad6e8d90e973fcbd3/docs/Guide.md): `onMessage`/`postMessage` string contract, `injectedJavaScriptBeforeContentLoaded`, `injectedJavaScriptObject`, `injectJavaScript`, `onLoadEnd`, `startInLoadingState`, `originWhitelist`, Android `textZoom`. Android 14 system font range: [Features and APIs overview](https://developer.android.com/about/versions/14/features) ("the system supports font scaling up to 200%").
- Injection timing and User-Agent behavior: issues [#1609](https://github.com/react-native-webview/react-native-webview/issues/1609) (`injectedJavaScriptBeforeContentLoaded` unreliable on Android), [#3703](https://github.com/react-native-webview/react-native-webview/issues/3703) ("Only on android and only in production APK or AAB build"; custom `userAgent` sent only on the first page) / [#1971](https://github.com/react-native-webview/react-native-webview/issues/1971) ("applicationNameForUserAgent only works on first request, not on further navigation").
- Back button and renderer lifecycle: React Native [`BackHandler`](https://reactnative.dev/docs/backhandler); issues [#2810](https://github.com/react-native-webview/react-native-webview/issues/2810) (`goBack()` no-op regression), [#2199](https://github.com/react-native-webview/react-native-webview/issues/2199) (iOS blank WebView after idle) — iOS renderer death; [#2559](https://github.com/react-native-webview/react-native-webview/issues/2559) is historical only (`onContentProcessDidTerminate` not called in 11.22.0–11.22.4; "resolved in version 11.22.5", 2022-07-06); Android `onRenderProcessGone` is covered in [android-webview](./android-webview.md).
- `postMessage` dispatch targets, pinned to d65a961: Android [`RNCWebViewManager.kt#L773`](https://github.com/react-native-webview/react-native-webview/blob/d65a961080dad3e82d33370ad6e8d90e973fcbd3/android/src/main/java/com/reactnativecommunity/webview/RNCWebViewManager.kt#L773) (`document.dispatchEvent(event)`) and iOS [`RNCWebViewImpl.m#L1085`](https://github.com/react-native-webview/react-native-webview/blob/d65a961080dad3e82d33370ad6e8d90e973fcbd3/apple/RNCWebViewImpl.m#L1085) (`window.dispatchEvent(new MessageEvent('message', …))`).
- Surface color derived from `backgroundColor` alpha: react-native-webview `apple/RNCWebViewImpl.m` `setBackgroundColor:`, pinned v16.0.0 [`#L698-L703`](https://github.com/react-native-webview/react-native-webview/blob/d65a961080dad3e82d33370ad6e8d90e973fcbd3/apple/RNCWebViewImpl.m#L698-L703) (alpha → `opaque`, then `_webView.scrollView.backgroundColor` and `_webView.backgroundColor`) and default `clearColor` [`#L159-L161`](https://github.com/react-native-webview/react-native-webview/blob/d65a961080dad3e82d33370ad6e8d90e973fcbd3/apple/RNCWebViewImpl.m#L159-L161).
