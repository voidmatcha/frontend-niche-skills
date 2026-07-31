---
name: constraint-validation-contracts
description: "Use when wiring HTML form validation through the Constraint Validation API — required fields painted red on page load (`:invalid` vs `:user-invalid` timing), `setCustomValidity()` left set so the field is permanently invalid and submit is blocked, or choosing between `checkValidity()` / `reportValidity()` / `novalidate` and reading `ValidityState`. Native form-validity scope; for ARIA error/role semantics see a11y-contract-testing, for error-message copy/localization see i18n-copy-and-layout, for `autocomplete`/auth-specific fields see frontend-auth-flow-contracts."
---

# Constraint validation contracts

The browser ships a whole form-validation engine — `required`, `type`, `pattern`, `min`/`max`,
`minlength`/`maxlength`, `step`, plus a JS API and CSS pseudo-classes. The bugs come from
driving it slightly wrong, and they're pure spec behavior, not framework quirks: a form that
**shows every field red before the user types a character**, and a field that is
**permanently invalid because a custom message was set and never cleared**, silently blocking
submit. Both pass a quick happy-path test and surface only in real use.

This skill is the native validity mechanics. For the ARIA role/name/focus *contract* around
errors use **a11y-contract-testing**; for the *wording* and localization of messages use
**i18n-copy-and-layout**; for `autocomplete` tokens and auth-field specifics use
**frontend-auth-flow-contracts**.

## Checklist (lead with the trap; details in references/)

→ [validation-api-and-states](./references/validation-api-and-states.md)

1. **Style invalid with `:user-invalid`, not `:invalid`.** `:invalid` matches from first
   paint, so `required` fields render red before any interaction. `:user-invalid` applies only
   after the user has interacted (edited/blurred) or tried to submit — which is the state you
   actually want to style.
2. **Always clear `setCustomValidity`.** `setCustomValidity("non-empty")` marks the control
   invalid; you must call `setCustomValidity("")` once it's valid again (typically on the next
   `input` event), or the field stays invalid forever and submit is blocked with no obvious
   cause.
3. **Choose the API on purpose.** `checkValidity()` returns a boolean and fires a cancelable
   `invalid` event but shows no UI; `reportValidity()` does the same *and* shows the native
   bubble and focuses the first invalid field; `novalidate` (form) / `formnovalidate` (submit
   button) suppress native UI and submit-blocking while leaving the API and `ValidityState`
   fully usable.
4. **Branch on `ValidityState`, don't re-parse.** Read `input.validity.valueMissing`,
   `typeMismatch`, `patternMismatch`, `rangeOverflow`/`rangeUnderflow`, `tooLong`/`tooShort`,
   `stepMismatch`, `badInput`, `customError` to decide which message to show.
5. **Know what participates.** `willValidate` is `false` for disabled, `readonly` (where
   applicable — `input`/`textarea`, not `select`/`button`), and certain hidden/`type`
   controls — those don't validate, don't fire `invalid`, and don't match `:invalid`. Don't
   rely on validity for a field you've disabled.
6. **Connect validity to accessibility, but stay in lane.** Set `aria-invalid="true"` only
   *after* interaction/submit — same gate as item 1, since (per MDN) you shouldn't mark an
   untouched `required` field invalid. Associate the message with `aria-errormessage` (MDN's
   purpose-built attribute, paired with `aria-invalid="true"`; `aria-describedby` is the
   broadly supported alternative, better suited to persistent hints) — and clear `aria-invalid`
   once the field is valid, since `aria-errormessage` is only conveyed while
   `aria-invalid="true"`. Focus the first invalid control on a failed submit — while the ARIA
   role/name contract lives in **a11y-contract-testing** and the message copy in
   **i18n-copy-and-layout**.
7. **Test the timing, not just the value.** Assert the `ValidityState`, that errors appear
   *after* interaction (not on load), and that custom validity is cleared when the user
   corrects the input.

## PR-worthiness gate

Raw `:invalid` and `setCustomValidity` searches are noisy. Treat a case as PR-worthy only when
one of these user-visible contracts is violated:

- **Timing contract**: errors appear before interaction/submission, or fail to appear after a
  failed submit.
- **Clearing contract**: a field stays invalid after the user changes it to a valid value
  (`validationMessage`, `checkValidity()`, or disabled-submit state shows it).
- **Submission contract**: `novalidate`, `checkValidity()`, or `reportValidity()` lets an invalid
  value through, blocks a valid value, or focuses the wrong field.

Reject weak findings:

- `:invalid` is scoped under `.submitted`, `.touched`, `:user-invalid`, or equivalent state.
- Every non-empty `setCustomValidity(...)` path has a paired `setCustomValidity('')` on input or
  revalidation.
- A form library owns validity and already has tests verifying native validity is cleared.
- The only problem is wording/localization of an otherwise correct message; use
  `i18n-copy-and-layout` instead.

Minimal useful PR: include a failing sequence test such as invalid -> edit valid ->
`expect(input.validationMessage).toBe('')` -> submit succeeds.

## Output shape

Report the native validity owner, failing invalid-to-valid or submit sequence,
`ValidityState`/message evidence, smallest lifecycle fix, and the browser test
that confirms timing, clearing, and submission behavior.

## References

| File | Covers |
|------|--------|
| [validation-api-and-states](./references/validation-api-and-states.md) | CSS state & timing (`:user-invalid` vs `:invalid`, `:valid`, `:required`, `:in-range`); the JS API (`checkValidity`, `reportValidity`, `setCustomValidity`, `validationMessage`, `willValidate`, the `invalid` event, `novalidate`/`formnovalidate`); the `ValidityState` flags; and the a11y / i18n boundary |

Sources are listed in the reference file.
