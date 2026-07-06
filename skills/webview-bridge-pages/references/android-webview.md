# Host reference: Android WebView

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

- `addWebMessageListener`: app injects `window.<objectName>` with a
  `postMessage(string)` method into frames whose origin matches the allowlist.
  Native replies (via the `JavaScriptReplyProxy`) arrive on the same object:
  `window.<objectName>.onmessage = (e) => ...` / `addEventListener('message', ...)`.
- `addJavascriptInterface`: app injects `window.<objectName>` with the
  `@JavascriptInterface`-annotated methods. Calls are **synchronous** (JS blocks until
  native returns) and run on a background thread natively. Require API 17+: it exposes
  only `@JavascriptInterface`-annotated methods (older Android exposed all public
  methods — reflection RCE, CVE-2012-6636).
- Either way, from the page: `window.<objectName>.postMessage(jsonString)` —
  fits the universal transport adapter.

## Security notes

- `addJavascriptInterface` has **no origin control** — any iframe can call it, and the
  app cannot reliably determine the calling frame's URL. This is why the skill's rule
  "native must treat bridge input as untrusted" exists.
- Apps should use `addWebMessageListener` with explicit `allowedOriginRules`
  (never bare `*`; rules must be scheme-qualified — `https://*.example.com` is a valid
  subdomain wildcard, but it matches subdomains only, **not** `https://example.com`
  itself, so list the apex origin as a separate rule; a scheme-less `*.example.com`
  throws `IllegalArgumentException`).
- **File inputs**: the default `WebChromeClient` does not show a file chooser for
  `<input type="file">` — the request is silently dropped unless the app overrides
  `WebChromeClient.onShowFileChooser` (API 21+, `FileChooserParams`; classic mistake:
  looking for it on `WebViewClient`). The tap is a silent no-op with no page-observable
  error, and the same page works in browsers and WKWebView, so it ships unnoticed.

## Loading & lifecycle

- `WebViewClient.onPageFinished`: official docs — receiving the callback "does not
  guarantee that the next frame drawn by WebView will reflect the state of the DOM at
  this point." Not a render signal; use a web-sent `READY` message.

## Layout

- Android WebView window-inset support depends on Chromium milestone and WebView
  bounds. Official rollout: **M136** forwards `displayCutout()`/`systemBars()` via
  CSS safe-area insets for **fullscreen WebViews only**; **M139** adds IME support
  through visual-viewport resizing for **all WebViews**; **M144** expands
  `displayCutout()`/`systemBars()` support to **all WebViews**. Until your user base
  and host layout are inside that support envelope, take insets from the app (query
  params or injected CSS variables; divide injected pixel values by `initial-scale`
  when ≠ 1).
- **Viewport height can be wrong in specific old-engine cases.** Public Chromium bug
  reports/repros point to pre-M139 `clientHeight`/visual-viewport issues around
  keyboard-during-navigation, and separate reports exist for non-keyboard
  `dvh`-too-tall-at-load cases. Treat this as an affected-version bug, not a blanket
  Android rule. Fallback candidates are JS `--vh` from `innerHeight` and anchoring
  critical bottom UI inside that measured container (→ [page-implementation](./page-implementation.md)).
  A modern emulator may not reproduce it — test the affected version.
- Keyboard (M139+): IME resizes the **visual viewport only**, bottom edge only.
  Don't clear element focus in resize handlers — focus-loss/keyboard-dismiss loop.
- **System font scale maps to `textZoom`** (community-documented: ~85 at the smallest
  preset; up to ~130 before Android 14, up to **200%** non-linear on Android 14+).
  Layouts must tolerate it, or the app clamps (`webView.settings.textZoom`). Don't pin
  to 100 without an accessibility review.
- Viewport meta is mandatory or WebView may lay out at ~980px desktop width.
- **Dark mode app-side knob**: targetSdk 33+ uses
  `WebSettingsCompat.setAlgorithmicDarkeningAllowed(true)`, which darkens only content
  that does **not** use `prefers-color-scheme`; `setForceDark` is deprecated and a
  no-op for apps targeting API 33+. The page-side `color-scheme` meta requirement →
  [page-implementation](./page-implementation.md).

## Legacy engine smoke matrix

Record evidence by **WebView/Chrome engine version**, not OS name alone. Two Android 9
devices can differ if one has an updated WebView package.

- Fast browser/Playwright with a forced fallback marker exercises branch shape only.
- Android WebView Shell or an emulator with the affected WebView version checks engine
  JavaScript/CSS compatibility.
- App WebView checks host integration: bridge injection, safe-area params, auth,
  deep links, and native lifecycle.

For each run, capture device model/AVD, Android API, WebView package/version, loaded
URL environment, console errors, and screenshots. If the fix is a CSS fallback such as
`gap` replacement, include before/after screenshots at the same viewport and a modern
control where the fallback marker is absent.

## Rotation diagnostics

For Android WebView rotation bugs, do not start with native background masking. First
classify the artifact:

- If the WebView surface flashes white/blank while DOM state is otherwise correct,
  investigate native WebView background/layer behavior.
- If content is shifted, clipped, or using the previous orientation width for a
  frame, treat it as layout/visual viewport settling. Prefer a page-side fix that
  avoids mixing a narrow centered root with `100vw` children, and remeasure via
  `resize` / `orientationchange` / `visualViewport.resize` if JS dimensions are
  involved.

## Sources

- Android Developers: [`WebView`](https://developer.android.com/reference/android/webkit/WebView),
  [`WebViewCompat`](https://developer.android.com/reference/androidx/webkit/WebViewCompat)
  (`addWebMessageListener` / `postWebMessage`),
  [`@JavascriptInterface`](https://developer.android.com/reference/android/webkit/JavascriptInterface)
  (API 17+ annotation requirement), and
  [`WebViewClient.onPageFinished`](https://developer.android.com/reference/android/webkit/WebViewClient)
  (does "not guarantee that the next frame drawn by WebView will reflect the state of the DOM at this point"; request a visual state callback to know the DOM is ready to render).
- `addJavascriptInterface` reflection RCE on pre-API-17 WebViews:
  [CVE-2012-6636](https://nvd.nist.gov/vuln/detail/CVE-2012-6636).
- File chooser: [`WebChromeClient.onShowFileChooser`](https://developer.android.com/reference/android/webkit/WebChromeClient#onShowFileChooser(android.webkit.WebView,%20android.webkit.ValueCallback%3Candroid.net.Uri[]%3E,%20android.webkit.WebChromeClient.FileChooserParams))
  (base implementation returns false → request dropped).
- Dark theme: [Darken web content in WebView](https://developer.android.com/develop/ui/views/layout/webapps/dark-theme)
  (`setAlgorithmicDarkeningAllowed`, `color-scheme` meta requirement, `setForceDark` deprecation).
- Window-insets / viewport / keyboard behavior across Chromium milestones and
  `textZoom`: [Chrome for Developers — Web on Android](https://developer.chrome.com/docs/android)
  and [viewport resize behavior](https://developer.chrome.com/blog/viewport-resize-behavior);
  additional inset/viewport source anchors → [page-implementation](./page-implementation.md) Sources.
