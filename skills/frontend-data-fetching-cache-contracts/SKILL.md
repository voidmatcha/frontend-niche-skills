---
name: frontend-data-fetching-cache-contracts
description: "Use when client-side data reads go stale or wasteful against a cache — a list or detail still shows old data after a mutation succeeds because the wrong query key or cache tag was invalidated (or none was), a query refetches on every render because its key is rebuilt as a fresh object/array each time, two different result sets collide in one cache entry (or entries that should share it do not) from key/serialization design, a request waterfall where sequential awaits or dependent queries should run in parallel or be prefetched, over-fetching (refetch storms on focus/mount) or under-fetching (staleTime Infinity so data never refreshes), an infinite-scroll list that replaces instead of appends or grows unbounded and loses scroll on back-navigation, or an Apollo fetchPolicy/nextFetchPolicy stuck cache-only/cache-first (never hits network) or looping refetches. Covers React Query / SWR / RTK Query / Apollo / hand-rolled reads and caching. For the write/mutation/rollback lifecycle see optimistic-update-rollback-contracts; for live delta streams pushed into the cache see realtime-transport-contracts; for server-fetched initial data vs client cache hydration see ssr-hydration-mismatch; for raw fetch-in-effect response races beneath a library see async-effect-race-contracts."
---

# Frontend data fetching cache contracts

Client data libraries cache reads by key and serve them stale-while-revalidate; the read side breaks when a write does not invalidate the exact key the reader subscribes to, when the key itself is unstable or mis-partitioned, or when fetch timing (waterfalls, focus refetch, pagination growth, fetchPolicy) is left to a default that does not match the data. This lens owns reads and caching; the mutation and rollback that produce the new data are the sibling skill.

## Checklist (lead with the trap)

1. **Invalidate the key the reader actually uses — or the read never refreshes.** After a write, a list/detail stays stale unless the exact query key / cache tag it subscribes to is invalidated. TanStack matches fuzzily by key *prefix* (`['todos']` invalidates `['todos', {page}]`) unless `exact: true`; a mismatched key leaves stale data, an over-broad one refetches the world. RTK Query needs `providesTags` on the query and `invalidatesTags` on the mutation to line up (plus a `LIST` id so a newly created row appears). Apollo keys the normalized cache by `__typename:id`, so a new list item will not show up unless you update the list field or refetch. Whether the mutation *fires* the invalidation is the sibling skill; whether it targets the reader's key is here.
2. **Build the key from stable, serialized params — not a fresh object each render.** Keys hash deterministically and object property order does not matter, but the key must be JSON-serializable and stable across renders. A non-serializable value (Date, class, function) or one that changes identity every render fragments the cache into permanent misses; omitting a param the fetch actually depends on collides two different results into one entry. Array item order in the key *is* significant.
3. **Partition the cache key by what selects a different result set — not by what re-slices it.** Filter/sort/search params that change *which* rows come back belong in the key (TanStack key array, Apollo `keyArgs`, RTK `serializeQueryArgs`); params that only re-view the same cached data do not. Wrong grouping means one filter's results bleed into another, or the cache never hits.
4. **Parallelize independent requests; prefetch dependent ones — do not await in series.** Sequential `await`s, or a child query that needs the parent's result, render as a waterfall. Flatten by hoisting/restructuring the API, running independent queries together (`useQueries`/parallel), or prefetching in the parent or router so the second request starts before the child mounts.
5. **Set staleTime/gcTime and focus/reconnect refetch on purpose — defaults differ per library.** TanStack defaults `staleTime: 0` (refetch on every mount/focus) and `gcTime` 5 min; SWR revalidates on focus and reconnect by default and dedupes within a short window; RTK Query does *not* refetch on focus/reconnect unless you opt in (`setupListeners` + `refetchOnFocus`/`refetchOnReconnect`) and drops unused data after ~60s. Over-fetching is a refetch storm on a rarely-changing resource; under-fetching is `staleTime: Infinity` with no invalidation, so it never refreshes. Do not carry one library's mental default into another.
6. **Infinite/paginated cache: append vs replace, and cap growth.** `useSWRInfinite`/`useInfiniteQuery` accumulate pages; a merge or setter that overwrites drops earlier pages. Unbounded page arrays balloon memory and slow back-navigation — TanStack `maxPages` (with both `getNextPageParam` and `getPreviousPageParam`) caps retained pages; on refetch it refetches pages sequentially from the first to avoid stale-cursor duplicates, and if the query is garbage-collected pagination restarts at page one (lost scroll position). Apollo needs a field-policy `merge` (with `keyArgs`) or the list overwrites; RTK Query infinite scroll uses `serializeQueryArgs` + `merge` + `forceRefetch` (or `build.infiniteQuery`).
7. **Apollo fetchPolicy/nextFetchPolicy: do not strand a query off-network or in a refetch loop.** `cache-only`/`cache-first` can leave a screen showing empty or stale data that never revalidates; `cache-and-network`/`network-only` without a `nextFetchPolicy` that demotes to `cache-first` refetches on every render. `nextFetchPolicy` resets to the initial policy when variables change (reason `variables-changed`).
8. **Fetch the shape the view needs — not more, not one-at-a-time.** Selecting whole objects when the screen renders two fields is over-fetch; N+1 per-row detail requests a single list/`useQueries` batch could cover is under-fetch and usually also a waterfall.

## Quick probes

Treat hits as leads; confirm the write->read refresh seam and the key at the call site. Route mechanical key hygiene (unstable keys, missing deps, infinite-query property order) to the authoritative linter `@tanstack/eslint-plugin-query` (rules `exhaustive-deps`, `no-unstable-deps`, `infinite-query-property-order`) — it catches key mistakes faster than review.

```sh
rg -n 'useQuery|useInfiniteQuery|useQueries|useSWR|useSWRInfinite|createApi|queryKey' src/ app/ 2>/dev/null
rg -n 'invalidateQueries|setQueryData|refetch|providesTags|invalidatesTags|refetchQueries|cache\.evict|mutate\(' src/ app/ 2>/dev/null   # write->read refresh seam
rg -n 'staleTime|gcTime|cacheTime|refetchOnWindowFocus|refetchOnReconnect|revalidateOnFocus|keepUnusedDataFor|dedupingInterval' src/ app/ 2>/dev/null
rg -n 'fetchPolicy|nextFetchPolicy|keyArgs|typePolicies|serializeQueryArgs|maxPages|getNextPageParam|fetchMore' src/ app/ 2>/dev/null
rg -nU 'await [^\n]+\n\s*(const|let|await)[^\n]*await' src/ app/ 2>/dev/null   # rough sequential-await smell; inspect the block
```

## Boundary with sibling skills

- This skill: the read/cache side — which key/tag a refresh must invalidate, key design and serialization, waterfalls and prefetch, `staleTime`/`gcTime` and focus/reconnect timing, pagination/infinite cache, and Apollo `fetchPolicy`.
- **optimistic-update-rollback-contracts** — the write side: snapshot, rollback on failure, temp-to-server id swap, and reconcile lifecycle of a mutation. The `invalidate`-after-mutation call is the seam (fires there; must target *this* skill's key).
- **realtime-transport-contracts** — live delta streams (WebSocket/SSE) writing updates into the cache vs polled or on-demand refetched reads.
- **ssr-hydration-mismatch** — server-fetched initial data vs client cache hydration (`dehydrate`/`hydrate`, `initialData`) diverging on first render.
- **async-effect-race-contracts** — raw `fetch`-in-`useEffect` response races (out-of-order resolves, missing `AbortController`) beneath or without a data library.

## PR-worthiness gate

File a finding only when a user-visible read/cache contract is broken:

- **Stale read**: a mutation succeeds but the list/detail shows old data because nothing, or the wrong key/tag, was invalidated.
- **Cache miss/collision**: the key is rebuilt each render (permanent miss/refetch) or two distinct result sets share one entry.
- **Waterfall**: independent requests serialized, or a dependent chain a hoist/prefetch would flatten, with real added latency on the critical path.
- **Pagination**: an infinite list that replaces instead of appends, grows unbounded, or loses position on back-nav with no `maxPages`/restore.
- **Wrong revalidation**: a `fetchPolicy` that strands a screen off-network, or a refetch storm on a near-static resource.

Reject weak findings:

- A query with a stable, correctly-partitioned key whose writes invalidate the matching key/tag — that is the correct pattern.
- Pure `staleTime`/`gcTime` tuning with no user-visible staleness or measurable cost — config preference.
- The mutation's own rollback/temp-id/reconcile handling — sibling skill.
- A raw effect fetch race with no library cache involved — sibling skill.
- "Could add prefetch" with no actual waterfall on the path a user waits for — speculative.

Minimal useful PR: a test that mutates then asserts the reader's key/tag returns fresh data; or a trace showing two requests moved serial->parallel; or an infinite-list test asserting append plus a capped page count.

## Output shape

- **Contract**: invalidation-key match | key design/serialization | cache partitioning | waterfall/prefetch | staleTime/focus timing | pagination cache | fetchPolicy.
- **Evidence**: file/line — the query key/tag, the invalidate/refetch call, the fetch sequence, or the page merge.
- **Symptom**: stale after mutation, cache miss/collision, waterfall latency, list replace/unbounded/lost-scroll, off-network stale, refetch storm.
- **Fix**: smallest change — align the invalidation key/tag, stabilize/serialize the key, parallelize/prefetch, set `staleTime`/`maxPages`, or correct `fetchPolicy`/`nextFetchPolicy`.
- **Verification**: a test or network trace that catches the regression (mutation -> fresh read, parallel requests, append + cap).

## Sources

- TanStack Query — Query Invalidation (prefix/fuzzy key matching, `exact: true`, predicate): <https://tanstack.com/query/v5/docs/framework/react/guides/query-invalidation>
- TanStack Query — Query Keys (deterministic hashing, object order irrelevant, array order significant, must be JSON-serializable): <https://tanstack.com/query/latest/docs/framework/react/guides/query-keys>
- TanStack Query — Important Defaults (`staleTime: 0`, `gcTime` 5 min, `refetchOnWindowFocus`/`refetchOnReconnect` default true): <https://tanstack.com/query/v5/docs/framework/react/guides/important-defaults>
- TanStack Query — Infinite Queries (`maxPages`, both page-param fns, sequential refetch from first, restart on GC): <https://tanstack.com/query/latest/docs/framework/react/guides/infinite-queries>
- TanStack Query — Performance & Request Waterfalls (hoist/restructure, prefetch in parent or router to flatten): <https://tanstack.com/query/latest/docs/framework/react/guides/request-waterfalls>
- SWR — Pagination / `useSWRInfinite` (pages append via mapping, `parallel`, `revalidateAll`, `revalidateFirstPage`, `persistSize`): <https://swr.vercel.app/docs/pagination>
- SWR — Automatic Revalidation (`revalidateOnFocus`/`revalidateOnReconnect`, deduping): <https://swr.vercel.app/docs/revalidation>
- RTK Query — Automated Re-fetching (`providesTags`/`invalidatesTags`, `LIST` id, no cross-endpoint normalization): <https://redux-toolkit.js.org/rtk-query/usage/automated-refetching>
- RTK Query — Customizing Queries (`serializeQueryArgs` + `merge` + `forceRefetch` for a single accumulating cache entry): <https://redux-toolkit.js.org/rtk-query/usage/customizing-queries>
- RTK Query — Cache Behavior (`keepUnusedDataFor`, opt-in `refetchOnFocus`/`refetchOnReconnect` via `setupListeners`): <https://redux-toolkit.js.org/rtk-query/usage/cache-behavior>
- Apollo Client — Queries (`fetchPolicy`/`nextFetchPolicy`, reset on variables change): <https://www.apollographql.com/docs/react/data/queries>
- Apollo Client — Core pagination API (`fetchMore`, field-policy `merge`/`read`, `keyArgs` partitioning): <https://www.apollographql.com/docs/react/pagination/core-api>
- MDN — Cache-Control (`stale-while-revalidate`: serve stale while revalidating in the background): <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cache-Control>
