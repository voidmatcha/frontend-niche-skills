---
name: payment-page-client-security
description: "Use when reviewing checkout/payment pages for frontend-owned payment security: Stripe/Adyen/Braintree/Razorpay/PayPal hosted fields, iframes, redirects, wallets, direct card forms; PAN/CVV/CVC/cardholder data in DOM, React/Vue/Svelte state, logs, analytics, storage, URLs, replay tools; payment-page runtime script inventory, tag managers, third-party scripts, CSP/SRI/header controls, PCI DSS 6.4.3/11.6.1 evidence, SAQ A vs SAQ A-EP scope signals. This does not decide legal PCI scope, SAQ eligibility, or QSA acceptance. Route token-storage/CSP/XSS to frontend-security-baseline; route WebView-host payment pages to webview-bridge-pages."
---

# Payment page client security

Use this as a **payment-page evidence pass**, not as a generic security checklist and not as PCI certification. The goal is to collect reviewer-ready evidence about whether card data stays out of merchant JavaScript, payment-page scripts are known and justified, and script/header tamper signals are observable.

## Scope and non-goals

- Cover browser/client code, checkout page composition, hosted payment iframes/fields, redirects, CSP/SRI/header evidence, logs, storage, analytics, tag managers, replay tools, and payment-page script monitoring.
- Do not decide legal PCI scope, SAQ eligibility, QSA acceptance, or whether a site is "PCI compliant." Say "PCI evidence/risk discussion," not "compliance verdict."
- For generic XSS, token storage, open redirects, or CSP hardening outside payment context, use `frontend-security-baseline` first.
- For native WebView bridge messages around checkout, pair this with `webview-bridge-pages`.

## Workflow

1. **Classify payment architecture.** Identify redirect, hosted iframe, hosted fields, wallet, direct merchant card form, saved-card flow, or non-card flow. This determines what frontend code can see.
2. **Draw the PAN boundary.** PAN/CVV/CVC should not enter merchant-controlled DOM inputs, framework state, logs, analytics, storage, URLs, replay tools, error breadcrumbs, or telemetry unless the project intentionally owns full cardholder-data handling.
3. **Inventory browser-executed code on the payment path.** List first-party, third-party, inline, dynamically injected, tag-manager, analytics, chat, A/B, replay, and payment-provider scripts that actually execute on checkout/payment URLs. `package.json` source imports are not enough.
4. **Check authorization and justification evidence.** Each payment-path script should have an owner, purpose, approved source, and business/technical justification. "Loaded by GTM" is not justification by itself.
5. **Check integrity and tamper evidence.** Prefer provider-compatible controls: narrow CSP (`script-src`, `connect-src`, `frame-src`, `form-action`), nonces/hashes for first-party inline code, SRI only where bytes are stable, and change detection/alerts for payment-page scripts and security-impacting headers.
6. **Separate risk from compliance claims.** Map findings to PCI DSS 6.4.3 / 11.6.1 / SAQ A signals only as reviewer-facing evidence. Escalate ambiguous scope to a payment/security owner.

## Default-looking traps

| Trap | Why it matters | Better direction |
| --- | --- | --- |
| "We use Stripe/Adyen/Braintree, so PCI is solved" | Hosted providers reduce card-data handling, but merchant page scripts can still attack or overlay embedded fields. | Verify integration mode, TPSP guidance, and script-attack protections around the embedded payment surface. |
| Merchant-controlled `<input>` captures card number/CVV | PAN/CVV can enter framework state, logs, storage, analytics, replay, and error reports. | Use hosted fields/iframe/redirect/tokenization so merchant JS never handles raw card data. |
| Payment page includes tag manager, analytics, chat, replay, or A/B by default | These tools can inject or load more scripts and may observe sensitive payment context. | Remove them from payment paths or require explicit owner, purpose, allowlist, and runtime monitoring. |
| Script inventory equals `package.json` imports | PCI-style evidence concerns scripts executed in the consumer browser, including dynamic third-party chains. | Capture runtime script/iframe/header inventory from the actual payment URL. |
| Broad CSP allowlist (`https:`, `*.cdn.com`, whole tag-manager origins) | Broad origins weaken meaningful script authorization. | Use minimal origins, first-party nonces/hashes, `strict-dynamic` where appropriate, and roll out report-only first. |
| SRI pasted onto dynamic payment-provider scripts | Some payment vendors require live scripts whose bytes change; incorrect SRI can break checkout or create false confidence. | Follow provider guidance; use CSP, runtime inventory, and change/tamper detection where SRI is not stable or supported. |
| Client validation/logging handles full card data | "Temporary" validation or debug logging is still cardholder-data exposure. | Validate through provider components; mask only last4 after tokenization; scrub telemetry. |
| SAQ A assumed while merchant page scripts affect payment iframe/form | SAQ A eligibility depends on implementation and script-attack protection; assumptions can change scope discussions. | Gather evidence and ask the acquirer, QSA, or payment owner. Treat SAQ A vs A-EP as a decision, not an agent verdict. |

## Quick probes

Use these as leads, then verify data flow and runtime behavior:

```sh
# Payment surfaces and providers
rg -n -i 'checkout|payment|billing|card(number)?|\bpan\b|cvv|cvc|expiry|stripe|adyen|braintree|paypal|razorpay|square|klarna|checkout\.com' src/ pages/ app/ public/ 2>/dev/null

# Card data accidentally entering state, logs, storage, URLs, telemetry, replay, or analytics
rg -n -i 'card(number)?|\bpan\b|cvv|cvc|expiry' src/ pages/ app/ public/ 2>/dev/null \
  | rg -i 'useState|store|localStorage|sessionStorage|console\.|logger|sentry|analytics|gtag|dataLayer|hotjar|fullstory|posthog|segment|url|searchParams'

# Runtime-script risk indicators near checkout
rg -n -i '<script|dangerouslySetInnerHTML|innerHTML|insertAdjacentHTML|eval\(|new Function\(|GTM-|dataLayer|gtag|analytics|chat|intercom|hotjar|fullstory|posthog|segment' src/ pages/ app/ public/ 2>/dev/null

# Header/policy ownership in common frontend stacks
rg -n -i 'Content-Security-Policy|script-src|frame-src|connect-src|form-action|integrity=|crossorigin=|headers\(|next\.config|helmet|vercel\.json|netlify\.toml' . 2>/dev/null
```

Browser evidence to collect when a runnable app exists:

- URL route containing the payment element.
- Runtime script/iframe inventory: external script URLs, inline script count/hashes if available, and dynamically added scripts after interaction.
- Security-impacting headers: CSP, `frame-ancestors`, `X-Frame-Options` if relevant, HSTS, and SRI/crossorigin on static third-party assets.
- Storage/log evidence: no PAN/CVV/CVC in local/session storage, query params, console logs, analytics payloads, error breadcrumbs, or replay tooling.

## PCI evidence mapping

Read [pci-payment-page-scope](./references/pci-payment-page-scope.md) when the user asks about PCI DSS, SAQ A/A-EP, or payment-page script monitoring.

Use this mapping carefully:

- **6.4.3-style evidence**: scripts on payment pages are authorized, integrity-assured, inventoried, and have business/technical justification.
- **11.6.1-style evidence**: a change/tamper-detection mechanism alerts on unauthorized changes to payment-page scripts and security-impacting HTTP headers.
- **SAQ A signal**: even where 6.4.3/11.6.1 are not directly in SAQ A, merchants still need confidence that the site is not susceptible to script attacks affecting e-commerce systems. A TPSP/payment processor may provide part of this evidence.

## PR-worthiness gate

File a payment-page finding only with concrete evidence: PAN/CVV/CVC crossing into merchant-controlled DOM, framework state, logs, storage, URLs, or telemetry, or a runtime script/CSP/SRI gap observed on the actual payment path — not speculation from imports or provider names.
Reject weak findings: "we use Stripe, so PCI is solved," a `package.json` import that never executes at runtime, a broad-CSP note with no payment-path script, or SRI proposed for a provider script whose bytes are expected to change.
Minimal useful PR: one PAN-boundary fix (hosted field/iframe/tokenization or telemetry scrub), one payment-path script removed or justified with owner and allowlist, or one narrowed CSP/header plus a runtime-inventory or change-detection artifact.

## Output shape

Return concise findings:

- **Payment architecture**: redirect / hosted iframe / hosted fields / wallet / direct PAN / unclear.
- **PAN boundary**: what merchant JS can or cannot see, with evidence.
- **Script surface**: runtime scripts and high-risk loaders on the payment path.
- **Risk**: exploitable data flow or missing evidence, not just a grep hit.
- **PCI evidence impact**: 6.4.3 / 11.6.1 / SAQ signal, phrased as an evidence gap.
- **Fix**: the narrowest frontend change or evidence artifact needed.
- **Verification**: runtime capture, header check, regression test, or monitoring/inventory artifact that would detect this gap reopening.

## References

| File | Covers |
| --- | --- |
| [pci-payment-page-scope.md](./references/pci-payment-page-scope.md) | PCI DSS 6.4.3 / 11.6.1 script-authorization and change-detection evidence, SAQ A vs A-EP scope signals, and official source anchors. |
