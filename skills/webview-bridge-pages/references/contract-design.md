# Contract design (agree these with the app team)

Decisions to settle in the web↔native contract doc before writing page code.

## Message contract

- **Prefer one-way (WEB → native).** If the screen renders purely from URL params, do
  not add an inbound (`window.addEventListener('message')`) listener at all — fewer
  moving parts and no origin-validation surface.
- If inbound is unavoidable, validate origin and schema. Any iframe in the page can
  call the bridge too (Android `addJavascriptInterface` is injected into **every
  frame** with no origin control), so the native side must treat incoming payloads as
  untrusted — remote-origin iframes have reached bridge/IPC endpoints with no
  allow-listing (Tauri CVE-2024-35222). Keep the bridge off untrusted frames, and keep
  native capability away from anything that renders untrusted HTML. (General HTML-sink
  XSS hardening and CSP belong to **frontend-security-baseline**; the bridge-specific
  rule here is origin+schema validation on every inbound message.)
- One shape for every message: `{ type: string, data?: object }`, `JSON.stringify`
  once. Keep `type` constants + payload types in one module, mirrored with the app's
  handler definitions. Strong typing on both sides catches misspelled actions at
  compile time.
- Request/reply exists natively on some hosts (iOS 14+ `WKScriptMessageHandlerWithReply`
  returns a Promise; Android `addWebMessageListener` gives a reply proxy) — use it only
  when the host set is fixed; a cross-host contract should assume fire-and-forget.

## Native chrome owns close/back

- **Let the app render and handle the close (X) button and the Android hardware back
  button.** The web page draws no close UI. Benefits: no inbound listener needed,
  Android back handled natively, exit-confirmation flows stay in one place.
- Layout around the native button: reserve the status-bar height plus the agreed
  button area (per platform/notch) so content never sits under native chrome.
- **Do not rely on WebView history for SPA pages.** WebView `goBack()`/history
  behaves unreliably with SPA client-side routing on Android: after an in-SPA
  navigation `canGoBack` reads false and both native `goBack()` and injected
  `history.back()` fail, while the same code works on iOS (react-native-webview #3100;
  #2810 related). Tauri on Android hits a related but distinct `canGoBack()`
  unreliability — it reads false after programmatic navigations until the user first
  taps the WebView (#13957). Design bridge screens as **single
  screens with native close** (exception: multi-step funnels — see below).
- Only add a WEB → native `CLOSE`-type message when the web itself must trigger
  dismissal.
- **Multi-step funnels are the exception — decide back semantics explicitly.** If one
  webview hosts a multi-step flow (signup, checkout, onboarding), the default (native
  closes on back) dumps users out of the funnel on the first back press. Pick one in
  the contract: (a) **web owns intra-funnel history** — `history.pushState` per step +
  a `popstate` handler — but this inherits the Android flakiness above, so track your
  own step index rather than trusting `canGoBack`, and verify hardware-back and
  edge-swipe per host; or (b) **native forwards back, web decides** — native fires one
  inbound `BACK` event and takes no native action; the web steps back by its own step
  index, or at step 1 sends a `CLOSE` message so native dismisses (the established
  Capacitor App-plugin `backButton` pattern, copied by Tauri PR #14133 — registering the
  listener disables native's default back entirely, so there is no native "consumed"
  reply). If the event carries a `canGoBack` field it is just the WebView's own
  unreliable `canGoBack()` — advisory at most; never let it drive the close decision.
  Adds one inbound listener — weigh against the one-way preference.

## Actions with unobservable results (purchases etc.)

When the web sends a request (e.g. `REQUEST_PURCHASE`) and the result lands natively
(IAP sheet), the web cannot observe cancel/failure in a one-way design:

- **Never permanently disable the button after sending unless the contract includes
  an explicit native ack/result or a web-side timeout.** With no re-enable signal,
  one cancelled purchase kills the CTA permanently.
- Write into the contract doc: native ignores duplicate requests while one is in flight
  (the OS payment sheet is modal anyway), and native closes the screen on success.

## Loading signal (blank-screen prevention)

- Document load (`onLoadEnd` / `didFinish` / `onPageFinished`) ≠ content rendered.
  The `load` event "doesn't necessarily correspond with anything the user cares about"
  (web.dev); Android docs state that an `onPageFinished` callback "does not
  guarantee that the next frame drawn by WebView will reflect the state of the DOM
  at this point"; SPA frameworks render meaningful content only after hydration
  (Next.js: `router.query` is empty until then).
- For screens where a blank cold load is costly (payment, onboarding): app shows a
  native loading state, web posts a `READY`-type message after first meaningful render,
  app swaps with a timeout fallback. Load-finished callbacks cannot detect a broken JS
  bundle (they fire on failure too); `READY` shows the web app actually ran.
- Skip the signal for low-stakes screens — it costs an app-side loading + timeout
  policy.
- **Pair READY with an error policy** in the same contract: what the app does when
  `READY` never arrives (timeout → fallback or dismiss), what the page shows on its
  own API failures (web-owned error state with retry — native can't see them),
  bridge-unavailable = noop by design, and who logs which telemetry (exposure and
  purchase events app-side; page errors web-side).
- **The renderer can die mid-session, not just on cold load.** iOS WKWebView's
  out-of-process WebContent can be killed under memory pressure
  (`webViewWebContentProcessDidTerminate` — which itself sometimes doesn't fire,
  rn-webview #2559); Android fires `onRenderProcessGone` (API 26+), after which the
  WebView can't be reused and must be recreated. The page comes back **blank with no JS
  state**. Native owns the recreate/reload; the web-side rule is the cold-load rule
  again — keep the screen reconstructable from params/native and **re-post `READY` on
  every (re)load** so native can re-handshake (restore route/scroll). Never assume
  in-memory DOM/JS state survived.

## Auth & session handoff

Decide in the contract where identity comes from — in order of preference. (Scope: this
is only the **WebView handoff** — where identity originates once the page is already
inside a native session; login/signup/returnTo flows → **frontend-auth-flow-contracts**,
token storage / CSP / cookie SameSite → **frontend-security-baseline**.)

- **None** — the page renders purely from params (simplest; no identity surface).
- **Shared cookie session** — host-specific behavior (e.g. React Native WebView's
  `sharedCookiesEnabled` is an **iOS/macOS** prop, bridging `NSHTTPCookieStorage` into
  WKWebView's separate cookie store; Android's WebView already shares the cookie store,
  so the flag is a no-op there. Verify per host and OS version).
- **Bridge-injected token** — app sends it after a handshake message; note this
  requires an inbound message, weigh against the one-way preference.
- **Query-param token — avoid.** URLs leak into server logs, browser history, and
  referrer headers; treat any token that touched a URL as exposed.
- **Never initiate OAuth/social login inside the webview.** Google rejects
  authorization requests from embedded webviews with `403: disallowed_useragent`
  (all embedded webviews blocked since 2021, per RFC 8252 native-app guidance);
  other IdPs behave similarly. A "Sign in with …" button rendered in a bridge page
  dead-ends with no web-side recovery. The contract must route login through the
  system browser (Android Custom Tabs / iOS `ASWebAuthenticationSession`) via a
  bridge message or deep link, with the app re-entering the page with the session.

## Navigation & capabilities

Bridge screens should be single screens — but define in the contract what happens
when the page would navigate or use device capabilities:

- External links: in-app, system browser, or blocked? Deep links into other native
  screens: which scheme/route? Downloads, `<a download>`, file inputs/camera,
  permission prompts: several of these **silently no-op or behave differently inside
  WebViews** — don't assume browser behavior; test the specific host.
- **New-window navigations are a distinct path**: `target="_blank"` / `window.open`
  don't hit the same interception hooks as plain navigations. iOS cancels them unless
  the app implements `WKUIDelegate` `webView(_:createWebViewWith:…)` (JS `window.open`
  additionally gated by `javaScriptCanOpenWindowsAutomatically`, default off); Android
  requires `setSupportMultipleWindows(true)` + `WebChromeClient.onCreateWindow`, and
  these requests bypass `shouldOverrideUrlLoading`. Web-side rule: bridge pages emit
  **no new-window navigations** — same-window nav the app intercepts, or an
  `OPEN_EXTERNAL`-type bridge message. (Opener-leak / `rel=noopener` concerns in plain
  browsers → **frontend-security-baseline**.)
- **`input[type=file]` dead-taps on Android hosts** unless the app implements
  `WebChromeClient.onShowFileChooser`; the page cannot detect the miss (silent no-op,
  works fine in browsers and WKWebView). Confirm support in the contract, gate/hide
  upload UI on host capability, or route the upload through a bridge message —
  mechanism → [android-webview](./android-webview.md).
- The app side typically enforces the policy via navigation interception
  (e.g. RN `onShouldStartLoadWithRequest`, `originWhitelist`); the web side should not
  emit navigations that aren't in the agreed policy.

## A/B variants via query params

- One remote-config key (Firebase Remote Config, an in-house flag system — any
  assignment source) per experiment variable → one query param each. The app reads
  the keys and composes the URL. Orthogonal slots compose; whole-URL swapping explodes
  combinatorially with parallel experiments.
- Implement each axis as an independent slot: text variants as a
  `Record<VariantType, i18nKey>` map, visual variants as CSS-class modifiers, block
  variants as conditional render. Adding a variant = one union member + one map line.
- Keep a separate base-URL config key for emergency URL swaps.
- Metrics: prefer logging exposure/clicks/conversion on the **app side** (it knows the
  assigned variants); web analytics is secondary — beware double counting.

## Sources

- web.dev "User-centric performance metrics"; Android `WebViewClient.onPageFinished`
  reference; Next.js Automatic Static Optimization docs; Zellic "WebView security";
  Android "Access native APIs with JavaScript bridge"; Apple WKUserContentController /
  WKScriptMessageHandlerWithReply; react-native-webview docs + issues #2810/#3100.
- Renderer-death recovery: Apple `WKNavigationDelegate.webViewWebContentProcessDidTerminate`;
  Android `WebViewClient.onRenderProcessGone` (API 26+); react-native-webview #2199 / #2559.
- Bridge security boundary: [CVE-2024-35222](https://nvd.nist.gov/vuln/detail/CVE-2024-35222)
  (Tauri remote-origin iframes reached IPC without allow-listing) ·
  [tauri #13957](https://github.com/tauri-apps/tauri/issues/13957) (Android `canGoBack()`
  unreliable). Funnel back option (b): Capacitor App-plugin `backButton`, adopted by
  Tauri PR #14133.
- OAuth-in-webview block: Google Developers Blog
  ["Upcoming security changes to Google's OAuth 2.0 authorization endpoint in embedded webviews"](https://developers.googleblog.com/en/upcoming-security-changes-to-googles-oauth-20-authorization-endpoint-in-embedded-webviews/)
  and Google's `disallowed_useragent` remediation FAQ; IETF
  [RFC 8252](https://datatracker.ietf.org/doc/html/rfc8252) (OAuth 2.0 for Native Apps).
- New-window path: Apple
  [`webView(_:createWebViewWith:for:windowFeatures:)`](https://developer.apple.com/documentation/webkit/wkuidelegate/webview(_:createwebviewwith:for:windowfeatures:))
  (navigation canceled when unimplemented/nil); Android
  [`WebChromeClient.onCreateWindow`](https://developer.android.com/reference/android/webkit/WebChromeClient)
  (+ `setSupportMultipleWindows`); in the wild:
  [Capacitor #798](https://github.com/ionic-team/capacitor/issues/798)
  (`window.open` `target=_blank` silently ignored).
