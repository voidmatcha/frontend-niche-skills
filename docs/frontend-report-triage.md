# Frontend report triage

`frontend-report-triage` is the front door for ambiguous frontend bug reports. It is not an extra audit checklist and it should not run every skill. Its job is to turn a messy report into a small ranked plan.

## Why it exists

18 focused skills can feel like too much when a raw user report mentions several domains at once:

- "The modal is visible, but keyboard focus is behind it."
- "Korean users press Enter and search submits too early."
- "The checkout page uses Stripe, but it also loads analytics."
- "The CSV export opens in Excel and runs weird formulas."

Without a triage layer, agents may choose the first keyword they see or load too many skills. This skill keeps the pack usable by ranking likely failure classes first.

## Evidence status

This document contains synthetic routing examples, not external OSS defect evidence. Use it to pick follow-up skills and evidence gaps. Use [`skill-evidence-coverage.md`](./skill-evidence-coverage.md) to see each skill's evidence status. Use [`oss-validation-cases.md`](./oss-validation-cases.md), [`oss-maintainer-candidate-backlog.md`](./oss-maintainer-candidate-backlog.md), and per-skill references when you need source-backed examples.

## Triage result contract

A good triage result should include:

1. **Ranked hypotheses** — top 1-3 likely failure classes with confidence.
2. **Evidence gap** — the smallest missing artifact that would change the route.
3. **Follow-up skills** — exact skill names in recommended order.
4. **First verification** — one concrete inspection, test, or reproduction step.
5. **Boundary note** — what not to claim yet.

## Examples

| Report | Good route | Avoid |
| --- | --- | --- |
| "Clickable but invisible in WebView" | Separate layout, hit-test, paint, and host lifecycle evidence. | CSS retry or desktop Chrome-only fix. |
| "aria-hidden warning in modal" | Inspect active element, hidden subtree, focus restore, and scroll lock. | Generic a11y checklist without runtime state. |
| "CSV export user data" | Inspect final spreadsheet cells and formula policy. | Calling every CSV string a vulnerability. |
| "Payment page loads third-party scripts" | Inventory runtime scripts and PAN/CVV boundary. | Declaring payment compliance from source alone. |
| "Hydration warning after login redirect" | Separate URL state, auth state, and first-render determinism. | Treating it as only router or only SSR before evidence. |

## Relationship to the skill list

- README `Skills` shows the catalog by domain.
- README `Symptom map` helps humans find a skill directly.
- `frontend-report-triage` is for agents/users who start from a messy report and need a ranked path before choosing a domain skill.
