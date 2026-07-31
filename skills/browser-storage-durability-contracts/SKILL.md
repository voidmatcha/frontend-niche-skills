---
name: browser-storage-durability-contracts
description: "Use when browser-local data is reported saved but disappears, an IndexedDB schema upgrade hangs behind another tab, writes fail with TransactionInactiveError or abort after request success, storage pressure causes QuotaExceededError or suspected eviction, navigator.storage.persist() is treated as backup assurance, or recovery UI overstates what remains durable. Covers IndexedDB lifecycle plus StorageManager evidence. Use pwa-offline-cache-contracts for service-worker Cache Storage, frontend-data-fetching-cache-contracts for HTTP/client read caches, and frontend-security-baseline for sensitive-data policy."
---

# Browser storage durability contracts

Review one claim: whether browser-local data was successfully committed and
whether the product can truthfully recover when that local copy is blocked,
aborted, unavailable, or removed. Keep IndexedDB transaction and schema
lifecycle evidence connected to origin-level quota and persistence evidence;
do not turn this into generic storage-selection advice.

## Checklist

1. **Name the failed durability stage.** Separate open/upgrade, transaction
   execution, transaction commit, quota/persistence, unexpected connection
   closure, and recovery. Record the database name and version, transaction
   mode and stores, request/transaction events, browser context, and the exact
   user-visible loss. “IndexedDB is flaky” is not a diagnosis.
2. **Reproduce upgrades with at least two live contexts.** Keep an older
   connection open in tab A, request a higher version in tab B, and record
   `blocked` on B plus `versionchange` on A. A `blocked` event means an open
   connection is preventing the versionchange transaction; a slow open without
   that event is not enough to file a cross-tab ownership defect.
3. **Make every long-lived connection yield ownership.** Attach
   `versionchange` as soon as a connection opens, stop creating new work,
   close that connection, and let the affected UI ask the user to reload or
   retry. `close()` returns immediately, prevents new transactions, and
   finishes closing after existing transactions complete. Cover windows,
   workers, and any shared database wrapper; one forgotten owner can keep the
   upgrade blocked.
4. **Keep schema work inside the upgrade transaction.** Inspect
   `upgradeneeded`/the wrapper's upgrade callback, old and requested versions,
   and the versionchange transaction's `abort`/`error` outcome. Do not “fix” a
   blocked migration by deleting the database or clearing all site data unless
   destructive reset is the explicit product contract and recoverability is
   proven.
5. **Keep asynchronous gaps out of a live transaction.** A transaction is
   active in its creation task and in its request event-handler tasks, inactive
   in other tasks, and auto-commits when no request remains and no new request
   is queued. Fetch, timers, unrelated promises, or user prompts between IDB
   requests can leave later requests with `TransactionInactiveError`. Finish
   external work before opening the transaction, or split the operation at an
   explicit consistency boundary. When the final write depends on an earlier
   read, re-read the record or compare a revision inside the final readwrite
   transaction so a fresh put cannot overwrite a newer concurrent value.
6. **Treat transaction completion as the write result.** A request's success
   shows that request produced a result, not that the whole transaction
   committed. Report success only after the transaction's `complete` event (or
   a wrapper's equivalent completion promise); surface `abort` and `error`,
   including `transaction.error`. A later constraint error, exception, I/O
   failure, quota failure, or explicit `abort()` can roll back the transaction.
   This is the application-visible commit boundary, not evidence that bytes
   survived an immediate device/browser crash or that a backup exists. If that
   distinction matters, record the transaction's durability hint and verify
   the target browser/profile instead of silently upgrading `complete` into a
   stronger retention claim.
7. **Use StorageManager values as evidence, not exact accounting.** Capture
   `navigator.storage.estimate()` near the failing write and record `usage`,
   `quota`, and available `usageDetails`, but label them approximate and
   origin-level. Confirm quota exhaustion with the actual rejected write and
   `QuotaExceededError`; a high percentage or a source grep alone is only a
   lead.
8. **Distinguish best-effort from persistent storage.** Record
   `navigator.storage.persisted()` before claiming protection, and record the
   boolean returned by `persist()` when the product requests it. Denial is a
   supported outcome. Persistent storage protects an origin from automatic
   storage-pressure eviction, but the user can still remove it; do not present
   a granted request as permanent retention or backup.
9. **Make recovery wording truthful.** Detect an absent database/schema,
   unexpected `close`, aborted migration, rejected write, and unavailable
   storage separately. State whether the data is reconstructible, remotely
   authoritative, exportable, or browser-local-only. This skill may require a
   recovery gap to be disclosed, but it does not design application sync,
   conflict resolution, or backup architecture.
10. **Add the smallest browser regression that crosses the failed boundary.**
    Use a second tab for blocked upgrades, a deliberately delayed non-IDB await
    for transaction lifetime, a later failing request for rollback, controlled
    storage pressure or injected `QuotaExceededError` for write handling, and
    cleared/absent storage for recovery wording. Assert both stored state and
    what the UI tells the user.

## Quick probes

Treat source hits as leads and correlate them with runtime events:

```sh
rg -n "indexedDB\.open|openDB|upgradeneeded|blocked|versionchange|\\.close\\(" src/ app/ 2>/dev/null
rg -n "transaction\\(|TransactionInactiveError|\\.commit\\(|\\.abort\\(|oncomplete|onabort|tx\\.done" src/ app/ 2>/dev/null
rg -n "navigator\\.storage|\\.estimate\\(|\\.persisted\\(|\\.persist\\(|QuotaExceededError" src/ app/ 2>/dev/null
rg -n "deleteDatabase|clear.*storage|saved|offline|backup|recover|restore" src/ app/ 2>/dev/null
```

At runtime, log old/new database versions, `blocked`, `versionchange`,
`complete`, `abort`, `error`, unexpected `close`, and the failing exception
name. Take `estimate()` snapshots before and after a controlled write, but do
not use the delta as exact per-record size.

## Boundary with sibling skills

- `pwa-offline-cache-contracts` owns service-worker lifecycle, Cache Storage,
  precached assets, offline navigation, and stale deployed bytes.
- `frontend-data-fetching-cache-contracts` owns HTTP/client read-cache keys,
  invalidation, revalidation, pagination, and request waterfalls.
- `frontend-security-baseline` owns whether sensitive values, credentials, or
  personalized responses may be stored client-side and their privacy policy.
- This skill records whether browser-local data is reconstructible or
  browser-local-only. It does not own server synchronization, conflict
  resolution, backup design, or choosing IndexedDB versus `localStorage`.

## Minimal regression shapes

- **Blocked upgrade:** tab A opens version N; tab B requests N+1; assert A
  receives `versionchange`, closes, B leaves `blocked`, and the upgrade
  completes without deleting user data.
- **Commit/abort:** queue two writes where the later request violates a
  constraint; assert no “saved” UI appears from the first request and the
  transaction abort leaves no partial state.
- **Inactive transaction:** place a controllable non-IDB task between requests;
  reproduce the failure, then move that task outside the transaction. If the
  work is split, let another context update the record and assert that a
  revision check in the final transaction prevents a stale overwrite.
- **Quota:** reject a write with `QuotaExceededError` or run in a controlled
  constrained profile; assert no success claim and only policy-authorized
  cleanup or export behavior.
- **Unexpected close/recovery:** close unexpectedly or reopen an absent
  database; assert that every window or worker owner yields its connection and
  that the UI reports local loss and reconstructibility without calling an
  empty replacement a successful recovery.

## PR-worthiness gate

File or patch only when runtime evidence ties a broken durability stage to
user-visible loss, a permanently blocked upgrade, a false saved/synced claim,
an unrecoverable destructive reset, or a repeated write failure:

- **Upgrade ownership:** `blocked` plus a live owner that ignores
  `versionchange` or never closes.
- **Transaction lifetime:** a later IDB request fails after an asynchronous gap,
  and moving or splitting that work preserves the intended consistency.
- **False commit:** UI or calling code treats request success as durable even
  though the transaction can be shown to abort.
- **Quota/persistence:** the actual write rejects, persistence state contradicts
  the product claim, or recovery behavior misstates what survives.
- **Unexpected loss:** absent or cleared origin storage reaches a recovery path
  that lies, loops, destroys the remaining copy, or cannot explain the boundary.

Reject weak findings:

- The presence of IndexedDB, `blocked`, `versionchange`, `abort`, or
  `navigator.storage` without a failing sequence.
- A multi-tab upgrade whose old connections close on `versionchange` and whose
  new connection completes.
- `estimate().usage / estimate().quota` alone, because the values are
  approximate and origin-wide.
- `persist()` returning `false` when the application correctly continues with
  a best-effort and recoverable local copy.
- A transaction that awaits only its own queued IDB requests and completes.
- A service-worker/Cache Storage defect, stale client query cache, security
  policy review, generic `localStorage` comparison, or proposed sync system.

## Output shape

Start with a disposition: **confirmed**, **candidate/needs evidence**,
**reject**, or **route**. Then report:

- **Stage:** open/upgrade | transaction activity | commit/abort |
  quota/persistence | unexpected close | recovery.
- **Evidence:** browser and contexts, database versions, transaction scope,
  ordered events/exceptions, `persisted()` result, and approximate
  `estimate()` snapshot when relevant.
- **Impact:** data not committed, upgrade blocked, false saved claim, write
  rejected, local copy removed, or recovery overstated.
- **Boundary:** why this belongs here or which sibling owns it.
- **Smallest fix:** connection yielding, async-boundary change, transaction
  completion handling, quota fallback, or truthful recovery behavior.
- **Verification:** the focused multi-context or failure-injection regression
  and any remaining browser/profile gap.

Never say data is “durable,” “backed up,” or “safe offline” when the evidence
is limited to request success, a granted persistence request, or current
presence in one browser profile.

## Sources

- MDN, `IDBOpenDBRequest: blocked` (an open connection blocks a versionchange
  transaction): <https://developer.mozilla.org/en-US/docs/Web/API/IDBOpenDBRequest/blocked_event>
- MDN, `IDBDatabase: versionchange` (a schema change or deletion requested in
  another context): <https://developer.mozilla.org/en-US/docs/Web/API/IDBDatabase/versionchange_event>
- MDN, `IDBDatabase.close()` (new transactions stop; existing transactions
  finish before the connection closes): <https://developer.mozilla.org/en-US/docs/Web/API/IDBDatabase/close>
- MDN, `IDBDatabase: close` (unexpected closure after underlying removal or
  user clearing): <https://developer.mozilla.org/en-US/docs/Web/API/IDBDatabase/close_event>
- MDN, `IDBTransaction` (active/inactive tasks, auto-commit, abort causes,
  rollback, and commit semantics):
  <https://developer.mozilla.org/en-US/docs/Web/API/IDBTransaction>
- MDN, `IDBTransaction: complete` (fires after successful transaction commit):
  <https://developer.mozilla.org/en-US/docs/Web/API/IDBTransaction/complete_event>
- MDN, `IDBTransaction.durability` (reports the transaction's durability hint):
  <https://developer.mozilla.org/en-US/docs/Web/API/IDBTransaction/durability>
- MDN, `StorageManager.estimate()` (approximate origin usage/quota and
  imprecision): <https://developer.mozilla.org/en-US/docs/Web/API/StorageManager/estimate>
- MDN, `StorageManager.persist()` (requests persistence and returns whether it
  was granted): <https://developer.mozilla.org/en-US/docs/Web/API/StorageManager/persist>
- MDN, `StorageManager.persisted()` (reports whether the current bucket is
  persistent): <https://developer.mozilla.org/en-US/docs/Web/API/StorageManager/persisted>
- MDN, Storage quotas and eviction criteria (best-effort versus persistent,
  `QuotaExceededError`, pressure eviction, user deletion, and origin-wide
  storage): <https://developer.mozilla.org/en-US/docs/Web/API/Storage_API/Storage_quotas_and_eviction_criteria>
- Jake Archibald, `idb` public API and prior art (`blocked`, `blocking`,
  `terminated`, transaction lifetime, and `tx.done`):
  <https://github.com/jakearchibald/idb#opendb>
- Public prior-art issue reproducing `TransactionInactiveError` between
  successive IndexedDB requests in a worker; the reported engine bug was later
  closed as fixed, so use it as a failure shape rather than a current support
  claim: <https://github.com/jakearchibald/idb/issues/73>
