---
name: component-extraction-judgment
description: "Use when React code has near-duplicate components, copy-pasted cards/rows/banners, boolean-prop variant sprawl, wrapper-only components, duplicated hooks/handlers, or AI-generated UI that needs a decision: extract a shared component, create thin wrappers, move logic to a hook, or deliberately keep implementations separate without breaking design fidelity, accessibility, i18n, or data contracts. React-only scope; route to design-to-code-fidelity, a11y-contract-testing, or i18n-copy-and-layout for those dimensions."
---

# Component extraction judgment

Use this skill before refactoring generated or organically grown frontend UI into shared components. The goal is not "deduplicate everything"; it is to decide which reuse boundary preserves product semantics, design fidelity, accessibility contracts, and testability.

## Evidence tiers

| Tier | Claim allowed | Evidence required |
| --- | --- | --- |
| T1 | Safe extraction candidate | Two or more concrete source locations, same user-facing semantics, same accessibility role/name/state contract, same design variant axis, and a targeted regression test path. Optional local tools such as `react-unify`/`duplicalis` may support the finding, but the final decision still needs code evidence. |
| T2 | Plausible extraction candidate | Similar structure and props are visible, but one contract dimension still needs confirmation (design token, responsive state, copy/i18n, loading/empty state, focus behavior, or data shape). |
| T3 | Smell only | Duplication is suspected from names, screenshots, or token overlap, but source locations or contracts are not confirmed. Do not edit yet. |
| T4 | Blocked / not judged | Missing source, missing design authority, generated bundle only, no safe test path, or the change would require product/API decisions. |

Only T1 should be implemented as a refactor. T2/T3 can become a cleanup plan or TODO with explicit missing evidence. T4 is reported as blocked with the specific missing input (source, design authority, test path, or product/API decision), not edited.

## Workflow

1. **Freeze the contract before merging.** For every candidate, list the component names/files, caller contexts, user-visible purpose, design reference or token authority, accessibility role/name/state, i18n/copy ownership, data shape, loading/error/empty states, and responsive breakpoints.
2. **Find candidate clusters.** Prefer existing repo evidence first: repeated JSX shape, prop names, Tailwind/class token sets, copied handlers/hooks, repeated mapping logic, or duplicated fixtures/stories/tests. If already installed or explicitly allowed, run read-only tools such as `react-unify scan <src>` or `duplicalis scan`; otherwise do not add dependencies just to inspect. react-unify ships its own Claude Code skill that triggers on "find duplicate components"; this skill governs the merge/keep decision over any react-unify report, and react-unify stays read-only/`--propose` (never auto-apply).
3. **Classify the duplication.** Use the smallest fitting category:
   - `prop-parameterizable`: same component, differences are data/text/icon/color props.
   - `slot-composition`: same shell, variable inner content should be a slot/children/render prop.
   - `thin-wrapper`: shared primitive is safe, but old exported names/routes should remain wrappers.
   - `logic-hook`: UI differs, but hook/handler/state-machine logic is duplicated.
   - `style-token`: repeated visual treatment belongs in tokens/classes/primitives, not a mega-component.
   - `false-friend`: code looks similar, but semantics, state, accessibility, design variant, or lifecycle differ.
4. **Choose the boundary.** Prefer a shared primitive plus thin named wrappers over one generic component with many booleans. Prefer custom hooks for behavior duplication. Prefer local helpers/data maps when extraction would make the public API vague.
5. **Lock behavior.** Add or update the smallest regression: unit/component test for props and states, `getByRole`/accessible-name assertions for semantic surfaces, visual/story snapshots for design-sensitive variants, or type tests for discriminated unions.

## Decision matrix

| Decision | Use when | Avoid when |
| --- | --- | --- |
| Extract shared component | Same semantic role, same state model, same interaction contract, same design primitive, and differences can be expressed as named props or data. | Props become `showX`, `isFoo`, `variant="custom"`, or callers need escape hatches immediately. |
| Shared primitive + wrappers | Existing component names carry route/domain meaning, but render through the same primitive. | Wrappers only rename every prop without preserving domain defaults or tests. |
| Custom hook/helper | Logic, formatting, sorting, keyboard handling, or async state repeats while UI differs. | Hook would import presentation details or make state ownership unclear. |
| Token/class extraction | Repeated colors/spacing/radius/shadows should follow design-system tokens. | It hides one-off product exceptions or bypasses a stronger design-to-code fidelity check. |
| Keep separate | Similar shape hides different semantics, roles, copy ownership, business rules, responsive behavior, or future roadmap. | "They might diverge someday" is the only reason and current contracts are identical. |

## Red flags before editing

- Several variant booleans or mutually exclusive optional props appear in the proposed API (the classic "boolean trap"; ~3+ is a rough smell, not a hard rule — mutually exclusive flags that should collapse into one discriminated `variant` prop matter more than the exact count).
- The extracted component would accept both domain data and presentation escape hatches (`className`, `style`, arbitrary render callbacks) to satisfy every caller.
- Visual duplication is used to merge components with different accessible roles, names, focus behavior, keyboard handling, or live-region expectations.
- Design variants are not the same axis: e.g. product card vs user profile card, status banner vs payment banner, table row vs navigation row.
- Shared code would pull copy/i18n keys, analytics events, auth/security checks, or data fetching into a generic UI primitive.
- Refactor removes caller-level tests/stories without replacing them at the new boundary.
- The first patch is a repo-wide move/rename rather than a one-cluster extraction with rollback-friendly diff.

## Output shape

Return a compact table before editing:

| Candidate | Evidence | Classification | Decision | Test/verification | Confidence |
| --- | --- | --- | --- | --- | --- |
| `A`, `B` | files + exact repeated contract | `prop-parameterizable` | extract primitive + wrappers | component test + a11y role/name | high |

Then, if implementation is requested, edit one cluster at a time and report:

- changed files,
- behavior preserved,
- tests run,
- any T2/T3 candidates intentionally left untouched.

## Boundary with sibling skills

- Use `design-to-code-fidelity` when the extraction may alter measured pixels, spacing, tokens, fixed bars, or design variants.
- Use `a11y-contract-testing` when roles, accessible names, focus, menus, comboboxes, tabs, dialogs, or live regions are involved.
- Use `i18n-copy-and-layout` for copy concatenation, locale-specific text expansion, plural rules, or RTL/logical props.
- Use `frontend-security-baseline` / `frontend-auth-flow-contracts` when duplication touches auth, redirects, tokens, or browser security primitives.
- Use framework-specific test guidance already present in the target repo before adding new tooling.

## Public prior art

See [prior-art.md](./references/prior-art.md) for public tools and docs that shaped this skill. Treat those tools as optional evidence sources, not as automatic refactor authority.
