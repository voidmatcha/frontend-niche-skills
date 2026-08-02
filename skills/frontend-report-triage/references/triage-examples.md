# Frontend report triage examples

Use this reference when the report is vague or multi-symptom and examples help calibrate routing.

## Example outputs

### WebView paint vs layout

Report: "Button still works after app resume, but text disappears in React Native WebView."

- Likely classes: `webview-bridge-pages` high; `design-to-code-fidelity` low unless reference mismatch exists.
- Evidence: native WebView video, DOM box metrics, hit-test result, screenshot after resume.
- First verification: confirm whether box receives taps while child paint disappears.

### Browser iframe handshake and sizing

Report: "Our embedded widget is blank for some partners; when it does load, the iframe height flickers and login disappears in Safari."

- Likely classes: `iframe-embed-contracts` high; `frontend-security-baseline` medium only if the underlying cookie/CSP policy needs a site-wide change.
- Evidence: parent iframe attributes, guest response headers, exact parent/guest origins, READY/init message trace, height messages, and third-party storage behavior.
- First verification: reproduce with two real origins and reject a wrong-origin/wrong-source message before changing layout code.

### Modal warning and scroll leak

Report: "Console says aria-hidden blocked because focused element is hidden; after closing drawer page cannot scroll."

- Likely classes: `overlay-focus-scroll-contracts` high, `a11y-contract-testing` medium.
- Evidence: active element before/after open, aria-hidden/inert timing, body overflow before/after close.
- First verification: keyboard open/close test with focus restore and body style assertions.

### Form stays invalid after correction

Report: "URL field shows invalid after I fix it; submit stays disabled."

- Likely classes: `constraint-validation-contracts` if native validity APIs are used; `js-form-validation-contracts` if a library owns form state.
- Evidence: component code around validity/error state and submit disabled logic.
- First verification: invalid -> valid edit sequence test.

### Payment page concern

Report: "Checkout embeds a Stripe iframe but also loads analytics and chat widgets."

- Likely classes: `payment-page-client-security` high; `frontend-security-baseline` possible for broader script/CSP review.
- Evidence: runtime script inventory, PAN/CVV field ownership, CSP/SRI/header state.
- First verification: inspect runtime DOM/network while entering test card data; do not infer PCI scope from source files alone.

## Why this skill exists

41 focused skills can feel like too much when a raw user report mentions several domains at once:

- "The modal is visible, but keyboard focus is behind it."
- "Korean users press Enter and search submits too early."
- "The checkout page uses Stripe, but it also loads analytics."
- "The CSV export opens in Excel and runs weird formulas."

Without a triage layer, agents may choose the first keyword they see or load too many skills. This skill keeps the pack usable by ranking likely failure classes first.

## Routing quick reference

| Report | Good route | Avoid |
| --- | --- | --- |
| "Clickable but invisible in WebView" | Separate layout, hit-test, paint, and host lifecycle evidence. | CSS retry or desktop Chrome-only fix. |
| "aria-hidden warning in modal" | Inspect active element, hidden subtree, focus restore, and scroll lock. | Generic a11y checklist without runtime state. |
| "CSV export user data" | Inspect final spreadsheet cells and formula policy. | Calling every CSV string a vulnerability. |
| "Payment page loads third-party scripts" | Inventory runtime scripts and PAN/CVV boundary. | Declaring payment compliance from source alone. |
| "Hydration warning after login redirect" | Separate URL state, auth state, and first-render determinism. | Treating it as only router or only SSR before evidence. |

## Evidence status

This document contains synthetic routing examples, not external OSS defect evidence. Use it to pick follow-up skills and evidence gaps. Use [`skill-evidence-coverage.md`](../../../docs/skill-evidence-coverage.md) to see each skill's evidence status. Use [`oss-validation-cases.md`](../../../docs/oss-validation-cases.md) and per-skill references when you need source-backed examples.
