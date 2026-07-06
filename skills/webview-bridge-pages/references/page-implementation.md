# Page implementation (parsing, timers, layout)

Web-side implementation rules once the contract is settled.

## Query params on SPA hydration

- All render inputs (variant flags, prices, expiry, locale, status-bar height) arrive
  as URL query params. Parse them in **one tested function** (e.g.
  `parseScreenQuery()`).
- Gate on router readiness (Next.js `router.isReady`); handle `string | string[]`. The
  readiness mechanic itself (router.query empty on first render, redirects firing before
  `router.isReady`, lost deep-link destinations) is owned by **deeplink-hydration** —
  here the params are render inputs the app composed into the URL, not a destination.
- Unknown/missing enum values → fall back to `control`/default. Never crash on a param.
- Pre-formatted values (currency strings) are display-only — require the app to
  `encodeURIComponent` them; hide the row when missing.
- Timers: compute from an absolute timestamp every tick
  (`Math.max(0, expiresAtMs - Date.now())`), never decrement a counter — WebViews
  suspend/resume. Clamp at zero. Agree on the unit (unix seconds vs ms) in the
  contract.

## Layout & viewport inside a WebView

- **Viewport meta is mandatory** — without it Android WebView may lay out at ~980px
  desktop width: `width=device-width, initial-scale=1, viewport-fit=cover`.
- **Don't trust `100vh`.** It measures the large viewport; use `100svh` for stable
  full-height layouts, `100dvh` only when you want reflow as chrome shows/hides.
- **Even `svh`/`dvh` can be wrong at *initial load* on older Android WebView.** Some
  pre-M139 Chromium versions compute the viewport too tall on first paint and freeze it
  until a *real* viewport change (rotation/keyboard/resize), pushing a full-height
  page's bottom below the fold (see bug 331326389, the keyboard-during-nav `clientHeight`
  case, fixed M139; non-keyboard `dvh`-too-tall-at-load is reported separately). An
  app-side 1px container resize does **not** clear it — only a genuine viewport change
  does. When you must support old WebViews, drive height from JS instead of the CSS
  unit: `--vh = innerHeight*0.01` → `height: calc(var(--vh, 1vh) * 100)`, updated on
  `resize`. `innerHeight` read at mount escapes the CSS-unit-at-load bug in a chrome-less
  in-app WebView (no URL bar). And **don't pin the bottom CTA with `position:fixed`**
  here — fixed anchors to that buggy viewport (changing the page's height unit won't move
  it, and it lands below the fold); anchor it `position:absolute` to the `--vh`-sized
  page container instead. Verify on a *real old device* — modern emulators (WebView
  ≥M139) have it fixed and can't reproduce it. Most robust of all: have the **app pass
  the absolute pixel height** as a param and use
  `height: var(--app-height, calc(var(--vh, 1vh) * 100))` — independent of every CSS/JS
  viewport quirk, with `--vh` then the unit as graceful fallbacks.
- **Gate first paint on a measured height.** If the base can be briefly wrong at first
  paint (`--vh`/`--app-height` not set yet → `1vh` falls back to the large viewport),
  hold rendering until the JS height is measured (`> 0`) so the page doesn't flash at the
  wrong height. Always pair the gate with a forced-reveal timeout, so a measurement that
  never arrives can't leave the page stuck blank.
- **Safe-area insets are not portable.** `env(safe-area-inset-*)` works in WKWebView,
  but Android WebView support depends on Chromium milestone and whether the host
  WebView is fullscreen or overlapping system UI: M136 handles display-cutout/system-bar
  safe areas for fullscreen WebViews, M139 handles IME via visual viewport, and M144
  expands display-cutout/system-bar safe areas to all WebViews. The robust cross-host
  pattern: **the app passes `statusBarHeight` (and bottom inset if needed) as query
  params** — prefer params over app-injected CSS variables (no injection-timing race,
  testable in a browser).
  Combine with `env()` as progressive enhancement:
  `padding-top: max(var(--inset-top, 0px), env(safe-area-inset-top, 0px))`.
  If the app does inject pixel insets, divide by `initial-scale` when it isn't 1.
- **An app-override inset var must not share a name with a global token.** If `--sab` is
  defined on `:root` (e.g. `--sab: env(safe-area-inset-bottom)`), then `var(--sab, 16px)`
  uses that global value and **never the `16px` fallback** — per spec a `var()` fallback
  applies only when the property is *undefined*, and the `:root` rule makes it always
  defined (computing to `0` in a broken Android WebView). For "use the app value, else a
  hardcoded design default", read a **distinct app-only variable** (e.g. `--app-safe-bottom`)
  set inline only when the app passes it; otherwise the fallback is dead code and you
  silently inherit `env()`/`0`. The `max(var(--app-x,0px), env(...))` pattern above
  sidesteps this — the trap is reusing one shared name for both the global token and the
  app override.
- **Bottom-fixed CTA hides trailing content.** Reserve its height plus the bottom
  inset:
  `padding-bottom: calc(<cta-height> + max(var(--inset-bottom,0px), env(safe-area-inset-bottom,0px)))`.
  The height-reserve is needed everywhere (check it on desktop too); only the inset
  portion is device-only — `env()` reads 0 on desktop.
- **iOS scroll/overscroll quirks.** Scope `overscroll-behavior` to the scrolling
  element, not blanket `html` — on iOS it disables intended inner bounce and has clashed
  with the native `bounces` setting (WebKit 243270; use `contain` on inner scroll
  areas). A `position:fixed` element's hit area can also desync from its painted
  position after an interrupted/fast scroll (taps land in the old spot until the next
  touch) — avoid critical taps in fixed bars mid-momentum.
- **Keyboard (IME):** modern Chrome/WebView resizes only the *visual* viewport by
  default; `svh/dvh` units do NOT react to the keyboard. The `interactive-widget`
  viewport meta and the VirtualKeyboard API are Chromium-*browser* mechanisms and are
  **not honored inside an in-app WebView**: on Android, keyboard resize is
  host-controlled (`windowSoftInputMode="adjustResize"` / inset forwarding — put it in
  the app contract; the Chrome 108 `interactive-widget` change explicitly does not
  affect WebView, and M139+ resizes the visual viewport so obscured content becomes
  scrollable), and iOS WKWebView supports neither (`interactive-widget` unimplemented,
  WebKit bug 259770; VirtualKeyboard API is Chromium-only). To keep an input visible
  above the keyboard in a WebView, listen to `visualViewport` `resize`/`scroll` and
  `scrollIntoView` the focused input; in Chromium *browser* contexts you may
  additionally use `interactive-widget=resizes-content` or the VirtualKeyboard API.
  Never clear element focus in resize handlers — that creates a
  focus-loss/keyboard-dismiss loop.
- **iOS auto-zooms on focus when an input's `font-size` is < 16px**, and often does
  not restore zoom on blur (page left shifted/clipped). Set `font-size: 16px` on
  `input`/`select`/`textarea`/`contenteditable`. The `maximum-scale=1`/`user-scalable=no`
  viewport hack also stops the zoom, but a default in-app WKWebView honors those scale
  limits (`ignoresViewportScaleLimits` defaults to `false`), so the hack actually disables
  pinch-zoom and fails WCAG 1.4.4 — unlike mobile Safari, which ignores `user-scalable=no`
  since iOS 10. Prefer the 16px fix.
- **System font scale breaks layouts on Android.** WebView text follows the OS
  accessibility font size via `textZoom` (~85% at the smallest preset; up to ~130%
  before Android 14, up to **200%** non-linear on Android 14+). Don't silently
  override it to 100 — that defeats user accessibility. Verify the layout at 130%
  (and ideally 200% on Android 14+), and agree with the app side on a clamp
  (e.g. RN `textZoom` prop capped to a max the layout tolerates).
- **Dark mode: the `color-scheme` meta tag is load-bearing in Android WebView.**
  Unlike browsers, Android WebView's default Force Dark strategy ignores
  `prefers-color-scheme` media queries unless the page declares
  `<meta name="color-scheme" content="light dark">` — without it the host can
  user-agent-darken (auto-invert) the page with `prefers-color-scheme` evaluating
  false, producing broken brand colors or double-darkening when the app theme is dark.
  Web-side fix: the meta tag (or explicit `content="light"` to opt out of darkening)
  plus `prefers-color-scheme` styles. The app-side knob →
  [android-webview](./android-webview.md).

## Sources

- Chrome for Developers "Web on Android"
  (https://developer.chrome.com/docs/android/) and Chrome Android
  viewport-resize-behavior changes
  (https://developer.chrome.com/blog/viewport-resize-behavior/).
- Android Developers window-insets, edge-to-edge, and display-cutout docs:
  https://developer.android.com/develop/ui/views/layout/insets,
  https://developer.android.com/develop/ui/views/layout/edge-to-edge,
  https://developer.android.com/develop/ui/views/layout/display-cutout.
- CSS Values viewport-relative lengths (svh/dvh/lvh)
  (https://drafts.csswg.org/css-values-4/#viewport-relative-lengths) and
  CanIWebView (https://caniwebview.com/).
- Scroll/overscroll & input-zoom: WebKit bug 243270
  (https://bugs.webkit.org/show_bug.cgi?id=243270; `bounces` vs `overscroll-behavior`,
  fixed ~iOS 16.2) and bug 262287
  (https://bugs.webkit.org/show_bug.cgi?id=262287; `position:fixed`
  interrupted-momentum hit-test, fixed in Safari Technology Preview 239);
  WCAG 1.4.4 resize-text understanding
  (https://www.w3.org/WAI/WCAG22/Understanding/resize-text.html).
- Initial-load viewport-height bug: Chromium issue 331326389 (`clientHeight` wrong on
  first load when keyboard was up during nav, fixed M139; repro:
  Zwyx/chrome-android-clientheight), Stack Overflow 77033005 (`100dvh` extends past
  bottom on Android Chrome) and 79831083 (Chrome PWA `dvh` wrong on initial load); JS
  `--vh` trick: CSS-Tricks "The trick to viewport units on mobile".
- Keyboard mechanisms: Chrome 108 viewport-resize change ("These changes do not
  affect WebView") — https://developer.chrome.com/blog/viewport-resize-behavior;
  WebKit bug 259770 (`interactive-widget` unimplemented) —
  https://bugs.webkit.org/show_bug.cgi?id=259770; MDN VirtualKeyboard API
  (Chromium-only, experimental).
- Dark mode: Android WebView dark-theme doc
  (https://developer.android.com/develop/ui/views/layout/webapps/dark-theme;
  meta tag required for `prefers-color-scheme` in default Force Dark mode).

## Paint / hit-test diagnostics

When a WebView UI element is present but visually wrong, split the symptom before changing layout or padding. Check these axes separately:

- DOM existence: element is mounted with expected text/assets/classes.
- Geometry/layout: box size and position are correct in `getBoundingClientRect()`.
- Hit testing: tap/click target works at the painted or expected location.
- Paint: background, text, images, gradients, and opacity actually draw.
- Compositing/layering: parent background, child layers, transforms, clipping, `z-index`, and WebView resume/re-exposure timing.

If the container background and hit area exist but child text/buttons disappear, layout height/padding is less likely than paint/compositing/layering. Prefer a small confirming probe (DevTools styles/computed box, temporary solid color, remove gradient, isolate child layer) before adding JS remeasurement, timeouts, or extra safe-area padding. Keep any layer-promotion workaround local to the affected component and backed by device evidence.

## Rotation and viewport settling

On mobile WebViews, rotation can briefly expose a mismatch between the layout
viewport and the visible viewport. Treat this as a measurement problem before
masking it with background color.

1. Keep the WebView page root viewport-based (`width: 100%` or `100vw` as the
   page requires), then cap the readable/card content with inner `max-width`. Avoid
   a narrow centered root that contains children sized to `100vw`; during rotation
   this can make the old viewport overflow from one side.
2. If the page needs JS-derived viewport values, listen to `window.resize`,
   `orientationchange`, and `window.visualViewport.resize` when present. Re-read
   dimensions in `requestAnimationFrame` and, for Android WebView, once more after
   a short settle delay.
3. Use native WebView background/container styling only for native surface flash or
   blank-layer issues. It does not fix DOM alignment drift.
4. Keep page-specific compensation local to that page. Do not promote transforms,
   forced repaint tricks, or fixed delays as a general WebView rule without device
   evidence.

Evidence anchors: MDN `VisualViewport` documents visual-vs-layout viewport and the
`resize` event; Chrome's Visual Viewport article documents viewport API
inconsistency and listening to visual viewport changes; Android Developers documents
WebView layout/visual viewport mechanics; field reports show orientation values can
stabilize only after resize/rAF/short delays.

Sources:
- https://developer.mozilla.org/en-US/docs/Web/API/VisualViewport
- https://developer.chrome.com/blog/visual-viewport-api
- https://developer.android.com/develop/ui/views/layout/webapps/understand-window-insets
- https://stackoverflow.com/questions/12452349/mobile-viewport-height-after-orientation-change
