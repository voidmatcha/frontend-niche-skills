# Library validity lifecycle (reference)

How JS form libraries expose the validity lifecycle, and where each checklist trap lives. Generic —
applies to any app using these libraries.

## react-hook-form

### `mode` — when the FIRST validation runs (per field)

`useForm({ mode })`, default `'onSubmit'`.

| `mode` | First validation | Effect |
|--------|------------------|--------|
| `onSubmit` (default) | on submit | A corrected field keeps its error until the next submit. Subscribing to `formState.isValid` triggers eager validation, so it is not simply stuck `false` — but do not use it as the submit gate here. |
| `onChange` | on every change | Validates while the user types; can show errors after the first edit and can cause many re-renders. This is eager validation, not a mount-time error by itself. |
| `onBlur` | on blur | Error after leaving the field; does not then update live while fixing (see `reValidateMode`). |
| `onTouched` | on first blur, then on change | Error after blur, then live as the user fixes it. **This is the "validate on touch, re-validate on change" contract.** |
| `all` | blur + change | Like `onTouched` but also validates the very first change. |

### `reValidateMode` — when validation runs AFTER the first error

`'onChange'` (default) | `'onBlur'` | `'onSubmit'`. Default `onChange` is usually correct: once a field
has errored, re-check it live as the user edits. `reValidateMode: 'onSubmit'` recreates the
stale-error bug even when `mode` is reasonable.

### `formState` flags

- `isValid` — **mode-dependent.** Reading it subscribes to it and makes RHF validate eagerly (from
  first render), so `disabled={!isValid}` reflects validity but forces full-form validation on mount.
  Prefer gating on submit *attempt* under `onSubmit`; treat it as a clean live gate only under
  `onChange`/`onTouched`/`all`.
- `isSubmitting` — `true` while the `handleSubmit` async callback is in flight; resets when the
  promise settles (resolve **or** reject) — but only if your `onSubmit` actually returns/awaits it.
- `isValidating` — `true` while an async resolver/validator is running.
- `isSubmitted`, `submitCount` — gate "show errors only after a submit attempt" if you prefer
  submit-time UX over `onTouched`.
- `errors` — the error map. An entry here with no bound UI = a submit blocked with no visible message.

### `setError` / `clearErrors` — manual + server errors

- `setError(name, { type, message })` ownership depends on the target. For a registered field,
  React Hook Form does not persist the associated input error once that input passes its registered
  validation rules. For unregistered/manual targets, root/server errors, or field errors not covered
  by the active validation rules, treat the error as manually owned: clear it with `clearErrors(name)`
  on the next edit or move it into resolver/server-error lifecycle.
- Server-side field errors (409 / uniqueness / "email already taken"): `setError('email',
  { type: 'server', message }, { shouldFocus: true })`. Reconcile to the owning field — never only a
  toast — and decide whether the next edit clears the server answer or revalidates it against the server.
- `handleSubmit(onValid, onInvalid)` — `onInvalid` fires when submit is attempted with errors; use it
  to focus/announce. `shouldFocusError` (default `true`) focuses the first error on a failed submit.

### Async resolvers

`resolver: zodResolver(schema)` / `yupResolver` / `valibotResolver`. For async checks (e.g. remote
uniqueness): debounce per-field async validation so each keystroke does not launch a request; gate the
submit on `isSubmitting || isValidating`; reconcile the server's authoritative answer with `setError`
when it disagrees with the optimistic client result.

## Formik

- `validateOnBlur` (default `true`), `validateOnChange` (default `true`) — leave on.
- `validateOnMount` (default `false`) — **keep off**; turning it on paints errors before any interaction.
- `isSubmitting` / `setSubmitting(false)` — Formik does **not** auto-reset `isSubmitting` if your
  `onSubmit` is async and you neither call `setSubmitting(false)` nor return an awaitable promise; a
  rejected submit then leaves the button stuck.
- `setFieldError(field, msg)` for server field errors; `status` (via `setStatus`) for a form-level error.
- Gate display on `touched[field] && errors[field]` to avoid errors before interaction.

## vee-validate / Final Form

Same lifecycle, different names — but the mapping is not 1:1, so check each default. vee-validate's
live-validation triggers are `validateOnChange` and `validateOnModelUpdate` (both default `true`);
`validateOnInput` defaults `false` and `validateOnBlur` defaults `true`. vee-validate `validateOnBlur`/`validateOnInput`/`validateOnMount`,
`meta.touched`, `setErrors`, `isSubmitting`; Final Form `meta.touched`/`meta.error`, `submitting`,
`submitError`, and per-field/record-level submission errors. Map each checklist item to the equivalent flag.

## The four user-visible contracts (what a reviewer/test must verify)

1. **Timing** — no error on mount; error after touch; updates live while fixing.
2. **Clearing** — a corrected field clears its error (schema-driven *and* manual/server `setError`).
3. **Submission** — submit blocked only with a visible, field-or-form-level message; never gated on an
   `isValid` that can't become `true` in the chosen mode.
4. **In-flight / async** — button disabled while submitting/validating and re-enabled on settle
   (including reject); async field validation debounced; no double-submit; server errors mapped to the
   right field and focused.

## Boundary

- **Native `<input required>` / Constraint Validation API** (`:user-invalid`, `setCustomValidity`,
  `checkValidity`/`reportValidity`, `ValidityState`) with no library owning validity →
  **constraint-validation-contracts**.
- **ARIA error semantics** (`aria-invalid` timing, `aria-errormessage`/`aria-describedby`, focus
  management, `role="alert"` live region) → **a11y-contract-testing**.
- **Message wording / localization / pluralization** → **i18n-copy-and-layout**.

## Sources

- React Hook Form `useForm` API: <https://react-hook-form.com/docs/useform>
- React Hook Form `setError`: <https://react-hook-form.com/docs/useform/seterror>
- React Hook Form `clearErrors`: <https://react-hook-form.com/docs/useform/clearerrors>
- React Hook Form resolvers: <https://github.com/react-hook-form/resolvers>
- Formik validation guide (`validateOnBlur`, `validateOnChange`): <https://formik.org/docs/guides/validation>
- Formik API (`validateOnMount`, `isSubmitting`, `setFieldError`, `setStatus`): <https://formik.org/docs/api/formik>
- vee-validate form API: <https://vee-validate.logaretm.com/v4/api/form/>
- Final Form field state: <https://final-form.org/docs/final-form/types/FieldState>
- Vercel Web Interface Guidelines, Forms: <https://vercel.com/design/guidelines#forms>
