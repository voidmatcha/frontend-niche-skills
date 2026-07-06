# Why a Dedicated Reference for WebView Bridge Pages Is Necessary: An Evidence Dossier

**A bridge page is an HTML/CSS/JS document loaded inside a native app's embedded WebView and wired to the native shell through a JavaScript message bridge.** It is not "just a web page": it runs inside a host (WKWebView on iOS, Android System WebView, or a framework wrapper such as React Native, Capacitor, or Flutter) whose viewport, lifecycle, safe-area, font-scaling, and JavaScript-bridge behavior diverge from a normal mobile browser tab in ways that are not obvious, are version-gated, and recur across unrelated projects. This dossier collects primary-source evidence (specs, browser bug trackers, official docs, and open-source framework code) showing those pitfalls are real and recurring enough to justify a dedicated reference.

> **Last updated: 2026-06-25** — Validation environment: claims are pinned to the browser/OS/framework versions cited inline.

---

## TL;DR

Building bridge pages inside native WebViews hits a fixed cluster of non-obvious, version-gated failures: `100vh` overshoots the visible area (use `svh`/`dvh`), the Android viewport height is wrong on initial load until a touch or keyboard toggle forces a recalculation, `env(safe-area-inset-*)` reports `0px` or arrives late, the native↔JS message bridge is not ready when your first message fires (so the message is dropped), and a renderer crash leaves a blank screen unless the host explicitly recreates the WebView. Every pitfall below is backed by a primary source — a spec, a browser bug tracker, official platform docs, or open-source framework code — and most are corroborated by multiple independent projects.

---

## Background: why this exists

A bridge page must survive a host environment that controls the viewport sizing, the safe-area insets, the page lifecycle (freeze/resume), and the timing of the bridge handshake. The failures below are not edge cases discovered once; they appear verbatim in browser specifications, in browser-engine bug trackers that are still open, and in the source code of multiple unrelated WebView wrapper projects. That convergence is the argument for a dedicated reference: a generic "responsive web" guide does not cover them, and each team rediscovers them the hard way.

---

## How well-corroborated are these pitfalls?

Every pitfall in this dossier is backed by at least one primary source — a web standard, a browser-engine bug tracker, official platform documentation, or open-source framework code — and most are independently corroborated by more than one project. The corroborating open-source ecosystems cited inline below include React Native WebView, Capacitor (`@capacitor-community/safe-area`), `flutter_inappwebview`, Hotwire Turbo (turbo-android / turbo-ios), the WebViewJavascriptBridge family, and Tailwind CSS, alongside the W3C CSS specifications, the Chromium and WebKit bug trackers, and Android's official WebView documentation. The convergence — unrelated projects independently hitting and documenting the same failures — is the core argument for a dedicated reference.

For the complementary, source-line view — concrete defects this skill catches in real open-source code — see [open-source validation cases](./oss-validation-cases.md).

---

## Is a consolidated reference like this already available in open source?

Short answer: public guidance appears fragmented as of 2026-06. CSS/viewport writing (for example web.dev and CSS-Tricks viewport-unit posts) and native bridge/lifecycle writing (framework docs and engineering blogs) usually cover separate slices, so this reference consolidates the web-page-side cluster.

The closest existing resources each cover only a slice:

- **Library code, not author guidance:** [gronxb/webview-bridge](https://github.com/gronxb/webview-bridge) ships a typed RN↔web bridge with an `onReady` handshake, but it is runtime code covering the bridge axis only — no viewport, safe-area, renderer-death, or input-zoom guidance.
- **Single-framework docs:** [react-native-webview](https://github.com/react-native-webview/react-native-webview/blob/master/docs/Guide.md), Capacitor/Ionic, `flutter_inappwebview`, Apache Cordova, and Hotwire Turbo each document their own bridge/native-prop surface (Capacitor is notably strong on safe-area and font-scaling), but each is single-framework and native-prop-centric, not a web-author pitfall reference.
- **Single-topic posts:** viewport (`100vh`/`svh`/`dvh`), iOS 16px input zoom, and "blank WKWebView after a crash" each have solid standalone write-ups, but none combines them.

The clearest whitespace: **no public resource combines the bridge-handshake + initial-load viewport-freeze + renderer-death-recovery trio**, and two items — the Android first-paint viewport freeze *as a named pitfall*, and suppressing/withstanding Android `textZoom` from the page side — are barely documented anywhere. Consolidation across both literatures, framed from the web page's side, is the gap this reference fills.

---

## Problem → evidence table

| # | Pitfall (symptom) | Root cause / mechanism | Primary evidence |
|---|---|---|---|
| 1 | `100vh` is taller than the visible area; content sits under dynamic browser/app chrome | Default `vh` maps to the **large** viewport (`vh == lvh`) for web-compat; it assumes retractable UA chrome is retracted | [W3C CSS Values 4 §6.1.2.1](https://www.w3.org/TR/css-values-4/#viewport-relative-lengths); [MDN `<length>`](https://developer.mozilla.org/en-US/docs/Web/CSS/length) |
| 2 | Android WebView/Chrome reports the wrong height on initial load; a touch or keyboard toggle "fixes" it | Initial-load viewport/`clientHeight` is wrong until a re-render is forced | [Chromium issue 331326389](https://issues.chromium.org/issues/331326389); [Next.js discussion #63724](https://github.com/vercel/next.js/discussions/63724); [SO 77033005](https://stackoverflow.com/questions/77033005); [SO 79831083](https://stackoverflow.com/questions/79831083) |
| 3 | `env(safe-area-inset-*)` returns `0px` on Android, or arrives late on iOS | Chromium `< 140` does not correctly report insets; WKWebView does not set the env() variables until some time after page load | [@capacitor-community/safe-area README](https://github.com/capacitor-community/safe-area/blob/master/README.md); [WebKit bug 191872](https://bugs.webkit.org/show_bug.cgi?id=191872); [react-native-webview #3828](https://github.com/react-native-webview/react-native-webview/issues/3828) / [#155](https://github.com/react-native-webview/react-native-webview/issues/155) |
| 4 | The first message to native (READY/auth) is silently dropped on cold start | The bridge object/queue is not initialized when the page's first call fires; messages must be buffered and flushed on bridge load | [WebViewJavascriptBridge README](https://github.com/marcuswestin/WebViewJavascriptBridge/blob/master/README.md); [react-native-webview #1698](https://github.com/react-native-webview/react-native-webview/issues/1698); [flutter_inappwebview #218](https://github.com/pichillilorenzo/flutter_inappwebview/issues/218) |
| 5 | Blank screen after the WebView renderer crashes or is killed for memory | The dead WebView cannot be reused; the host must destroy it and create a new instance | [Android "Manage WebView objects"](https://developer.android.com/develop/ui/views/layout/webapps/managing-webview); [Hotwire turbo-android `TurboSession.kt`](https://github.com/hotwired/turbo-android/blob/main/turbo/src/main/kotlin/dev/hotwire/turbo/session/TurboSession.kt) |
| 6 | iOS zooms the page in when an input is focused | iOS Safari/WebKit auto-zooms when an input's `font-size` is `< 16px` | [CSS-Tricks "16px or larger text prevents iOS form zoom"](https://css-tricks.com/16px-or-larger-text-prevents-ios-form-zoom/) |
| 7 | Layout breaks under large accessibility font scaling on Android | Android 14 supports nonlinear font scaling up to 200%; WebView text zoom is a separate `setTextZoom` (default 100%) | [Android 14 features](https://developer.android.com/about/versions/14/features); [Chromium WebView `web-page-layout.md`](https://chromium.googlesource.com/chromium/src/+/master/android_webview/docs/web-page-layout.md) |
| 8 | Timers (`setTimeout`/`setInterval`) drift or stop when the WebView is backgrounded | Hidden/frozen pages suspend freezable tasks and throttle chained timers | [Chrome Page Lifecycle API](https://developer.chrome.com/docs/web-platform/page-lifecycle-api); [Chrome 88 timer throttling](https://developer.chrome.com/blog/timer-throttling-in-chrome-88) |
| 9 | Page renders at ~980px wide / wrong scale when no viewport meta is set | No `<meta viewport>` → Chrome for Android falls back to a 980px layout width | [Chromium WebView `web-page-layout.md`](https://chromium.googlesource.com/chromium/src/+/master/android_webview/docs/web-page-layout.md) |
| 10 | `svh`/`dvh` do not shrink when the on-screen keyboard opens | Default `interactive-widget=resizes-visual` resizes only the visual viewport; CSS viewport units derive from the initial/layout viewport | [CSSWG css-viewport §3.4](https://drafts.csswg.org/css-viewport/) |

---

## Why doesn't `100vh` fill the screen correctly in a WebView?

Because the default `vh` unit is defined against the **large viewport**, not the currently visible one. The W3C CSS Values & Units 4 spec defines `vh`, `svh`, `lvh`, and `dvh` so that `vh == lvh` — the large viewport size, "assuming any UA interfaces that are dynamically expanded and retracted to be retracted." So `100vh` is the height with chrome hidden; when chrome is showing, `100vh` overshoots the visible area.

> "The large viewport-percentage units (`lv*`) and default viewport-percentage units (`v*`) are defined with respect to the large viewport size: the viewport sized assuming any UA interfaces that are dynamically expanded and retracted to be retracted." — [W3C CSS Values & Units 4 §6.1.2.1](https://www.w3.org/TR/css-values-4/#viewport-relative-lengths)

The spec is explicit that this is a web-compatibility decision, not an accident: "following Safari's lead, most UAs mapped these units to the larger size … However at this point the mapping to the large viewport-percentage units is presumed to be required for Web compatibility." MDN restates the rule plainly: "`vh` is equivalent to `lvh`" ([MDN `<length>`](https://developer.mozilla.org/en-US/docs/Web/CSS/length)).

**Fix:** use the small/dynamic viewport units. `svh` is the smallest (chrome shown), `dvh` tracks the current size, `lvh` is the largest. These shipped in Chrome/Edge 108, Firefox 101, and Safari 15.4 ([MDN `<length>`](https://developer.mozilla.org/en-US/docs/Web/CSS/length)), and Tailwind CSS exposed them as utilities (`h-svh`, `h-dvh`, `h-lvh`) in v3.4 ([Tailwind v3.4 blog](https://tailwindcss.com/blog/tailwindcss-v3-4)). For older WebViews lacking unit support, the long-standing fallback is to publish `innerHeight` into a CSS variable from JavaScript and consume it as `calc(var(--vh, 1vh) * 100)` ([CSS-Tricks "The trick to viewport units on mobile"](https://css-tricks.com/the-trick-to-viewport-units-on-mobile/)).

## Why is the WebView viewport height wrong right after the page loads on Android?

On Android, the viewport/`clientHeight` value can be wrong on the **first** load and only correct itself after a touch or an on-screen-keyboard toggle forces a re-layout. The Chromium tracker issue is titled "Wrong clientHeight value leads to dangerous layout shift on Android" ([Chromium issue 331326389](https://issues.chromium.org/issues/331326389), status Fixed), and it describes a first-load layout shift that can cause an unwanted click.

This is reproduced repeatedly in the wild. On Stack Overflow, `html { height: 100dvh }` draws a correct full-screen border until fullscreen mode, where "the page extends past the bottom… (Touching the screen, will cause the page to re-render, which fixes the issue)" on Chrome 116, Android 13 ([SO 77033005](https://stackoverflow.com/questions/77033005)). A separate report on a `display: standalone` PWA with `body { height: 100dvh }` says it "stopped calculating the height correctly on initial page load… If I open and close the on-screen keyboard… the forced height recalculation properly adjusts the visible height," on Chrome 142, November 2025 ([SO 79831083](https://stackoverflow.com/questions/79831083)). The Next.js community documents the same class of bug and the workaround of capturing `window.innerHeight` before interaction ([Next.js discussion #63724](https://github.com/vercel/next.js/discussions/63724)).

**Version note (honest):** the underlying Chromium bug 331326389 is reported as fixed in **Chrome M139** — but this is *corroborated indirectly*, not read from the tracker UI: the milestone is asserted by the bug reporter's own reproduction repo and the linked Next.js thread, not extracted from the gated tracker fields. Even with M139 in hand, the same symptom keeps recurring in PWA/standalone, older WebView, and iOS edge cases (the November 2025 PWA report above runs on Chrome 142). **Inferred/anecdotal, not spec-confirmed:** the common claim that a 1px programmatic resize is enough to clear the frozen viewport is not corroborated by any cited primary source; the reliably reported triggers are a real touch event or an on-screen-keyboard open/close.

## How do `svh`/`dvh` behave when the on-screen keyboard opens?

By default they do **not** shrink, because the keyboard resizes only the *visual* viewport, while CSS viewport units derive from the *initial/layout* viewport. The CSSWG css-viewport draft states that when `interactive-widget` is unset, "the behavior implied by `resizes-visual` is used as the default," and `resizes-visual` means UI widgets "MUST resize the visual viewport but MUST NOT resize the initial viewport" ([CSSWG css-viewport §3.4](https://drafts.csswg.org/css-viewport/)). Since `svh`/`dvh` are computed from the initial viewport, the keyboard leaves them unchanged.

**Fix:** if you need the layout to react to the keyboard, opt in with `interactive-widget=resizes-content` in the viewport meta tag, which resizes the initial viewport (and therefore both initial and visual). This is the same opt-in the Next.js community adopted (`interactiveWidget: 'resizes-content'`) ([Next.js discussion #63724](https://github.com/vercel/next.js/discussions/63724)).

## Why is `env(safe-area-inset-*)` zero or late inside a WebView?

On Android it can be reported as `0px`, and on iOS WKWebView it can arrive after first paint. The `@capacitor-community/safe-area` README states: "If a user has a Chromium version lower than 140… The `env(safe-area-inset-*)` values will be set to `0px`," and notes a separate keyboard issue: "The webview has another known bug to not properly report bottom insets when the keyboard is shown. Which will be fixed in Chromium 144" ([@capacitor-community/safe-area README](https://github.com/capacitor-community/safe-area/blob/master/README.md)).

On iOS the failure mode is timing rather than zero. The WebKit bug is titled "WkWebView does not set the `env(safe-area-inset-*)` CSS variables until some arbitrary time after page load," and its status is **NEW** — still open ([WebKit bug 191872](https://bugs.webkit.org/show_bug.cgi?id=191872)). The React Native WebView project mirrors both: issue #155, "Webview safe-area-inset-* CSS variables are not available on initial page load," notes "they are immediately available in iOS Safari" ([#155](https://github.com/react-native-webview/react-native-webview/issues/155)), and issue #3828, "`env(safe-area-inset-*)` always 0px in webview 138 or higher," reports the Android regression starting at WebView 138 ([#3828](https://github.com/react-native-webview/react-native-webview/issues/3828)).

**Version note (honest):** the Android `env()` safe-area fix lands around **Chromium M140** (correct insets) with the keyboard bottom-inset case fixed in **M144**, per the Capacitor plugin README. The README phrases it as "`< 140`" broken and "all other versions" correct, so "M140 correct" is an accurate paraphrase, not a verbatim milestone label. Note the React Native repro shows breakage already at WebView 138, so the exact threshold varies by report; the practical takeaway is that these gates matter mainly for **older WebViews**, and iOS WKWebView timing (bug 191872) remains unresolved regardless of version.

## Why does my first message to native get dropped on app cold start?

Because the JavaScript bridge object or its queue is not yet initialized when the page fires its first message; the message goes nowhere unless it is buffered and flushed once the bridge loads. The classic pattern is explicit in the WebViewJavascriptBridge setup snippet, which pushes callbacks onto `window.WVJBCallbacks` until the bridge exists and the native side drains the queue on load ([WebViewJavascriptBridge README](https://github.com/marcuswestin/WebViewJavascriptBridge/blob/master/README.md)).

```js
function setupWebViewJavascriptBridge(callback) {
  if (window.WebViewJavascriptBridge) { return callback(WebViewJavascriptBridge); }
  if (window.WVJBCallbacks) { return window.WVJBCallbacks.push(callback); }
  window.WVJBCallbacks = [callback];
  // ... native side flushes the queue once the bridge initializes
}
```

> **Mechanism caveat (honest):** the current (v6) snippet triggers bridge load via a hidden iframe pointing at `https://__bridge_loaded__`, *not* a `WebViewJavascriptBridgeReady` DOM event. The DOM-event form existed only in older (pre-v6) versions; the README explicitly warns you must update the snippet when upgrading from v5.0.x to 6.0.x. The buffer-and-flush *concept* is unchanged.

The same first-message reliability problem appears across frameworks. React Native WebView issue #1698 is "`window.ReactNativeWebView` in undefined on iOS and Android" — the bridge object is not yet available when code reads it ([#1698](https://github.com/react-native-webview/react-native-webview/issues/1698)). In `flutter_inappwebview`, issue #218 is "`window.flutter_inappwebview.callHandler is not a function`," and the documented fix is to gate the JS call on a `flutterInAppWebViewPlatformReady` event and register the Dart-side handler early ([#218](https://github.com/pichillilorenzo/flutter_inappwebview/issues/218)).

**Fix:** never assume the bridge exists at script-eval time. Buffer outbound messages (e.g., a `READY`/auth handshake) in a queue and flush them when the bridge signals it is loaded, and register native-side handlers before the page's JS can call them.

## How do I recover from a blank screen after the WebView renderer dies?

The crashed WebView cannot be reused — the host app must detect the renderer death, remove and destroy the dead instance, and create a new WebView. Android's official guidance provides the Termination Handling API:

> "`override fun onRenderProcessGone(view: WebView, detail: RenderProcessGoneDetail): Boolean { if (!detail.didCrash()) { // Renderer is killed because the system ran out of memory. The app can recover gracefully by creating a new WebView instance in the foreground. … } }`" — [Android "Manage WebView objects"](https://developer.android.com/develop/ui/views/layout/webapps/managing-webview)

The docs are explicit that the WebView whose renderer is gone must be removed from the hierarchy, destroyed, and replaced; returning `true` lets the app keep running. Hotwire Turbo implements exactly this in production code: turbo-android's `TurboSession.kt` overrides `onRenderProcessGone`, sets an `isRenderProcessGone` flag so the session is not reused, and returns `true` ([turbo-android `TurboSession.kt`](https://github.com/hotwired/turbo-android/blob/main/turbo/src/main/kotlin/dev/hotwire/turbo/session/TurboSession.kt)). The iOS analog is `webViewWebContentProcessDidTerminate(_:)` on the `WKNavigationDelegate`, which Turbo also implements (in turbo-ios `Session.swift`) to notify its delegate.

**Implication for the page side:** a bridge page must tolerate being reloaded into a fresh WebView at any time — it cannot assume in-memory JS state survives, so render inputs should be reconstructible from query params or a re-fetched state, and the `READY` handshake (above) must be idempotent.

## Why does iOS zoom in when I focus a text input?

iOS Safari/WebKit auto-zooms the viewport when a focused input's `font-size` is below 16px, as an accessibility heuristic:

> "If the `font-size` of an `<input>` is 16px or larger, Safari on iOS will focus into the input normally. But as soon as the `font-size` is 15px or less, the viewport will zoom into that input." — [CSS-Tricks "16px or Larger Text Prevents iOS Form Zoom"](https://css-tricks.com/16px-or-larger-text-prevents-ios-form-zoom/)

This is iOS/WebKit-specific (macOS Safari and non-iOS engines do not do it). **Fix:** set form-control `font-size` to at least 16px. The boundary is at 16px (16px and up = no zoom; 15px and below = zoom).

## How does Android font scaling affect a WebView page?

Two separate mechanisms apply, and they come from different sources. First, Android 14 added nonlinear font scaling up to 200%: "the system supports font scaling up to 200%… the system applies a nonlinear scaling curve," and as a result "`scaledDensity` … is no longer accurate" ([Android 14 features](https://developer.android.com/about/versions/14/features)). Second, the WebView has its own `WebSettings.setTextZoom`, "the text zoom of the page in percent. The default is 100% (no zoom)," documented in the Chromium WebView layout notes ([Chromium WebView `web-page-layout.md`](https://chromium.googlesource.com/chromium/src/+/master/android_webview/docs/web-page-layout.md)). `setTextZoom` is a long-standing WebView API and is **not** part of the Android 14 release notes — these are two independent knobs that can both inflate text. A bridge page must therefore be layout-robust to text that grows well beyond its design size.

## Why does no `<meta viewport>` make the page render at ~980px?

If the page does not declare a viewport meta tag, Chrome for Android falls back to a 980px layout width and fits-to-screen. The Chromium WebView layout table states verbatim that with "No viewport tag" the layout width is **980px** with initial scale "Fit on Screen," whereas `content="width=device-width"` yields a `device-width` layout at initial scale 1.0 ([Chromium WebView `web-page-layout.md`](https://chromium.googlesource.com/chromium/src/+/master/android_webview/docs/web-page-layout.md)). The same doc notes `setUseWideViewPort` defaults to `false`. **Fix:** always ship `<meta name="viewport" content="width=device-width, initial-scale=1">` (plus `viewport-fit=cover` when you rely on safe-area insets).

## Why do my timers drift or stop when the WebView is backgrounded?

A hidden or frozen page suspends freezable tasks and throttles chained timers, so `setTimeout`/`setInterval` do not fire on schedule. In the frozen state "the browser suspends execution of freezable tasks… This means things like JavaScript timers and fetch callbacks don't run" ([Chrome Page Lifecycle API](https://developer.chrome.com/docs/web-platform/page-lifecycle-api)). Chrome 88 (January 2021) "will heavily throttle chained JavaScript timers for hidden pages" — checked once per second under throttling, and once per minute under intensive throttling (hidden > 5 minutes, chain count ≥ 5) ([Chrome 88 timer throttling](https://developer.chrome.com/blog/timer-throttling-in-chrome-88)).

**Fix (flagged as inference):** the suspend/throttle mechanism is spec- and docs-confirmed, but the specific remediation — compute durations from an absolute timestamp (`Date.now()`) and recompute elapsed time on resume rather than trusting timer cadence — is **derived engineering guidance**, not a verbatim instruction in Chrome's official docs. The docs justify it (freeze/resume events let you record state and resume work) but do not literally prescribe "use an absolute timestamp."

---

## A note on `position: fixed` inside a frozen/oversized viewport

When the viewport height is wrong (pitfall #2) or the dynamic viewport disagrees with the layout viewport, a `position: fixed` CTA can render off-screen or under the app chrome. This is mechanism, not opinion: **`position: fixed` anchors to the layout (initial containing block / ICB) viewport**, so it follows the same frozen/large-viewport sizing that misplaced your full-height container. A reliable workaround is to anchor the bar with `position: absolute` against a positioned container sized in `svh`/`dvh` instead — **`absolute` resolves against the nearest positioned ancestor**, so the CTA is pinned to a box you control rather than to the misreported viewport. (The mechanism — fixed→ICB, absolute→nearest positioned ancestor — is standard CSS positioning; the claim that this specifically rescues the frozen-viewport CTA case is an applied inference, not a single-source citation.)

---

## Scope: when this still matters vs. already fixed upstream

| Pitfall | Already fixed upstream? | When it still bites you |
|---|---|---|
| `100vh` overshoot | Mitigated by `svh`/`dvh` (Chrome/Edge 108, Firefox 101, Safari 15.4) | WebViews older than those baselines; teams still hardcoding `100vh` |
| Android initial-load viewport freeze (Chromium 331326389) | Reported fixed in **Chrome M139** (corroborated indirectly, not read from tracker) | PWA/`standalone`, older WebViews, and iOS edge cases — still reproduced on Chrome 142 (Nov 2025) |
| Android `env(safe-area-inset-*)` = 0px | Fixed around **Chromium M140**; keyboard bottom-inset around **M144** | Chromium WebViews older than ~140 (RN reports breakage from WebView 138); needs the polyfill/plugin |
| iOS `env()` arrives late (WebKit 191872) | **Not fixed** — bug status NEW | All WKWebView versions; read insets after load or use a native bridge |
| First message dropped before bridge ready | Never "fixed" — it is inherent to bridge startup | Every cold start; you must buffer + flush |
| Renderer death → blank screen | Host APIs exist (`onRenderProcessGone`, `webViewWebContentProcessDidTerminate`) | Whenever the host does not recreate the WebView; the page must be reload-safe regardless |
| iOS sub-16px input auto-zoom | Behavior by design, not a bug to be fixed | Any iOS WebView with form `font-size < 16px` |
| Android nonlinear font scaling (200%) + `setTextZoom` | Platform features, not bugs | Any Android 14+ device with large accessibility text, or a host that sets `setTextZoom` |
| Background timer throttling | Platform behavior since Chrome 88 (Jan 2021) | Any backgrounded WebView running timers |
| Missing viewport meta → 980px | N/A (author error) | Any page shipped without `width=device-width` |

The pattern: roughly half of these are version-gated browser fixes that matter mainly for **older** WebViews, and the other half are inherent host behaviors (bridge timing, renderer lifecycle, input zoom, font scaling, timer throttling) that no browser version will ever "fix" for you. A bridge page has to handle both classes, which is precisely why a dedicated reference is warranted.

---

## FAQ

### Should I use `svh`, `lvh`, or `dvh` for a full-height WebView layout?

Use `svh` for the smallest viewport height class (browser chrome shown) when avoiding overflow matters, and `dvh` when layout should track current viewport size. `lvh` equals default `vh` (largest). These units shipped in Chrome/Edge 108, Firefox 101, and Safari 15.4; for older WebViews, fall back to a JS-set `--vh` variable.

### Is the Android initial-load viewport bug fixed?

Chromium issue 331326389 is reported fixed in Chrome M139, but that milestone is corroborated indirectly (the reporter's repo and a Next.js thread), not read from the tracker. The same symptom still recurs in standalone PWAs, older WebViews, and on iOS — a Chrome 142 PWA report from November 2025 shows it persisting — so do not assume it is gone.

### What triggers the frozen Android viewport to recalculate?

A real touch event or opening/closing the on-screen keyboard reliably forces the recalculation, per multiple Stack Overflow reproductions. The often-repeated claim that a 1px programmatic resize alone clears it is inferred/anecdotal and is not confirmed by any cited primary source.

### Why is `env(safe-area-inset-*)` zero on Android?

Chromium versions below ~140 do not correctly report safe-area insets and return `0px`, per the `@capacitor-community/safe-area` README; React Native WebView reports breakage from WebView 138. Correct reporting lands around Chromium M140, with the keyboard bottom-inset case around M144. On iOS, the insets are nonzero but arrive late (WebKit bug 191872, still open).

### How do I keep the first native message from being dropped?

Buffer outbound messages in a queue and flush them when the bridge signals it has loaded, and register native-side handlers before the page's JS runs. The WebViewJavascriptBridge `window.WVJBCallbacks` pattern, React Native WebView #1698, and `flutter_inappwebview` #218 all document the same buffer-until-ready requirement.

### How do I avoid a blank screen after a WebView crash?

The host must detect renderer death (`onRenderProcessGone` on Android, `webViewWebContentProcessDidTerminate` on iOS), destroy the dead WebView, and create a new one — the crashed instance cannot be reused. On the page side, make rendering reconstructible from query params or re-fetched state and keep the `READY` handshake idempotent so a reload into a fresh WebView recovers cleanly.

### How do I stop iOS from zooming in on input focus?

Set the `font-size` of form controls to at least 16px. iOS Safari/WebKit zooms when a focused input's font is 15px or smaller; 16px and above focuses without zooming. This is iOS/WebKit-specific behavior, not a bug.

---

*Sources are linked inline. Every cited claim is anchored to a spec section, a browser bug tracker entry, official platform documentation, or open-source framework source code, and is pinned to the relevant version/date where one exists. Indirectly corroborated and inferred claims are labeled as such in the body.*

---

## Related ecosystem references

The WebView skill is the knowledge layer: it describes the page-side contract,
layout, lifecycle, and diagnostics. Transport implementations and ecosystem
references remain useful, but none of them replaces the consolidated checklist.

### Bridge libraries and transport implementations

| Library | What it gives the web side |
| --- | --- |
| [gronxb/webview-bridge](https://github.com/gronxb/webview-bridge) | Type-safe React Native ↔ web bridge with a dedicated `@webview-bridge/web` package. |
| [daangn/metabridge](https://github.com/daangn/metabridge) | JSON-Schema-driven bridge codegen from one schema to typed web/native stubs. |
| [marcuswestin/WebViewJavascriptBridge](https://github.com/marcuswestin/WebViewJavascriptBridge) | Classic iOS JavaScript bridge family with `registerHandler` / `callHandler` style APIs. |
| [kibotu/jsbridge](https://github.com/kibotu/jsbridge) | One injected `bridge.js` API for Android `@JavascriptInterface` and iOS `WKScriptMessageHandler`. |
| [inokawa/react-native-react-bridge](https://github.com/inokawa/react-native-react-bridge) | Bundles a React app into a React Native WebView message bridge. |

### Engineering write-ups and platform docs

- [우아한형제들 — 플로팅웹뷰 도입기](https://techblog.woowahan.com/24165/) — native chrome overlapping web popups, safe-area, and page-to-page messaging.
- [Wonderwall — 웹뷰 브릿지 개선기](https://tech.wonderwall.kr/articles/webviewsinglebridge/) — single typed bridge entrypoint and version-branch reduction.
- [Toss 앱인토스 — WebView 시작하기](https://developers-apps-in-toss.toss.im/tutorials/webview.html) — production mini-app WebView docs, including SafeAreaInsets API.
- [CanIWebView](https://caniwebview.com/) — W3C WebView Community Group compatibility reference for Android WebView and WKWebView.
- [W3C WebView Community Group](https://www.w3.org/community/webview/) — standards-side effort on embedded WebView friction.
- [web.dev — Web on Android](https://web.dev/articles/web-on-android) — WebView vs Custom Tabs vs Trusted Web Activity from a web developer's perspective.

### Demand signal checked 2026-06-25

- `react-native-webview`: approximately 3.2M npm weekly downloads and 7k+ GitHub stars at the time of review.
- `@webview-bridge/web`: approximately 60k npm weekly downloads at the time of review.
- Small viewport-fix hooks exist but show low adoption, so this project keeps WebView diagnostics as skill guidance rather than shipping another generic viewport utility.

