---
name: user-activation-contracts
description: "Use when a gesture-gated browser API works from a direct click but fails after async work or in stricter browsers: window.open returns null, OAuth popup login is blocked after await, clipboard/share/file picker/fullscreen/payment requests reject with NotAllowedError, or one gated call consumes activation before the next. User-gesture timing and recovery scope. For copy/export reports, route here only when inactive or consumed activation is the evidenced failure; payload selection, fallback content, and premature success-state defects remain download-export-safety. Use frontend-auth-flow-contracts for OAuth/returnTo policy, payment-page-client-security for payment data boundaries, and iframe-embed-contracts for embedded permissions and host-guest capability policy."
---

# User activation contracts

Some browser capabilities require transient or sticky user activation. Sticky
activation records that the user has interacted with the page and does not
expire or get consumed. For transient activation, the contract is not "there
is a click handler"; the gated call must happen while activation is still
active and before another API consumes it.

## Checklist

1. Identify the exact gated API and whether it requires transient or sticky
   activation. Do not generalize from another browser capability with similar
   UI.
2. Trace the call from a trusted user event to the gated API. Record each
   `await`, timer, queued task, framework transition, and earlier gated call.
   Do not assume activation survives arbitrary asynchronous work or multiple
   consuming APIs.
3. Check `navigator.userActivation.isActive` as diagnostic evidence when
   available, but keep the actual API result and recovery path authoritative.
4. Keep the activation-sensitive step inside the trusted event when possible.
   For an OAuth popup that needs asynchronous URL construction, a bounded
   pattern is to synchronously open a named blank window, perform the async
   work, navigate that window, and close it if preparation fails. Confirm that
   this matches the product's security and accessibility flow; do not weaken
   the existing opener or cross-origin isolation policy to keep the handle.
5. Handle denial, cancellation, and `window.open() === null`. Preserve a
   usable redirect/manual fallback and never report success before the gated
   operation resolves.
6. Do not synthesize a click or dispatch a programmatic event as a workaround;
   untrusted events do not create user activation.
7. Test the real sequence in every supported browser family that matters to
   the product, including the slow preparation path and a second rapid action
   that may expose activation consumption.

## Quick probes

- Log `navigator.userActivation.isActive` immediately inside the handler,
  before and after async preparation, and immediately before the gated call.
- Stub or delay URL/token preparation so the success path crosses the timing
  boundary reliably.
- Assert the blocked/cancelled path restores the button, closes any blank
  popup, and offers the intended fallback.
- For multiple gated operations, reverse their order to detect which call
  consumes activation.

## Boundary with sibling skills

- `frontend-auth-flow-contracts` owns OAuth callback, return target, passkey,
  autocomplete, and auth-state policy.
- `download-export-safety` owns clipboard/export contents, Blob/file lifecycle,
  rejection handling, fallback correctness, and false-success UI. This skill
  owns whether a gesture-gated clipboard or file-picker call remains inside
  transient activation and whether an earlier gated call consumed it. An
  anchor/Object URL export does not establish an activation defect by itself.
- `payment-page-client-security` owns PAN/CVV and payment-page script evidence.
- `iframe-embed-contracts` owns sandbox, Permissions Policy, and parent/guest
  capability delegation.

## PR-worthiness gate

Name the actually gated API, capture the trusted gesture-to-call sequence, and
reproduce the denial or blocked result in a real supported browser. The minimal
PR keeps the sensitive step within activation or adds a truthful recovery path,
plus a browser test for the delayed/blocked sequence.

Reject weak findings: a generic `await` with no gated API after it, a popup
that is intentionally blocked by product policy, an API rejection caused by
permissions or insecure context rather than activation, or advice to add a
click handler when the call already runs within valid activation.

## Output shape

Start with a disposition: confirmed, candidate/needs evidence, reject, or route.
Report the gated API and activation type, trusted event, async/consumption
boundary, browser evidence and exception/result, smallest ordering or fallback
change when one is warranted, sibling-skill handoff, and the test that covers
both success and denial.

## Sources

- MDN, Features gated by user activation: <https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/User_activation>
- MDN, `UserActivation`: <https://developer.mozilla.org/en-US/docs/Web/API/UserActivation>
- HTML Standard, tracking user activation: <https://html.spec.whatwg.org/multipage/interaction.html#tracking-user-activation>
- MDN, `window.open()`: <https://developer.mozilla.org/en-US/docs/Web/API/Window/open>
- Public prior-art issue reproducing a Safari OAuth popup blocked after asynchronous preparation: <https://github.com/tkhq/sdk/issues/1451>
