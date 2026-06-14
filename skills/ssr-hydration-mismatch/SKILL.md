---
name: ssr-hydration-mismatch
description: "Use when server-rendered HTML and the client's first render diverge — React/Next \"Hydration failed\" or \"text content did not match\", a tree silently re-rendering on the client, or render output that depends on `Date.now()` / `Math.random()` / `new Date()` / timezone / `typeof window` / locale. Determinism + re-render blast-radius scope; for first-render router/query-param readiness see deeplink-hydration; for the timezone/`Date` trigger specifically see datetime-correctness."
---

# SSR hydration mismatch

Server-side rendering only pays off if the client can **hydrate** the server's HTML — attach
event handlers to the existing DOM without rebuilding it. The moment the client's first
render disagrees with what the server sent, the framework throws out the server tree and
re-renders on the client, and you lose the SSR benefit you paid for (plus a visible flash and,
on React 18+, an error that is *silently recovered in production*). The triggers are almost
all forms of one thing: **the first render is not deterministic across the server/client
boundary** — it reads the clock, a random value, the timezone, the locale, or `window`.

For first-render **router/query-param readiness** (params empty until hydration), use
**deeplink-hydration**. Timezone/locale-dependent text is one trigger here; its fix
(serialize a stable instant, render in a fixed zone) lives in **datetime-correctness**.

## Checklist (lead with the trap; details in references/)

→ [triggers-and-containment](./references/triggers-and-containment.md)

1. **Render must be deterministic.** No `Date.now()`, `Math.random()`, `new Date()`,
   locale/timezone formatting, or `if (typeof window !== "undefined")` branching *during
   render*. Same inputs → same output on server and client.
2. **Client-only values go after mount.** Read `window`, `localStorage`, media queries, etc.
   in `useEffect` (a two-pass render: first render matches the server, then update), or via
   `useSyncExternalStore` with a server snapshot — never inline in the first render.
3. **Keep HTML nesting valid.** `<div>`/`<p>` inside `<p>`, or raw text/`<div>` directly
   under `<table>`/`<tbody>`, gets repaired by the browser's parser, so the client DOM no
   longer matches the string the server emitted — a guaranteed mismatch.
4. **`suppressHydrationWarning` is one level deep.** It silences the warning for a single
   element's own text/attributes (e.g. an unavoidable timestamp), not its descendants. It's a
   scalpel for known-divergent leaves, not a blanket fix.
5. **A React 18+ mismatch is a *recoverable* error.** In production React recovers by
   re-rendering on the client, so nothing visibly breaks and the bug hides — surface it via
   `hydrateRoot`'s `onRecoverableError` / your error monitoring, not just local dev.
6. **Bound the blast radius.** For genuinely client-only UI, isolate it behind `<Suspense>`
   or a no-SSR dynamic import (`next/dynamic` `{ ssr: false }`) so a mismatch re-renders that
   island instead of cascading the whole route.
7. **Framework-agnostic principle, framework-specific tools.** React/Next is the worked
   example; Vue/Nuxt (`<ClientOnly>`), Svelte/SvelteKit, and Astro (`client:only`) expose the
   same "render this only on the client" escape hatch — see the reference.

## References

| File | Covers |
|------|--------|
| [triggers-and-containment](./references/triggers-and-containment.md) | Trigger taxonomy (non-determinism, browser-only APIs in render, invalid nesting), fixes (two-pass `useEffect`, `useSyncExternalStore`, no-SSR dynamic import), and containment/diagnosis (Suspense blast radius, `suppressHydrationWarning` limits, the recoverable-error model, finding the diverging node) |

Sources are listed in the reference file.
