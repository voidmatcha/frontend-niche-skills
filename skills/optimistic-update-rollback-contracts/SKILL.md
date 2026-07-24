---
name: optimistic-update-rollback-contracts
description: "Use when a UI applies a mutation before the server confirms and reconciliation goes wrong — an optimistic change that never rolls back on failure, a created row that shows up twice (temp entry plus refetched real one), an item that flickers or reverts when the server response races a background refetch, a temp client id never swapped for the server id (a later edit/delete hits the wrong record or orphans the temp row), concurrent mutations landing out of order, or a `useOptimistic`/`optimisticData` value that snaps back with nothing persisted. Optimistic-apply/rollback/reconcile lifecycle scope; for form double-submit races see js-form-validation-contracts, announcing rollback to assistive tech see a11y-contract-testing, server-vs-client first render see ssr-hydration-mismatch."
---

# Optimistic update rollback contracts

Optimistic UI shows a mutation's result before the server confirms it, so every optimistic write owes three things: a **snapshot** taken before the change, a **rollback** to that exact snapshot on any failure, and a **reconcile** against true server state on settle. The bugs are never in the happy path — they surface as un-rolled-back fakes, duplicated rows, temp ids that outlive the response, and flicker when a refetch races the mutation.

## Checklist (lead with the trap)

1. **Snapshot before you apply — and roll back to the snapshot, not by inverting the delta.** Capture the prior value (`getQueryData`, the prior list, prior form state) *before* the optimistic write and restore it on failure. Rolling back by re-subtracting/undoing the delta double-counts once a second mutation has touched the same value; restore the captured snapshot instead.
2. **Cancel in-flight refetches before the optimistic write.** In TanStack Query, `await cancelQueries({ queryKey })` inside `onMutate`; otherwise a refetch already running resolves *after* your optimistic write and silently clobbers it (the docs call this out inline).
3. **Wire rollback to every failure exit.** `onError` restores the snapshot; a `mutationFn`/promise that rejects (or throws before the request even leaves) with no rollback leaves the fake state permanently. SWR rolls back by default (`rollbackOnError: true`, and it accepts a per-error function), so confirm any error types you exempt (e.g. `AbortError`) are exempted on purpose.
4. **Reconcile with server truth on settle — don't trust the optimistic value.** Invalidate/refetch in `onSettled` so server-derived fields (ids, timestamps, normalized or partially-rejected values) replace the guess. Return the invalidation promise if the mutation should stay pending until the refetch resolves.
5. **Swap the temp client id for the server id — don't leave both.** An optimistic insert uses a temp id (a uuid or `temp-` prefix); when the response arrives, replace that entry, don't append the real one beside it, or a refetch shows the row twice. In Apollo, include `__typename` + id so the normalized cache can merge temp to real, and use an `update` fn to place new objects into list queries. A later edit/delete still pointing at the temp id hits nothing.
6. **Don't both write the result and invalidate the same query un-guarded.** Writing the server result in `onSuccess` *and* invalidating fires a redundant refetch that can flicker; pick one reconcile path per query (write-through, or invalidate-and-refetch).
7. **Order concurrent mutations to the same resource.** Mutations run in parallel by default; two writes to one record race and last-response-wins can corrupt state. Give related mutations a `scope: { id }` (TanStack) so same-scope mutations run serially, or debounce/queue at the call site.
8. **Know the concurrent-refetch window.** If a second mutation starts while the first is still in flight there is nothing for it to cancel; when the first mutation's invalidation refetch resolves faster than the second mutation settles, the UI reverts (the "window of inconsistency"). Mitigate with query cancellation plus fine-grained invalidation — tag related mutations with a `mutationKey` and gate on `isMutating`.
9. **`useOptimistic`: pure reducer off the *current* base, and something must persist.** The reducer must recompute from its current-state argument, not a captured stale list — React re-runs it if the base changes mid-transition (e.g. another client's insert lands). The value auto-reverts when the action/transition completes, so if no real mutation runs inside that transition it simply snaps back.

## Quick probes

Treat hits as leads; confirm the snapshot to apply to rollback to reconcile path at the call site.

```sh
rg -n 'onMutate|cancelQueries|getQueryData|setQueryData|invalidateQueries|onSettled' src/ app/ 2>/dev/null
rg -n 'optimisticData|rollbackOnError|populateCache|useOptimistic|optimisticResponse' src/ app/ 2>/dev/null
rg -n 'temp-|tmpId|tempId|nanoid\(|crypto\.randomUUID' src/ app/ 2>/dev/null   # temp-id creation -> is it ever swapped?
rg -n 'scope:\s*\{|mutationKey|isMutating' src/ app/ 2>/dev/null               # concurrency ordering
```

## Boundary with sibling skills

- This skill: the optimistic-apply / rollback / reconcile *lifecycle* — snapshot, cancel, apply, roll back on failure, temp-to-server id swap, refetch reconcile, and ordering of concurrent optimistic writes.
- **js-form-validation-contracts** — submit-in-flight, double-submit, and async/server-error races *inside a form* (a create mutation is often both; keep the form's submit-gating there and the cache rollback here).
- **a11y-contract-testing** — announcing success, failure, and rollback to assistive tech (a live region / `role="alert"` for a silent revert).
- **ssr-hydration-mismatch** — server vs client *initial* render divergence (an optimistic value seeded at hydration is a different bug from one applied on user action).
- The cache-invalidation *mechanics* of one specific data library (exact `invalidateQueries` filters, Apollo `keyFields`/`typePolicies`, SWR key scoping) are adjacent implementation detail — cite that library's own docs. This skill owns the cross-library contract, not any one API surface.

## PR-worthiness gate

File a finding only when a user-visible reconciliation contract is broken:

- **No rollback**: an optimistic write with no snapshot, or the `onError`/`rollbackOnError` path missing, so a failed request leaves fake state.
- **Un-swapped temp id**: create shows the row twice after refetch, or a follow-up edit/delete targets a temp id the server never knew.
- **Clobber / flicker**: missing `cancelQueries` before an optimistic write, or an `onSuccess` cache-write plus invalidation both firing, producing a visible revert-then-reappear.
- **Ordering**: concurrent mutations to the same record with no serialization/queue where order actually matters.

Reject weak findings:

- A mutation that already has snapshot + rollback + `onSettled` invalidate — that is the correct pattern, not a defect.
- Optimistic UI on a low-failure single-surface action using `useOptimistic`/variables with no cache rollback — intentionally simpler; don't demand the full cache dance.
- Pure "which `queryKey` to invalidate" tuning with no user-visible drift — that is library config.
- A non-optimistic mutation (spinner until confirmed) — out of scope.

Minimal useful PR: one failing test that drives apply -> server-error -> assert rollback to the snapshot; plus, for creates, apply temp id -> server response -> assert a single row under the real id and no duplicate after refetch.

## Output shape

- **Contract**: snapshot/rollback | temp-to-server id swap | refetch reconcile | concurrency ordering.
- **Evidence**: file/line and the mutation's `onMutate`/`onError`/`onSettled` (or `optimisticData`/`useOptimistic`) path.
- **Symptom**: un-rolled-back fake, duplicate row, flicker/revert, orphaned temp id, out-of-order write.
- **Fix**: smallest change — add snapshot+rollback, add `cancelQueries`, temp-id swap, `scope.id`, or the missing invalidate.
- **Verification**: unit/integration test asserting rollback and post-settle single-source state.

## Sources

- TanStack Query — Optimistic Updates (cache approach: `cancelQueries` -> snapshot -> `setQueryData` -> roll back in `onError` -> invalidate in `onSettled`; return the invalidation promise): <https://tanstack.com/query/v5/docs/framework/react/guides/optimistic-updates>
- TanStack Query — Mutations / `useMutation` (`scope: { id }` runs same-scope mutations serially; otherwise parallel): <https://tanstack.com/query/latest/docs/framework/react/guides/mutations>
- TkDodo — Concurrent Optimistic Updates in React Query (query cancellation, the "window of inconsistency", `mutationKey` + `isMutating`): <https://tkdodo.eu/blog/concurrent-optimistic-updates-in-react-query>
- TkDodo — Mastering Mutations in React Query (when optimistic is overkill; returning the invalidation promise to hold the pending state): <https://tkdodo.eu/blog/mastering-mutations-in-react-query>
- SWR — Mutation & Revalidation (`optimisticData`, `rollbackOnError`, `populateCache`, `revalidate`): <https://swr.vercel.app/docs/mutation>
- React — `useOptimistic` (auto-revert when the action completes; pure reducer recomputed from the current base state): <https://react.dev/reference/react/useOptimistic>
- Apollo Client — Optimistic mutation results (`optimisticResponse` with `__typename` + temp id; `update` fn to add to lists; temp-to-canonical cache-id swap): <https://www.apollographql.com/docs/react/performance/optimistic-ui>
- Apollo Client — Caching overview (normalized cache id = `__typename:id`, which makes the temp-to-real merge possible): <https://www.apollographql.com/docs/react/caching/overview>
