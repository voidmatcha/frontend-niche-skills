---
name: a11y-contract-testing
description: "Use when accessibility regressions keep slipping through review — unnamed dialogs, wrong roles on wrappers, menus/comboboxes/tabs losing ARIA state, modals invisible to getByRole, field errors that screen readers never hear (`aria-invalid` on load or never set, `aria-errormessage`/`aria-describedby` missing or pointing at hidden text, no announcement on a failed submit) — or tests need to lock accessibility semantics (roles, names, focus, state) as a contract instead of one-off audits. For when a field becomes invalid see constraint-validation-contracts (native) or js-form-validation-contracts (library); for auth-form-specific cases see frontend-auth-flow-contracts."
---

# Accessibility contract testing

Core principle: treat accessibility semantics as a **testable contract**, not an audit checklist. A component's role, accessible name, focus behavior, state, and AT-visibility are API surface for assistive technology and role-based tests.

Use this skill when UI refactors keep preserving pixels while breaking semantics: an unnamed modal, a styled `div` pretending to be a button, a combobox whose selected option is no longer exposed, or tabs that visually switch panels without updating ARIA state.

## The contract

Lock only semantics users and automation rely on:

- **Role**: query the element by the role users encounter (`dialog`, `button`, `menuitem`, `combobox`, `tab`, `tabpanel`, `status`). Avoid querying implementation wrappers.
- **Accessible name**: assert the label users hear, not incidental visible text. Prefer `aria-labelledby`/native labels over brittle `aria-label` copies when a visible label already exists.
- **State**: assert ARIA/native state that changes behavior (`aria-expanded`, `aria-selected`, `aria-checked`, selected `option`, `disabled`, `aria-invalid` and its error message — see [Form error exposure](#form-error-exposure)). Native form validity (`:user-invalid`, `setCustomValidity`, `ValidityState`) is owned by `constraint-validation-contracts`; library-driven validity (react-hook-form, Formik, and similar) is owned by `js-form-validation-contracts`.
- **Focus and keyboard path**: assert focus lands where the pattern promises and can move with the expected keyboard controls.
- **AT-visibility**: role queries intentionally exclude elements hidden from the ARIA tree (`aria-hidden`, `display:none`, `hidden`). If `getByRole` cannot find it, many users cannot either.

This complements, not replaces, an audit runner. Axe-style checks catch broad violations; contract tests catch product-specific regressions after refactors.

## Dialog-specific minimum

Dialog is still the canonical example because it fails loudly in production:

1. The dialog container exposes `role="dialog"` (or `alertdialog`). Add `aria-modal="true"` **only when the dialog truly behaves modally for everyone**: content outside is visually obscured and interaction outside is blocked.
2. The dialog has an **accessible name**: `aria-label` for string-only titles, or `aria-labelledby` pointing at the rendered title element for visible titles. Unnamed dialogs fail WAI-ARIA's requirement that authors provide an accessible name for `dialog` (and `alertdialog`); axe reports this as `aria-dialog-name`, a Deque best-practice rule rather than a WCAG-mapped one, so whether it is also cited as an SC 4.1.2 failure depends on the audit.
3. Purely decorative wrappers (dim layers, positioning shells) get no interactive role. Putting `role="button"` on an overlay container is worse than it looks: ARIA buttons have presentational children, so descendants can disappear from the accessibility tree.
4. Focus moves into the dialog on open and, by default, returns to the trigger on close unless the APG-documented workflow has a more logical return target.

## Form error exposure

This skill owns how a field error reaches assistive technology, whichever engine produced it (native Constraint Validation → `constraint-validation-contracts`; a JS form library → `js-form-validation-contracts`). Those skills decide *when* a field is invalid; this contract decides what AT receives:

1. **`aria-invalid` after interaction, not on load.** This is the one timing rule the form skills point to. Set `aria-invalid="true"` when the value is invalid *and* either the user has committed an edit (for a text field, changed the value and then left it) or attempted to submit. For an **empty `required`** field — including one the user only focused and left, or typed into and then cleared — wait for a submit attempt: WAI-ARIA says authors SHOULD NOT set it on required widgets "simply because the user has not yet entered data", and MDN says not to set it on empty required elements "until after the user attempts to submit the form". Native `:user-invalid` does not always agree with this rule. Focus alone sets neither, but on an `input` a committed change sets user validity to true, so a `required` input the user typed into, cleared, and left matches `:user-invalid` on blur while `aria-invalid` still waits for submit. That difference is expected, not a defect, so don't derive `aria-invalid` from `:user-invalid` alone. Remove it (or set `false`) once the value is valid.
2. **Associate the message with the field.** Use `aria-errormessage` pointing at the error element (WAI-ARIA: authors MUST pair it with `aria-invalid`, and user agents MUST NOT expose it while `aria-invalid` is `false`), or `aria-describedby` on the same element. Keep hint text in `aria-describedby`; do not rely on an `aria-errormessage` target for text that must be heard while the field is valid.
3. **The message target is not hidden while it is pertinent.** WAI-ARIA requires that the `aria-errormessage` content is not hidden when `aria-invalid` is true, so an error rendered inside an `aria-hidden` or `display:none` wrapper is a broken contract.
4. **Announce on submit.** A failed submit either moves focus to the first invalid field or announces the new error through a live region (`role="alert"` or `aria-live`). WAI-ARIA notes a live region is appropriate "when an error message is displayed to users after they have provided an invalid value"; the WAI forms tutorial recommends setting focus to the first input that contains an error.

Test shape: `getByRole('textbox', { name })` → type an invalid value and blur, or submit → assert `aria-invalid="true"` and the accessible description or error message text → correct the value → assert `aria-invalid` is gone and the stale message is no longer exposed.

## Test patterns

- **Query by role + name, nothing else**: `getByRole('dialog', { name: /delete project/i })` (Playwright / Testing Library). This asserts role, accessible name, and **AT-visibility** in one locator. If a refactor drops `aria-labelledby`, the locator fails for the right reason.
- **Sentinel spec**: one data-driven test file that opens every modal or repeated widget in the app and asserts each resolves through its semantic contract. New unnamed modals, menus with missing item roles, or tabs without selected state fail before shipping.
- **Don't lock tests to visual text** that may be `aria-hidden`. If a visual title is duplicated for layout (for example a sticky clone), hide only the clone from AT and point `aria-labelledby` at the canonical label.
- **i18n caveat**: role+name queries hardcode copy. For localized apps, drive expected names from message IDs/fixtures or assert stable accessible labels only where copy is intentionally contractual.
- **Auth form boundary**: login/code/passkey forms need role/name/status assertions too; use `frontend-auth-flow-contracts` for browser-auth-specific autofill, error, and lifecycle cases.
- **Static analysis is not enough**: lint rules catch attribute-level mistakes; these tests verify that rendered DOM exposes the final accessible tree users receive.

## Non-dialog widget examples

These are the cases that make the skill more than "modal name testing". Keep examples small and pattern-specific: one happy path plus the semantic state most likely to regress.

### Menu button / menu items

```ts
await page.getByRole('button', { name: /more actions/i }).click();
await expect(page.getByRole('menuitem', { name: /archive/i })).toBeVisible();
await expect(page.getByRole('menuitem', { name: /delete/i })).toBeVisible();
```

Failure this catches: replacing a real menuitem with a clickable `div`, or hiding menu text behind `aria-hidden`, so screen-reader and keyboard users lose the command list.

### Combobox / listbox option

```ts
const assignee = page.getByRole('combobox', { name: /assignee/i });
await assignee.click();
await page.getByRole('option', { name: 'Ada Lovelace' }).click();
await assignee.click();
await expect(page.getByRole('option', { name: 'Ada Lovelace' })).toHaveAttribute('aria-selected', 'true');
```

Note: `toHaveValue` is for native `<select>`/`<input>` only and matches the option *value*, not the visible label; for ARIA listbox/combobox widgets assert `aria-selected` on the option.

Scope this assertion: it holds for a **select-only** listbox popup, where the chosen option keeps `aria-selected='true'` when the listbox reopens (APG Select-Only Combobox). **Editable/autocomplete** comboboxes (`aria-autocomplete='list'`/`'both'`) track the active option via `aria-activedescendant` and may expose no `aria-selected` option — assert the `combobox` input value there, not `aria-selected`.

Failure this catches: custom select UI that looks selected but exposes no named combobox, no options, or no selected value to assistive tech.

### Tabs / tabpanel pairing

```ts
await page.getByRole('tab', { name: /billing/i }).click();
await expect(page.getByRole('tab', { name: /billing/i })).toHaveAttribute('aria-selected', 'true');
await expect(page.getByRole('tabpanel', { name: /billing/i })).toBeVisible();
```

Failure this catches: visual tab switching that never updates `aria-selected`, disconnects the tab from its panel, or leaves multiple panels exposed.

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
- Visible heading is inside an `aria-hidden` wrapper, so `aria-labelledby` points to text AT cannot use.
- A modal opens visually, but focus remains behind it or tab order escapes the modal.
- A wrapper gets a role while the interactive child keeps focus, creating duplicate or contradictory semantics.
- `role="presentation"` / `role="none"` is applied to an interactive element and erases required semantics.
- A menu, combobox, or tab component is implemented as clickable `div`s without the APG role/state/keyboard contract.
- Tests use `getByText`/CSS selectors and keep passing after the accessible tree breaks.
- A field shows red error text, but the input has no `aria-invalid`, no message association, or points `aria-errormessage` at an element that is still hidden.

## PR-worthiness gate

A role/ARIA grep hit is not enough. Count a finding only when all three are true:

1. **User-operated surface**: the element is a control or widget users must operate, not a decorative/layout wrapper.
2. **Rendered contract is broken**: after rendering and interaction, the widget cannot be found by role/name, exposes the wrong state, loses focus order, or hides required content from the accessibility tree.
3. **Small regression test exists**: a `getByRole(..., { name })` / keyboard-state test would fail before the patch and pass after it.

Reject weak findings:

- A missing `role` on a native element that already has the correct implicit role.
- A wrapper with no ARIA because semantics are supplied by a child component or headless library.
- A visual navigation list that is not actually a tab interface; do not force APG tabs onto links.
- A pure copy/name preference where the role/state/focus contract already works.

## Output shape

Report the operated surface, rendered role/name/state/focus evidence, user impact, smallest semantic or test change, and the regression assertion. Keep copy preferences and visual-only concerns separate from the accessibility contract.

## Sources

- WCAG 2.x SC 4.1.2 Name, Role, Value: <https://www.w3.org/WAI/WCAG22/Understanding/name-role-value>
- WAI-ARIA Authoring Practices Guide patterns: Dialog (Modal), Menu Button, Combobox, Tabs: <https://www.w3.org/WAI/ARIA/apg/patterns/>
- WAI-ARIA `presentation`/`none` role definition: <https://www.w3.org/TR/wai-aria/#presentation>
- WAI-ARIA `dialog` role ("Authors MUST provide an accessible name for a dialog") and `alertdialog` role (characteristics: "Accessible Name Required: True"): <https://www.w3.org/TR/wai-aria/#dialog>, <https://www.w3.org/TR/wai-aria/#alertdialog>
- axe `aria-dialog-name` rule (Standard(s): "Deque Best Practice"): <https://dequeuniversity.com/rules/axe/4.10/aria-dialog-name>
- WAI-ARIA `aria-invalid` ("authors SHOULD NOT set the aria-invalid attribute on required widgets simply because the user has not yet entered data"): <https://www.w3.org/TR/wai-aria/#aria-invalid>
- MDN `aria-invalid` ("Do not set aria-invalid="true" on empty required elements until after the user attempts to submit the form."): <https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Attributes/aria-invalid>
- WHATWG HTML `input` user validity ("any time the user commits the change, the user agent must … set its user validity to true and fire an event named change"): <https://html.spec.whatwg.org/multipage/input.html>; `:user-invalid` ("must match input, textarea, and select elements whose user validity is true, are candidates for constraint validation but do not satisfy their constraints"): <https://html.spec.whatwg.org/multipage/semantics-other.html#selector-user-invalid>
- WAI-ARIA `aria-errormessage` ("Authors MUST use aria-invalid in conjunction with aria-errormessage"; "When aria-errormessage is pertinent, authors MUST ensure the content is not hidden"; "User agents MUST NOT expose aria-errormessage for an object with an aria-invalid value of false"; live region "appropriate when an error message is displayed to users after they have provided an invalid value"): <https://www.w3.org/TR/wai-aria/#aria-errormessage>
- W3C WAI Forms Tutorial, User Notifications ("If the submitted data contains errors, it is convenient to set the focus to the first `<input>` element that contains an error"): <https://www.w3.org/WAI/tutorials/forms/notifications/>
- Testing Library `ByRole` docs: <https://testing-library.com/docs/queries/byrole/>
- Playwright `getByRole` docs: <https://playwright.dev/docs/locators#locate-by-role>
- See `frontend-auth-flow-contracts` for auth-specific browser/autofill/error cases.
