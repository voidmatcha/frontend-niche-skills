---
name: view-transitions-contracts
description: "Use when a View Transitions API animation silently aborts or captures the wrong state: duplicate view-transition-name values, an unpainted Suspense/streaming/image state, missing reduced-motion handling, a React update outside startTransition, interruption that skips animation but still applies the DOM change, stale names, top-layer paint conflicts, or a cross-document navigation that is cross-origin or not opted in on both pages. Covers review and PR-worthiness. Use overlay-focus-scroll-contracts for overlay focus/stacking, ssr-hydration-mismatch for first-render determinism, and a11y-contract-testing for reduced-motion regression coverage."
---

# View transitions contracts

A view transition is a visual enhancement wrapped around a DOM change: the DOM update always happens, so a broken transition fails silently — no console error, just no animation (or a frozen frame). This lens spots the silent-abort, stale-snapshot, and reduced-motion bugs in review; it is not a guide for building transitions.

## Checklist (lead with the trap)

1. **Duplicate `view-transition-name` on the same frame silently aborts the whole transition.** If two rendered elements carry the same name at the same time, `ViewTransition.ready` rejects and the animation is skipped — but the DOM still updates, so it reads as "the animation randomly doesn't fire." This is the classic list bug: reusing one static name across items. Suffix each with a unique id/key (or use `view-transition-name: match-element` where supported).
2. **A frozen old frame means a slow update callback; a wrong new state means the committed DOM was not the intended view.** The old state is a static snapshot; the new state is a live representation of the DOM after the update. Rendering is paused while the update callback is pending, so a slow callback freezes the old frame on screen. If the committed DOM is still a Suspense fallback or a not-yet-streamed server component, the transition animates to the fallback. Hoist the matched (shared) element above the Suspense boundary so it exists on both sides. React `<ViewTransition>` waits for Suspense data, `precedence` stylesheets, new fonts (up to 500 ms), and wrapped images before animating; it does not wait for data fetched outside Suspense (for example in an Effect). For the vanilla API, await data readiness or image `decode()` inside the update callback, and keep that wait short because rendering is paused meanwhile.
3. **`prefers-reduced-motion` is NOT honored automatically.** The UA default cross-fade plus the group transform still run. Needs an explicit reduced-motion block on the pseudos, e.g. `@media (prefers-reduced-motion: reduce) { ::view-transition-group(*), ::view-transition-old(*), ::view-transition-new(*) { animation: none !important; } }` (or gate `startViewTransition` in JS / pass `skipTransition`). Note reduced does not mean none — `animation: none` is an instant cut; a very short cross-fade is often the gentler choice. Missing this is an accessibility defect, not a nicety.
4. **React: the state update must be inside a Transition, and `flushSync` opts you out.** With `<ViewTransition>`, only updates wrapped in a Transition (`startTransition`), a `<Suspense>` reveal, or `useDeferredValue` activate it — plain `setState`, `useSyncExternalStore`, and updates after an `await`/`setTimeout` are not marked as Transitions and will not animate; a stray `flushSync` mid-flow makes React skip the transition entirely. The vanilla API is the opposite: you wrap the `setState` in `flushSync` inside the `startViewTransition` callback so the DOM applies synchronously before the snapshot. Pick one pattern; do not mix them.
5. **Only one document-scoped transition runs at a time; a new one interrupts and skips the current.** Element-scoped transitions on non-overlapping subtrees can run concurrently (item 7). `skipTransition()` and interruption cancel only the animation — `updateCallback` and the DOM change still run. "It skipped" never means "the state did not update." Rapid navigations fast-forward to the end state (a visual jump); chain update callbacks into one `startViewTransition` if smoothness matters.
6. **Leftover `view-transition-name` causes ghost animations.** A dynamically-set name not cleared after the snapshot persists (including in the bfcache on back/forward), so an unrelated element morphs later, or a duplicate-name abort appears on the next `pagereveal`. Remove names once the snapshot has been taken.
7. **Fixed chrome and top-layer content can paint behind the overlay.** A document-scoped transition paints the `::view-transition` layer above everything (including the top layer), so `position: fixed` headers and popovers get baked into the flat `root` snapshot and slide/disappear. Give them their own `view-transition-name` plus a high `::view-transition-group()` z-index, or, where supported, use an element-scoped transition. Naming works for a single element but is cumbersome to maintain (Chrome's element-scoped guide): each named group is ordered only against `root` and the other named groups, so raising a fixed header's group also lifts it above an unnamed `showModal()` dialog baked into `root`. When a top-layer modal and fixed chrome both change, prefer an element-scoped transition on the changing subtree over more name/z-index patches, and route the modal's own top-layer/backdrop/stacking contract to overlay-focus-scroll-contracts.
8. **Cross-document transitions need a same-origin navigation and an opt-in on both pages.** A cross-document view transition only runs for a same-origin navigation (no cross-origin redirects in between) where both pages opt in with `@view-transition { navigation: auto; }`; a cross-origin or same-site-but-cross-origin navigation gets no transition. Chrome's cross-document doc notes that Chrome 126 limited these transitions to main-frame navigations, with iframe navigations planned for a future release, so check that doc's current note before promising a transition inside an iframe.

## Quick probes

Use these as leads, then read the transition-to-snapshot path:

```sh
rg -n 'startViewTransition|view-transition-name|viewTransitionName|::view-transition|@view-transition' src/ app/ 2>/dev/null
rg -n 'ViewTransition|startTransition|flushSync' src/ app/ 2>/dev/null
rg -n 'prefers-reduced-motion' src/ app/ 2>/dev/null   # absence anywhere near view-transition CSS is the a11y smell
rg -n "view-transition-name:\s*['\"a-z-]+" src/ app/ 2>/dev/null | rg -v '\$\{|\+ *id|`'   # static names that may repeat across list items
```

Then confirm in a Chromium browser: the DevTools Animations panel shows the `::view-transition` pseudo tree; log `transition.ready.catch(...)` to catch a duplicate-name rejection; toggle the OS reduced-motion setting and re-run.

## Boundary with sibling skills

- **This skill owns only the review / PR-worthiness lens** — spotting silent-abort, stale-snapshot, reduced-motion, ghost-name, and layering bugs. For *implementing* view transitions (wiring the animation, choosing names, route integration), defer to the framework skill: React `<ViewTransition>` (stable since React 19.3), the Vercel `next-view-transitions` library, or the Next.js `experimental.viewTransition` config. Do not turn a review into a re-implementation guide.
- **overlay-focus-scroll-contracts** — when the real issue is top-layer/focus/stacking of a modal, popover, or drawer (the transition overlay is only a symptom of the stacking contract).
- **ssr-hydration-mismatch** — when the stale snapshot is really a first-render / streaming / Suspense determinism problem, or names diverge between server and client render.
- **browser-page-lifecycle-bfcache-contracts** — when the real issue is the restored document's resume path after Back/Forward, not the names it carried back.
- **a11y-contract-testing** — to lock the reduced-motion behavior (and focus/announcement) as a durable test contract rather than a one-off manual check.

## PR-worthiness gate

Count a finding only when all hold:

1. A user-visible transition exists (`startViewTransition` / `<ViewTransition>` / `@view-transition`).
2. The animation silently aborts, freezes, ignores reduced-motion, or ghosts — not merely "could be smoother."
3. The current code lacks the guard: unique name, decode/data readiness, a reduced-motion block, correct Transition wrapping, name cleanup, or overlay z-index.
4. The fix is narrow: one id-suffixed name, one reduced-motion block, one `startTransition` wrap, one hoist above Suspense, or one name cleanup.

Reject weak findings: a transition that simply does not animate in an unsupported browser is graceful degradation, not a bug. A single static `view-transition-name` that is never duplicated at runtime is fine. `skipTransition`/interruption dropping an animation is by design as long as the DOM change lands.

## Output shape

- **Contract**: unique-name / snapshot-readiness / reduced-motion / transition-wrapping / name-cleanup / overlay-z-index / cross-document-opt-in.
- **Evidence**: file:line plus the elements sharing a name, the Suspense/await gap, or the missing media block.
- **Symptom**: silent abort, frozen old frame, unhonored reduced-motion, ghost morph, chrome behind overlay, or no transition on a cross-origin or un-opted-in navigation.
- **Fix**: smallest change — id-suffixed name, decode await, `::view-transition-*` reduced-motion block, `startTransition` wrap, or name removal.
- **Verification**: a reduced-motion test, a `ready`-rejects assertion for the duplicate-name case, or a browser check of the `::view-transition` tree.

## Sources

- MDN — Using the View Transition API: https://developer.mozilla.org/en-US/docs/Web/API/View_Transition_API/Using
- MDN — view-transition-name (uniqueness, match-element): https://developer.mozilla.org/en-US/docs/Web/CSS/view-transition-name
- MDN — ViewTransition.skipTransition(): https://developer.mozilla.org/en-US/docs/Web/API/ViewTransition/skipTransition
- W3C — CSS View Transitions Module Level 1 (transition as an enhancement; abort on duplicate name): https://www.w3.org/TR/css-view-transitions-1/
- Chrome for Developers — Same-document view transitions (ready/finished, reduced-motion): https://developer.chrome.com/docs/web-platform/view-transitions/same-document
- Chrome for Developers — Misconceptions about view transitions (reduced-motion is not automatic; "Chrome is limited to running one view transition per document at the same time"; the old snapshot is a screenshot, the new one "a live representation of the node"): https://developer.chrome.com/blog/view-transitions-misconceptions
- W3C — CSS View Transitions Module Level 1, View Transition Lifecycle ("Rendering paused" while the update callback runs, then the new state is captured): https://www.w3.org/TR/css-view-transitions-1/#lifecycle
- Chrome for Developers — Element-scoped view transitions (z-index / top-layer fix; "multiple element-scoped view transitions can run simultaneously if they have a different scope"): https://developer.chrome.com/docs/css-ui/view-transitions/element-scoped-view-transitions
- Chrome for Developers — Cross-document view transitions (same-origin navigation, both pages opt in, Chrome 126 main-frame note, bfcache name cleanup "Remove view-transition-names after snapshots have been taken // (this to deal with BFCache)"; checked 2026-09-25): https://developer.chrome.com/docs/web-platform/view-transitions/cross-document
- React — `<ViewTransition>` (Transition requirement, flushSync opt-out, waits for data, precedence CSS, fonts up to 500 ms and images; Suspense reveals): https://react.dev/reference/react/ViewTransition
- React — React 19.3 release post (`<ViewTransition>` "stable in React 19.3"): https://react.dev/blog/2026/09/09/react-19-3
- React — `useSyncExternalStore` ("mutations to the external store cannot be marked as non-blocking Transition updates"): https://react.dev/reference/react/useSyncExternalStore
- React — `<Suspense>` (does not detect data fetched inside an Effect or event handler): https://react.dev/reference/react/Suspense
- React — startTransition (updates after an await or in setTimeout are not marked as Transitions): https://react.dev/reference/react/startTransition
- Next.js — View transitions guide (experimental.viewTransition config, fixed-header z-index, next-view-transitions): https://nextjs.org/docs/app/guides/view-transitions
- next-view-transitions — Vercel community library for View Transitions in the Next.js App Router (the implement-side skill to defer to): https://github.com/shuding/next-view-transitions
- caniuse — View Transitions API (consult current target-browser support and pair it with feature detection): https://caniuse.com/view-transitions
