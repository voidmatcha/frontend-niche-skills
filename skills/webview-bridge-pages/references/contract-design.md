# Contract design (agree these with the app team)

Decisions to settle in the web↔native contract doc before writing page code.

## Message contract

- **Prefer one-way (WEB → native).** If the screen renders purely from URL params, do
  not add an inbound (`window.addEventListener('message')`) listener at all — fewer
  moving parts and no origin-validation surface.
- If inbound is unavoidable, validate origin and schema. Any iframe in the page can
  call the bridge too (Android `addJavascriptInterface` is injected into **every
  frame** with no origin control); the native side must also treat incoming payloads
  as untrusted input. Two real-world demonstrations of why: in Tauri, remote-origin
  iframes could reach the IPC endpoints without being allow-listed, letting an
  attacker-controlled iframe invoke real commands ("delete project", "transfer
  credits") — CVE-2024-35222, fixed in 1.6.7 / 2.0.0-beta.20 by requiring explicit
  origin/capability allow-listing. And the context that *renders* untrusted HTML must not itself hold
  native power: Joplin rendered note content in an Electron window with
  `nodeIntegration` enabled, so a note-content XSS escalated to remote code execution
  (CVE-2018-1000534). Keep the bridge off untrusted frames; keep native capability
  away from anything that renders untrusted content.
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
  (react-native-webview #2810 — thread points at `history.pushState` navigation).
  And it isn't RN-specific: in Tauri, Android `canGoBack()` returned `false` until the
  user physically touched the WebView, so a programmatically navigated page would exit
  the app on back-press despite having real history (tauri #13957). Design bridge
  screens as **single screens with native close**.
- Only add a WEB → native `CLOSE`-type message when the web itself must trigger
  dismissal.

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
- **Shared cookie session** — host-specific behavior (e.g. React Native WebView's
  `sharedCookiesEnabled` is an **iOS/macOS** prop, bridging `NSHTTPCookieStorage` into
  WKWebView's separate cookie store; Android's WebView already shares the cookie store,
  so the flag is a no-op there. Verify per host and OS version).
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
- Bridge security boundary — [CVE-2024-35222](https://nvd.nist.gov/vuln/detail/CVE-2024-35222)
  (Tauri: remote-origin iframes reached IPC without allow-listing; patched 1.6.7 /
  2.0.0-beta.20 per advisory GHSA-57fm-592m-34r7 — the NVD text's "beta.19" is still
  affected) · [CVE-2018-1000534](https://nvd.nist.gov/vuln/detail/CVE-2018-1000534)
  (Joplin: note-content XSS → RCE via Electron `nodeIntegration`) ·
  [tauri #13957](https://github.com/tauri-apps/tauri/issues/13957) (Android `canGoBack()`
  false until WebView interaction).
