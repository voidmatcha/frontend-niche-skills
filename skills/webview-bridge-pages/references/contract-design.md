# Contract design (agree these with the app team)

Decisions to settle in the web↔native contract doc before writing page code.

## Message contract

- **Prefer one-way (WEB → native).** If the screen renders purely from URL params, do
  not add an inbound (`window.addEventListener('message')`) listener at all — fewer
  moving parts and no origin-validation surface.
- If inbound is unavoidable, validate origin and schema. Any iframe in the page can
  call the bridge too (Android `addJavascriptInterface` is injected into **every
  frame** with no origin control); the native side must also treat incoming payloads
  as untrusted input.
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
  behaves unreliably with SPA client-side routing on some Android devices
  (react-native-webview #2810 — thread points at `history.pushState` navigation;
  same class of issue exists on other hosts). Design bridge screens as
  **single screens with native close**.
- Only add a WEB → native `CLOSE`-type message when the web itself must trigger
  dismissal.

## Actions with unobservable results (purchases etc.)

When the web sends a request (e.g. `REQUEST_PURCHASE`) and the result lands natively
(IAP sheet), the web cannot observe cancel/failure in a one-way design:

- **Never disable the button after sending.** With no re-enable signal, one cancelled
  purchase kills the CTA permanently.
- Write into the contract doc: native ignores duplicate requests while one is in flight
  (the OS payment sheet is modal anyway), and native closes the screen on success.

## Loading signal (blank-screen prevention)

- Document load (`onLoadEnd` / `didFinish` / `onPageFinished`) ≠ content rendered.
  The `load` event "doesn't necessarily correspond with anything the user cares about"
  (web.dev); Android docs state that an `onPageFinished` callback "does not guarantee
  that the next frame drawn by WebView will reflect the state of the DOM at this
  point"; SPA frameworks render meaningful content only after hydration
  (Next.js: `router.query` is empty until then).
- For screens where a blank cold load is costly (payment, onboarding): app shows a
  native loading state, web posts a `READY`-type message after first meaningful render,
  app swaps with a timeout fallback. Load-finished callbacks cannot detect a broken JS
  bundle (they fire on failure too); `READY` proves the web app actually ran.
- Skip the signal for low-stakes screens — it costs an app-side loading + timeout
  policy.
- **Pair READY with an error policy** in the same contract: what the app does when
  `READY` never arrives (timeout → fallback or dismiss), what the page shows on its
  own API failures (web-owned error state with retry — native can't see them),
  bridge-unavailable = noop by design, and who logs which telemetry (exposure and
  purchase events app-side; page errors web-side).

## Auth & session handoff

Decide in the contract where identity comes from — in order of preference:

- **None** — the page renders purely from params (simplest; no identity surface).
- **Shared cookie session** — host-specific behavior (e.g. React Native WebView has a
  `sharedCookiesEnabled` prop for Android; verify per host and OS version).
- **Bridge-injected token** — app sends it after a handshake message; note this
  requires an inbound message, weigh against the one-way preference.
- **Query-param token — avoid.** URLs leak into server logs, browser history, and
  referrer headers; treat any token that touched a URL as exposed.

## Navigation & capabilities

Bridge screens should be single screens — but define in the contract what happens
when the page would navigate or use device capabilities:

- External links: in-app, system browser, or blocked? Deep links into other native
  screens: which scheme/route? Downloads, `<a download>`, file inputs/camera,
  permission prompts: several of these **silently no-op or behave differently inside
  WebViews** — don't assume browser behavior; test the specific host.
- The app side typically enforces the policy via navigation interception
  (e.g. RN `onShouldStartLoadWithRequest`, `originWhitelist`); the web side should not
  emit navigations that aren't in the agreed policy.

## A/B variants via query params

- One Remote Config key per experiment variable → one query param each. The app reads
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
  WKScriptMessageHandlerWithReply; react-native-webview docs + issue #2810.
