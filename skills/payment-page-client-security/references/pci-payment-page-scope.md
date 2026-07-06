# PCI payment-page scope notes

Use this reference to avoid overclaiming. Agents can identify frontend evidence and risk, but cannot certify PCI compliance, choose an SAQ type, or replace QSA/acquirer/payment-owner decisions.

## What PCI DSS 6.4.3 and 11.6.1 are about

PCI SSC describes PCI DSS v4.x Requirements 6.4.3 and 11.6.1 as controls that reduce e-commerce skimming risk by ensuring payment-page scripts are authorized, integrity-checked, inventoried, and monitored for tampering.

Practical evidence:

- **6.4.3**: every script executing on the payment page has authorization, integrity assurance, and an inventory entry with technical/business justification.
- **11.6.1**: unauthorized changes to payment-page scripts and security-impacting HTTP headers are detected and alerted on. PCI SSC guidance discusses targeted risk analysis and cadence where applicable.

The payment page is not just "the card input iframe." Parent-page scripts can affect embedded payment elements, overlay UI, intercept clicks, or change the security posture of the payment flow.

## SAQ A / SAQ A-EP caution

Public PCI SSC guidance says SAQ A eligibility criteria changed for e-commerce merchants. SAQ A no longer directly includes 6.4.3 and 11.6.1, but merchants still must confirm the site is not susceptible to script attacks that could affect e-commerce systems. PCI SSC FAQ guidance says this may be supported by techniques like those in 6.4.3/11.6.1 or by confirmation from a PCI DSS-compliant TPSP/payment processor that the embedded payment page/form solution protects against script attacks when implemented as instructed.

Agent output should say:

- "This is an evidence gap for SAQ/compliance review."
- "This may affect the SAQ A vs SAQ A-EP discussion."
- "Ask the acquirer, QSA, or payment owner."

Do not say:

- "This site is/is not PCI compliant."
- "This definitely qualifies for SAQ A."
- "This definitely requires SAQ A-EP."

## Open-source prior art found

- `mr-yum/pci-dss-page-tampering` — very low-star but closest public OSS match found. It implements inventory, detection, and validation workflows for PCI DSS 6.4.3 / 11.6.1: staging inventory discovers scripts/headers, production detection compares against approved inventory, and CI validates inventory files. The README notes the repository is largely agent-developed, so treat it as prior art, not proof of demand.
- `shyshlakov/pci-dss-mcp` — very low-star MCP scanner focused on Go payment services. It is broader PCI DSS service-code analysis, with payment-page script checks among other checks. Useful as a comparison point, not a replacement for frontend runtime evidence review.
- `OWASP/www-project-pci-dss-toolkit` — OWASP project repository with low GitHub signal. Useful mostly for terminology/checklist framing, not mature frontend tooling.

This means the niche skill should not pretend to replace scanners. Its useful layer is judgment: classify the payment architecture, trace whether PAN/CVV crosses the merchant-JS boundary, decide whether third-party scripts actually run on the payment path, and translate missing artifacts into concrete evidence requests.

## Sanitization/XSS boundary

If a payment page renders CMS, marketing, or rich HTML near checkout, use `frontend-security-baseline` for raw HTML and CSP details. Payment risk is higher because XSS can overlay or observe a payment form and defeat intended hosted-field isolation.

## Sources

- PCI SSC Blog — [FAQ Clarifies New SAQ A Eligibility Criteria for E-Commerce Merchants](https://blog.pcisecuritystandards.org/faq-clarifies-new-saq-a-eligibility-criteria-for-e-commerce-merchants)
- PCI SSC Blog — [New Information Supplement: Payment Page Security and Preventing E-Skimming](https://blog.pcisecuritystandards.org/new-information-supplement-payment-page-security-and-preventing-e-skimming)
- PCI SSC Document Library — [PCI DSS v4.0.1 SAQ guidance](https://www.pcisecuritystandards.org/document_library/)
- GitHub — [`mr-yum/pci-dss-page-tampering`](https://github.com/mr-yum/pci-dss-page-tampering)
- GitHub — [`shyshlakov/pci-dss-mcp`](https://github.com/shyshlakov/pci-dss-mcp)
