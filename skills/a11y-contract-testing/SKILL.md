---
name: a11y-contract-testing
description: "Use when accessibility regressions keep slipping through review — unnamed dialogs, wrong roles on wrappers, menus/comboboxes/tabs losing ARIA state, modals invisible to getByRole — or tests need to lock accessibility semantics (roles, names, focus, state) as a contract instead of one-off audits. For native HTML form-validity wiring see constraint-validation-contracts; for auth-form-specific cases see frontend-auth-flow-contracts."
---

# Accessibility contract testing

Core principle: treat accessibility semantics as a **testable contract**, not an audit
checklist. A component's role, accessible name, focus behavior, state, and AT-visibility
are API surface for assistive technology and role-based tests.

Use this skill when UI refactors keep preserving pixels while breaking semantics: an
unnamed modal, a styled `div` pretending to be a button, a combobox whose selected option
is no longer exposed, or tabs that visually switch panels without updating ARIA state.

## The contract

Lock only semantics users and automation rely on:

- **Role**: query the element by the role users encounter (`dialog`, `button`, `menuitem`,
  `combobox`, `tab`, `tabpanel`, `status`). Avoid querying implementation wrappers.
- **Accessible name**: assert the label users hear, not incidental visible text. Prefer
  `aria-labelledby`/native labels over brittle `aria-label` copies when a visible label
  already exists.
- **State**: assert ARIA/native state that changes behavior (`aria-expanded`,
  `aria-selected`, `aria-checked`, selected `option`, `disabled`, validation error text).
  Native form validity (`:user-invalid`, `setCustomValidity`, `ValidityState`) is owned by
  `constraint-validation-contracts`.
- **Focus and keyboard path**: assert focus lands where the pattern promises and can move
  with the expected keyboard controls.
- **AT-visibility**: role queries intentionally exclude elements hidden from the ARIA tree
  (`aria-hidden`, `display:none`, `hidden`). If `getByRole` cannot find it, many users
  cannot either.

This complements, not replaces, an audit runner. Axe-style checks catch broad violations;
contract tests catch product-specific regressions after refactors.

## Dialog-specific minimum

Dialog is still the canonical example because it fails loudly in production:

1. The dialog container exposes `role="dialog"` (or `alertdialog`). Add
   `aria-modal="true"` **only when the dialog truly behaves modally for everyone**: content
   outside is visually obscured and interaction outside is blocked.
2. The dialog has an **accessible name**: `aria-label` for string-only titles, or
   `aria-labelledby` pointing at the rendered title element for visible titles. Unnamed
   dialogs violate WCAG SC 4.1.2 (Name, Role, Value).
3. Purely decorative wrappers (dim layers, positioning shells) get no interactive role.
   Putting `role="button"` on an overlay container is worse than it looks: ARIA buttons
   have presentational children, so descendants can disappear from the accessibility tree.
4. Focus moves into the dialog on open and, by default, returns to the trigger on close
   unless the APG-documented workflow has a more logical return target.

## Test patterns

- **Query by role + name, nothing else**: `getByRole('dialog', { name: /delete project/i })`
  (Playwright / Testing Library). This asserts role, accessible name, and **AT-visibility**
  in one locator. If a refactor drops `aria-labelledby`, the locator fails for the right
  reason.
- **Sentinel spec**: one data-driven test file that opens every modal or repeated widget
  in the app and asserts each resolves through its semantic contract. New unnamed modals,
  menus with missing item roles, or tabs without selected state fail before shipping.
- **Don't lock tests to visual text** that may be `aria-hidden`. If a visual title is
  duplicated for layout (for example a sticky clone), hide only the clone from AT and point
  `aria-labelledby` at the canonical label.
- **i18n caveat**: role+name queries hardcode copy. For localized apps, drive expected
  names from message IDs/fixtures or assert stable accessible labels only where copy is
  intentionally contractual.
- **Auth form boundary**: login/code/passkey forms need role/name/status assertions too;
  use `frontend-auth-flow-contracts` for browser-auth-specific autofill, error, and
  lifecycle cases.
- **Static analysis is not enough**: lint rules catch attribute-level mistakes; these tests
  verify that rendered DOM exposes the final accessible tree users receive.

## Non-dialog widget examples

These are the cases that make the skill more than "modal name testing". Keep examples
small and pattern-specific: one happy path plus the semantic state most likely to regress.

### Menu button / menu items

```ts
await page.getByRole('button', { name: /more actions/i }).click();
await expect(page.getByRole('menuitem', { name: /archive/i })).toBeVisible();
await expect(page.getByRole('menuitem', { name: /delete/i })).toBeVisible();
```

Failure this catches: replacing a real menuitem with a clickable `div`, or hiding
menu text behind `aria-hidden`, so screen-reader and keyboard users lose the command list.

### Combobox / listbox option

```ts
const assignee = page.getByRole('combobox', { name: /assignee/i });
await assignee.click();
await page.getByRole('option', { name: 'Ada Lovelace' }).click();
await assignee.click();
await expect(page.getByRole('option', { name: 'Ada Lovelace' })).toHaveAttribute('aria-selected', 'true');
```

Note: `toHaveValue` is for native `<select>`/`<input>` only and matches the option *value*,
not the visible label; for ARIA listbox/combobox widgets assert `aria-selected` on the option.

Scope this assertion: it holds for a **select-only** listbox popup, where the chosen option keeps
`aria-selected='true'` when the listbox reopens (APG Select-Only Combobox). **Editable/autocomplete**
comboboxes (`aria-autocomplete='list'`/`'both'`) track the active option via `aria-activedescendant`
and may expose no `aria-selected` option — assert the `combobox` input value there, not `aria-selected`.

Failure this catches: custom select UI that looks selected but exposes no named combobox,
no options, or no selected value to assistive tech.

### Tabs / tabpanel pairing

```ts
await page.getByRole('tab', { name: /billing/i }).click();
await expect(page.getByRole('tab', { name: /billing/i })).toHaveAttribute('aria-selected', 'true');
await expect(page.getByRole('tabpanel', { name: /billing/i })).toBeVisible();
```

Failure this catches: visual tab switching that never updates `aria-selected`, disconnects
the tab from its panel, or leaves multiple panels exposed.

## Advanced contract notes

### Virtualized listbox / combobox / table

Virtualization is not a defect by itself. Test the rendered contract users receive:

- Active option should be present in accessibility tree when `aria-activedescendant` points at it, or component must use a documented pattern that keeps a stable active descendant.
- Keyboard navigation should scroll the active row/option into view and keep the visible selection, focused input, and ARIA state aligned.
- Role tests should cover boundary movement: first item, last visible item, item just outside current window, filtered-empty state.

### Reduced-motion and animated state changes

Use this skill for motion only when animation affects accessibility contract: focus moves after exit animation, hidden content remains focusable, live-region/status update delayed, or `prefers-reduced-motion` users still get motion required to understand or operate UI. Pure visual timing belongs in design/motion review, not a role/name/state finding.

## Common defects

- `role="dialog"` exists, but the dialog has no accessible name.
- Visible heading is inside an `aria-hidden` wrapper, so `aria-labelledby` points to text AT
  cannot use.
- A modal opens visually, but focus remains behind it or tab order escapes the modal.
- A wrapper gets a role while the interactive child keeps focus, creating duplicate or
  contradictory semantics.
- `role="presentation"` / `role="none"` is applied to an interactive element and erases
  required semantics.
- A menu, combobox, or tab component is implemented as clickable `div`s without the APG
  role/state/keyboard contract.
- Tests use `getByText`/CSS selectors and keep passing after the accessible tree breaks.

## PR-worthiness gate

A role/ARIA grep hit is not enough. Count a finding only when all three are true:

1. **User-operated surface**: the element is a control or widget users must operate, not a
   decorative/layout wrapper.
2. **Rendered contract is broken**: after rendering and interaction, the widget cannot be found
   by role/name, exposes the wrong state, loses focus order, or hides required content from the
   accessibility tree.
3. **Small regression test exists**: a `getByRole(..., { name })` / keyboard-state test would
   fail before the patch and pass after it.

Do **not** count these as defects without more evidence:

- A missing `role` on a native element that already has the correct implicit role.
- A wrapper with no ARIA because semantics are supplied by a child component or headless library.
- A visual navigation list that is not actually a tab interface; do not force APG tabs onto links.
- A pure copy/name preference where the role/state/focus contract already works.

## Sources

- WCAG 2.x SC 4.1.2 Name, Role, Value: <https://www.w3.org/WAI/WCAG21/Understanding/name-role-value>
- WAI-ARIA Authoring Practices Guide patterns: Dialog (Modal), Menu Button, Combobox, Tabs: <https://www.w3.org/WAI/ARIA/apg/patterns/>
- WAI-ARIA `presentation`/`none` role definition: <https://www.w3.org/TR/wai-aria/#presentation>
- Testing Library `ByRole` docs: <https://testing-library.com/docs/queries/byrole/>
- Playwright `getByRole` docs: <https://playwright.dev/docs/locators#locate-by-role>
- See `frontend-auth-flow-contracts` for auth-specific browser/autofill/error cases.
