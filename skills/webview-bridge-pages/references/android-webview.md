# Host reference: Android WebView

## Contents

- [Three bridge mechanisms (official comparison)](#three-bridge-mechanisms-official-comparison)
- [Security notes](#security-notes)
- [Loading & lifecycle](#loading--lifecycle)
- [Layout](#layout)
- [Legacy JavaScript compatibility](#legacy-javascript-compatibility)
- [Legacy CSS fallbacks](#legacy-css-fallbacks)
- [Legacy engine smoke matrix](#legacy-engine-smoke-matrix)
- [Rotation diagnostics](#rotation-diagnostics)
- [Sources](#sources)

`android.webkit.WebView` (+ Jetpack `WebViewCompat`) — the web page's view of it.

## Three bridge mechanisms (official comparison)

| | `addWebMessageListener` | `postWebMessage` | `addJavascriptInterface` |
|---|---|---|---|
| Direction | Bidirectional (reply proxy) | Bidirectional (via `WebMessageChannel` ports) | Web → app only |
| Security | **Highest** (origin allowlist, `sourceOrigin` in callback) | High (origin aware) | Low (no origin checks) |
| Frames | All frames matching the origin allowlist | Main frame only | **Every frame incl. iframes** |
| Min version | WebView 82 / Webkit 1.3.0 | WebView 45 / Webkit 1.1.0 | All |
| Recommended | **Yes** | No | No (legacy) |

What the web page sees:

- `addWebMessageListener`: app injects `window.<objectName>` with a `postMessage(string)` method into frames whose origin matches the allowlist. Native replies (via the `JavaScriptReplyProxy`) arrive on the same object: `window.<objectName>.onmessage = (e) => ...` / `addEventListener('message', ...)`.
- `addJavascriptInterface`: app injects `window.<objectName>` with the `@JavascriptInterface`-annotated methods. Calls are **synchronous** (JS blocks until native returns) and run on a background thread natively. Target API 17+ (and run on API 17+): only then does it expose just the `@JavascriptInterface`-annotated methods — apps targeting API 16 or earlier expose all public methods to reflection (RCE, CVE-2012-6636).
- From the page, `addWebMessageListener` is always `window.<objectName>.postMessage(jsonString)`. With `addJavascriptInterface` the method name and parameter types are whatever the app annotates (the bridge coerces JS numbers/booleans to Java primitives); the universal transport adapter fits only if the app names a `postMessage(String)` method — agree on that in the contract.

## Security notes

- `addJavascriptInterface` has **no origin control** — any iframe can call it, and the app cannot reliably determine the calling frame's URL. This is why the skill's rule "native must treat bridge input as untrusted" exists.
- Apps should use `addWebMessageListener` with explicit `allowedOriginRules` (never bare `*`; rules must be scheme-qualified — `https://*.example.com` is a valid subdomain wildcard, but it matches subdomains only, **not** `https://example.com` itself, so list the apex origin as a separate rule; a scheme-less `*.example.com` throws `IllegalArgumentException`).
- **File inputs**: the default `WebChromeClient` does not show a file chooser for `<input type="file">` — the request is silently dropped unless the app overrides `WebChromeClient.onShowFileChooser` (API 21+, `FileChooserParams`; classic mistake: looking for it on `WebViewClient`). The tap is a silent no-op with no page-observable error, and the same page works in browsers and WKWebView, so it ships unnoticed.
- **Camera/microphone**: when web content requests a resource whose permission "currently isn't granted or denied", the app gets `WebChromeClient.onPermissionRequest`; "If this method isn't overridden, the permission is denied." The app must `grant()` the requested `PermissionRequest.RESOURCE_VIDEO_CAPTURE`/`RESOURCE_AUDIO_CAPTURE` resources (react-native-webview also asks for the matching `CAMERA`/`RECORD_AUDIO` runtime permissions first) — host-grant contract → [contract-design](./contract-design.md#navigation--capabilities).

## Loading & lifecycle

- `WebViewClient.onPageFinished`: official docs — receiving the callback "does not guarantee that the next frame drawn by WebView will reflect the state of the DOM at this point." Not a render signal; use a web-sent `READY` message.

## Layout

- Android WebView window-inset support depends on Chromium milestone and WebView bounds. Official rollout: **M136** forwards `displayCutout()`/`systemBars()` via CSS safe-area insets for **fullscreen WebViews only**; **M139** adds IME support through visual-viewport resizing for **all WebViews**; **M144** expands `displayCutout()`/`systemBars()` support to **all WebViews**. Until your user base and host layout are inside that support envelope, take insets from the app (query params or injected CSS variables; divide injected pixel values by `initial-scale` when ≠ 1).
- **Viewport height can be wrong in target-specific cases.** Chromium issue 331326389 documents a `clientHeight` failure around navigation and keyboard state; separate reports cover other `dvh`-too-tall-at-load symptoms. These reports do not establish one version cutoff or one repair. Capture layout and visual viewport values on the failing host before choosing a JS-measured height or moving critical bottom UI into a measured container (→ [page-implementation](./page-implementation.md)).
- Keyboard (M139+): IME resizes the **visual viewport only**, bottom edge only. Don't clear element focus in resize handlers — focus-loss/keyboard-dismiss loop.
- **System font scale maps to `textZoom`** (`setTextZoom` default 100; Android 14+ "supports font scaling up to 200%" with a nonlinear curve; the smaller and pre-14 presets vary, so read the actual scale on the target device). Layouts must tolerate it, or the app clamps (`webView.settings.textZoom`). Don't pin to 100 without an accessibility review.
- Viewport meta is mandatory: with `setUseWideViewPort(true)` (react-native-webview's `scalesPageToFit` default) a page without one gets a wide, desktop-style viewport; with the platform default (false) the layout width is the WebView's width.
- **Dark mode app-side knob**: targetSdk 33+ uses `WebSettingsCompat.setAlgorithmicDarkeningAllowed(true)`, which darkens only content that does **not** use `prefers-color-scheme`; `setForceDark` is deprecated and a no-op for apps targeting API 33+. The page-side `color-scheme` meta requirement → [page-implementation](./page-implementation.md).

## Legacy JavaScript compatibility

If an old Android WebView shows a generic client-side error while modern Chrome works, debug the WebView engine, not just the Android OS version. Pull the browser console from remote debugging or reproduce with the missing feature removed, then separate:

- Syntax support: parse/transpile target issues.
- Runtime API support: missing globals or methods such as `globalThis`, `Array.prototype.at`, `Object.hasOwn`, or `URL.canParse`.
- Browser-native `window.postMessage(message)` compatibility: the options-dictionary overload that makes `targetOrigin` optional shipped in Chromium 70 (WebView included), so older engines such as an un-updated WebView 66 can reject a one-argument call; use `window.postMessage(message, window.location.origin)` for same-page events.

For feature fixes, prefer feature detection over User-Agent gates. In Next.js Pages Router, a polyfill required before the app boots should be loaded from `pages/_document` with `next/script` `strategy="beforeInteractive"` (App Router: same strategy from the root `app/layout`); verify the rendered HTML places it before `_next/static/chunks/*` and re-test on the old WebView. Do not rely on normal client imports when the failing code can run before hydration.

## Legacy CSS fallbacks

Treat old CSS failures like runtime compatibility issues, not design tweaks. Prefer feature detection and a narrow marker such as `html[data-legacy-webview='true']` over Android-version or User-Agent gates. The marker can cover an old WebView class of issues, but each CSS rule under it should still be local to the failing component.

For unsupported layout features such as flex/grid `gap`, `dvh`, or safe-area values, show the failure in an affected engine, add the smallest fallback branch, then compare against the same viewport without the marker. Playwright can force the marker for fast regression coverage; it does not establish old engine parsing/rendering. Use an actual old Android WebView/WebView Shell or app WebView for that.

Do not verify legacy support against a dev server (`next dev`/HMR or any bundler dev mode). The framework's dev runtime and untranspiled `node_modules` ship modern syntax (optional chaining, nullish coalescing) that a `browserslist`/target setting does not downlevel — it lowers *your* app code but not the framework's own dev bundle — so a legacy WebView parse-errors there even when the production build is clean. In Next.js, a live WebView target with `document.readyState === 'complete'` can still stay blank because the Pages-Router-dev-only `style[data-next-hide-fouc]` FOUC guard leaves `body{display:none}` in old WebView HMR; treat that as dev-runtime evidence, not a product CSS regression. Iterate layout on a modern WebView (where HMR works); run the engine and app-integration tiers against a production build or deployed environment.

## Legacy engine smoke matrix

Record evidence by **WebView/Chrome engine version**, not OS name alone. Two Android 9 devices can differ if one has an updated WebView package.

- Fast browser/Playwright with a forced fallback marker exercises branch shape only.
- Android WebView Shell or an emulator with the affected WebView version checks engine JavaScript/CSS compatibility.
- App WebView checks host integration: bridge injection, safe-area params, auth, deep links, and native lifecycle.

For each run, capture device model/AVD, Android API, WebView package/version, loaded URL environment, console errors, and screenshots. If the fix is a CSS fallback such as `gap` replacement, include before/after screenshots at the same viewport and a modern control where the fallback marker is absent.

## Rotation diagnostics

For Android WebView rotation bugs, do not start with native background masking. First classify the artifact:

- If the WebView surface flashes white/blank while DOM state is otherwise correct, investigate native WebView background/layer behavior.
- If content is shifted, clipped, or using the previous orientation width for a frame, treat it as layout/visual viewport settling. Prefer a page-side fix that avoids mixing a narrow centered root with `100vw` children, and remeasure via `resize` / `orientationchange` / `visualViewport.resize` if JS dimensions are involved.

## Sources

- Android Developers: [`WebView`](https://developer.android.com/reference/android/webkit/WebView), [`WebViewCompat`](https://developer.android.com/reference/androidx/webkit/WebViewCompat) (`addWebMessageListener` / `postWebMessage`), [`@JavascriptInterface`](https://developer.android.com/reference/android/webkit/JavascriptInterface) (API 17+ annotation requirement), and [`WebViewClient.onPageFinished`](https://developer.android.com/reference/android/webkit/WebViewClient) (does "not guarantee that the next frame drawn by WebView will reflect the state of the DOM at this point"; request a visual state callback to know the DOM is ready to render).
- Bridge payload types: [Android Developers — Access native APIs with JavaScript bridge](https://developer.android.com/develop/ui/views/layout/webapps/native-api-access-jsbridge) (`addWebMessageListener` "sends data as either strings or byte[] arrays"; `addJavascriptInterface` parameter mapping coerces JS `Number`/`Boolean` into Java primitive parameter types).
- `addJavascriptInterface` reflection RCE on pre-API-17 WebViews: [CVE-2012-6636](https://nvd.nist.gov/vuln/detail/CVE-2012-6636).
- File chooser: [`WebChromeClient.onShowFileChooser`](https://developer.android.com/reference/android/webkit/WebChromeClient#onShowFileChooser(android.webkit.WebView,%20android.webkit.ValueCallback%3Candroid.net.Uri[]%3E,%20android.webkit.WebChromeClient.FileChooserParams)) (base implementation returns false → request dropped).
- Camera/microphone grant: [`WebChromeClient.onPermissionRequest`](https://developer.android.com/reference/android/webkit/WebChromeClient) ("If this method isn't overridden, the permission is denied") and [`PermissionRequest`](https://developer.android.com/reference/android/webkit/PermissionRequest); react-native-webview pinned [`RNCWebChromeClient.java#L143-L190`](https://github.com/react-native-webview/react-native-webview/blob/d65a961080dad3e82d33370ad6e8d90e973fcbd3/android/src/main/java/com/reactnativecommunity/webview/RNCWebChromeClient.java#L143-L190) (maps to `CAMERA`/`RECORD_AUDIO`).
- Dark theme: [Darken web content in WebView](https://developer.android.com/develop/ui/views/layout/webapps/dark-theme) (`setAlgorithmicDarkeningAllowed`, `color-scheme` meta requirement); `setForceDark` deprecation from [`WebSettings.setForceDark`](https://developer.android.com/reference/android/webkit/WebSettings) ("deprecated in API level 33 … In apps with targetSdkVersion ≥ Build.VERSION_CODES.TIRAMISU this API is a no-op").
- Font scale: `WebSettings.setTextZoom` ("The default is 100"); Android 14 [Features and APIs overview](https://developer.android.com/about/versions/14/features) ("Starting in Android 14, the system supports font scaling up to 200%").
- Legacy `window.postMessage` arity: Chrome Platform Status ["Options dictionary for postMessage methods"](https://chromestatus.com/feature/6219707585658880) (Window included; shipped in milestone 70 for desktop, Android, and WebView; checked 2026-09-25).
- Next.js: [`next/script`](https://nextjs.org/docs/pages/api-reference/components/script) ("beforeInteractive scripts must be placed inside the Document Component (pages/_document.js)"); App Router [`next/script`](https://nextjs.org/docs/app/api-reference/components/script) ("Scripts with the beforeInteractive strategy must be placed inside a root layout"); dev-only FOUC guard, pinned [`packages/next/src/pages/_document.tsx#L713-L730`](https://github.com/vercel/next.js/blob/cb95ca373be557309a962d8a6e64a75c6732bc5d/packages/next/src/pages/_document.tsx#L713-L730) (`isDevelopment` → `<style data-next-hide-fouc>` with `body{display:none}`) and [`packages/next/src/client/dev/fouc.ts#L16-L33`](https://github.com/vercel/next.js/blob/cb95ca373be557309a962d8a6e64a75c6732bc5d/packages/next/src/client/dev/fouc.ts#L16-L33) (removed only when the dev client runs `displayContent()`).
- Wide viewport and new windows: [`WebSettings`](https://developer.android.com/reference/android/webkit/WebSettings) (`setUseWideViewPort` default false → layout width is the WebView width; `setSupportMultipleWindows` default false → `window.open`/`target="_blank"` "treated as top-level navigations, replacing the current page in the same WebView").
- Window-insets / viewport / keyboard behavior across Chromium milestones: [Android Developers — Understand window insets in WebView](https://developer.android.com/develop/ui/views/layout/webapps/understand-window-insets). Browser viewport behavior and WebView background: [Chrome for Developers — Web on Android](https://developer.chrome.com/docs/android) and [viewport resize behavior](https://developer.chrome.com/blog/viewport-resize-behavior); additional inset/viewport source anchors → [page-implementation](./page-implementation.md) Sources.
