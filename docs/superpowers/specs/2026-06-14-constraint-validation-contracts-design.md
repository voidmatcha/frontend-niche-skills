# Design — `constraint-validation-contracts` skill

Status: approved 2026-06-14. Collection skill #10.

## Purpose

The bug class created by misusing the HTML Constraint Validation API: required fields painted
red on first paint (`:invalid` matches before the user types), and `setCustomValidity()` left
set so a field is permanently invalid and submit is blocked forever. These are pure spec
behaviors that generic "validate your forms" advice actively causes. Zero overlap with the
existing nine skills.

Scope: **native form-control validity** — CSS state timing, the JS API, and `ValidityState`.
Not ARIA role/name semantics (a11y-contract-testing), not message copy/localization
(i18n-copy-and-layout), not `autocomplete`/auth fields (frontend-auth-flow-contracts).

## Conventions

Inherits the collection's compact `SKILL.md` + `references/`, strict-YAML frontmatter,
verify-against-official-sources rule, and boundary cross-references.

## Frontmatter

- `name: constraint-validation-contracts`
- `description`: "Use when wiring HTML form validation through the Constraint Validation API —
  required fields painted red on page load (`:invalid` vs `:user-invalid` timing),
  `setCustomValidity()` left set so the field is permanently invalid and submit is blocked, or
  choosing between `checkValidity()` / `reportValidity()` / `novalidate` and reading
  `ValidityState`. Native form-validity scope; for ARIA error/role semantics see
  a11y-contract-testing, for error-message copy/localization see i18n-copy-and-layout, for
  `autocomplete`/auth-specific fields see frontend-auth-flow-contracts."

## `SKILL.md` — trap-first checklist (7 items)

1. Style the invalid state with **`:user-invalid`**, not `:invalid` — `:invalid` matches from
   first paint, painting required fields red before the user types. `:user-invalid` applies
   only after interaction/blur/submit.
2. `setCustomValidity(msg)` makes the control invalid and **must be cleared with
   `setCustomValidity("")`** when it's valid again (e.g. on `input`), or the field stays
   permanently invalid and submit is blocked forever.
3. Pick the API deliberately: `checkValidity()` (returns a bool, fires the `invalid` event, no
   UI) vs `reportValidity()` (validates + shows the native bubble + focuses) vs `novalidate`
   (suppress native UI but keep the API/`ValidityState`).
4. Branch messages off `ValidityState` flags (`valueMissing`, `typeMismatch`,
   `patternMismatch`, `rangeOverflow`/`rangeUnderflow`, `tooLong`/`tooShort`, `stepMismatch`,
   `customError`) — don't re-parse the value.
5. Know what participates: `willValidate` is false for disabled/readonly/hidden and certain
   control types, so they don't validate or match `:invalid`.
6. Wire native validity to **accessible** error exposure (`aria-invalid`, `aria-describedby`
   to the message, focus the first invalid control on submit) — but the ARIA role/name
   contract belongs to a11y-contract-testing and the message copy to i18n-copy-and-layout.
7. Test: assert the `ValidityState`, that errors appear at the right *time* (after interaction,
   not on load), and that custom validity is cleared on correction.

## `references/`

- `validation-api-and-states.md` — CSS state & timing (`:user-invalid` vs `:invalid`,
  `:valid`, `:required`, `:in-range`/`:out-of-range`); the JS API (`checkValidity`,
  `reportValidity`, `setCustomValidity`, `validationMessage`, `willValidate`, the `invalid`
  event, `novalidate`/`formnovalidate`); the `ValidityState` flags; and the a11y / i18n
  boundary. *(May split styling-timing / api if it grows.)*

## Boundaries / cross-references

- `a11y-contract-testing` — ARIA error/role/name semantics and focus contracts; this skill
  owns the native validity mechanics that those semantics surface.
- `i18n-copy-and-layout` — the wording/localization of error messages; this skill owns *when*
  and *how* the browser flags invalid, not the copy.
- `frontend-auth-flow-contracts` — `autocomplete` tokens and auth-field specifics; this skill
  is generic field validity.
- Add reverse pointers where low-risk.

## Sources (verify against during build)

MDN: Constraint validation guide; `ValidityState`; `:user-invalid` / `:invalid` /
`:valid`; `setCustomValidity()`; `checkValidity()` / `reportValidity()`;
`HTMLObjectElement/HTMLInputElement.willValidate`; the `invalid` event; `novalidate`. WHATWG
HTML "constraint validation" section for the algorithm/terms.

## Build checklist (implementation plan)

1. `skills/constraint-validation-contracts/SKILL.md`.
2. `skills/constraint-validation-contracts/references/validation-api-and-states.md`.
3. Web-verification workflow over every non-trivial claim (MDN/WHATWG); apply corrections.
4. Register: plugin.json skills[] + description; marketplace.json description + keywords; codex
   plugin.json description/longDescription + keywords + defaultPrompt; README table +
   references prose; CHANGELOG [Unreleased] Added entry. (Version stays 0.4.0 until release.)
5. Add reverse cross-refs in a11y / i18n / auth if low-risk.
6. Verify (JSON, links, frontmatter) and commit.
