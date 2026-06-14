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
  native returns) and run on a background thread natively. Pre-API-17 (Android 4.2) all
  public methods were exposed, so JS could reach `getClass()` and use reflection for
  arbitrary code execution (CVE-2012-6636); from API 17 only `@JavascriptInterface`
  methods are reachable — so require API 17+ and the annotation.
- Either way, from the page: `window.<objectName>.postMessage(jsonString)` —
  fits the universal transport adapter.

## Security notes

- `addJavascriptInterface` has **no origin control** — any iframe can call it, and the
  app cannot reliably determine the calling frame's URL. This is why the skill's rule
  "native must treat bridge input as untrusted" exists.
- Apps should use `addWebMessageListener` with explicit `allowedOriginRules`
  (never bare `*`; `*.example.com` subdomain wildcards are fine).

## Loading & lifecycle

- `WebViewClient.onPageFinished`: official docs — receiving the callback "does not
  guarantee that the next frame drawn by WebView will reflect the state of the DOM at
  this point." Not a render signal; use a web-sent `READY` message.

## Layout

- `env(safe-area-inset-*)` returned **0px** on Android WebView until recently.
  Chromium rollout: M136 (cutout/system bars, fullscreen only) → M139 (IME via visual
  viewport resize) → M144 (all WebViews). Until your user base is past that, take
  insets from the app (query params or injected CSS variables; divide injected pixel
  values by `initial-scale` when ≠ 1).
- Keyboard (M139+): IME resizes the **visual viewport only**, bottom edge only.
  Don't clear element focus in resize handlers — focus-loss/keyboard-dismiss loop.
- **System font scale maps to `textZoom`** (community-documented: ~85 at the smallest
  preset; up to ~130 before Android 14, up to **200%** non-linear on Android 14+).
  Layouts must tolerate it, or the app clamps (`webView.settings.textZoom`). Don't pin
  to 100 without an accessibility review.
- Viewport meta is mandatory or WebView may lay out at ~980px desktop width.
