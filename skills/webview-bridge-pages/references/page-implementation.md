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
- **Safe-area insets are not portable.** `env(safe-area-inset-*)` works in WKWebView,
  but Android WebView returned `0px` until recent versions (Chromium M136–M144
  rollout, fullscreen-only at first). The robust cross-host pattern: **the app passes
  `statusBarHeight` (and bottom inset if needed) as query params** — prefer params
  over app-injected CSS variables (no injection-timing race, testable in a browser).
  Combine with `env()` as progressive enhancement:
  `padding-top: max(var(--inset-top, 0px), env(safe-area-inset-top, 0px))`.
  If the app does inject pixel insets, divide by `initial-scale` when it isn't 1.
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
  default (`interactive-widget=resizes-visual`); `svh/dvh` units do NOT react to the
  keyboard. If an input must stay visible above the keyboard, use the VirtualKeyboard
  API or `interactive-widget=resizes-content`, and never clear element focus in resize
  handlers — that creates a focus-loss/keyboard-dismiss loop.
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

## Sources

- Chrome for Developers "Pixel-perfect WebView" and "viewport-resize-behavior";
  Android "Understand window insets in WebView" (M136/M139/M144 timeline) and
  "Make WebViews edge-to-edge"; CSS viewport-unit specs (svh/dvh/lvh);
  CanIWebView (caniwebview.com).
- Scroll/overscroll & input-zoom: WebKit bug 243270 (`bounces` vs `overscroll-behavior`,
  fixed ~iOS 16.2) and bug 262287 (`position:fixed` interrupted-momentum hit-test, fixed
  in Safari Technology Preview 239); WCAG 1.4.4 (`maximum-scale`/`user-scalable` is
  honored in WKWebView, unlike mobile Safari).
