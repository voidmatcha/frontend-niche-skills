---
name: js-form-validation-contracts
description: "Use when wiring form validation through a JS library (react-hook-form, Formik, vee-validate, Final Form, TanStack Form) with a schema resolver (zod/yup/valibot) — errors painted before the user touches a field (`validateOnMount`/eager display), an error that stays after the value is corrected (`reValidateMode`, an unregistered or root `setError`), a submit button stuck disabled on `isValid`, an async/server validation that races a double-submit, or a server-side field error (uniqueness, 409) that never reaches the right field. Library validity-lifecycle scope; for the native Constraint Validation API (`:user-invalid`, `setCustomValidity`, `reportValidity`) see constraint-validation-contracts, for ARIA error role/name/focus see a11y-contract-testing, for message wording/localization see i18n-copy-and-layout."
---

# JS form-validation contracts

Form libraries own validity instead of the browser, and the same user-visible bugs the native Constraint Validation API produces reappear one layer up — just spelled `mode`, `reValidateMode`, `setError`, `trigger`, `isValid`, and resolver promises. They pass the happy path and surface only in real use: a form that **flags every field before the user types**, an error that **persists after the field is corrected**, a **submit blocked with no visible message**, a submit button **stuck disabled forever**, or an **async/server error that lands on the wrong field or races a double click**.

This skill is the library validity *lifecycle*. For the browser's own engine (`:user-invalid` timing, `setCustomValidity`, `checkValidity`/`reportValidity`) use **constraint-validation-contracts**; for the ARIA role/name/focus contract around errors use **a11y-contract-testing**; for the *wording* and localization of messages use **i18n-copy-and-layout**; for `autocomplete` tokens and auth-field specifics use **frontend-auth-flow-contracts**. Keep a11y, `autocomplete`/input-`type`, and wording observations as clearly-labelled *secondary* notes — they belong to those skills, not this one's contracts.

Library choice is out of scope: the contracts below apply to whichever library owns validity. Check the library's own release history before assuming it is actively maintained (for example, Formik's latest GitHub release was `formik@2.4.9` on 2025-11-10, checked 2026-09-24). TanStack Form's validity lifecycle maps to the same contracts (field vs form validators, `isValidating`, submit gating on validation state).

## Checklist (lead with the trap; details in references/)

→ [library-validity-lifecycle](./references/library-validity-lifecycle.md)

1. **Validate on touch, re-validate on change — not on mount, not only on submit.** The field should error *after* the user leaves it, then update live as they fix it. In react-hook-form that is `mode: 'onTouched'` + the default `reValidateMode: 'onChange'`; in Formik it is `validateOnBlur` with `validateOnMount` left off. `validateOnMount` is the mount-time red-field case; `mode: 'onChange'` validates on the first edit and can be noisy/perf-heavy, but it is not a first-render error by itself. `mode: 'onSubmit'` (the RHF default) shows nothing until the first submit; after that, the default `reValidateMode: 'onChange'` re-validates fields with errors live. Only `reValidateMode: 'onSubmit'` keeps a corrected field's error until the next submit. If `aria-invalid` is derived from the library error, the empty-`required` wait-for-submit rule in **a11y-contract-testing** (Form error exposure, item 1) still applies: an `onTouched` `required` error on focus-and-leave must not flip `aria-invalid` before a submit attempt.
2. **Clear errors when the value becomes valid — and know which manual errors clear themselves.** Schema-driven errors clear themselves only if re-validation actually runs (item 1). For manual `setError(...)`, persistence follows the target *name*, not the error `type`: an error on a **registered** field (including `{ type: 'server' }`) is replaced by that field's next validation run, so after a submit under the default `reValidateMode: 'onChange'` it disappears on the next edit whose value passes the client rules — even though the server never re-checked it. An error on an **unregistered** name persists until `clearErrors(name)` (RHF documents this for built-in field-level validation), and a **`root.*`** error survives edits and is dropped on the next submit. `clearErrors` is therefore needed for unregistered or root errors, or for a registered field when no re-validation runs (before the first submit under `mode: 'onSubmit'`, or under `reValidateMode: 'onSubmit'`). Miss that and the field stays invalid and submit is blocked with no obvious cause (the `setCustomValidity('')` bug, one layer up).
3. **Don't naively gate submit on `isValid`.** Reading `formState.isValid` subscribes to it and makes RHF validate eagerly (from first render — the mount effect runs full validation once `isValid` is tracked), so `disabled={!isValid}` does track validity — but it forces full-form validation on mount, and a conditional read (`!isDirty || !isValid`) is not subscribed while the short-circuit skips it, which RHF's docs mark as the wrong pattern. Gate on submit *attempt*, not on `isValid`; if you disable, disable only on `isSubmitting`/`isValidating`, and re-enable on settle.
4. **Make the in-flight + double-submit contract explicit.** Disable (or ignore re-entry) while `isSubmitting`/`isValidating` is true and re-enable on settle — success, error, *and* reject. A promise that rejects without re-enabling is a permanently dead button. Don't fire the submit handler twice; debounce async field validation so each keystroke doesn't launch a request.
5. **Map server-side errors back onto fields.** A 409 / uniqueness / "email taken" from the API must be reconciled to the owning field (`setError('email', { type: 'server', message })`) and focused, not dropped into a toast. A server error is **two separate contracts** — this mapping, *and* its lifecycle after the next edit (item 2): on a registered field RHF drops the server answer as soon as the new value passes client rules, which is acceptable only if the product is fine with the next submit being the re-check; otherwise re-check against the server or hold the answer in a slot you clear explicitly. Report and fix them as two findings, never one. Decide whose error wins when client and server disagree.
6. **Surface a form-level error too.** If submit fails for a non-field reason (network, 500), show a persistent form-level error surface tied to the failed submit (for example `setError('root.serverError', …)` in RHF or `setStatus` in Formik) — a missing UI *surface*, not a copy bug: a one-off `toast(e.message)` is not the same thing. How that message is announced or focused is the Form error exposure contract in **a11y-contract-testing**; don't prescribe the live-region mechanism here.
7. **Test the timing and the lifecycle, not just the value.** Assert: no error on mount; error after blur; error clears after correction; submit blocked only with a visible message; the button re-enables after a rejected submit; a server field error lands on (and focuses) the right field.

## PR-worthiness gate

Raw `useForm` / `<Formik>` / `mode` / `setError` matches are noisy. Treat a case as PR-worthy only when a user-visible contract is violated:

- **Timing**: `validateOnMount` or display logic that shows errors before interaction; `mode: 'onChange'` alone is only eager first-change validation, not a mount-time error. Also flag `reValidateMode: 'onSubmit'` flows where corrected fields do not re-validate until the next submit.
- **Stuck submit**: `isValid` read conditionally (a short-circuit such as `disabled={!formState.isDirty || !formState.isValid}`), so the Proxy is not subscribed while the short-circuit skips it and the button does not follow validity; submit gating that expects a server `setError` to hold `isValid` at `false` (RHF overwrites it the next time validation runs); or `isSubmitting` never reset after a failed submit (button never re-enables).
- **Stale error**: a corrected field keeps its error — schema error under `reValidateMode: 'onSubmit'`, or a `setError` on an unregistered name or `root.*` with no `clearErrors` on the next edit. A manual error on a registered field already clears on that field's next passing validation, so don't flag it as stale; flag instead a server answer the product needed kept or re-checked. Raise as its own finding, separate from the mapping bug below.
- **Dropped server error**: API field errors shown only as a toast / not `setError`'d to the owning field and focused.
- **Async race**: per-keystroke async validation with no debounce, or a submit handler reachable twice while a request is in flight.

Reject weak findings:

- `mode: 'onChange'` alone, or `mode: 'onTouched'` / `'onBlur'` with default `reValidateMode` and submit gated on attempt — correct.
- `disabled` bound to `isSubmitting`/`isValidating` only (not `isValid`), reset in `finally`.
- The library/schema owns validity and tests already verify error-clears-on-correct and re-enable-on-reject.
- It's purely the native `<input required>` engine (no library owns it) → use **constraint-validation-contracts**; or purely message wording → **i18n-copy-and-layout**.

Minimal useful PR: a failing sequence test — mount (no error) → blur invalid (error) → type valid (error clears) → submit rejects (button re-enabled) → server `setError('email')` (focused, then cleared on edit).

## Output shape

Report the library and state owner, exact mount-touch-edit-submit sequence, visible error/button/focus evidence, smallest validity-lifecycle change, and a test that covers clearing, rejected-submit recovery, and server-error mapping.

## References

| File | Covers |
|------|--------|
| [library-validity-lifecycle](./references/library-validity-lifecycle.md) | react-hook-form `mode`/`reValidateMode`/`formState` (`isValid`/`isSubmitting`/`isValidating`/`errors`)/`trigger`/`setError`/`clearErrors`/`shouldFocusError`/resolvers; Formik `validateOnBlur`/`validateOnMount`/`isSubmitting`/`setFieldError`; zod/yup/valibot async resolver + server-error reconciliation; the constraint-validation / a11y / i18n boundary |

Sources are listed in the reference file.
