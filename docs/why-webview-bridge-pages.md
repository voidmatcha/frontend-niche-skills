# Why a Dedicated Reference for WebView Bridge Pages Is Necessary: An Evidence Dossier

**A bridge page is an HTML/CSS/JS document loaded inside a native app's embedded WebView and wired to the native shell through a JavaScript message bridge.** It is not "just a web page": it runs inside a host (WKWebView on iOS, Android System WebView, or a framework wrapper such as React Native, Capacitor, or Flutter) whose viewport, lifecycle, safe-area, font-scaling, and JavaScript-bridge behavior diverge from a normal mobile browser tab in ways that are not obvious, are version-gated, and recur across unrelated projects. This dossier collects primary-source evidence (specs, browser bug trackers, official docs, and open-source framework code) showing those pitfalls are real and recurring enough to justify a dedicated reference.

> **Last checked: 2026-07-31.** Standards and official platform docs describe
> durable mechanisms. Bug status, support milestones, issue reports, and library
> guidance are dated observations, not guarantees for every WebView build.

---

## TL;DR

Building bridge pages inside native WebViews hits a fixed cluster of non-obvious, version-gated failures: `100vh` overshoots the visible area (use `svh`/`dvh`), the Android viewport height is wrong on initial load until a touch or keyboard toggle forces a recalculation, `env(safe-area-inset-*)` reports `0px` or arrives late, the native↔JS message bridge is not ready when your first message fires (so the message is dropped), and a renderer crash leaves a blank screen unless the host explicitly recreates the WebView. Every pitfall below is backed by a primary source — a spec, a browser bug tracker, official platform docs, or open-source framework code — and most are corroborated by multiple independent projects.

---

## Background: why this exists

A bridge page must survive a host environment that controls the viewport sizing, the safe-area insets, the page lifecycle (freeze/resume), and the timing of the bridge handshake. The failures below appear in browser specifications, browser-engine issue reports, official platform documentation, and the source of unrelated WebView wrappers. That convergence is the argument for a dedicated reference: generic responsive-web guidance does not own the host bridge and renderer lifecycle.

---

## How well-corroborated are these pitfalls?

Each row points to at least one opened source — a web standard, browser-engine issue, official platform document, or open-source implementation. Some rows have independent corroboration; others are explicitly issue- or project-specific and require target-runtime reproduction. The cited ecosystems include React Native WebView, Capacitor (`@capacitor-community/safe-area`), `flutter_inappwebview`, Hotwire Turbo, and WebViewJavascriptBridge alongside CSS specifications, browser issue trackers, and Android documentation.

For the complementary, source-line view — concrete defects this skill catches in real open-source code — see [open-source validation cases](./oss-validation-cases.md).

---

## Is a consolidated reference like this already available in open source?

Short answer: public guidance appears fragmented as of 2026-06. CSS/viewport writing (for example web.dev and CSS-Tricks viewport-unit posts) and native bridge/lifecycle writing (framework docs and engineering blogs) usually cover separate slices, so this reference consolidates the web-page-side cluster.

The closest existing resources each cover only a slice:

- **Library code, not author guidance:** [gronxb/webview-bridge](https://github.com/gronxb/webview-bridge) ships a typed RN↔web bridge with an `onReady` handshake, but it is runtime code covering the bridge axis only — no viewport, safe-area, renderer-death, or input-zoom guidance.
- **Single-framework docs:** [react-native-webview](https://github.com/react-native-webview/react-native-webview/blob/d65a961080dad3e82d33370ad6e8d90e973fcbd3/docs/Guide.md), Capacitor/Ionic, `flutter_inappwebview`, Apache Cordova, and Hotwire Turbo each document their own bridge/native-prop surface, but each is single-framework and native-prop-centric rather than a cross-host page-author reference.
- **Single-topic posts:** viewport (`100vh`/`svh`/`dvh`), iOS 16px input zoom, and "blank WKWebView after a crash" each have solid standalone write-ups, but none combines them.

In the non-exhaustive public snapshot opened for this pack, no single resource covered the bridge-handshake, target-specific initial viewport failure, and renderer-death recovery together. That is the narrower gap this reference fills; it is not an ecosystem-wide uniqueness claim.

---

## Problem → evidence table

| # | Pitfall (symptom) | Root cause / mechanism | Primary evidence |
|---|---|---|---|
| 1 | `100vh` is taller than the visible area; content sits under dynamic browser/app chrome | Default `vh` maps to the **large** viewport (`vh == lvh`) for web-compat; it assumes retractable UA chrome is retracted | [W3C CSS Values 4 §6.1.2.1](https://www.w3.org/TR/css-values-4/#viewport-relative-lengths); [MDN `<length>`](https://developer.mozilla.org/en-US/docs/Web/CSS/length) |
| 2 | A target Android WebView/browser reports wrong initial height that later changes | A Chromium issue and separate community reports capture related, environment-specific viewport failures | [Chromium issue 331326389](https://issues.chromium.org/issues/331326389); [Next.js discussion #63724](https://github.com/vercel/next.js/discussions/63724); [SO 77033005](https://stackoverflow.com/questions/77033005); [SO 79831083](https://stackoverflow.com/questions/79831083) |
| 3 | `env(safe-area-inset-*)` is zero or late in a target WebView | A Capacitor plugin documents version-gated Android workarounds; a WebKit issue reports delayed WKWebView variables | [Pinned `@capacitor-community/safe-area` README](https://github.com/capacitor-community/safe-area/blob/3042a26e278c7babf83c72c37fa0e1e9c0a32d35/README.md); [WebKit bug 191872](https://bugs.webkit.org/show_bug.cgi?id=191872); [react-native-webview #3828](https://github.com/react-native-webview/react-native-webview/issues/3828) / [#155](https://github.com/react-native-webview/react-native-webview/issues/155) |
| 4 | The first message to native (READY/auth) is dropped on cold start | The bridge object/queue may not be initialized when the page's first call fires; buffer until the host-specific ready signal | [Pinned WebViewJavascriptBridge README](https://github.com/marcuswestin/WebViewJavascriptBridge/blob/9a1ae72d99241065cdad6e56f9474c107820e61a/README.md); [react-native-webview #1698](https://github.com/react-native-webview/react-native-webview/issues/1698); [flutter_inappwebview #218](https://github.com/pichillilorenzo/flutter_inappwebview/issues/218) |
| 5 | Blank screen after the WebView renderer crashes or is killed for memory | Android requires removing and replacing the affected WebView; page state must be reconstructible | [Android "Manage WebView objects"](https://developer.android.com/develop/ui/views/layout/webapps/managing-webview); [Pinned Hotwire `TurboSession.kt`](https://github.com/hotwired/turbo-android/blob/daceb0a42109f4494e90a098e3cb4a9383369b79/turbo/src/main/kotlin/dev/hotwire/turbo/session/TurboSession.kt) |
| 6 | An iOS WebKit target zooms on small form-control text | The commonly reported `< 16px` threshold is authoring guidance rather than a standards-defined boundary; reproduce on the supported WKWebView matrix | [CSS-Tricks target-device reproduction](https://css-tricks.com/16px-or-larger-text-prevents-ios-form-zoom/); [Apple `ignoresViewportScaleLimits`](https://developer.apple.com/documentation/webkit/wkwebviewconfiguration/ignoresviewportscalelimits) |
| 7 | Layout breaks under large accessibility font scaling on Android | Android 14 supports nonlinear font scaling up to 200%; WebView text zoom is a separate host setting | [Android 14 features](https://developer.android.com/about/versions/14/features); [Pinned Chromium WebView layout notes](https://chromium.googlesource.com/chromium/src/+/63bff19b5ebeb07282b0845d31c5a2d2858e9619/android_webview/docs/web-page-layout.md) |
| 8 | Timers (`setTimeout`/`setInterval`) drift or stop when the WebView is backgrounded | Hidden/frozen pages suspend freezable tasks and throttle chained timers | [Chrome Page Lifecycle API](https://developer.chrome.com/docs/web-platform/page-lifecycle-api); [Chrome 88 timer throttling](https://developer.chrome.com/blog/timer-throttling-in-chrome-88) |
| 9 | Page renders at ~980px wide / wrong scale when no viewport meta is set | Chromium's documented no-viewport fallback uses a 980px layout width | [Pinned Chromium WebView layout notes](https://chromium.googlesource.com/chromium/src/+/63bff19b5ebeb07282b0845d31c5a2d2858e9619/android_webview/docs/web-page-layout.md) |
| 10 | Fixed UI is obscured when the on-screen keyboard opens | Browser viewport policy and in-app WebView host policy differ; do not assume `interactive-widget` controls an embedded host | [CSSWG css-viewport §3.4](https://drafts.csswg.org/css-viewport/); [Chrome viewport resize behavior](https://developer.chrome.com/blog/viewport-resize-behavior/) |

---

## Why doesn't `100vh` fill the screen correctly in a WebView?

Because the default `vh` unit is defined against the **large viewport**, not the currently visible one. The W3C CSS Values & Units 4 spec defines `vh`, `svh`, `lvh`, and `dvh` so that `vh == lvh` — the large viewport size, "assuming any UA interfaces that are dynamically expanded and retracted to be retracted." So `100vh` is the height with chrome hidden; when chrome is showing, `100vh` overshoots the visible area.

> "The large viewport-percentage units (`lv*`) and default viewport-percentage units (`v*`) are defined with respect to the large viewport size: the viewport sized assuming any UA interfaces that are dynamically expanded and retracted to be retracted." — [W3C CSS Values & Units 4 §6.1.2.1](https://www.w3.org/TR/css-values-4/#viewport-relative-lengths)

The spec is explicit that this is a web-compatibility decision, not an accident: "following Safari's lead, most UAs mapped these units to the larger size … However at this point the mapping to the large viewport-percentage units is presumed to be required for Web compatibility." MDN restates the rule plainly: "`vh` is equivalent to `lvh`" ([MDN `<length>`](https://developer.mozilla.org/en-US/docs/Web/CSS/length)).

**Fix:** prefer the unit whose semantics match the target: `svh` for the
small viewport, `dvh` for the dynamic viewport, and `lvh` for the large
viewport. Check current support for the WebView versions the host actually
ships. If a supported target lacks the units, a JS-published `innerHeight`
custom property is a compatibility option, but it needs resize, keyboard, and
rotation regression evidence rather than being installed unconditionally
([MDN `<length>`](https://developer.mozilla.org/en-US/docs/Web/CSS/length);
[CSS-Tricks fallback pattern](https://css-tricks.com/the-trick-to-viewport-units-on-mobile/)).

## Why is the WebView viewport height wrong right after the page loads on Android?

Chromium issue 331326389 documents a wrong `clientHeight` and dangerous layout
shift on Android. Separate community reports describe related first-load,
fullscreen, and standalone-PWA symptoms that change after touch or keyboard
activity ([Chromium issue 331326389](https://issues.chromium.org/issues/331326389);
[SO 77033005](https://stackoverflow.com/questions/77033005);
[SO 79831083](https://stackoverflow.com/questions/79831083);
[Next.js discussion #63724](https://github.com/vercel/next.js/discussions/63724)).

These reports do not establish one cross-version WebView invariant: they cover
different modes, browser builds, and host surfaces. Record initial
`innerHeight`, `documentElement.clientHeight`, `visualViewport.height`, host
insets, and the event that changes them on the failing target. Do not infer a
milestone or install a forced-resize workaround from the issue title alone.

## How do `svh`/`dvh` behave when the on-screen keyboard opens?

In browser contexts, the CSS viewport draft defines
`interactive-widget=resizes-visual` as the default: the visual viewport changes
while the initial viewport does not. Chrome documents
`interactive-widget=resizes-content` as a browser opt-in
([CSSWG css-viewport §3.4](https://drafts.csswg.org/css-viewport/);
[Chrome viewport resize behavior](https://developer.chrome.com/blog/viewport-resize-behavior/)).

An in-app WebView adds host window and keyboard policy, so the browser opt-in
is not proof that the embed will resize the same way. Measure both viewports on
the supported host, coordinate native inset/keyboard configuration, and keep
focused controls reachable without assuming a particular unit will shrink.

## Why is `env(safe-area-inset-*)` zero or late inside a WebView?

The pinned `@capacitor-community/safe-area` README documents its own
version-gated Android workaround and a keyboard bottom-inset issue. Treat those
numbers as the plugin maintainers' compatibility policy at that commit, not as
a general platform support matrix
([pinned README](https://github.com/capacitor-community/safe-area/blob/3042a26e278c7babf83c72c37fa0e1e9c0a32d35/README.md)).

WebKit bug 191872 reports delayed WKWebView values; its status was `NEW` when
rechecked on 2026-07-31. React Native WebView issues #155 and #3828 provide
wrapper-specific reproductions for delayed iOS values and zero Android values
([WebKit bug 191872](https://bugs.webkit.org/show_bug.cgi?id=191872);
[#155](https://github.com/react-native-webview/react-native-webview/issues/155);
[#3828](https://github.com/react-native-webview/react-native-webview/issues/3828)).
Use a runtime inset probe and host/app version matrix; do not convert one
wrapper's threshold into a universal WebView cutoff.

## Why does my first message to native get dropped on app cold start?

Because a host-specific bridge object or queue may not be initialized when the
page fires its first message. The classic WebViewJavascriptBridge pattern
pushes callbacks onto `window.WVJBCallbacks` until that bridge exists
([pinned README](https://github.com/marcuswestin/WebViewJavascriptBridge/blob/9a1ae72d99241065cdad6e56f9474c107820e61a/README.md)).

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

The docs are explicit that the affected Android WebView must be removed,
destroyed, and replaced; returning `true` lets the app keep running. Hotwire
Turbo's pinned `TurboSession.kt` marks a lost renderer so that session is not
reused ([pinned source](https://github.com/hotwired/turbo-android/blob/daceb0a42109f4494e90a098e3cb4a9383369b79/turbo/src/main/kotlin/dev/hotwire/turbo/session/TurboSession.kt)).

**Implication for the page side:** a bridge page must tolerate being reloaded into a fresh WebView at any time — it cannot assume in-memory JS state survives, so render inputs should be reconstructible from query params or a re-fetched state, and the `READY` handshake (above) must be idempotent.

## Why does iOS zoom in when I focus a text input?

Small form-control text can trigger focus zoom in iOS WebKit contexts. A widely
cited target-device reproduction reports this threshold:

> "If the `font-size` of an `<input>` is 16px or larger, Safari on iOS will focus into the input normally. But as soon as the `font-size` is 15px or less, the viewport will zoom into that input." — [CSS-Tricks "16px or Larger Text Prevents iOS Form Zoom"](https://css-tricks.com/16px-or-larger-text-prevents-ios-form-zoom/)

Treat `16px` as a conservative authoring mitigation, not a standards-defined
boundary across every OS/WebView version. Reproduce focus and blur on the
supported host. Avoid disabling user scaling: Apple documents that
`WKWebViewConfiguration.ignoresViewportScaleLimits` defaults to `false`, so a
default WKWebView honors author scale restrictions
([Apple documentation](https://developer.apple.com/documentation/webkit/wkwebviewconfiguration/ignoresviewportscalelimits)).

## How does Android font scaling affect a WebView page?

Two separate mechanisms apply. Android 14 introduced nonlinear font scaling up
to 200% ([Android 14 features](https://developer.android.com/about/versions/14/features)).
WebView also has a host-controlled text-zoom setting, documented separately in
the [pinned Chromium WebView layout notes](https://chromium.googlesource.com/chromium/src/+/63bff19b5ebeb07282b0845d31c5a2d2858e9619/android_webview/docs/web-page-layout.md).
Do not derive one from the other; verify layout with the OS accessibility scale
and the host's actual WebView setting.

## Why does no `<meta viewport>` make the page render at ~980px?

The pinned Chromium layout table documents a 980px layout width and
fit-to-screen initial scale for its no-viewport case, while
`width=device-width` yields device width at scale 1
([pinned layout notes](https://chromium.googlesource.com/chromium/src/+/63bff19b5ebeb07282b0845d31c5a2d2858e9619/android_webview/docs/web-page-layout.md)).
Ship an explicit viewport contract and verify host settings rather than
assuming mobile defaults.

## Why do my timers drift or stop when the WebView is backgrounded?

Chrome documents suspension of freezable tasks in a frozen page and throttling
of chained timers in hidden pages
([Page Lifecycle API](https://developer.chrome.com/docs/web-platform/page-lifecycle-api);
[timer throttling](https://developer.chrome.com/blog/timer-throttling-in-chrome-88)).
The host decides how an embedded WebView is backgrounded, so record
`visibilitychange`, page/host lifecycle, and elapsed wall time on the failing
surface before assigning the mechanism.

**Fix (flagged as inference):** the suspend/throttle mechanism is spec- and docs-confirmed, but the specific remediation — compute durations from an absolute timestamp (`Date.now()`) and recompute elapsed time on resume rather than trusting timer cadence — is **derived engineering guidance**, not a verbatim instruction in Chrome's official docs. The docs justify it (freeze/resume events let you record state and resume work) but do not literally prescribe "use an absolute timestamp."

---

## A note on `position: fixed` inside a frozen/oversized viewport

When the viewport height is wrong or the visual and layout viewports disagree,
a fixed CTA can render under host chrome. Fixed positioning normally uses the
viewport, while absolute positioning uses its containing block
([MDN `position`](https://developer.mozilla.org/en-US/docs/Web/CSS/position)).
Moving the bar into a measured positioned container can be a local workaround,
but it is an applied fix that needs geometry and hit-test evidence on the
failing host.

---

## Scope: durable mechanism vs. target-runtime evidence

| Pitfall | Durable contract | Evidence required before changing code |
|---|---|---|
| Viewport units | `vh`, `svh`, `dvh`, and `lvh` have different semantics | Computed units plus layout/visual viewport measurements on the shipped host |
| Initial viewport mismatch | Issue reports show target-specific failures | Cold-load trace before and after the event that changes geometry |
| Safe-area values | Insets cross native, viewport, and CSS boundaries | Computed `env()` value, native inset, host/engine version, rotation/keyboard state |
| Bridge readiness | Readiness is host-protocol state, not script-load state | Cold-start READY/auth ordering and bounded buffer/ack trace |
| Renderer death | The host recreates the renderer; page state must be reconstructible | Host termination callback and fresh-WebView recovery |
| Input focus zoom | Preserve readable controls and user scaling | Focus/blur reproduction on supported iOS/WKWebView targets |
| Font scaling | OS scale and host text zoom are separate inputs | Layout checks at supported accessibility and host zoom settings |
| Background time | Timer cadence is not a clock | Visibility/host lifecycle plus wall-clock reconciliation |
| Viewport metadata | Page and host jointly determine layout | Explicit meta tag, host settings, and measured layout width |

---

## FAQ

### Should I use `svh`, `lvh`, or `dvh` for a full-height WebView layout?

Use `svh` when the smallest viewport is the safe contract and `dvh` when
layout should track the current viewport; `lvh` matches the large viewport.
Check the actual embedded-engine matrix. Add a JS-set fallback only for a
supported target that lacks the required unit, and test its resize, rotation,
and keyboard lifecycle.

### Is the Android initial-load viewport bug fixed?

Do not answer from a browser milestone alone. Chromium issue 331326389 and the
community reports cover related but not identical environments. Reproduce a
cold load on the supported app/WebView pair and record the viewport values and
event sequence before classifying or removing a workaround.

### What triggers the frozen Android viewport to recalculate?

Touch and keyboard activity changed geometry in the cited reports; that does
not make either a reliable general-purpose repair. Record which event changes
the failing target and fix the page/host contract instead of synthesizing a
touch or resize.

### Why is `env(safe-area-inset-*)` zero on Android?

Possible causes include engine behavior, edge-to-edge host configuration,
viewport metadata, and wrapper-specific inset forwarding. The pinned Capacitor
README and React Native issues provide concrete versioned reports, not a
universal cutoff. Compare native and computed insets on the failing host.

### How do I keep the first native message from being dropped?

Buffer outbound messages in a queue and flush them when the bridge signals it has loaded, and register native-side handlers before the page's JS runs. The WebViewJavascriptBridge `window.WVJBCallbacks` pattern, React Native WebView #1698, and `flutter_inappwebview` #218 all document the same buffer-until-ready requirement.

### How do I avoid a blank screen after a WebView crash?

The host must detect renderer death (`onRenderProcessGone` on Android, `webViewWebContentProcessDidTerminate` on iOS), destroy the dead WebView, and create a new one — the crashed instance cannot be reused. On the page side, make rendering reconstructible from query params or re-fetched state and keep the `READY` handshake idempotent so a reload into a fresh WebView recovers cleanly.

### How do I stop iOS from zooming in on input focus?

Use readable form-control text; `16px` is a conservative, widely reproduced
mitigation. Preserve user scaling and verify focus/blur on the supported
WKWebView versions instead of treating the threshold as standards-defined.

---

*Sources are linked inline. Immutable repository sources are commit-pinned;
official living documentation and issue trackers are labeled as current or
dated observations. Community reports are reproduction leads rather than
platform-level evidence.*

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

The download/star figures above are a dated discovery snapshot and were not
re-fetched in the 2026-07-31 claim-entailment pass; do not reuse them as current
adoption numbers.
