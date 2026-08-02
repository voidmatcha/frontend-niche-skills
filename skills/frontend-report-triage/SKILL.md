---
name: frontend-report-triage
description: "Use when the user gives a frontend bug report, QA note, screenshot description, support ticket, PR concern, or vague UI failure and wants one integrated pass across this skill pack. Rank the relevant runtime, browser, data, accessibility, security, performance, design, and maintenance failure classes; return evidence gaps and the 1-3 most specific follow-up skills instead of loading the whole catalog."
---

# Frontend report triage

Use this skill as the front door for ambiguous or multi-symptom frontend reports. Do not load every sibling skill by default. First classify the report, identify evidence gaps, and route the smallest useful set of follow-up skills.

## Triage workflow

1. **Extract report facts** — user-visible symptom, environment, route/page, device/browser/WebView, reproduction steps, expected vs actual behavior, logs/screenshots/videos, and recent changes.
2. **Separate evidence channels** — layout, paint, hit-test, DOM, accessibility tree, URL/router state, network/cache/stream, storage, iframe/WebView messages, delivered policies/headers, locale/input behavior, date/time, validation state, runtime scripts, exported files, performance traces, and design reference.
3. **Score likely failure classes** — mark each class `likely`, `possible`, or `unlikely` with one short reason.
4. **Pick follow-up skills** — choose at most 3 unless the user explicitly asks for a broad audit. Prefer the most specific runtime evidence over generic categories.
5. **Ask for missing evidence only when needed** — if the next safe step is inspection, inspect. Ask for screenshots/videos/URLs/logs only when they would change the route or reduce risk.
6. **Hand off quickly** — if one sibling skill clearly owns the issue, name it and use that skill next.

## Failure class map

| Report signal | Likely follow-up skill |
| --- | --- |
| Native WebView, in-app browser, bridge messages, safe-area/keyboard, app resume, hit-test vs paint | `webview-bridge-pages` |
| Browser iframe/embed/widget, parent-guest postMessage, sandbox/allow, READY/init, dynamic height, embedded storage | `iframe-embed-contracts` |
| Browser Back/Forward restores stale state, duplicates resources, or exposes bfcache eligibility/lifecycle problems | `browser-page-lifecycle-bfcache-contracts` |
| SPA Back/Forward or same-document hash navigation restores the wrong scroll position, double-scrolls after async rendering, or misses a fragment target | `history-scroll-restoration-contracts` |
| Camera/microphone permission, device selection/change, MediaStreamTrack state, teardown, or reacquisition fails | `media-capture-device-contracts` |
| Div/button/link/heading/label/list/table/interactive nesting concern | `semantic-markup-contracts` |
| Modal, drawer, sheet, popover, menu, command palette, focus trap, inert, aria-hidden, scroll lock, Escape/backdrop | `overlay-focus-scroll-contracts` |
| Single-pointer drag/swipe/resize/draw loses active-pointer ownership or event delivery, sticks after cancellation, or conflicts with native scrolling; not pinch/rotate/multi-contact geometry | `pointer-gesture-contracts` |
| Dialog/menu/combobox/tab/custom widget role/name/state/focus regression | `a11y-contract-testing` |
| View Transitions API silently aborts, freezes on an old snapshot, ignores reduced motion, or ghosts | `view-transitions-contracts` |
| CSS enter/exit transition is cut off, or cleanup waits forever for transition completion | `css-transition-animation-contracts` |
| Responsive image chooses the wrong candidate, over-downloads, lazy-loads the hero, or causes CLS | `responsive-image-contracts` |
| Contenteditable/rich-text caret or selection jumps, one edit is applied twice, undo breaks, paste/drop lands at the wrong range, composition is replaced, or stale selection work runs after teardown | `contenteditable-selection-contracts` |
| Korean/Japanese/Chinese input, IME, composition, Enter, grapheme length, CJK wrapping | `cjk-text-and-input` |
| Translation expansion, pluralization, bidi/RTL, locale formatting, hardcoded copy | `i18n-copy-and-layout` |
| Money/quantity total, rounding, minor units, exact-integer range, or localized amount parsing | `money-and-precision-contracts` |
| Deep link, query params, router readiness, auth redirect landing on wrong page | `deeplink-hydration` |
| WebSocket/SSE reconnect, resume cursor, duplicate/gapped deltas, zombie connection, backpressure, socket auth | `realtime-transport-contracts` |
| Login/signup/reset/OAuth/passkey/OTP/autocomplete/return-target UI contract | `frontend-auth-flow-contracts` |
| Popup, clipboard, share, picker, fullscreen, or payment API fails outside valid user activation | `user-activation-contracts` |
| XSS, raw HTML, sanitizer, CSP, opener, storage, URL parsing, third-party scripts outside payment | `frontend-security-baseline` |
| Frontend-owned BFF/API proxy, client-selected target/path, multipart relay, alternate ingress, forwarded auth/headers | `bff-proxy-security-contracts` |
| Checkout/payment/PAN/CVV/hosted fields/runtime scripts/CSP/SRI/PCI evidence | `payment-page-client-security` |
| Files entering the page through drag-drop, picker, paste, directories, type checks, or preview URLs | `file-ingest-contracts` |
| CSV/Excel export, Blob URL, file download, clipboard, filename, export schema | `download-export-safety` |
| Timezone, DST, date-only input, `datetime-local`, relative time, server/client clock | `datetime-correctness` |
| Native validation, `setCustomValidity`, `reportValidity`, `:user-invalid`, invalid-to-valid clearing | `constraint-validation-contracts` |
| React Hook Form, Formik, Final Form, vee-validate, schema resolver, stale errors, disabled submit, async/server validation | `js-form-validation-contracts` |
| Hydration warning, server/client mismatch, randomness, locale/time, browser-only APIs, storage/auth state | `ssr-hydration-mismatch` |
| Figma/screenshot/design-reference mismatch, visual drift, pixel diff, missing states | `design-to-code-fidelity` |
| Duplicate components, wrapper-only abstractions, behavior reuse, variant sprawl, design-system boundary | `component-extraction-judgment` |
| Optimistic mutation flickers, duplicates, fails to roll back, or races a refetch/temp-id swap | `optimistic-update-rollback-contracts` |
| Frontend errors are missing, minified, reduced to `Script error.`, fragmented, or leaking sensitive context | `client-error-observability-contracts` |
| LCP/CLS/INP/TTFB fails and needs element/shift/long-task/response attribution | `core-web-vitals-performance-contracts` |
| Client data cache is stale after mutation, collides on keys, waterfalls, or refetches too much/little | `frontend-data-fetching-cache-contracts` |
| IndexedDB upgrade is blocked, a browser-local write becomes inactive or aborts, saved data disappears, quota/persistence evidence is misread, or recovery overstates durability | `browser-storage-durability-contracts` |
| Raw async effect has stale-response wins, missing abort/cleanup, StrictMode duplication, or stale closure | `async-effect-race-contracts` |
| Service worker serves a stale build/chunk, misses precache, mishandles update/eviction, or caches auth data | `pwa-offline-cache-contracts` |
| Virtualized list/grid jumps, loses focus/find-in-page/a11y totals, or drifts pinned layout | `large-list-data-grid-contracts` |
| ResizeObserver loops, writes size back into its own measurement, measures the wrong box, or leaks old targets | `resize-observer-layout-contracts` |

## Output shape

Return a compact triage result:

1. **Report facts** — what is known and what is missing.
2. **Ranked hypotheses** — top 1-3 failure classes with confidence and one reason each.
3. **Evidence gaps** — the smallest missing artifact that would change the route.
4. **Follow-up skills** — exact skill names in recommended order.
5. **First verification** — one concrete test, inspection, or reproduction step.
6. **Boundary note** — what not to claim yet.

## Guardrails

- Do not claim a root cause from the report alone unless the report includes enough evidence.
- Do not route to security, payment, or compliance-adjacent skills without data-boundary or runtime-script evidence.
- Do not route to all skills. This is a ranking pass, not an exhaustive audit.
- If one sibling skill clearly owns the issue, hand off quickly instead of restating the full map.

## References

| File | Covers |
| --- | --- |
| [triage-examples.md](./references/triage-examples.md) | Worked triage outputs (WebView paint-vs-layout, browser iframe handshake/sizing, overlay/scroll leak, form validity, payment page) to calibrate routing on vague or multi-symptom reports. |
