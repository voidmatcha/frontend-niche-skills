# Design — `ssr-hydration-mismatch` skill

Status: approved 2026-06-14. Collection skill #9.

## Purpose

The bug class where server-rendered HTML and the client's first render diverge. When they
do, the framework discards the server output for the affected tree and re-renders on the
client ("Hydration failed" / "text content did not match"), costing SEO, performance, and
visible flashes. Many triggers (timezone, locale, `Date.now()`, `typeof window`) never fire
on a UTC/English/same-machine dev setup — the collection's thesis.

Scope: **render determinism + containment of the re-render blast radius.** Not router
readiness (that is `deeplink-hydration`).

## Conventions

Inherits the collection's: compact `SKILL.md` (trap-first checklist + boundary + sources)
plus `references/`; strict-YAML frontmatter; every claim verified against an official source;
cross-references mark boundaries.

## Frontmatter

- `name: ssr-hydration-mismatch`
- `description`: "Use when server-rendered HTML and the client's first render diverge —
  React/Next "Hydration failed" / "text content did not match", a tree silently re-rendering
  on the client, or render output that depends on `Date.now()` / `Math.random()` /
  `new Date()` / timezone / `typeof window` / locale. Determinism + blast-radius scope; for
  first-render router/query-param readiness see deeplink-hydration; for the timezone/`Date`
  trigger specifically see datetime-correctness."

## `SKILL.md` — trap-first checklist (7 items)

1. Render must be **deterministic**: no `Date.now()` / `Math.random()` / `new Date()` /
   locale-or-timezone formatting / `typeof window` branching during render
   (→ datetime-correctness, deeplink-hydration).
2. Client-only values belong **after mount** (`useEffect` two-pass) or via
   `useSyncExternalStore`; the first client render must match the server's.
3. Invalid HTML nesting (`<div>` inside `<p>`, raw text directly in `<table>`) is repaired by
   the browser → guaranteed mismatch. Keep markup valid.
4. `suppressHydrationWarning` suppresses **one level only** (the element's own text/attrs, not
   descendants) — for genuinely unavoidable cases (a timestamp), not a blanket silencer.
5. A React 18+ mismatch is a **recoverable error**: in production it's silently recovered by
   re-rendering on the client, so it won't surface unless you watch logs / `onRecoverableError`.
6. **Bound the blast radius**: wrap unavoidable client-only regions in `Suspense` or a
   no-SSR dynamic import so a mismatch re-renders that island, not the whole tree.
7. Framework notes: React/Next is the worked example (error text + recovery model); Vue/Nuxt
   (`<ClientOnly>`), Svelte/SvelteKit, and Astro (`client:only`) get brief equivalents.

## `references/`

- `triggers-and-containment.md` — the trigger taxonomy (non-determinism, browser-only APIs in
  render, invalid nesting), the fixes (two-pass `useEffect`, `useSyncExternalStore`, no-SSR
  dynamic import), and containment/diagnosis (Suspense blast radius, `suppressHydrationWarning`
  limits, the React 18 recoverable-error model, how to find the diverging node).
  *(May split into triggers / containment if it grows.)*

## Boundaries / cross-references

- `deeplink-hydration` — router/query-param readiness on first render (e.g. App Router
  `useSearchParams` + Suspense). This skill owns server-vs-client DOM divergence and bounding
  the re-render. Add a reverse pointer.
- `datetime-correctness` — zone/locale-dependent text is one trigger; the fix (stable
  serialized instant, fixed render zone) lives there. Cross-reference both ways.

## Sources (verify against during build)

Next.js `react-hydration-error` guide; react.dev hydration-mismatch + `hydrateRoot`
(`onRecoverableError`) + `Suspense`; React 18 server-errors RFC (recoverable errors);
`suppressHydrationWarning` docs; Vue SSR hydration-mismatch + `<ClientOnly>`/Nuxt; Svelte/
SvelteKit + Astro `client:only` for the framework notes.

## Build checklist (implementation plan)

1. `skills/ssr-hydration-mismatch/SKILL.md`.
2. `skills/ssr-hydration-mismatch/references/triggers-and-containment.md`.
3. Web-verification workflow over every non-trivial claim (React/Next/Vue official docs);
   apply confirmed corrections.
4. Register: plugin.json skills[] + description; marketplace.json description + keywords;
   codex plugin.json description/longDescription + keywords + defaultPrompt; README table +
   references prose; CHANGELOG [Unreleased] Added entry. (Manifest version stays 0.4.0 until
   the maintainer cuts a release.)
5. Add reverse cross-refs in deeplink-hydration and datetime-correctness if low-risk.
6. Verify (JSON, links, frontmatter) and commit.
