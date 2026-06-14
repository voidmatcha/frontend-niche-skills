---
name: frontend-auth-flow-contracts
description: "Use when implementing or reviewing frontend authentication flows: login, signup, password reset, email verification, one-time code entry, passkeys/WebAuthn, auth callbacks/returnTo redirects, autofill/autocomplete, account-enumeration-safe errors, or fresh verification before sensitive account actions. Frontend/browser contract scope; for token storage, cookies, SameSite, CSRF, CSP, and XSS hardening use frontend-security-baseline."
---

# Frontend auth flow contracts

Auth UI is a browser/backend contract, not just a form. Use this skill when the
frontend must preserve auth intent, expose the right browser hints, handle retry and
expiry states, and avoid turning auth navigation into an open redirect or unusable
passkey flow.

## Boundary with neighboring skills

- **Use `frontend-security-baseline`** for token storage, cookies, SameSite, CSRF,
  Origin/content-type gates, CSP, XSS, source maps, and open-redirect security
  primitives.
- **Use `deeplink-hydration`** for generic router readiness, cold direct-navigation
  tests, and URL-to-screen reconstruction. This skill owns the auth-specific
  `returnTo`/callback contract layered on top.
- **Use `a11y-contract-testing`** for generic role/name/focus semantics. This skill
  adds auth-specific autofill, error, fallback, and passkey test cases.
- **Do not implement backend crypto here**: Argon2/Bcrypt, CBOR, ECDSA/RSA/EdDSA,
  and session-token storage are server/security implementation details. Translate
  them only into frontend contracts such as expiry, retry, challenge, and fallback
  behavior.

For detailed checklists, read
[references/browser-auth-contracts.md](./references/browser-auth-contracts.md).

## Default workflow

1. Identify the flow: login, signup, password reset, email verification, one-time
   code sign-in, passkey registration/authentication, auth callback, or sensitive
   account action.
2. Define the browser-visible contract before editing: URL inputs, allowed return
   destinations, form fields/autocomplete, pending/expired/retry states, error copy,
   and fallback paths.
3. Add or update tests that enter from a cold URL, assert accessible form/error
   semantics, and cover failure states (expired code, invalid return URL, passkey
   cancel/unsupported/pending).
4. Keep backend guarantees explicit in the UI contract: server-issued challenges,
   one-time code invalidation, rate-limit/retry windows, and fresh verification for
   high-risk actions.

## Quick contract map

| Area | Frontend contract |
|---|---|
| Auth redirects | Preserve intended destination, but validate `returnTo`/`next`/callback targets before restoring. |
| Password forms | Do not silently trim/normalize/sanitize credentials; use correct autocomplete and generic login errors. |
| Email/code flows | Show expiry/retry/resend state; use one-time-code autofill; avoid account enumeration. |
| Passkeys/WebAuthn | Use server challenges, feature detection, conditional mediation fallback, and passkey autofill hints. |
| Sensitive actions | Require fresh identity verification before password/email/passkey/account destructive changes. |
| Tests | Direct-navigation auth URLs, accessible errors, autocomplete attributes, invalid-return rejection, expired-code and passkey-cancel paths. |

## Sources

- Pilcrow auth book: CSRF, sessions, email verification codes, email-code
  authentication, passkeys, WebAuthn, passkey registration/authentication.
- OWASP CSRF and Session Management cheat sheets for the server/security boundary.
- MDN Web Authentication API and HTML `autocomplete` guidance for browser behavior.
