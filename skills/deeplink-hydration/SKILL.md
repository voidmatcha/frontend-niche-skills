---
name: deeplink-hydration
description: "Use when deep links into an SPA/SSR page lose query params or land on the wrong screen — Next.js router.query empty on first render, redirects firing before router.isReady, login bounces dropping the intended destination, or deep-linkable pages lacking direct-navigation tests. Router/param-readiness scope; for server/client DOM divergence (\"Hydration failed\" / \"text content did not match\") see ssr-hydration-mismatch."
---

# Deep-link hydration survival

A deep link is a contract: the URL alone must reconstruct the screen. SPAs break this
contract during the window between document load and router hydration, when the
router's state lags the real URL. If this page renders inside a native WebView, see
`webview-bridge-pages`; this skill owns plain-SPA router/param readiness only.

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
   this means `router.isReady` in client-side `useEffect`. Vue Router has
   `router.isReady()`. React Router does **not** have an equivalent router-ready
   flag; use `useLocation()` / `useParams()` / loader data from the current route,
   and treat deferred loader/network data as data readiness rather than param
   hydration. Next.js **App Router** has no `router.isReady` flag —
   `useSearchParams()` is synchronous in client components, but reading it forces
   the subtree up to the nearest `Suspense` boundary into client rendering, so the
   equivalent discipline is wrapping the param-reading component in `Suspense`
   (render a skeleton as its fallback). Either way: never redirect on "missing"
   params before they're known.
2. **`window.location` is the client-side source of truth when the router lags.**
   If a decision can't wait for hydration (e.g. choosing the initial screen), read
   `window.location.pathname` / `.search` directly and treat router state as
   eventually consistent. In a pure CSR SPA you may read `window.location` on first
   render; under SSR defer this read until after mount — the `typeof window` guard
   that gates it is itself the hydration-mismatch trigger, so see
   `ssr-hydration-mismatch`.
3. **Don't lose the URL across auth bounces — they're still deep links.** Login
   redirects must carry the intended destination (`returnTo`-style param or session
   storage) and restore it after authentication; a deep link that survives hydration
   but dies at the login wall is still a broken deep link. Keep auth-specific
   return-target validation in `frontend-auth-flow-contracts` (and open-redirect
   primitives in `frontend-security-baseline`).
4. **Every deep-linkable page gets a direct-navigation test**: e2e test that opens the
   full URL cold (fresh context, no in-app navigation) and asserts the
   reconstructed screen. In-app navigation tests never catch hydration loss.
   Client-side redirects right after load can race the assertion — wait for the
   final URL, not the first response.
5. Normalize parsing in one function per page (`string | string[] | undefined` for
   repeated params), with explicit fallbacks — same discipline as any URL-driven
   screen.

## Smells that predict deep-link loss

- `useEffect(() => { if (!router.query.id) router.replace('/') }, [])` — fires before
  hydration fills `query`; add `router.isReady` to the condition and deps.
- Param parsing scattered across components — one of them will forget the
  not-ready state.
- Deep-link bugs that "can't be reproduced" in dev navigation but appear from
  notification/share links — that's the cold-start path nobody tests.

## PR-worthiness gate

Require a cold direct navigation, refresh, callback, or auth-bounce sequence
whose URL state is correct but whose screen or redirect becomes wrong before
router/loader readiness. Capture the URL and readiness state, then add the
smallest direct-navigation regression.

Reject weak findings: an in-app navigation that never crosses the cold path, a
missing parameter that is genuinely absent from the URL, a server/client DOM
divergence owned by `ssr-hydration-mismatch`, or an auth open-redirect policy
owned by `frontend-auth-flow-contracts` and `frontend-security-baseline`.

## Output shape

Report the entry URL, cold-start and readiness sequence, first wrong decision,
router/framework evidence, smallest gating or URL-preservation fix, and the
direct-navigation test that confirms the final screen and URL.

## Sources

- Next.js Pages Router `useRouter` docs (`query`, `isReady`): <https://nextjs.org/docs/pages/api-reference/functions/use-router>
- Next.js Automatic Static Optimization docs (empty `query` during prerender, populated after hydration): <https://nextjs.org/docs/pages/building-your-application/rendering/automatic-static-optimization>
- Vue Router API reference (`router.isReady()`; the typedoc interface pages were retired): <https://router.vuejs.org/api/>
- React Router `useLocation`: <https://reactrouter.com/api/hooks/useLocation>
- React Router `useParams`: <https://reactrouter.com/api/hooks/useParams>
- React Router data routers/loaders: <https://reactrouter.com/start/data/route-object>
- MDN `window.location`: <https://developer.mozilla.org/en-US/docs/Web/API/Window/location>
