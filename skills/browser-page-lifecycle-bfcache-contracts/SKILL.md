---
name: browser-page-lifecycle-bfcache-contracts
description: "Use when browser Back/Forward restores a stale or half-alive page instead of rerunning startup: logged-out or changed data reappears, a spinner/socket/observer stays paused or duplicates after return, analytics double-count, an unload/beforeunload handler harms back-forward cache behavior, or a fix blindly reloads every pageshow. Top-level browser document freeze/restore scope; use deeplink-hydration for first navigation/router readiness, pwa-offline-cache-contracts for service-worker bytes, realtime-transport-contracts for reconnect protocol, and webview-bridge-pages for native WebView lifecycle."
---

# Browser page lifecycle and bfcache contracts

The back-forward cache can preserve a complete in-memory document and later
restore it. Treat restoration as a resume path: startup may not rerun, old DOM
and JavaScript state may still exist, and resources may need explicit,
idempotent reconciliation.

## Checklist

1. Reproduce with a real same-tab history traversal in a target browser. Record
   the `pageshow` event and `event.persisted`; do not infer bfcache from a fast
   Back navigation alone.
2. Separate **eligibility** from **correctness**. A page can be eligible and
   restore stale user-visible state, or be ineligible for a legitimate reason.
   Use browser diagnostics before prescribing headers or event removal.
3. On `pageshow` with `persisted === true`, revalidate only volatile state that
   may have changed while the page was frozen: authentication visibility,
   permissions, cart/account data, connection state, and time-sensitive UI.
   Make the resume path idempotent so repeated restores do not duplicate
   listeners, observers, timers, sockets, or analytics.
4. Release or pause resources on the appropriate lifecycle signal and reopen
   them on restore when their API requires it. Do not use `unload` as a reliable
   finalization hook; mobile termination can skip it and it can affect bfcache
   behavior.
5. Register `beforeunload` only while there is real unsaved user data that needs
   a confirmation. Remove it when the dirty state clears.
6. Do not default to `location.reload()` on every persisted `pageshow`. A blind
   reload can discard drafts, repeat unsafe navigation, double instrumentation,
   or hide the missing resume contract. Prefer targeted reconciliation unless
   a fresh document load is the product's explicit safe contract.
7. Add a browser regression that loads state, mutates it or changes it from a
   second context, navigates away, goes Back, confirms whether restoration was
   persisted, and asserts the post-restore state and resource counts.

## Quick probes

- Listen once for `pageshow` and log `persisted`, current auth/data version, and
  active connection/listener counts.
- In browser DevTools, run the bfcache eligibility test and record the blocking
  reason instead of guessing from source.
- Traverse A -> B -> Back twice; a duplicate callback on the second cycle often
  exposes non-idempotent resume wiring.
- Change logout/account/cart state in another tab before Back and assert that
  private or stale state is not exposed after restore.

## Boundary with sibling skills

- `deeplink-hydration` owns the first cold URL-to-screen reconstruction.
- `pwa-offline-cache-contracts` owns service-worker and Cache Storage bytes.
- `realtime-transport-contracts` owns reconnect, resume cursor, heartbeat, and
  event ordering. This skill owns only whether restore triggers exactly one
  resource reopen.
- `webview-bridge-pages` owns native WebView renderer/app lifecycle.

## PR-worthiness gate

Require a real browser history traversal plus evidence of either a persisted
restore or a concrete eligibility blocker. Tie the lifecycle path to a
user-visible stale/private state, duplicated or dead resource, lost work, or
measurable navigation regression, then add the smallest Back/Forward test.

Reject weak findings: the mere presence of `pageshow`, `pagehide`, `unload`, a
cache header, or a fast Back navigation; a cleanup that is already idempotent;
or a hypothetical stale-state claim with no restore sequence. Do not propose
`no-store` or unconditional reload solely to silence a bfcache diagnostic.

## Output shape

Start with a disposition: confirmed, candidate/needs evidence, reject, or route.
Report the navigation sequence, browser, `persisted`/eligibility evidence,
state or resource that became wrong, sibling-skill boundary, smallest
reconciliation or eligibility fix, and the Back/Forward regression that
confirms the result. State explicitly when the browser did not restore from
bfcache. If the report lacks `persisted` or eligibility evidence, label it as a
candidate with an evidence gap rather than a confirmed lifecycle defect.

## Sources

- web.dev, Back/forward cache: <https://web.dev/articles/bfcache>
- MDN, `pageshow`: <https://developer.mozilla.org/en-US/docs/Web/API/Window/pageshow_event>
- MDN, `pagehide`: <https://developer.mozilla.org/en-US/docs/Web/API/Window/pagehide_event>
- MDN, `PageTransitionEvent.persisted`: <https://developer.mozilla.org/en-US/docs/Web/API/PageTransitionEvent/persisted>
- Public prior-art issue showing stale restored state and the risks of simplistic unload/reload remedies: <https://github.com/undur/wonder-slim/issues/27>
