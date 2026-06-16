---
name: deeplink-hydration
description: "Use when deep links into an SPA/SSR page lose query params or land on the wrong screen — Next.js router.query empty on first render, redirects firing before router.isReady, login bounces dropping the intended destination, or deep-linkable pages lacking direct-navigation tests. Router/param-readiness scope; for server/client DOM divergence (\"Hydration failed\" / \"text content did not match\") see ssr-hydration-mismatch."
---

# Deep-link hydration survival

A deep link is a contract: the URL alone must reconstruct the screen. SPAs break this
contract during the window between document load and router hydration, when the
router's state lags the real URL.

## The failure mode

- **Next.js pages router**: statically optimized pages render first with an **empty
  `router.query`** — it's only populated after hydration triggers an update (Next.js
  docs: Automatic Static Optimization). `router.isReady` is the flag, usable only
  client-side (`useEffect`).
- Any logic that runs on first render — redirects, fallbacks, analytics, "param
  missing → go home" guards — sees the empty state and acts on it. The user followed
  a valid deep link and still lands on the default screen.

## Rules

1. **Gate param-dependent logic on router readiness.** In Next.js **Pages Router**,
   that means `router.isReady` in a client-side `useEffect`; React Router and Vue
   Router (`router.isReady()`) expose equivalent "params hydrated/parsed" signals.
   Next.js **App Router** has no such flag — `useSearchParams()` is synchronous in
   client components, but reading it forces the subtree up to the nearest `Suspense`
   boundary into client rendering, so the equivalent discipline is wrapping the
   param-reading component in `Suspense` (render a skeleton as its fallback). Either
   way: never redirect on "missing" params before they're known.
2. **`window.location` is the client-side source of truth when the router lags.**
   If a decision can't wait for hydration (e.g. choosing the initial screen), read
   `window.location.pathname` / `.search` directly on first client render and treat
   router state as eventually consistent. (Guard for SSR: `typeof window`.)
3. **Don't lose the URL across auth bounces.** Login redirects must carry the intended
   destination (`returnTo`-style param or session storage) and restore it after
   authentication — a deep link that survives hydration but dies at the login wall is
   still a broken deep link.
4. **Auth bounces are still deep links.** Preserve the intended destination,
   but keep auth-specific return-target validation in `frontend-auth-flow-contracts`
   (and open-redirect primitives in `frontend-security-baseline`).
5. **Every deep-linkable page gets a direct-navigation test**: e2e test that opens the
   full URL cold (fresh context, no in-app navigation) and asserts the
   reconstructed screen. In-app navigation tests never catch hydration loss.
   Client-side redirects right after load can race the assertion — wait for the
   final URL, not the first response.
6. Normalize parsing in one function per page (`string | string[] | undefined` for
   repeated params), with explicit fallbacks — same discipline as any URL-driven
   screen.

## Smells that predict deep-link loss

- `useEffect(() => { if (!router.query.id) router.replace('/') }, [])` — fires before
  hydration fills `query`; add `router.isReady` to the condition and deps.
- Param parsing scattered across components — one of them will forget the
  not-ready state.
- Deep-link bugs that "can't be reproduced" in dev navigation but appear from
  notification/share links — that's the cold-start path nobody tests.

## Sources

- Next.js Pages Router docs: Automatic Static Optimization (empty `query` during
  prerender, populated after hydration), `useRouter` (`isReady`: client-side only,
  in `useEffect`)
- MDN: `window.location`
- See `frontend-auth-flow-contracts` for auth-specific return-target validation.
