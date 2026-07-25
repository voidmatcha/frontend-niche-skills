---
name: component-extraction-judgment
description: "Use when component-based frontend code has near-duplicate components, copy-pasted cards/rows/banners, boolean-prop variant sprawl, wrapper-only components, duplicated hooks/composables/handlers, or AI-generated UI that needs a decision: extract a shared component, create thin wrappers, reuse behavior, or deliberately keep implementations separate without breaking design fidelity, accessibility, i18n, or data contracts. Framework-agnostic judgment for React, Vue, Svelte, Web Components, and similar component systems; route to design-to-code-fidelity, a11y-contract-testing, or i18n-copy-and-layout for those dimensions."
---

# Component extraction judgment

Use before refactoring generated or organically grown frontend UI into shared components — the goal is not "deduplicate everything" but choosing the reuse boundary that preserves product semantics, design fidelity, accessibility contracts, and testability.

## Evidence tiers

| Tier | Claim allowed | Evidence required |
| --- | --- | --- |
| T1 | Safe extraction candidate | Two or more concrete source locations, same user-facing semantics, same accessibility role/name/state contract, same design variant axis, and a targeted regression test path. Optional framework-specific duplicate scanners may support the finding, but the final decision still needs code evidence. |
| T2 | Plausible extraction candidate | Similar structure and props are visible, but one contract dimension still needs confirmation (design token, responsive state, copy/i18n, loading/empty state, focus behavior, or data shape). |
| T3 | Smell only | Duplication is suspected from names, screenshots, or token overlap, but source locations or contracts are not confirmed. Do not edit yet. |
| T4 | Blocked / not judged | Missing source, missing design authority, generated bundle only, no safe test path, or the change would require product/API decisions. |

Only T1 is implemented as a refactor. T2/T3 become a cleanup plan or TODO with the explicit missing evidence; T4 is reported as blocked with the specific missing input, not edited.

## Workflow

1. **Freeze the contract before merging.** For every candidate, list component names/files, caller contexts, user-visible purpose, design/token authority, accessibility role/name/state, i18n/copy ownership, data shape, loading/error/empty states, and responsive breakpoints.
2. **Find candidate clusters.** Prefer existing repo evidence: repeated JSX/template/SFC structure, prop/event names, slots/snippets/children, CSS/class token sets, copied handlers/hooks/composables, repeated mapping logic, or duplicated fixtures/stories/tests. If a framework-specific scanner is already installed or explicitly allowed (React: `react-unify scan <src>`, `duplicalis scan`), run it for leads only — scanners stay read-only/`--propose` (never auto-apply); do not add dependencies just to inspect.
3. **Classify the duplication.** Use the smallest fitting category:
   - `prop-parameterizable`: same component; differences are data/text/icon/color props.
   - `slot-composition`: same shell, variable inner content — use the framework's composition primitive (slot/children/snippet/render prop).
   - `thin-wrapper`: shared primitive is safe; old exported names/routes remain wrappers.
   - `logic-reuse`: UI differs; hook/composable/controller/state-machine logic is duplicated.
   - `style-token`: repeated visual treatment belongs in tokens/classes/primitives, not a mega-component.
   - `false-friend`: code looks similar, but semantics, state, accessibility, design variant, or lifecycle differ.
4. **Choose the boundary.** Apply the decision matrix; reuse behavior via the framework's narrow mechanism (hook/composable/controller/action/store slice) that imports no presentation; keep local helpers/data maps when extraction would blur the public API.
5. **Lock behavior.** Add the smallest regression: component test for props/states, `getByRole`/accessible-name assertions, visual/story snapshots for design-sensitive variants, or type tests for discriminated unions.

## Decision matrix

| Decision | Use when | Avoid when |
| --- | --- | --- |
| Extract shared component | Same semantic role, state model, interaction contract, and design primitive; differences are named props or data. | Props become `showX`, `isFoo`, `variant="custom"`, or callers need escape hatches immediately. |
| Shared primitive + wrappers | Existing names carry route/domain meaning but render through the same primitive. | Wrappers only rename every prop without preserving domain defaults or tests. |
| Behavior helper | Logic (formatting, sorting, keyboard handling, async state) repeats while UI differs. | The helper would import presentation details or make state ownership unclear. |
| Token/class extraction | Repeated colors/spacing/radius/shadows should follow design-system tokens. | It hides one-off product exceptions or bypasses a stronger design-to-code fidelity check. |
| Keep separate | Similar shape hides different semantics, roles, copy ownership, business rules, responsive behavior, or roadmap. | "They might diverge someday" is the only reason and current contracts are identical. |

## Red flags before editing

- Boolean-trap API: ~3+ variant booleans is a rough smell, not a hard rule — mutually exclusive flags that should collapse into one discriminated `variant` prop matter more than the count.
- Component accepts both domain data and presentation escape hatches (`className`, `style`, arbitrary render callbacks) to satisfy every caller.
- Visual similarity used to merge components whose accessible roles, names, focus, keyboard, or live-region contracts differ.
- Design variants are not the same axis: product card vs user profile card, status banner vs payment banner, table row vs navigation row.
- Shared code pulls copy/i18n keys, analytics events, auth/security checks, or data fetching into a generic UI primitive.
- Refactor removes caller-level tests/stories without replacements at the new boundary.
- The first patch is a repo-wide move/rename rather than a one-cluster extraction with rollback-friendly diff.

## Output shape

Return a compact table before editing:

| Candidate | Evidence | Classification | Decision | Test/verification | Confidence |
| --- | --- | --- | --- | --- | --- |
| `A`, `B` | files + exact repeated contract | `prop-parameterizable` | extract primitive + wrappers | component test + a11y role/name | high |

Then, if implementation is requested, edit one cluster at a time and report changed files, behavior preserved, tests run, and any T2/T3 candidates intentionally left untouched.

## Boundary with sibling skills

- Use `design-to-code-fidelity` when extraction may alter measured pixels, spacing, tokens, fixed bars, or design variants.
- Use `a11y-contract-testing` for roles, accessible names, focus, menus, comboboxes, tabs, dialogs, or live regions.
- Use `i18n-copy-and-layout` for copy concatenation, locale-specific text expansion, plural rules, or RTL/logical props.
- Use `frontend-security-baseline` / `frontend-auth-flow-contracts` when duplication touches auth, redirects, tokens, or browser security primitives.
- Use framework-specific test guidance already present in the target repo before adding new tooling.

## Public prior art

See [prior-art.md](./references/prior-art.md) for the public tools and docs that shaped this skill — optional evidence sources, never automatic refactor authority.
