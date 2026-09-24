# Constraint Validation API & states

## Contents

- [CSS state & timing: `:user-invalid` over `:invalid`](#css-state--timing-user-invalid-over-invalid)
- [The `ValidityState` object](#the-validitystate-object)
- [The methods](#the-methods)
- [The `invalid` event](#the-invalid-event)
- [Accessibility & i18n boundary](#accessibility--i18n-boundary)
- [Find these in your codebase](#find-these-in-your-codebase)
- [Sources](#sources)

The browser validates form controls against their constraints (`required`, `type`, `pattern`, `min`/`max`, `minlength`/`maxlength`, `step`) and exposes the result three ways: CSS pseudo-classes, a per-control `validity` object, and methods on the control and form. Getting the *timing* and the *lifecycle* right is the whole game.

## CSS state & timing: `:user-invalid` over `:invalid`

`:invalid` (and `:valid`) reflect the constraint result **immediately**, from first paint. So a `<input required>` matches `:invalid` before the user has done anything — style it red and the form looks broken on load.

`:user-invalid` matches **after the user has interacted with the control or attempted to submit** *and* it's still invalid — never on a pristine load. That's the reliable invariant and the state you want for error styling. WHATWG HTML defines it normatively through a per-control *user validity* flag, set to true in three places: for an `input`, when the user commits a change (the same moment it fires `change` — for typed-into inputs, when focus leaves after an edit); for a `select`, when the user changes the selection ("send select update notifications"); and for every submittable control, on a form submission attempt. `:user-invalid` matches while user validity is true and the control fails its constraints; the reset algorithm (for `input`, `select`, and `textarea`) sets the flag back to false. The `textarea` section defines no commit step that sets user validity, so a `<textarea>` becoming `:user-invalid` after edit-and-blur is UA behavior, not a normative HTML rule; for it, only the submit-attempt path is normative. (Selectors-4 calls the exact behavior UA-defined in general but points to the HTML specification "for the specific rules pertaining to HTML elements".) (Its counterpart `:user-valid` matches after interaction once valid.)

```css
/* WRONG: paints required fields red on page load */
input:invalid { border-color: red; }

/* Right: only after the user has engaged with the field */
input:user-invalid { border-color: red; }
input:user-invalid + .error { display: block; }
```

Related state pseudo-classes: `:required` / `:optional`, `:in-range` / `:out-of-range` (for `min`/`max`), `:placeholder-shown`. For older targets without `:user-invalid`, the manual equivalent is to add a class on `blur`/submit and gate `:invalid` styling on it.

## The `ValidityState` object

Every submittable control exposes `element.validity`, a `ValidityState` with a boolean per failure mode plus `valid`:

- `valueMissing` — `required` and empty
- `typeMismatch` — value wrong for `type` (`email`, `url`)
- `patternMismatch` — fails the `pattern` regex
- `tooLong` / `tooShort` — exceeds `maxlength` / under `minlength` (note: `tooLong`/`tooShort` apply only to a value the user has edited — the dirty-value-flag rule — so they never fire for programmatically-set or never-edited prefilled values; and since browsers block typing past `maxlength`, `tooLong` rarely fires in practice at all)
- `rangeOverflow` / `rangeUnderflow` — over `max` / under `min`
- `stepMismatch` — not aligned to `step`
- `badInput` — the UA can't convert the input (e.g. letters in `type="number"`)
- `customError` — a non-empty `setCustomValidity()` is in effect
- `valid` — true when all of the above are false

Branch your messaging off these flags rather than re-parsing the value:

```js
const v = input.validity;
if (v.valueMissing) msg = "This field is required.";
else if (v.typeMismatch) msg = "Enter a valid email.";
else if (v.patternMismatch) msg = input.title;        // pattern's hint
```

## The methods

- `checkValidity()` — returns `true`/`false`; if invalid, fires a **cancelable `invalid` event** on the control. Shows **no** UI. Use it to drive your own error rendering.
- `reportValidity()` — same validation, but if the `invalid` event is not cancelled the browser also reports the problem to the user, typically as its native error bubble. WHATWG says the UA "may run the focusing steps" for the control, so focus is common but not guaranteed. Use when you want the built-in UI.
- `setCustomValidity(message)` — sets `customError` and `validationMessage`. A **non-empty** string makes the control invalid; an **empty** string clears it. This is the lifecycle trap:

  ```js
  // Validate against your own rule, then ALWAYS reconcile both directions:
  function validatePassword(input) {
    input.setCustomValidity(isStrong(input.value) ? "" : "Password is too weak.");
  }
  input.addEventListener("input", () => validatePassword(input));  // clears on correction
  ```

  Forgetting the `""` branch is the "submit button does nothing and there's no error" bug — the control is stuck `customError: true`.
- `validationMessage` — the current message (native or your custom one); useful to render in your own UI.
- `willValidate` — `false` for disabled, `readonly` (where applicable), and non-participating controls; those are skipped by validation entirely.
- `novalidate` (on `<form>`) and `formnovalidate` (on a submit button) turn off native validation UI and submit-blocking **without** disabling the API — `checkValidity()`, `validity`, and the pseudo-classes keep working, which is exactly how you build fully custom validation UI while still using the engine.

## The `invalid` event

`invalid` fires per control when validation fails (via `checkValidity()`/`reportValidity()` or a native submit). It's cancelable: `e.preventDefault()` suppresses the native bubble so you can render your own message in its place. It does **not** bubble, so attach per control or use a capturing listener on the form.

## Accessibility & i18n boundary

Native validity is the *mechanism*; the user-facing contract is owned elsewhere:

- Reflect invalid state with `aria-invalid="true"` and clear it when the field becomes valid. *When* to set it is stated once in **a11y-contract-testing** (Form error exposure, item 1), which cites WAI-ARIA and MDN; don't restate that gate here. How the message is associated (`aria-errormessage` with `aria-invalid="true"`, or `aria-describedby`), kept un-hidden, and announced or focused on a failed submit — and how to lock that in tests — is the Form error exposure contract in **a11y-contract-testing**.
- The native `validationMessage` is localized by the browser but not controllable; once you render custom copy, its wording, pluralization, and translation are **i18n-copy-and-layout**.

## Find these in your codebase

A grep is a fast first pass — every hit is a review point, not an automatic bug:

```sh
# :invalid styling without the interaction gate → red fields on load
rg -n ':invalid' src/ | rg -v ':user-invalid'
# setCustomValidity set somewhere — confirm it is also cleared with "" on input
rg -n 'setCustomValidity' src/
```

## Sources

- MDN — [Constraint validation](https://developer.mozilla.org/en-US/docs/Web/HTML/Guides/Constraint_validation) (the validation-related attributes, API, and pseudo-classes)
- MDN — [Client-side form validation](https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Forms/Form_validation)
- MDN — [`ValidityState`](https://developer.mozilla.org/en-US/docs/Web/API/ValidityState) (the per-failure-mode flags)
- MDN — [`:user-invalid`](https://developer.mozilla.org/en-US/docs/Web/CSS/:user-invalid) and [`:invalid`](https://developer.mozilla.org/en-US/docs/Web/CSS/:invalid) (interaction-gated vs immediate)
- MDN — [`setCustomValidity()`](https://developer.mozilla.org/en-US/docs/Web/API/HTMLInputElement/setCustomValidity) (non-empty marks invalid; empty string clears)
- MDN — [`checkValidity()`](https://developer.mozilla.org/en-US/docs/Web/API/HTMLInputElement/checkValidity) / [`reportValidity()`](https://developer.mozilla.org/en-US/docs/Web/API/HTMLInputElement/reportValidity) / [`willValidate`](https://developer.mozilla.org/en-US/docs/Web/API/HTMLInputElement/willValidate)
- MDN — [`invalid` event](https://developer.mozilla.org/en-US/docs/Web/API/HTMLInputElement/invalid_event)
- WHATWG HTML — [Constraint validation](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#constraint-validation)
- WHATWG HTML — user validity: [`input` commits the change](https://html.spec.whatwg.org/multipage/input.html) ("any time the user commits the change, the user agent must … set its user validity to true and fire an event named change"; the input reset algorithm sets "its user validity … back to false"), [form submission](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#form-submission-algorithm) ("For each element field in the list of submittable elements whose form owner is form, set field's user validity to true"), and [`:user-invalid`](https://html.spec.whatwg.org/multipage/semantics-other.html#selector-user-invalid) ("must match input, textarea, and select elements whose user validity is true, are candidates for constraint validation but do not satisfy their constraints")
- WHATWG HTML — [`select` and `textarea`](https://html.spec.whatwg.org/multipage/form-elements.html): "send select update notifications" begins "Set element's user validity to true"; the `select` reset algorithm begins "Set selectElement's user validity to false"; "The reset algorithm for textarea elements is to set the user validity to false" (the `textarea` section has no step that sets it to true)
- WHATWG HTML — [interactive validation and `reportValidity()`](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#report-validity-steps) ("If report is true, then report the problems with the constraints of this element to the user. When reporting the problem with the constraints to the user, the user agent may run the focusing steps for element")
- CSSWG — [Selectors Level 4, `:user-invalid`](https://drafts.csswg.org/selectors-4/#user-pseudos) ("See the HTML specification for the specific rules pertaining to HTML elements")
- MDN — [`change` event](https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/change_event) ("When the element loses focus after its value was changed" for typed-into controls)
