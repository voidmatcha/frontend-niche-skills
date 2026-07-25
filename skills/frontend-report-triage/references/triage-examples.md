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
