# Triggers & containment

## Contents

- [What actually diverges (the trigger taxonomy)](#what-actually-diverges-the-trigger-taxonomy)
- [The fixes](#the-fixes)
- [Containment & the blast radius](#containment--the-blast-radius)
- [Diagnosing the diverging node](#diagnosing-the-diverging-node)
- [Other frameworks (same principle, different escape hatch)](#other-frameworks-same-principle-different-escape-hatch)
- [Sources](#sources)

Hydration is the client attaching to server HTML in place. React's rule is strict: *"React
expects that the rendered content is identical between the server and the client."* When it
isn't, you get a hydration error, the server markup for that tree is discarded, and the
client re-renders from scratch.

## What actually diverges (the trigger taxonomy)

React's own docs list the common causes. They all reduce to "the first client render computed
something different from the server."

- **Non-deterministic values in render** — `Date.now()`, `Math.random()`, `new Date()`
  rendered to text, or `crypto.randomUUID()` rendered into an **attribute** (`id`, `htmlFor`,
  `aria-labelledby`/`aria-describedby`, etc.). The server computes one value, the client
  another, so the serialized attribute diverges. (A random *key* is a separate bug: keys are
  never serialized to HTML, so a per-render key causes reconciliation churn, not a hydration
  mismatch.) For SSR-safe deterministic ids, use React's `useId()` — it produces the same id on
  server and client.
- **Timezone / locale formatting** — `date.toLocaleString()`,
  `new Intl.DateTimeFormat().format()`, or number/currency formatting without a pinned
  `timeZone`/`locale`. The server's zone/locale differs from the user's. (Fix in
  **datetime-correctness**: serialize a stable instant; format in a fixed zone, or after
  mount.)
- **Server/client branching in render** — `typeof window !== "undefined"`,
  `if (isServer) ... else ...`, or reading `window`/`document`/`localStorage`/`navigator`
  /`matchMedia` directly in the render body. The branch resolves differently on each side.
- **External, changing data without a snapshot** — reading a mutable browser store during
  render instead of through `useSyncExternalStore` (which has a dedicated server snapshot).
- **Invalid HTML nesting** — `<div>` or `<p>` inside `<p>`, `<a>` inside `<a>`, or text/`<div>`
  placed directly inside `<table>`/`<tbody>`/`<tr>`. The HTML parser *repairs* invalid
  nesting (e.g. closes the `<p>` early), so the parsed client DOM no longer matches the string
  the server streamed — a mismatch you didn't write explicitly.
- **Wrong/extra/missing attributes or whitespace-sensitive text** that one side trims.

## The fixes

- **Two-pass render for client-only output.** Render the server-safe version first, then
  update in `useEffect` (which runs only on the client, after hydration):

  ```jsx
  function LocalTime({ iso }) {
    const [text, setText] = useState(null);          // matches server: nothing
    useEffect(() => {
      setText(new Date(iso).toLocaleTimeString());   // client-only, after mount
    }, [iso]);
    return <time dateTime={iso}>{text ?? "…"}</time>;
  }
  ```

- **`useSyncExternalStore` for external/browser state.** It takes a client `getSnapshot` and a
  separate `getServerSnapshot`, so the server render is deterministic and the client subscribes
  after hydration — the supported way to read viewport size, media queries, online status, etc.
- **No-SSR dynamic import for irreducibly client-only widgets.** `next/dynamic(() => import(...),
  { ssr: false })` (or `React.lazy` behind a mounted flag) skips server rendering for that
  component, so there's nothing to mismatch.
- **`suppressHydrationWarning` for unavoidable, known-divergent leaves only.** React applies it
  **one level deep** — it suppresses the warning for that element's own text and attributes,
  not for its children. Use it on a single timestamp node, not a subtree. It silences the
  warning; it does not make the values agree, so the rendered text may still differ for a
  frame.

## Containment & the blast radius

- A mismatch is not local by default. In React 18, an error during hydration makes React
  **discard the server-rendered tree up to the nearest `<Suspense>` boundary and re-render it
  on the client** — without any boundary, that can be the whole document. Wrapping a risky,
  client-dependent region in its own `<Suspense>` (or rendering it no-SSR) limits the
  re-render to that island so the rest stays hydrated.
- **The prod signal is easy to miss.** React 18 treats a hydration mismatch as a *recoverable error*:
  it logs in **both** dev and production (via `onRecoverableError`, with dev additionally
  surfacing the server-vs-client diff) and then succeeds by client rendering. So a mismatch
  can ship unnoticed — wire `hydrateRoot(container, <App/>, {
  onRecoverableError })` (or your framework's hook) into monitoring instead of trusting that a
  broken hydration would have been obvious.

## Diagnosing the diverging node

- In development the error names the element and shows a server-vs-client diff — start there;
  the offending value is usually a clock, a random id, or a `window` read nearby.
- Reproduce with JS disabled (or "view source") to see the raw server HTML, then compare to
  the hydrated DOM. Diffs in text, attribute order that matters, or repaired nesting point to
  the cause.
- Toggle the suspect subtree to no-SSR; if the warning disappears, the trigger is inside it.

## Other frameworks (same principle, different escape hatch)

- **Vue / Nuxt** — Vue warns "Hydration node mismatch" / "Hydration text mismatch" in dev and
  falls back to client render for that subtree. Wrap client-only UI in Nuxt's `<ClientOnly>`
  (or guard browser APIs to `onMounted`).
- **Svelte / SvelteKit** — same determinism rule under SvelteKit SSR; keep browser-only reads
  in `onMount` / behind the `browser` guard from `$app/environment`.
- **Astro** — server-render by default; mark genuinely client-only components `client:only`
  (with the framework name) so Astro skips SSR for them entirely.

## Sources

- React — [Hydration mismatch errors](https://react.dev/link/hydration-mismatch) and
  [`hydrateRoot`](https://react.dev/reference/react-dom/client/hydrateRoot) (the identical
  server/client expectation; common-causes list; `onRecoverableError`;
  `suppressHydrationWarning` is one level deep)
- React — [`<Suspense>`](https://react.dev/reference/react/Suspense) (boundary behavior during
  hydration)
- React 18 RFC — [server-errors in React 18](https://github.com/reactjs/rfcs/blob/main/text/0215-server-errors-in-react-18.md)
  (hydration mismatch as a recoverable error; client-render fallback)
- Next.js — [Hydration error guide](https://nextjs.org/docs/messages/react-hydration-error)
  and [`next/dynamic` `{ ssr: false }`](https://nextjs.org/docs/app/guides/lazy-loading)
- React — [`useSyncExternalStore`](https://react.dev/reference/react/useSyncExternalStore)
  (`getServerSnapshot` for SSR-safe external state)
- Vue — [SSR Hydration Mismatch](https://vuejs.org/guide/scaling-up/ssr.html#hydration-mismatch)
  ; Nuxt [`<ClientOnly>`](https://nuxt.com/docs/api/components/client-only)
- Astro — [`client:only` directive](https://docs.astro.build/en/reference/directives-reference/#clientonly)
