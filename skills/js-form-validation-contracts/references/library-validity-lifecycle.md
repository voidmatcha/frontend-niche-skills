# Library validity lifecycle (reference)

## Contents

- [react-hook-form](#react-hook-form)
  - [`mode` — when the FIRST validation runs (per field)](#mode--when-the-first-validation-runs-per-field)
  - [`reValidateMode` — when fields with errors re-validate after a submit attempt](#revalidatemode--when-fields-with-errors-re-validate-after-a-submit-attempt)
  - [`formState` flags](#formstate-flags)
  - [`setError` / `clearErrors` — manual + server errors](#seterror--clearerrors--manual--server-errors)
  - [Async resolvers](#async-resolvers)
- [Formik](#formik)
- [vee-validate / Final Form](#vee-validate--final-form)
- [The four user-visible contracts (what a reviewer/test must verify)](#the-four-user-visible-contracts-what-a-reviewertest-must-verify)
- [Boundary](#boundary)
- [Sources](#sources)

How JS form libraries expose the validity lifecycle, and where each checklist trap lives. Generic — applies to any app using these libraries.

## react-hook-form

### `mode` — when the FIRST validation runs (per field)

`useForm({ mode })`, default `'onSubmit'`.

| `mode` | First validation | Effect |
|--------|------------------|--------|
| `onSubmit` (default) | on submit | No errors until the first submit; after it, inputs re-validate per `reValidateMode` (default `onChange`, so a corrected field clears live). Subscribing to `formState.isValid` triggers eager validation, so it is not simply stuck `false` — but prefer gating on submit attempt. |
| `onChange` | on every change | Validates while the user types; can show errors after the first edit and can cause many re-renders. This is eager validation, not a mount-time error by itself. |
| `onBlur` | on blur | Error after leaving the field; does not then update live while fixing (see `reValidateMode`). |
| `onTouched` | on first blur, then on change | Error after blur, then live as the user fixes it. **This is the "validate on touch, re-validate on change" contract.** |
| `all` | blur + change | Like `onTouched` but also validates the very first change. |

### `reValidateMode` — when fields with errors re-validate after a submit attempt

`'onChange'` (default) | `'onBlur'` | `'onSubmit'`. RHF documents it as the strategy "for when inputs with errors get re-validated after a user submits the form". Default `onChange` is usually correct: after a submit attempt, re-check an errored field live as the user edits. `reValidateMode: 'onSubmit'` recreates the stale-error bug even when `mode` is reasonable.

### `formState` flags

- `isValid` — `true` when the form has no errors. Reading it subscribes to it and makes RHF validate eagerly (from first render: the `useForm` mount effect calls `_setValid()`, which runs full validation when `isValid` is tracked), so `disabled={!isValid}` reflects validity but forces full-form validation on mount. Two documented traps: a **conditional read** (`!formState.isDirty || !formState.isValid`) means "the Proxy does not subscribe to changes of that state" while the short-circuit skips the read, so destructure it before use; and `setError` forces `isValid` to `false` only until the next validation run (next change, submit, or `trigger()`), so a server error cannot be relied on to keep submit disabled. Prefer gating on submit *attempt*.
- `isSubmitting` — `true` while the `handleSubmit` async callback is in flight; resets when the promise settles (resolve **or** reject) — but only if your `onSubmit` actually returns/awaits it.
- `isValidating` — `true` while an async resolver/validator is running.
- `isSubmitted`, `submitCount` — gate "show errors only after a submit attempt" if you prefer submit-time UX over `onTouched`.
- `errors` — the error map. An entry here with no bound UI = a submit blocked with no visible message.

### `setError` / `clearErrors` — manual + server errors

- `setError(name, { type, message })` persistence depends on the target *name*, not on `type`:
  - **Registered field** (including `type: 'server'`): the docs say the method "will not persist the associated input error if the input passes register's associated rules". In source, a field that currently has an error always goes through validation on the next change once the form is submitted (under the default `reValidateMode: 'onChange'`), and a passing result unsets the entry — so a server "email taken" error disappears on the next edit whose value passes client rules, before the server re-checks. Under `reValidateMode: 'onSubmit'`, or before the first submit under `mode: 'onSubmit'`, validation is skipped and the error stays until `clearErrors` or the next validation run.
  - **Unregistered name**: "persisted until cleared with `clearErrors`" (documented for built-in field-level validation; with a resolver, the next submit replaces the whole error map with the resolver's result).
  - **`root.*`** (for example `root.serverError`): not tied to a field, so edits do not clear it; the docs say it "will not persist with each submission", and the next submit drops it.
- Server-side field errors (409 / uniqueness / "email already taken"): `setError('email', { type: 'server', message }, { shouldFocus: true })`. Reconcile to the owning field — never only a toast — and decide whether dropping the server answer on the next passing edit is acceptable or whether it must be re-checked against the server (or held in a slot you clear explicitly).
- `handleSubmit(onValid, onInvalid)` — `onInvalid` fires when submit is attempted with errors; use it to move focus or trigger the error surface (how the error is announced is owned by **a11y-contract-testing**). `shouldFocusError` (default `true`) focuses the first error on a failed submit.

### Async resolvers

`resolver: zodResolver(schema)` / `yupResolver` / `valibotResolver`. For async checks (e.g. remote uniqueness): debounce per-field async validation so each keystroke does not launch a request; gate the submit on `isSubmitting || isValidating`; reconcile the server's authoritative answer with `setError` when it disagrees with the optimistic client result.

## Formik

- `validateOnBlur` (default `true`), `validateOnChange` (default `true`) — leave on.
- `validateOnMount` (default `false`) — **keep off**; turning it on paints errors before any interaction.
- `isSubmitting` / `setSubmitting(false)` — Formik's API docs say an async `onSubmit` gets `isSubmitting` set back to `false` automatically once its promise resolves, but a synchronous `onSubmit` (including one that starts a promise without returning it) must call `setSubmitting(false)` itself, or the button stays disabled. The docs describe only the resolve path, so assert the rejected-submit path in a test rather than assuming it.
- `setFieldError(field, msg)` for server field errors; `status` (via `setStatus`) for a form-level error.
- Gate display on `touched[field] && errors[field]` to avoid errors before interaction.

## vee-validate / Final Form

Same lifecycle, different names — but the mapping is not 1:1, so check each default. vee-validate's live-validation triggers are `validateOnChange` and `validateOnModelUpdate` (both default `true`); `validateOnInput` defaults `false` and `validateOnBlur` defaults `true`. vee-validate `validateOnBlur`/`validateOnInput`/`validateOnMount`, `meta.touched`, `setErrors`, `isSubmitting`; Final Form `meta.touched`/`meta.error`, `submitting`, `submitError`, and per-field/record-level submission errors. Map each checklist item to the equivalent flag.

## The four user-visible contracts (what a reviewer/test must verify)

1. **Timing** — no error on mount; error after touch; updates live while fixing.
2. **Clearing** — a corrected field clears its error (schema-driven errors and registered-field `setError` via the next validation run; unregistered and `root.*` errors via `clearErrors` or the next submit), and a server answer is dropped only where the product accepts that.
3. **Submission** — submit blocked only with a visible, field-or-form-level message; never gated on an `isValid` that is read conditionally (not subscribed while the short-circuit skips it) or expected to stay `false` after a server `setError`.
4. **In-flight / async** — button disabled while submitting/validating and re-enabled on settle (including reject); async field validation debounced; no double-submit; server errors mapped to the right field and focused.

## Boundary

- **Native `<input required>` / Constraint Validation API** (`:user-invalid`, `setCustomValidity`, `checkValidity`/`reportValidity`, `ValidityState`) with no library owning validity → **constraint-validation-contracts**.
- **ARIA error semantics** (`aria-invalid` timing, `aria-errormessage`/`aria-describedby`, focus management, `role="alert"` live region) → **a11y-contract-testing**.
- **Message wording / localization / pluralization** → **i18n-copy-and-layout**.

## Sources

- React Hook Form `useForm` API: <https://react-hook-form.com/docs/useform>
- React Hook Form `formState` (`isValid` and `setError`, conditional-read Proxy subscription): <https://react-hook-form.com/docs/useform/formstate>
- React Hook Form `setError`: <https://react-hook-form.com/docs/useform/seterror>
- React Hook Form `handleSubmit` source — catches an `onValid` rejection, sets `isSubmitting: false`, then rethrows: <https://github.com/react-hook-form/react-hook-form/blob/72a4c98f770d618c05a3fc726a7643b2d2db665b/src/logic/createFormControl.ts#L1934-L1957>
- React Hook Form field `onChange` source — a field with an existing error is never treated as having "no validation effect", `skipValidation` decides by `isSubmitted` and `reValidateMode`, and a passing result unsets the error: <https://github.com/react-hook-form/react-hook-form/blob/72a4c98f770d618c05a3fc726a7643b2d2db665b/src/logic/createFormControl.ts#L1229-L1243>, <https://github.com/react-hook-form/react-hook-form/blob/72a4c98f770d618c05a3fc726a7643b2d2db665b/src/logic/createFormControl.ts#L629-L631>, <https://github.com/react-hook-form/react-hook-form/blob/72a4c98f770d618c05a3fc726a7643b2d2db665b/src/logic/skipValidation.ts>
- React Hook Form `handleSubmit` source — built-in validation unsets the root error (L1922), a resolver replaces the whole error map (L1909), and `isSubmitted: true` is set after `onValid` (L1950): <https://github.com/react-hook-form/react-hook-form/blob/72a4c98f770d618c05a3fc726a7643b2d2db665b/src/logic/createFormControl.ts#L1899-L1950>
- React Hook Form eager `isValid` validation — `useForm` mount effect calls `control._setValid()`, which validates the whole form when `_isTracked('isValid')`: <https://github.com/react-hook-form/react-hook-form/blob/72a4c98f770d618c05a3fc726a7643b2d2db665b/src/useForm.ts#L183-L186>, <https://github.com/react-hook-form/react-hook-form/blob/72a4c98f770d618c05a3fc726a7643b2d2db665b/src/logic/createFormControl.ts#L254-L277>
- React Hook Form `clearErrors`: <https://react-hook-form.com/docs/useform/clearerrors>
- React Hook Form resolvers: <https://github.com/react-hook-form/resolvers>
- Formik validation guide (`validateOnBlur`, `validateOnChange`): <https://formik.org/docs/guides/validation>
- Formik API (`validateOnMount`, `isSubmitting`, `setFieldError`, `setStatus`; async `onSubmit` auto-resets `isSubmitting` "once it has resolved"): <https://formik.org/docs/api/formik>
- Formik releases (latest `formik@2.4.9`, 2025-11-10; checked 2026-09-24): <https://github.com/jaredpalmer/formik/releases>
- vee-validate form API: <https://vee-validate.logaretm.com/v4/api/form/>
- vee-validate "Customizing Validation Triggers" (`configure` defaults: `validateOnBlur: true`, `validateOnChange: true`, `validateOnInput: false`, `validateOnModelUpdate: true`): <https://vee-validate.logaretm.com/v4/guide/components/validation/#customizing-validation-triggers>
- Final Form field state: <https://final-form.org/docs/final-form/types/FieldState>
- TanStack Form (validity-lifecycle mapping for the same contracts): <https://tanstack.com/form/latest/docs/overview>
- Vercel Web Interface Guidelines, Forms: <https://vercel.com/design/guidelines#forms>
