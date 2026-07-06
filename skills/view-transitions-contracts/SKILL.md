---
name: view-transitions-contracts
description: "Use when reviewing or debugging a View Transitions API animation that misbehaves: a transition that silently aborts (ViewTransition.ready rejects) because two elements share a view-transition-name on the same frame — common on lists — a frozen or stale old snapshot because the incoming DOM was not painted when the snapshot was taken (Suspense fallback still loading, streamed server component, image not yet decoded), prefers-reduced-motion not honored (the default cross-fade/morph still animates), a React state update not wrapped in startTransition (or a stray flushSync) so no animation fires, an interrupted transition that skips the animation but still runs the callback and DOM change, leftover view-transition-name causing ghost animations, fixed chrome/top-layer painting behind the transition overlay, or iframe/cross-origin content that cannot be captured. Review/PR-worthiness scope; for top-layer/focus/stacking of overlays see overlay-focus-scroll-contracts, for Suspense/streaming/first-render determinism see ssr-hydration-mismatch, for locking the reduced-motion behavior as a test see a11y-contract-testing."
---

# View transitions contracts

A view transition is a visual enhancement wrapped around a DOM change: the DOM update always happens, so a broken transition fails silently — no console error, just no animation (or a frozen frame). This lens spots the silent-abort, stale-snapshot, and reduced-motion bugs in review; it is not a guide for building transitions.

## Checklist (lead with the trap)

1. **Duplicate `view-transition-name` on the same frame silently aborts the whole transition.** If two rendered elements carry the same name at the same time, `ViewTransition.ready` rejects and the animation is skipped — but the DOM still updates, so it reads as "the animation randomly doesn't fire." This is the classic list bug: reusing one static name across items. Suffix each with a unique id/key (or use `view-transition-name: match-element` where supported).
2. **A frozen or stale old snapshot means the incoming DOM was not painted when the snapshot was taken.** Snapshots are paint-based images, not live DOM. If the new view is still a Suspense fallback, a not-yet-streamed server component, or an image that has not decoded, the new snapshot captures the wrong/empty state and the old frame appears stuck. Hoist the matched (shared) element above the Suspense boundary so it exists on both sides; await image `decode()` / data readiness before `startViewTransition`. React `<ViewTransition>` waits for stylesheets and up to ~500ms for fonts, but not arbitrary data.
3. **`prefers-reduced-motion` is NOT honored automatically.** The UA default cross-fade plus the group transform still run. Needs an explicit reduced-motion block on the pseudos, e.g. `@media (prefers-reduced-motion: reduce) { ::view-transition-group(*), ::view-transition-old(*), ::view-transition-new(*) { animation: none !important; } }` (or gate `startViewTransition` in JS / pass `skipTransition`). Note reduced does not mean none — `animation: none` is an instant cut; a very short cross-fade is often the gentler choice. Missing this is an accessibility defect, not a nicety.
4. **React: the state update must be inside a Transition, and `flushSync` opts you out.** With `<ViewTransition>`, the mutation must run inside `startTransition` — plain `setState`, `useSyncExternalStore`, and updates after an `await`/`setTimeout` are not marked as Transitions and will not animate; a stray `flushSync` mid-flow makes React skip the transition entirely. The vanilla API is the opposite: you wrap the `setState` in `flushSync` inside the `startViewTransition` callback so the DOM applies synchronously before the snapshot. Pick one pattern; do not mix them.
5. **Only one transition runs at a time; a new one interrupts and skips the current.** `skipTransition()` and interruption cancel only the animation — `updateCallback` and the DOM change still run. "It skipped" never means "the state did not update." Rapid navigations fast-forward to the end state (a visual jump); chain update callbacks into one `startViewTransition` if smoothness matters.
6. **Leftover `view-transition-name` causes ghost animations.** A dynamically-set name not cleared after the snapshot persists (including in the bfcache on back/forward), so an unrelated element morphs later, or a duplicate-name abort appears on the next `pagereveal`. Remove names once the snapshot has been taken.
7. **Fixed chrome and top-layer content can paint behind the overlay.** A document-scoped transition paints the `::view-transition` layer above everything (including the top layer), so `position: fixed` headers and popovers get baked into the flat `root` snapshot and slide/disappear. Give them their own `view-transition-name` plus a high `::view-transition-group()` z-index, or use an element-scoped transition.
8. **iframe / cross-origin content cannot participate.** Transitions are same-origin only; cross-document transitions are main-frame + same-origin with a matching `@view-transition` opt-in, and iframe content is not snapshotted (it reloads when moved). Do not promise a shared-element morph across an iframe or cross-origin boundary.

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

- **This skill owns only the review / PR-worthiness lens** — spotting silent-abort, stale-snapshot, reduced-motion, ghost-name, and layering bugs. For *implementing* view transitions (wiring the animation, choosing names, route integration), defer to the framework skill: React's experimental `<ViewTransition>` (Canary/Experimental channels only, not stable React 19), the Vercel `next-view-transitions` library, or the Next.js `experimental.viewTransition` config. Do not turn a review into a re-implementation guide.
- **overlay-focus-scroll-contracts** — when the real issue is top-layer/focus/stacking of a modal, popover, or drawer (the transition overlay is only a symptom of the stacking contract).
- **ssr-hydration-mismatch** — when the stale snapshot is really a first-render / streaming / Suspense determinism problem, or names diverge between server and client render.
- **a11y-contract-testing** — to lock the reduced-motion behavior (and focus/announcement) as a durable test contract rather than a one-off manual check.

## PR-worthiness gate

Count a finding only when all hold:

1. A user-visible transition exists (`startViewTransition` / `<ViewTransition>` / `@view-transition`).
2. The animation silently aborts, freezes, ignores reduced-motion, or ghosts — not merely "could be smoother."
3. The current code lacks the guard: unique name, decode/data readiness, a reduced-motion block, correct Transition wrapping, name cleanup, or overlay z-index.
4. The fix is narrow: one id-suffixed name, one reduced-motion block, one `startTransition` wrap, one hoist above Suspense, or one name cleanup.

Do not over-file: a transition that simply does not animate in Firefox < 144 / Safari < 18 is graceful degradation, not a bug. A single static `view-transition-name` that is never duplicated at runtime is fine. `skipTransition`/interruption dropping an animation is by design as long as the DOM change lands.

## Output shape

- **Contract**: unique-name / snapshot-readiness / reduced-motion / transition-wrapping / name-cleanup / overlay-z-index / cross-origin.
- **Evidence**: file:line plus the elements sharing a name, the Suspense/await gap, or the missing media block.
- **Symptom**: silent abort, frozen old frame, unhonored reduced-motion, ghost morph, chrome behind overlay, or no-op across an iframe.
- **Fix**: smallest change — id-suffixed name, decode await, `::view-transition-*` reduced-motion block, `startTransition` wrap, or name removal.
- **Verification**: a reduced-motion test, a `ready`-rejects assertion for the duplicate-name case, or a browser check of the `::view-transition` tree.

## Sources

- MDN — Using the View Transition API: https://developer.mozilla.org/en-US/docs/Web/API/View_Transition_API/Using
- MDN — view-transition-name (uniqueness, match-element): https://developer.mozilla.org/en-US/docs/Web/CSS/view-transition-name
- MDN — ViewTransition.skipTransition(): https://developer.mozilla.org/en-US/docs/Web/API/ViewTransition/skipTransition
- W3C — CSS View Transitions Module Level 1 (transition as an enhancement; abort on duplicate name): https://www.w3.org/TR/css-view-transitions-1/
- Chrome for Developers — Same-document view transitions (ready/finished, bfcache name cleanup, reduced-motion): https://developer.chrome.com/docs/web-platform/view-transitions/same-document
- Chrome for Developers — Misconceptions about view transitions (reduced-motion is not automatic; snapshots vs. screenshots): https://developer.chrome.com/blog/view-transitions-misconceptions
- Chrome for Developers — Element-scoped view transitions (z-index / top-layer fix): https://developer.chrome.com/docs/css-ui/view-transitions/element-scoped-view-transitions
- Chrome for Developers — Cross-document view transitions (same-origin, main-frame): https://developer.chrome.com/docs/web-platform/view-transitions/cross-document
- React — `<ViewTransition>` (Canary/Experimental; Transition requirement, flushSync opt-out, waits for CSS/fonts/images, Suspense reveals): https://react.dev/reference/react/ViewTransition
- React — startTransition (updates after an await or in setTimeout are not marked as Transitions): https://react.dev/reference/react/startTransition
- Next.js — View transitions guide (experimental.viewTransition config, fixed-header z-index, next-view-transitions): https://nextjs.org/docs/app/guides/view-transitions
- next-view-transitions — Vercel community library for View Transitions in the Next.js App Router (the implement-side skill to defer to): https://github.com/shuding/next-view-transitions
- caniuse — View Transitions API (browser support: Chrome 111+, Safari 18+, Firefox 144+): https://caniuse.com/view-transitions
