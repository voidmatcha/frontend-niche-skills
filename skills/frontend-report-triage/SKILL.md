---
name: frontend-report-triage
description: "Use when the user gives a frontend bug report, QA note, screenshot description, support ticket, PR concern, or vague UI failure and wants one integrated pass across this skill pack. Triage across WebView, semantic markup, overlay focus/scroll, a11y contracts, CJK/IME, i18n, deep links, auth, frontend security, payment pages, exports, datetime, form validation, SSR hydration, design fidelity, and component extraction; return likely failure classes, evidence gaps, and 1-3 relevant follow-up skills."
---

# Frontend report triage

Use this skill as the front door for ambiguous or multi-symptom frontend reports. Do not load every sibling skill by default. First classify the report, identify evidence gaps, and route the smallest useful set of follow-up skills.

## Triage workflow

1. **Extract report facts** — user-visible symptom, environment, route/page, device/browser/WebView, reproduction steps, expected vs actual behavior, logs/screenshots/videos, and recent changes.
2. **Separate evidence channels** — layout, paint, hit-test, DOM, accessibility tree, URL/router state, network, storage, locale/input behavior, date/time, validation state, runtime scripts, exported files, and design reference.
3. **Score likely failure classes** — mark each class `likely`, `possible`, or `unlikely` with one short reason.
4. **Pick follow-up skills** — choose at most 3 unless the user explicitly asks for a broad audit. Prefer the most specific runtime evidence over generic categories.
5. **Ask for missing evidence only when needed** — if the next safe step is inspection, inspect. Ask for screenshots/videos/URLs/logs only when they would change the route or reduce risk.
6. **Hand off quickly** — if one sibling skill clearly owns the issue, name it and use that skill next.

## Failure class map

| Report signal | Likely follow-up skill |
| --- | --- |
| Native WebView, in-app browser, bridge messages, safe-area/keyboard, app resume, hit-test vs paint | `webview-bridge-pages` |
| Div/button/link/heading/label/list/table/interactive nesting concern | `semantic-markup-contracts` |
| Modal, drawer, sheet, popover, menu, command palette, focus trap, inert, aria-hidden, scroll lock, Escape/backdrop | `overlay-focus-scroll-contracts` |
| Dialog/menu/combobox/tab/custom widget role/name/state/focus regression | `a11y-contract-testing` |
| Korean/Japanese/Chinese input, IME, composition, Enter, grapheme length, CJK wrapping | `cjk-text-and-input` |
| Translation expansion, pluralization, bidi/RTL, locale formatting, hardcoded copy | `i18n-copy-and-layout` |
| Deep link, query params, router readiness, auth redirect landing on wrong page | `deeplink-hydration` |
| Login/signup/reset/OAuth/passkey/OTP/autocomplete/token storage/CSRF UI contract | `frontend-auth-flow-contracts` |
| XSS, raw HTML, sanitizer, CSP, opener, storage, URL parsing, third-party scripts outside payment | `frontend-security-baseline` |
| Checkout/payment/PAN/CVV/hosted fields/runtime scripts/CSP/SRI/PCI evidence | `payment-page-client-security` |
| CSV/Excel export, Blob URL, file download, clipboard, filename, export schema | `download-export-safety` |
| Timezone, DST, date-only input, `datetime-local`, relative time, server/client clock | `datetime-correctness` |
| Native validation, `setCustomValidity`, `reportValidity`, `:user-invalid`, invalid-to-valid clearing | `constraint-validation-contracts` |
| React Hook Form, Formik, Final Form, vee-validate, schema resolver, stale errors, disabled submit, async/server validation | `js-form-validation-contracts` |
| Hydration warning, server/client mismatch, randomness, locale/time, browser-only APIs, storage/auth state | `ssr-hydration-mismatch` |
| Figma/screenshot/design-reference mismatch, visual drift, pixel diff, missing states | `design-to-code-fidelity` |
| Duplicate components, wrapper-only abstractions, hook extraction, design-system boundary | `component-extraction-judgment` |

## Output shape

Return a compact triage result:

1. **Report facts** — what is known and what is missing.
2. **Ranked hypotheses** — top 1-3 failure classes with confidence and one reason each.
3. **Evidence gaps** — the smallest missing artifact that would change the route.
4. **Follow-up skills** — exact skill names in recommended order.
5. **First verification** — one concrete test, inspection, or reproduction step.

## Guardrails

- Do not claim a root cause from the report alone unless the report includes enough evidence.
- Do not route to security, payment, or compliance-adjacent skills without data-boundary or runtime-script evidence.
- Do not route to all skills. This is a ranking pass, not an exhaustive audit.
- If one sibling skill clearly owns the issue, hand off quickly instead of restating the full map.

## References

| File | Covers |
| --- | --- |
| [triage-examples.md](./references/triage-examples.md) | Worked triage outputs (WebView paint-vs-layout, overlay/scroll leak, form validity, payment page) to calibrate routing on vague or multi-symptom reports. |
