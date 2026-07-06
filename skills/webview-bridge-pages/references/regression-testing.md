# WebView regression testing evidence

WebView regressions need separate evidence tiers. Do not treat one browser test as proof for every host.

## Evidence tiers

1. **Unit/component tests**
   - Use for copy, query parsing, timer math, price formatting, message payload shape, and pure render contracts.
   - Does not establish browser/WebView layout or old engine compatibility.

2. **Fast browser/Playwright check**
   - Use for route/query behavior, visual snapshots, and forced feature-detection marker branches.
   - Good for as-is/to-be screenshots and fast fallback regression.
   - Not proof that an old Android WebView can parse/render the page.

3. **Android actual-engine check**
   - Use Android emulator, WebView Shell (`org.chromium.webview_shell` — the bare
     system-WebView harness preinstalled on emulator images), or the app package that
     hosts the WebView. Chrome is a supporting check only: Chrome and the WebView
     provider are separate packages that can differ in version and behavior.
   - Capture screenshot, console/logcat, loaded URL, Android API, device/AVD, and WebView/Chrome package version.
   - At minimum, compare the affected old engine with one modern Android/WebView control.
     Pinning an old engine usually means an emulator system image old enough to ship the
     affected WebView, with auto-update disabled — Play-enabled images and retail devices
     update WebView on first sync, so a fresh modern emulator cannot reproduce old-engine bugs.

4. **App integration check**
   - Required when the claim includes RN bridge, safe-area query injection, deep links, auth/API, QA menus, close/back behavior, payments, or native lifecycle.
   - Android/iOS app WebView evidence should be reported separately from direct browser/WebView Shell evidence.

5. **iOS WebKit/WKWebView check**
   - Simulator Safari direct URL is a WebKit layout smoke only.
   - App deeplink/QA route is WKWebView integration evidence.
   - Use physical device evidence for release candidates or issues involving payment, keyboard, notch/safe-area, GPU/compositing, or hardware-specific rendering.


## Runtime preflight before editing

Before changing WebView page code, freeze the runtime facts that can make a correct web fix look broken:

- App build: installed package/bundle is from the commit under test.
- Entry path: deeplink, QA menu, or direct URL is the intended route.
- Loaded URL: observed WebView URL matches the claim, not only the requested URL.
- Network path: local server, DNS/VPN, `adb reverse`, and API environment are known separately.
- Runtime identity: Android API/model/WebView or Chrome package version, or iOS simulator/device + WebKit/WKWebView path.
- Orientation state: initial orientation and any rotation sequence are recorded.

If any item is unknown, treat the next step as environment diagnosis, not UI fixing.

## Hypothesis and scope guard

Do not convert a WebView symptom directly into a CSS or bridge patch. First split the symptom by axis:

- JS compatibility or hydration failure.
- CSS/layout/safe-area fallback.
- Native WebView container size, background, or rotation timing.
- Bridge lifecycle, close/back ownership, or first message delivery.
- Asset/API/data failure.
- Paint/compositing failure distinct from hit testing.

Keep one fix to one confirmed axis. If a bridge change, dummy asset fallback, layout max-width change, and CSS fallback all seem helpful, split them into separate patches unless one experiment shows they share the same root cause. Treat prior incidents, teammate theories, and loaded skills as candidate generators, not evidence.

## When to run what

| Change type | Minimum evidence | Add when risk is WebView-specific |
| --- | --- | --- |
| Copy/parser/query only | Unit/component | Browser smoke if visible text or CTA contract changed |
| CTA/native message | Unit/component + browser smoke | App WebView smoke |
| SCSS layout, ribbon, price, RTL, localized wrapping | Browser/Playwright visual matrix | Android/iOS screenshots when old engine or WebKit risk exists |
| JavaScript syntax/API compatibility, polyfill, transpile target | Browser smoke + marker branch if applicable | Affected Android actual-engine capture |
| CSS fallback for `gap`, `dvh`, safe-area, visual viewport, fixed CTA | Forced marker visual regression + modern branch comparison | Android actual-engine + app WebView if native params are involved |
| Deep link, auth/API, QA menu, close/back/native lifecycle | App WebView evidence | Browser tests are only supporting checks |
| Stage/release WebView launch | Browser regression suite | Affected old engine + modern Android control + iOS evidence |

## Visual regression for WebView CSS fallbacks

Use visual regression for layout-affecting WebView fixes, especially CSS polyfills or legacy markers. The useful question is not only "does the branch run?" but "does the branch render the same intended UI?"

Minimum matrix:

- **Modern default:** marker/fallback off on a supported browser/runtime.
- **Forced fallback:** marker/fallback on in the same browser/runtime to show the CSS branch stays visually aligned.
- **Affected actual engine:** old Android WebView or app WebView where the marker/fallback is naturally needed.
- **Control runtime:** modern Android/WebView or iOS/WebKit when the code path could leak into supported engines.

Rules:

- Capture before and after when changing fallback CSS.
- Compare same route, viewport, DPR, locale, content payload, feature flags, safe-area params, and dynamic time.
- Include design-sensitive extremes: long localized labels, RTL, large discount/price values, fixed CTA, and narrow width.
- Treat Playwright forced-marker snapshots as fast regression evidence, not legacy engine proof.
- Do not update snapshots until the diff is explained as a fix or accepted intentional difference.
- If actual-engine screenshots differ from Playwright screenshots, debug by WebView/Chrome version first, then Android OS/device.

## Android workflow

Official anchors:

- Chrome DevTools documents Android WebView remote debugging via app-side `WebView.setWebContentsDebuggingEnabled(true)` and `chrome://inspect`.
- Android `WebView.VisualStateCallback` / `postVisualStateCallback` documents visual-state readiness; do not treat `onPageFinished` alone as final visual proof.
- Android emulator CLI supports `-avd`, `-dns-server`, and `-no-snapshot-load`.

Workflow:

1. Start the target AVD with any required DNS settings.
2. Verify device/API/WebView identity before judging the UI.
3. Open the URL in WebView Shell or the target app package.
4. Capture screenshot, logcat/console, URL, and device metadata.
5. Repeat on a modern Android/WebView control.
6. If bridge/safe-area/deeplink/auth is part of the claim, repeat through the app WebView.

Useful metadata commands:

```sh
adb shell getprop ro.build.version.release
adb shell getprop ro.build.version.sdk
adb shell getprop ro.product.model
adb shell dumpsys webviewupdate | grep -E 'Current WebView|versionName|Package'
adb shell dumpsys package com.google.android.webview | grep -E 'versionName|versionCode'
```

## Android VM pain points and automation targets

Common failure modes are environmental, not UI regressions. Separate them before debugging CSS:

- AVD not visible or not booted; `adb devices` empty or unauthorized.
- Local server not reachable from emulator; missing `adb reverse tcp:<port> tcp:<port>`.
- Required DNS/VPN unavailable; hostname fails while direct IP works.
- WebView URL and API environment confused: local web URL can still call a non-local API.
- App setup, QA menu, or deeplink preconditions block the target WebView.
- WebView/Chrome package differs across same Android OS versions.
- Screenshots taken before visual state settles.

Automate toward a single capture command that:

1. Boots or selects a named AVD.
2. Prints device/API/model/WebView version.
3. Applies DNS and `adb reverse` settings.
4. Opens the target URL or app deeplink.
5. Waits for a stable visual signal, not only page load.
6. Captures screenshot, logcat/console, URL, and metadata into one run directory.
7. Repeats the same matrix on a modern control device.

## iOS workflow

Official anchors:

- Apple Safari Developer Tools documents inspecting iOS/iPadOS web content from Mac using simulators to test webpages and apps.
- Apple WebKit documents `WKWebView.isInspectable` on iOS 16.4+ for Safari Web Inspector access to app WKWebView content.

Workflow:

1. Boot the target simulator.
2. Direct URL capture is Safari/WebKit smoke only.
3. Use an app deeplink or QA route for WKWebView integration evidence.
4. Do not close release/payment/keyboard/notch/GPU issues on simulator evidence alone when device-specific behavior is plausible.

## Report format

Include:

- URL environment: local, development, staging, or production.
- API environment separately from WebView URL environment.
- Evidence tier: browser, Android Shell, Android app, iOS Safari simulator, iOS app WKWebView, or physical device.
- Device/AVD/simulator, OS/API/runtime, and WebView/Chrome version where applicable.
- Screenshot/report path and visual regression artifact path.
- Whether fallback marker was forced or the actual engine naturally took the branch.
- DNS/API/auth blocker status.


## Sources

Use these as source anchors when updating this reference:

- Chrome DevTools: Android WebView remote debugging uses app-side `WebView.setWebContentsDebuggingEnabled(true)` and `chrome://inspect` (<https://developer.chrome.com/docs/devtools/remote-debugging/webviews>).
- Android docs: the WebView debugging page was restructured into a "Debug web apps" overview (<https://developer.android.com/develop/ui/views/layout/webapps/debugging>) that no longer shows `setWebContentsDebuggingEnabled` inline — the app-side flag + DevTools flow is documented in the Chrome DevTools guide above and the [`WebView` API reference](https://developer.android.com/reference/android/webkit/WebView#setWebContentsDebuggingEnabled(boolean)).
- Android adb docs: `adb forward` and `adb shell screenrecord` are documented platform tools (<https://developer.android.com/tools/adb>). `adb reverse` is an adb capability commonly required for emulator-to-host local servers; verify with `adb help` on the local SDK version.
- React Native WebView upstream reference: `window.ReactNativeWebView.postMessage` is injected when `onMessage` is set, and `data` must be a string ([react-native-webview/docs/Reference.md](https://github.com/react-native-webview/react-native-webview/blob/master/docs/Reference.md)).
- Appium context guide: native app and WebView contexts are separate; switching context changes what element lookup/interaction means (<https://appium.io/docs/en/latest/guides/context/>).
- Maestro upstream docs: `takeScreenshot` saves a PNG and `assertScreenshot` compares against a known-good screenshot for visual regression (`mobile-dev-inc/maestro-docs`).
- Local Xcode `xcrun simctl io help`: documents `screenshot` and `recordVideo` operations; it does not expose an absolute orientation setter, so any iOS rotation automation must state its mechanism and limitation.
