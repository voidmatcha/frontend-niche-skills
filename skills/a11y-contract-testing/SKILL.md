---
name: a11y-contract-testing
description: "Use when accessibility regressions keep slipping through review — unnamed dialogs, wrong roles on wrappers, modals invisible to getByRole — or when writing tests that lock in accessibility semantics (dialog names, roles, focus) as a contract instead of one-off audits."
---

# Accessibility contract testing

Core principle: treat accessibility semantics as a **testable contract**, not an audit
checklist. A modal's role and accessible name are API surface — query them in tests
by role + name, and the test fails the moment the contract breaks.

## The contract (minimum for any modal/dialog)

1. The dialog container exposes `role="dialog"` (or `alertdialog`). Add
   `aria-modal="true"` **only when the dialog truly behaves modally for everyone** —
   the APG warns that marking it modal while content outside stays interactive is
   worse than omitting it (interaction blocked + visually obscured are its two
   conditions).
2. The dialog has an **accessible name**: `aria-label` for string titles,
   `aria-labelledby` pointing at the rendered title element for node titles.
   Unnamed dialogs violate WCAG SC 4.1.2 (Name, Role, Value).
3. Purely decorative wrappers (dim layers, positioning shells) get
   `role="presentation"` — never an interactive role. Putting `role="button"` on an
   overlay container is worse than it looks: `button` has *presentational children*
   in ARIA, so user agents should strip every descendant from the accessibility
   tree — the overlay becomes one giant nameless button.
4. Focus moves into the dialog on open and, by default, returns to the trigger on
   close (ARIA APG dialog keyboard behavior; the APG documents narrow exceptions
   where another target is more logical).

## Test patterns

- **Query by role + name, nothing else**:
  `getByRole('dialog', { name: '...' })` (Playwright / Testing Library). This single
  query asserts role, accessible name, and **AT-visibility** (both tools exclude
  elements hidden from the ARIA tree — `aria-hidden`, `display:none` — which is not
  the same as CSS/visual visibility). If a refactor drops the `aria-labelledby`, the
  locator stops resolving and the test fails for the right reason.
- **Sentinel spec**: one test file that opens every modal in the app and asserts each
  resolves via `getByRole('dialog', { name })`. New unnamed modals fail the sentinel
  instead of shipping. Keep it data-driven (list of route + trigger + expected name).
- **Don't lock tests to visual text** that may be `aria-hidden`. If a visual title is
  duplicated for layout (e.g. a fixed clone), hide the clone from AT
  (`aria-hidden="true"`) and name the dialog from the canonical one.
- **i18n caveat**: role+name queries hardcode copy. Either pin the test locale, or
  resolve expected names from the same i18n source the app uses.
- Static-analysis passes (axe-core, eslint-plugin-jsx-a11y) catch attribute-level
  issues; they do NOT replace contract queries — axe can't know which name a dialog
  was *supposed* to have.

## Common defects this catches (all seen in production code)

| Defect | How the contract test fails |
|--------|------------------------------|
| Dialog without accessible name | `getByRole('dialog', { name })` times out |
| `role="button"` on dim/overlay wrapper | role query resolves to the wrong element / subtree assertions break |
| Visual-only duplicated title read twice by AT | name mismatch once the clone is `aria-hidden` |
| Title rendered as styled `div` instead of heading | `getByRole('heading', { level })` query fails |

## Sources

- WCAG 2.x SC 4.1.2 Name, Role, Value (w3.org/WAI/WCAG21/Understanding/name-role-value)
- WAI-ARIA Authoring Practices Guide — Dialog (Modal) pattern (w3.org/WAI/ARIA/apg/patterns/dialog-modal/)
- WAI-ARIA `presentation`/`none` role definition (w3.org/TR/wai-aria/#presentation)
- Testing Library "ByRole" docs; Playwright `getByRole` docs (role + accessible-name matching)
