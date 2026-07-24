---
name: js-form-validation-contracts
description: "Use when wiring form validation through a JS library (react-hook-form, Formik, vee-validate, Final Form, TanStack Form) with a schema resolver (zod/yup/valibot) — errors painted before the user touches a field (`validateOnMount`/eager display), an error that stays after the value is corrected (`reValidateMode`, server/root `setError`), a submit button stuck disabled on `isValid`, an async/server validation that races a double-submit, or a server-side field error (uniqueness, 409) that never reaches the right field. Library validity-lifecycle scope; for the native Constraint Validation API (`:user-invalid`, `setCustomValidity`, `reportValidity`) see constraint-validation-contracts, for ARIA error role/name/focus see a11y-contract-testing, for message wording/localization see i18n-copy-and-layout."
---

# JS form-validation contracts

Form libraries own validity instead of the browser, and the same user-visible bugs the native
Constraint Validation API produces reappear one layer up — just spelled `mode`, `reValidateMode`,
`setError`, `trigger`, `isValid`, and resolver promises. They pass the happy path and surface only
in real use: a form that **flags every field before the user types**, an error that **persists after
the field is corrected**, a **submit blocked with no visible message**, a submit button **stuck
disabled forever**, or an **async/server error that lands on the wrong field or races a double click**.

This skill is the library validity *lifecycle*. For the browser's own engine (`:user-invalid`
timing, `setCustomValidity`, `checkValidity`/`reportValidity`) use **constraint-validation-contracts**;
for the ARIA role/name/focus contract around errors use **a11y-contract-testing**; for the *wording*
and localization of messages use **i18n-copy-and-layout**; for `autocomplete` tokens and auth-field
specifics use **frontend-auth-flow-contracts**. Keep a11y, `autocomplete`/input-`type`, and wording
observations as clearly-labelled *secondary* notes — they belong to those skills, not this one's contracts.

Library currency (2026): react-hook-form is the mainstream default; **Formik is effectively in
maintenance mode** — its lifecycle guidance below stays valid for existing/legacy code but is not
the default for new forms. **TanStack Form** is a growing alternative whose validity lifecycle maps
to the same contracts (field vs form validators, `isValidating`, submit gating on validation state).

## Checklist (lead with the trap; details in references/)

→ [library-validity-lifecycle](./references/library-validity-lifecycle.md)

1. **Validate on touch, re-validate on change — not on mount, not only on submit.** The field should
   error *after* the user leaves it, then update live as they fix it. In react-hook-form that is
   `mode: 'onTouched'` + the default `reValidateMode: 'onChange'`; in Formik it is `validateOnBlur`
   with `validateOnMount` left off. `validateOnMount` is the mount-time red-field case;
   `mode: 'onChange'` validates on the first edit and can be noisy/perf-heavy, but it is not
   a first-render error by itself. Plain `onSubmit` mode means a corrected field can keep
   its error until the next submit.
2. **Clear errors when the value becomes valid.** Schema-driven errors clear themselves only if
   re-validation actually runs (item 1). For manual `setError(...)`, first identify ownership:
   registered field errors may clear when the field passes its registered rules, but server/root/
   unregistered errors are outside resolver ownership and need `clearErrors(name)` on the next edit
   or an explicit resolver/server-error lifecycle. Otherwise the field stays invalid and submit is
   blocked with no obvious cause (the `setCustomValidity('')` bug, one layer up).
3. **Don't naively gate submit on `isValid`.** Reading `formState.isValid` subscribes to it and makes
   RHF validate eagerly (from first render), so `disabled={!isValid}` does track validity — but it
   forces full-form validation on mount and its meaning still shifts with `mode`. Gate on submit
   *attempt*, not on `isValid`; if you disable, disable only on
   `isSubmitting`/`isValidating`, and re-enable on settle.
4. **Make the in-flight + double-submit contract explicit.** Disable (or ignore re-entry) while
   `isSubmitting`/`isValidating` is true and re-enable on settle — success, error, *and* reject. A
   promise that rejects without re-enabling is a permanently dead button. Don't fire the submit
   handler twice; debounce async field validation so each keystroke doesn't launch a request.
5. **Map server-side errors back onto fields.** A 409 / uniqueness / "email taken" from the API must
   be reconciled to the owning field (`setError('email', { type: 'server', message })`) and focused,
   not dropped into a toast. A server error is **two separate contracts** — this mapping, *and*
   clearing it on the next edit (item 2); report and fix them as two findings, never one. Decide whose
   error wins when client and server disagree.
6. **Surface a form-level error too.** If submit fails for a non-field reason (network, 500), show a
   persistent, `role="alert"` form-level message — a missing UI *surface*, not a copy bug: a one-off
   `toast(e.message)` is not the same as a form-level error tied to the failed submit.
7. **Test the timing and the lifecycle, not just the value.** Assert: no error on mount; error after
   blur; error clears after correction; submit blocked only with a visible message; the button
   re-enables after a rejected submit; a server field error lands on (and focuses) the right field.

## PR-worthiness gate

Raw `useForm` / `<Formik>` / `mode` / `setError` matches are noisy. Treat a case as PR-worthy only
when a user-visible contract is violated:

- **Timing**: `validateOnMount` or display logic that shows errors before interaction; `mode:
  'onChange'` alone is only eager first-change validation, not a mount-time error. Also flag
  `onSubmit`-only flows where corrected fields do not re-validate until the next submit.
- **Stuck submit**: `disabled={!formState.isValid}` with a non-`onChange`/`onTouched` mode (button
  never enables); or `isSubmitting` set true and not reset on a rejected promise (button never
  re-enables).
- **Stale error**: a corrected field keeps its error — schema error under `reValidateMode: 'onSubmit'`,
  or server/root/unregistered `setError` not cleared or re-owned on the next edit. Raise as its own
  finding, separate from the mapping bug below.
- **Dropped server error**: API field errors shown only as a toast / not `setError`'d to the owning
  field and focused.
- **Async race**: per-keystroke async validation with no debounce, or a submit handler reachable
  twice while a request is in flight.

Reject likely false positives:

- `mode: 'onChange'` alone, or `mode: 'onTouched'` / `'onBlur'` with default `reValidateMode`
  and submit gated on attempt — correct.
- `disabled` bound to `isSubmitting`/`isValidating` only (not `isValid`), reset in `finally`.
- The library/schema owns validity and tests already verify error-clears-on-correct and
  re-enable-on-reject.
- It's purely the native `<input required>` engine (no library owns it) → use
  **constraint-validation-contracts**; or purely message wording → **i18n-copy-and-layout**.

Minimal useful PR: a failing sequence test — mount (no error) → blur invalid (error) → type valid
(error clears) → submit rejects (button re-enabled) → server `setError('email')` (focused, then
cleared on edit).

## References

| File | Covers |
|------|--------|
| [library-validity-lifecycle](./references/library-validity-lifecycle.md) | react-hook-form `mode`/`reValidateMode`/`formState` (`isValid`/`isSubmitting`/`isValidating`/`errors`)/`trigger`/`setError`/`clearErrors`/`shouldFocusError`/resolvers; Formik `validateOnBlur`/`validateOnMount`/`isSubmitting`/`setFieldError`; zod/yup/valibot async resolver + server-error reconciliation; the constraint-validation / a11y / i18n boundary |

Sources are listed in the reference file.
