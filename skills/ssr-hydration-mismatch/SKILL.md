---
name: ssr-hydration-mismatch
description: "Use when server-rendered HTML and the client's first render diverge — React/Next \"Hydration failed\" or \"text content did not match\", a tree silently re-rendering on the client, or render output that depends on `Date.now()` / `Math.random()` / `new Date()` / timezone / `typeof window` / locale. Determinism + re-render blast-radius scope; for first-render router/query-param readiness see deeplink-hydration; for the timezone/`Date` trigger specifically see datetime-correctness."
---

# SSR hydration mismatch

Server-side rendering only pays off if the client can **hydrate** the server's HTML — attach
event handlers to the existing DOM without rebuilding it. The moment the client's first
render disagrees with what the server sent, the framework throws out the server tree and
re-renders on the client, and you lose the SSR benefit you paid for (plus a visible flash and,
on React 18+, a recoverable error that is easy to miss in production — item 5). The triggers are almost
all forms of one thing: **the first render is not deterministic across the server/client
boundary** — it reads the clock, a random value, the timezone, the locale, or `window`.

For first-render **router/query-param readiness** (params empty until hydration), use
**deeplink-hydration**. Timezone/locale-dependent text is one trigger here; its fix
(serialize a stable instant, render in a fixed zone) lives in **datetime-correctness**.

## Checklist (lead with the trap; details in references/)

→ [triggers-and-containment](./references/triggers-and-containment.md)

1. **Render must be deterministic.** No `Date.now()`, `Math.random()`, `new Date()`,
   locale/timezone formatting, or `typeof window` branching *during render*.
2. **Client-only values go after mount** — in `useEffect` (two-pass: first render matches
   the server) or via `useSyncExternalStore` with a server snapshot, never inline in the
   first render.
3. **Keep HTML nesting valid.** `<div>`/`<p>` inside `<p>`, or raw text/`<div>` directly
   under `<table>`/`<tbody>`, gets repaired by the browser's parser, so the client DOM no
   longer matches the string the server emitted — a deterministic mismatch.
4. **`suppressHydrationWarning` is one level deep.** It silences the warning for a single
   element's own text/attributes (e.g. an unavoidable timestamp), not its descendants. It's a
   scalpel for known-divergent leaves, not a blanket fix.
5. **A React 18+ mismatch is a *recoverable* error.** React logs it in both dev and prod by
   default, but the prod log is a minified error with no server-vs-client diff, so it is easy
   to miss — wire `hydrateRoot`'s `onRecoverableError` into monitoring with source maps to turn
   it into an actionable signal, not just local dev. React 19 improved the dev-mode diff —
   one error showing the mismatched node instead of per-node warnings — but the prod log
   stays minified, so the wiring still matters.
6. **Bound the blast radius.** For genuinely client-only UI, isolate it behind `<Suspense>`
   or a no-SSR dynamic import (`next/dynamic` `{ ssr: false }`) so a mismatch re-renders that
   island instead of cascading the whole route.
7. **Framework-agnostic principle, framework-specific tools.** React/Next is the worked
   example; Vue/Nuxt (`<ClientOnly>`), Svelte/SvelteKit, and Astro (`client:only`) expose the
   same "render this only on the client" escape hatch — see the reference.

## PR-worthiness gate

Hydration findings are easy to overclaim. Count a case only when you can tie a nondeterministic
first render to an SSR path:

- Confirm the component/module participates in server render or initial HTML generation. If it is a
  no-SSR dynamic import or purely client-rendered route, downgrade to "determinism cleanup," not a
  hydration bug.
- Show the exact first-render value that can differ: time, random id, locale/timezone formatting,
  browser-only API branch, invalid HTML repair, or persisted client state before hydration.
- Prefer evidence from a hydration smoke test, React `onRecoverableError`, Next.js dev warning, or
  a server-vs-client render diff.

Reject weak findings:

- `Math.random()`/`Date.now()` inside event handlers, effects, request handlers, or server-only code
  that does not affect the client first render.
- Locale formatting after mount, behind `useEffect`, behind `dynamic(..., { ssr: false })`, or inside
  an explicitly client-only island.
- Stable ids generated once on the server and serialized to the client.

Minimal useful PR: make initial HTML deterministic, render a placeholder until mounted, pin an
explicit locale/timeZone for SSR text, or isolate the widget as no-SSR; add a test that fails on
recoverable hydration errors.

## Output shape

Report the SSR path, exact server/client first-render divergence, hydration or
recoverable-error evidence, blast radius, smallest determinism or containment
fix, and the test that fails on the mismatch without suppressing it.

## References

| File | Covers |
|------|--------|
| [triggers-and-containment](./references/triggers-and-containment.md) | Trigger taxonomy (non-determinism, browser-only APIs in render, invalid nesting), fixes (two-pass `useEffect`, `useSyncExternalStore`, no-SSR dynamic import), and containment/diagnosis (Suspense blast radius, `suppressHydrationWarning` limits, the recoverable-error model, finding the diverging node) |

Sources are listed in the reference file.
