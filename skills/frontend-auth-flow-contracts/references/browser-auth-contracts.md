# Browser auth contracts

## Return destinations and auth callbacks

- Preserve the user's intended destination through login, email-code, passkey, and
  password-reset bounces. A deep link that reaches the login wall and then lands on
  a default dashboard is still broken.
- Treat `returnTo`, `next`, `redirect_uri`, callback URLs, and session-stored
  post-login destinations as untrusted input. Restore only same-origin relative
  paths or explicit allowlisted origins, validated with a real URL parser. The full
  open-redirect bypass catalog (scheme-relative `//evil`, the userinfo separator,
  encoded backslashes, `startsWith`/denylist evasion) and the allow-list-not-denylist
  rule are the canonical property of **frontend-security-baseline**
  (`references/navigation-and-supply-chain.md`) — don't restate them; this skill owns
  only the auth-bounce delta (carry intent through the flow, restore it afterward).
- Test from a cold URL, not only in-app navigation: unauthenticated direct link →
  login → complete auth → final intended path.

## Password and account identifier forms

- Password input is a credential, not prose. Do not silently trim, lowercase, or
  sanitize it. (Unicode normalization is the exception: NIST SP 800-63B says the
  verifier SHOULD apply NFC before hashing — if you normalize, do it consistently on
  both register and login, server-side, not as a silent client-side edit.) If a
  product disallows leading/trailing spaces or non-supported characters, reject with a
  clear error instead of changing input.
- Use browser hints deliberately: `autocomplete="username"` or `email` for the
  account identifier, `current-password` for login, and `new-password` for password
  creation/reset.
- Avoid account enumeration in login and reset flows. Keep failure copy equivalent
  for "account missing" and "credential wrong" unless the product has a deliberate
  recovery policy.
- Never log credential values, one-time codes, WebAuthn client data, or full reset
  URLs in frontend telemetry.

## Email verification and one-time code flows

- Code UI must reflect backend lifecycle: short expiry, resend throttle, attempt
  limits, one-time invalidation after success, and invalidation after email change or
  cancellation.
- Use `autocomplete="one-time-code"` and mobile-friendly input hints (`inputmode`,
  grouping, paste support) without changing the submitted code semantics.
- Prefer generic "check your email" states when sending reset or sign-in codes, so
  unknown-account responses do not reveal account existence.
- On expiry or resend, make state transitions explicit: disable stale submit paths,
  refresh challenge/code state, and explain whether the previous code still works.
- Test: valid code, expired code, reused code after success, resend cooldown, max
  attempts, paste full code, and accessible error/status announcements.

## Passkeys and WebAuthn UI

- WebAuthn requires a server-issued challenge. The frontend only initiates
  `navigator.credentials.create()` / `.get()` and sends binary response data back;
  the server validates challenge, origin, RP ID, user presence/verification, and
  signature.
- Feature-detect before showing passkey-first UI. Keep password/email-code fallback
  reachable when WebAuthn is unsupported, cancelled, blocked by browser policy, or
  still pending under conditional mediation.
- Prefer user verification for account access. Treat passkey registration/deletion as
  sensitive account actions that require fresh verification/action-specific session.
- For passkey autofill, include the `webauthn` autocomplete token on the account
  identifier field and start conditional mediation after page readiness. The promise
  can remain pending indefinitely; do not block normal form submission or route
  transitions on it.
- Let users name passkeys and manage multiple credentials. Registration should handle
  duplicate/excluded credentials and max-passkey limits gracefully.
- Test: unsupported browser, user cancel, conditional mediation pending, fallback
  submit still works, challenge expiry/refresh, duplicate registration, delete with
  stale verification rejected.

## Sensitive account actions

Require fresh identity verification before:

- changing password or primary email;
- registering, renaming, or deleting passkeys/security keys;
- disabling MFA or changing recovery methods;
- deleting the account or exporting highly sensitive data.

Do not silently reuse an old authenticated session as proof of recent identity. The UI
should surface verification expiry and restart the action-specific flow when needed.

## Minimal test checklist

- Cold unauthenticated auth redirect restores the intended same-origin destination.
- Invalid return URL is rejected and does not navigate off-origin.
- Login/reset errors are accessible and do not reveal account existence unless
  intentionally designed.
- Password fields keep exact user input; validation rejects rather than mutates.
- Email-code form covers expiry, resend cooldown, paste, reuse, and max attempts.
- Passkey flow covers unsupported/cancel/pending states and preserves fallback login.
- Sensitive passkey/password/email changes require fresh verification.
