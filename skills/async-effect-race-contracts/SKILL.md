---
name: async-effect-race-contracts
description: "Use when a raw async effect or concurrency primitive races or leaks below any data library — a fetch-on-deps useEffect where a slow earlier response resolves after a newer one and wins (results flicker back to stale data) because there is no ignore flag or AbortController take-latest; a missing cleanup so setState fires after unmount or a subscription/listener/interval/socket keeps running (leak, duplicated handlers, silent lost update); React 18/19 StrictMode double-invoking an effect in dev and exposing non-idempotent setup (analytics fired twice, two sockets, doubled subscriptions); a stale closure where a value captured in a long-lived setInterval/setTimeout/subscription/event handler never updates; or a dependency-array omission causing an infinite re-run loop or a stale read. Bare useEffect / async-primitive lens; when a data library owns the fetch use frontend-data-fetching-cache-contracts (its cancellation/dedupe), for mutation apply/rollback races see optimistic-update-rollback-contracts, for socket subscribe/unsubscribe lifecycle and recovery see realtime-transport-contracts."
---

# Async effect race contracts

A raw `useEffect` that touches the outside world (fetch, subscribe, listen, schedule) owes two things the happy path never shows: a **take-latest guard** so an older async result cannot overwrite a newer one, and a **cleanup that mirrors setup exactly** so nothing keeps running after the effect re-runs or the component unmounts. The bugs surface as stale data winning a race, leaked subscriptions, doubled side effects under StrictMode, values frozen in a long-lived callback, and dependency arrays that either loop or read stale.

## Checklist (lead with the trap)

1. **Take-latest, not last-response-wins: guard every fetch-on-deps effect.** When a dependency (query, id, page) drives an async fetch, responses can arrive out of order — a slow request for the old value resolves *after* the new one and calls `setState` last, so stale data wins. Fix with a per-run `let ignore = false` set to `true` in cleanup and checked before `setState`, or an `AbortController` whose `signal` you pass to `fetch` and `abort()` in cleanup. The `ignore` flag only discards the result; `AbortController` actually cancels the request (it rejects with an `AbortError` you should swallow, not surface as a real error).
2. **Every setup that subscribes/opens/schedules needs a cleanup that undoes it.** `subscribe`->`unsubscribe`, `addEventListener`->`removeEventListener` (same function reference), `setInterval`/`setTimeout`->`clear*`, `connect`->`disconnect`. A missing return means the effect leaks and accumulates a new listener/interval on every re-run, and a late async resolution calls `setState` on an unmounted component. React 18 removed the "can't perform a state update on an unmounted component" warning, so this leak is now silent — the console will not flag it for you.
3. **StrictMode double-invoke is a stress test, not a bug — make setup idempotent, do not suppress it.** In dev, React 18/19 runs an extra setup->cleanup->setup cycle to surface missing cleanup. If that produces two analytics events, two sockets, or a doubled subscription, the setup is not idempotent; fix the cleanup so setup->cleanup->setup is indistinguishable from a single setup. Blocking the second run with a `useRef` guard hides the bug — the real remount on navigate-away-and-back still leaks. A side effect that should not fire on display at all (a POST, a registration) belongs in an event handler, not an effect.
4. **Stale closure: a value read inside a long-lived callback is frozen at the render that created it.** An interval/timeout/subscription/event handler set up once (`[]`) captures that render's props and state forever, so it keeps reading the old value. In order of preference: a functional updater `setX(x => ...)` when you only need previous state; `useEffectEvent` to read the latest reactive value without restarting the timer (it is non-reactive, must be omitted from deps, and may only be called from inside an effect); or a ref you keep current (`ref.current`) on React without `useEffectEvent`. Adding the value to deps also works but restarts the timer on every change.
5. **Dependency array: omissions read stale; unstable references loop.** A reactive value the effect reads but omits from deps means the effect never re-runs when it changes (stale read). An object/array/function recreated every render, added to deps, makes the effect run every render (loop). Fixes: move the declaration inside the effect, wrap the reference in `useMemo`/`useCallback`, or use a functional updater. Do not silence `react-hooks/exhaustive-deps` with a disable comment — restructure instead; a suppressed dep is where these bugs hide.
6. **`[]`, no array, and `[a, b]` mean different things — confirm intent matches the effect.** No array runs after every render (usually a loop or an accident); `[]` runs once on mount plus cleanup on unmount (twice in StrictMode dev); `[a, b]` re-runs when `a` or `b` change by `Object.is`. An effect with `[]` that reads a prop or state is a stale closure waiting to happen — pick a different fix from item 4 rather than lying about the deps.

## Quick probes

Treat hits as leads; open each effect and trace setup -> cleanup -> dependency array.

```sh
rg -n 'useEffect\(|useLayoutEffect\(' src/ app/ 2>/dev/null            # each effect: does it fetch/subscribe/schedule, and does it return a cleanup?
rg -n 'await |\.then\(' src/ app/ 2>/dev/null | rg -i 'effect'         # async inside an effect -> is there a take-latest guard?
rg -n 'ignore|AbortController|\.abort\(|\bsignal\b' src/ app/ 2>/dev/null  # cancellation/ignore present on the fetch path?
rg -n 'addEventListener|subscribe\(|setInterval|setTimeout|new WebSocket|createObjectURL' src/ app/ 2>/dev/null  # setup -> matching teardown in the return?
rg -n 'eslint-disable.*exhaustive-deps' src/ app/ 2>/dev/null          # suppressed dependency checks -> likely stale read or hidden bug
```

Route the mechanical "is every reactive dependency listed" check to the `react-hooks/exhaustive-deps` ESLint rule; reserve human review for whether the effect should exist at all and whether its cleanup truly mirrors setup.

## Boundary with sibling skills

- This skill: the bare `useEffect`/`useLayoutEffect` and raw async primitives (`fetch`/Promise, `setInterval`/`setTimeout`, `addEventListener`, hand-rolled `subscribe`) — take-latest guarding, cleanup mirroring setup, StrictMode idempotency, stale closures, and dependency arrays.
- **frontend-data-fetching-cache-contracts** — when a data library (TanStack Query, SWR, RTK Query, Apollo) owns the fetch: its query cancellation, dedupe, staleness, and refetch are that layer's contract. If you are hand-writing `useEffect(() => { fetch(...) })`, you are here; if a `useQuery`/`useSWR` hook owns it, you are there.
- **optimistic-update-rollback-contracts** — races in the apply -> confirm -> rollback -> reconcile of a *mutation* (a failed write that never rolls back, a temp id never swapped). A read-side fetch race is here; a write-side reconciliation race is there.
- **realtime-transport-contracts** — the subscribe/unsubscribe *lifecycle and recovery* of a socket/SSE connection (reconnect backoff, resume cursor, heartbeat). A one-off listener/subscription cleanup inside an effect is here; connection-drop resilience is there.

## PR-worthiness gate

File a finding only when a user-visible or resource contract is actually broken:

- **Missing take-latest**: a deps-driven fetch with no ignore/abort where responses can realistically land out of order (search-as-you-type, tab/route switches) and stale data can win.
- **Missing/mismatched cleanup**: a subscription/listener/interval/socket opened with no return, or a cleanup that does not undo the setup — an accumulating leak or a setState after unmount.
- **Non-idempotent setup exposed by StrictMode**: a real duplicated side effect (two sockets, doubled analytics/POST), not merely "it runs twice in dev."
- **Stale closure with impact**: a long-lived callback reading a value that visibly goes stale (a timer showing the mount-time count, a handler using an old prop).
- **Dependency bug with impact**: an omission causing a stale read, or an unstable reference causing an actual re-render loop.

Reject weak findings:

- An effect that already pairs setup with a mirroring cleanup and a take-latest guard — that is the correct pattern, not a defect.
- "Runs twice in dev" with no observable duplicated effect — StrictMode working as intended.
- A data-library hook (`useQuery`/`useSWR`) — cancellation and dedupe are the library's job; route to the data-fetching skill.
- A lint-only `exhaustive-deps` nit with no resulting stale read or loop — let the linter own it rather than filing a review finding.
- An effect with `[]` that genuinely reads nothing reactive — not a stale closure.

Minimal useful PR: one failing test — fire two dependency changes, resolve the *first* response last, and assert the newer result wins (or that abort fired); or mount then unmount and assert the subscription/interval was torn down with no setState after unmount.

## Output shape

Return compact findings:

- **Contract**: take-latest / cleanup-mirrors-setup / StrictMode-idempotent / stale-closure / dependency-array.
- **Evidence**: file/line and the effect's setup, its cleanup (or the missing return), and its dependency array.
- **Symptom**: stale response wins, leak / setState after unmount, doubled side effect, frozen captured value, or re-run loop.
- **Fix**: smallest change — add an ignore/abort guard, add or repair the cleanup, move a POST into an event handler, use `useEffectEvent`/ref/updater, or correct the deps.
- **Verification**: unit/integration test driving the out-of-order race or the mount/unmount teardown.

## Sources

- React — Synchronizing with Effects (the race-condition `ignore`-flag cleanup; "fetch needs either cancel or ignore"; StrictMode dev double-fetch is harmless): <https://react.dev/learn/synchronizing-with-effects>
- React — `<StrictMode>` (dev-only extra setup+cleanup cycle to find missing cleanup; the `useRef`-to-block-the-second-run anti-pattern): <https://react.dev/reference/react/StrictMode>
- React — `useEffect` reference (cleanup, subscribe/unsubscribe, dependency semantics, `Object.is` comparison): <https://react.dev/reference/react/useEffect>
- React — Separating Events from Effects (`useEffectEvent` to read the latest reactive value from an interval/subscription without restarting it; non-reactive, omit from deps): <https://react.dev/learn/separating-events-from-effects>
- React — Removing Effect Dependencies (functional updater, move the declaration inside, do not lie to the linter): <https://react.dev/learn/removing-effect-dependencies>
- React — Lifecycle of Reactive Effects (each effect captures the values from its render; effects synchronize, they do not "run once"): <https://react.dev/learn/lifecycle-of-reactive-effects>
- React — `react-hooks/exhaustive-deps` ESLint rule (the authoritative mechanical dependency check; suppress by restructuring, not disabling): <https://react.dev/reference/eslint-plugin-react-hooks/lints/exhaustive-deps>
- React — You Might Not Need an Effect (effect-based fetching carries race/waterfall boilerplate; prefer a framework/cache; not every side effect needs an effect): <https://react.dev/learn/you-might-not-need-an-effect>
- MDN — AbortController (`abort()` cancels the fetch and rejects with an `AbortError` DOMException; pass `signal` to the request): <https://developer.mozilla.org/en-US/docs/Web/API/AbortController>
- MDN — AbortSignal (the signal object that communicates cancellation to an async operation): <https://developer.mozilla.org/en-US/docs/Web/API/AbortSignal>
