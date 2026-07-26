# Constraint Validation API & states

## Contents

- [CSS state & timing: `:user-invalid` over `:invalid`](#css-state--timing-user-invalid-over-invalid)
- [The `ValidityState` object](#the-validitystate-object)
- [The methods](#the-methods)
- [The `invalid` event](#the-invalid-event)
- [Accessibility & i18n boundary](#accessibility--i18n-boundary)
- [Find these in your codebase](#find-these-in-your-codebase)
- [Sources](#sources)

The browser validates form controls against their constraints (`required`, `type`, `pattern`,
`min`/`max`, `minlength`/`maxlength`, `step`) and exposes the result three ways: CSS
pseudo-classes, a per-control `validity` object, and methods on the control and form. Getting
the *timing* and the *lifecycle* right is the whole game.

## CSS state & timing: `:user-invalid` over `:invalid`

`:invalid` (and `:valid`) reflect the constraint result **immediately**, from first paint. So a
`<input required>` matches `:invalid` before the user has done anything — style it red and the
form looks broken on load.

`:user-invalid` matches **after the user has interacted with the control or attempted to submit**
*and* it's still invalid — never on a pristine load. That's the reliable invariant and the state
you want for error styling. The spec only normatively defines `:user-invalid` around submission
and otherwise leaves the timing UA-optional ("MAY match at other times"); current browsers
*tend* to flip it on blur for a field that was valid on focus, and during editing for one that
was already invalid when focused, but treat that precise focus/blur distinction as a
heuristic, not a contract. (Its counterpart `:user-valid` matches after
interaction once valid.)

```css
/* WRONG: paints required fields red on page load */
input:invalid { border-color: red; }

/* Right: only after the user has engaged with the field */
input:user-invalid { border-color: red; }
input:user-invalid + .error { display: block; }
```

Related state pseudo-classes: `:required` / `:optional`, `:in-range` / `:out-of-range` (for
`min`/`max`), `:placeholder-shown`. For older targets without `:user-invalid`, the manual
equivalent is to add a class on `blur`/submit and gate `:invalid` styling on it.

## The `ValidityState` object

Every submittable control exposes `element.validity`, a `ValidityState` with a boolean per
failure mode plus `valid`:

- `valueMissing` — `required` and empty
- `typeMismatch` — value wrong for `type` (`email`, `url`)
- `patternMismatch` — fails the `pattern` regex
- `tooLong` / `tooShort` — exceeds `maxlength` / under `minlength` (note: `tooLong`/`tooShort`
  apply only to a value the user has edited — the dirty-value-flag rule — so they never fire for
  programmatically-set or never-edited prefilled values; and since browsers block typing past
  `maxlength`, `tooLong` rarely fires in practice at all)
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

- `checkValidity()` — returns `true`/`false`; if invalid, fires a **cancelable `invalid`
  event** on the control. Shows **no** UI. Use it to drive your own error rendering.
- `reportValidity()` — same validation, but also displays the browser's native error bubble on
  the first invalid control and focuses it. Use when you want the built-in UI.
- `setCustomValidity(message)` — sets `customError` and `validationMessage`. A **non-empty**
  string makes the control invalid; an **empty** string clears it. This is the lifecycle trap:

  ```js
  // Validate against your own rule, then ALWAYS reconcile both directions:
  function validatePassword(input) {
    input.setCustomValidity(isStrong(input.value) ? "" : "Password is too weak.");
  }
  input.addEventListener("input", () => validatePassword(input));  // clears on correction
  ```

  Forgetting the `""` branch is the "submit button does nothing and there's no error" bug — the
  control is stuck `customError: true`.
- `validationMessage` — the current message (native or your custom one); useful to render in
  your own UI.
- `willValidate` — `false` for disabled, `readonly` (where applicable), and non-participating
  controls; those are skipped by validation entirely.
- `novalidate` (on `<form>`) and `formnovalidate` (on a submit button) turn off native
  validation UI and submit-blocking **without** disabling the API — `checkValidity()`,
  `validity`, and the pseudo-classes keep working, which is exactly how you build fully custom
  validation UI while still using the engine.

## The `invalid` event

`invalid` fires per control when validation fails (via `checkValidity()`/`reportValidity()` or
a native submit). It's cancelable: `e.preventDefault()` suppresses the native bubble so you can
render your own message in its place. It does **not** bubble, so attach per control or use a
capturing listener on the form.

## Accessibility & i18n boundary

Native validity is the *mechanism*; the user-facing contract is owned elsewhere:

- Reflect invalid state with `aria-invalid="true"` — but gate it on interaction like
  `:user-invalid`: per MDN, don't set `aria-invalid="true"` on an empty `required` field until
  the user has attempted to submit (they may still be filling it in). Associate the visible
  error text with **`aria-errormessage`** — MDN's purpose-built attribute for a validation
  message, used together with `aria-invalid="true"`; `aria-describedby` is the broadly
  supported alternative and the right tool for persistent hint text. Note that
  `aria-errormessage` is only conveyed to assistive tech while `aria-invalid="true"`; clear
  `aria-invalid` when the field becomes valid (otherwise the error silently does nothing or
  goes stale). On a failed submit, move focus to the first invalid control. The
  role/name/focus *contract* and how to lock it in tests is **a11y-contract-testing**.
- The native `validationMessage` is localized by the browser but not controllable; once you
  render custom copy, its wording, pluralization, and translation are **i18n-copy-and-layout**.

## Find these in your codebase

A grep is a fast first pass — every hit is a review point, not an automatic bug:

```sh
# :invalid styling without the interaction gate → red fields on load
rg -n ':invalid' src/ | rg -v ':user-invalid'
# setCustomValidity set somewhere — confirm it is also cleared with "" on input
rg -n 'setCustomValidity' src/
```

## Sources

- MDN — [Constraint validation](https://developer.mozilla.org/en-US/docs/Web/HTML/Guides/Constraint_validation)
  (the validation-related attributes, API, and pseudo-classes)
- MDN — [Client-side form validation](https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Forms/Form_validation)
- MDN — [`ValidityState`](https://developer.mozilla.org/en-US/docs/Web/API/ValidityState)
  (the per-failure-mode flags)
- MDN — [`:user-invalid`](https://developer.mozilla.org/en-US/docs/Web/CSS/:user-invalid)
  and [`:invalid`](https://developer.mozilla.org/en-US/docs/Web/CSS/:invalid)
  (interaction-gated vs immediate)
- MDN — [`setCustomValidity()`](https://developer.mozilla.org/en-US/docs/Web/API/HTMLInputElement/setCustomValidity)
  (non-empty marks invalid; empty string clears)
- MDN — [`checkValidity()`](https://developer.mozilla.org/en-US/docs/Web/API/HTMLInputElement/checkValidity)
  / [`reportValidity()`](https://developer.mozilla.org/en-US/docs/Web/API/HTMLInputElement/reportValidity)
  / [`willValidate`](https://developer.mozilla.org/en-US/docs/Web/API/HTMLInputElement/willValidate)
- MDN — [`invalid` event](https://developer.mozilla.org/en-US/docs/Web/API/HTMLInputElement/invalid_event)
- WHATWG HTML — [Constraint validation](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#client-side-form-validation)
