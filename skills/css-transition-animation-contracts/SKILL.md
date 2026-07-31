---
name: css-transition-animation-contracts
description: "Use when reviewing or implementing enter/exit transitions for dialog, popover, or other top-layer/display:none UI, or any cleanup gated on a transition finishing: the exit animation is cut off and the element just vanishes, the entry animation never plays on first open, the ::backdrop does not fade, the whole transition breaks in older browsers, or focus/unmount/scroll-unlock logic gets stuck because transitionend never fired. Transition/animation lifecycle scope; use overlay-focus-scroll-contracts for the focus-trap/scroll-lock contract itself, view-transitions-contracts for the View Transitions API (a different mechanism), and a11y-contract-testing for reduced-motion and role/name assertions."
---

# CSS transition/animation contracts

Enter/exit motion for `<dialog>`, popover, and anything toggling `display` looks fine in the happy path and breaks at the edges: the exit animation is skipped, the first open does not animate, or JS gated on `transitionend` never runs. This is a review lens for two failure families — discrete-property enter/exit on the top layer, and interrupted transitions whose completion event never arrives. It is not a how-to-animate tutorial (Chrome/MDN own that); it owns the gotcha/review layer.

## Checklist (lead with the trap)

1. **Exit animation cut off because `display` and `overlay` are missing from the transition list (the most common mistake).** An element toggling `display:none` (dialog, popover, top-layer) needs `display` in the `transition` list with `transition-behavior: allow-discrete`, or the element flips to `none` at once and the exit is never seen. For top-layer elements also transition `overlay` (with `allow-discrete`) so removal from the top layer is deferred until the animation ends — without it the element jumps out of the top layer (behind siblings) before it can animate out. Entry-only setups are the tell: they animate in but vanish on close.
2. **`allow-discrete` placement — prefer a separate `transition-behavior` line, and put it AFTER the shorthand.** Two independent traps push the same fix. (a) A standalone `transition-behavior: allow-discrete;` written *before* the `transition` shorthand is reset by the shorthand and ignored — it must come after. (b) Baking `allow-discrete` (or `overlay`) *inside* the `transition` shorthand value means a browser that does not know the keyword invalidates the *entire* declaration (CSS drops the whole value when any part is invalid), killing even the opacity/transform transition. A separate `transition-behavior: allow-discrete;` line after the shorthand degrades to just that one line being dropped, leaving the base transition intact.
3. **`@starting-style` must target the open-state selector, and sit after it.** Transitions do not fire on first style update or on the `display:none`->visible flip, so the entry animation needs a `@starting-style` block defining the from-state. It must select the *open* state (`:popover-open`, or `[open]` for `<dialog>`) and be written after that rule (equal specificity, source order wins). Targeting the base/closed selector is a no-op and the entry silently does not animate.
4. **`::backdrop` needs its own selector and its own `@starting-style`.** Give `dialog::backdrop` / `[popover]::backdrop` separate transition declarations and, if it animates in, its own `@starting-style`. That selector may be top-level or use native nesting such as `dialog { &::backdrop { ... } }`; the defect is inheriting or omitting the backdrop's state, not nesting itself.
5. **Do not gate cleanup/focus/unmount on `transitionend` alone — it does not always fire.** When the element is removed from the DOM, set to `display:none`, or the transition is cancelled (re-interrupted, ESC-closed mid-transition), `transitionend` is not generated. The cancel path fires `transitioncancel` instead (a standard, cross-browser event, Baseline since 2020 — not `transitionend`), and some interrupt/removal paths can still emit no usable transition event at all. Real bug class: React Aria's focus restoration runs through `runAfterTransition`, which must special-case `transitioncancel` and node removal precisely because `transitionend` is unreliable (see react-spectrum issue #7326, detached nodes retained when a multi-value transition is cancelled). Symptom: focus never restored, overlay never unmounts, body scroll stays locked.
6. **Gate on the animation finishing, not on one event.** Prefer `Promise.all(el.getAnimations({subtree:true}).map(a => a.finished))` — one code path that settles on complete or cancel. Mind that `finished` *rejects* (`AbortError`) when an animation is cancelled: run cleanup via `.then(done, done)` (or `await` inside `try/finally` with the rejection caught) — bare `.then(done)` skips cleanup on cancel, and a bare `.finally(done)` runs cleanup but still leaves the rejection unhandled. If you must use events, listen to `transitionrun` + `transitionend` + `transitioncancel` together and add a duration-based timeout fallback so a missing event cannot wedge the lifecycle.
7. **Honor `prefers-reduced-motion`.** Wrap decorative motion in `@media (prefers-reduced-motion: reduce)` and tone it down (e.g. to a fade) rather than blanket `* { animation: none !important; }` — some flows depend on the completion event, and JS-driven (Web Animations) motion is not covered by the CSS hack. Motion that is essential to conveyed meaning may stay.

## Quick probes

Use these as leads, then read the actual open/close CSS and the JS that waits on it:

```sh
rg -n 'allow-discrete|transition-behavior|@starting-style|\boverlay\b' src/ app/ packages/ 2>/dev/null
rg -n 'transitionend|transitioncancel|transitionrun|animationend|onTransitionEnd' src/ app/ packages/ 2>/dev/null
rg -n 'getAnimations|\.finished|::backdrop|:popover-open|\[open\]|runAfterTransition' src/ app/ packages/ 2>/dev/null
rg -n 'prefers-reduced-motion|matchMedia\(.*reduced-motion' src/ app/ packages/ 2>/dev/null
```

For a candidate exit-animation bug, confirm the transition list actually contains `display` and (for top-layer) `overlay`; a match on `transition:` alone is not evidence.

## Boundary with sibling skills

- Use **css-transition-animation-contracts** for the transition/animation *lifecycle*: discrete-property enter/exit (`display`/`overlay`/`allow-discrete`/`@starting-style`/`::backdrop`) and completion-event reliability (`transitionend`/`transitioncancel`/`getAnimations().finished`).
- Use **overlay-focus-scroll-contracts** for the overlay contract itself — focus trap/restore, `inert`/`aria-hidden`, scroll lock, dismissal, nested stacks. This skill adds the transition-lifecycle layer beneath it: the exact reason a lock or trap outlives the visual close is usually a completion event that never fired.
- Use **view-transitions-contracts** for the View Transitions API (`document.startViewTransition`, `::view-transition-*`) — a different mechanism from CSS transitions, not covered here.
- Use **a11y-contract-testing** for reduced-motion behavior verification and for role/name/state assertions on the animated element.
- Prior art: GoogleChrome/web.dev modern-web-guidance covers *how to* build these entry/exit animations; this skill owns the *review/gotcha* lens — the failure modes and what to flag in a diff.

## PR-worthiness gate

Count a finding only when all hold:

1. A real user path triggers the open/close or the gated cleanup.
2. The defect is user-visible or state-corrupting: exit skipped, entry never animates, backdrop does not fade, transition broken in a supported browser, or focus/unmount/scroll-unlock wedged.
3. Evidence is the actual CSS transition list / `@starting-style` selector / event-gated code, not just a grep hit.
4. The fix is narrow: add `display`+`overlay` to one transition list, move/split one `transition-behavior` line, re-target one `@starting-style`, give `::backdrop` its own selector/declarations, or swap one `transitionend` gate for `getAnimations().finished` plus a timeout.

Reject weak findings:

- A pure CSS `@keyframes` animation (not a transition to/from `display:none`) does not need `@starting-style` or `allow-discrete`.
- `transition` shorthand without `allow-discrete` is fine for non-discrete properties; the exit-animation trap only applies when `display`/`overlay` are being toggled.
- Radix, Headless UI, and similar libraries may already gate unmount on animation completion — inspect their config before filing.
- A `setTimeout(duration)` cleanup is a valid fallback, not automatically a bug.

## Output shape

Return compact findings:

- **Contract**: discrete-property enter/exit, `@starting-style` target, `::backdrop` rule, or completion-event gate.
- **Evidence**: file/line, the transition list or event-gated code path.
- **Risk**: exit skipped, entry not animated, backdrop static, older-browser breakage, or stuck focus/unmount/scroll-lock.
- **Fix**: the one-line/one-rule change above.
- **Verification**: a browser check of open->close (and an interrupt: reopen or ESC mid-transition), or a test asserting cleanup runs on cancel.

## Sources

- [transition-behavior (allow-discrete, discrete display/overlay) - MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/transition-behavior)
- [@starting-style at-rule - MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/@starting-style)
- [overlay property (defers top-layer removal) - MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/overlay)
- [Using CSS transitions (display + allow-discrete + @starting-style) - MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_transitions/Using_CSS_transitions)
- [Using CSS nesting (`&` with appended pseudo-element selectors) - MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_nesting/Using_CSS_nesting)
- [`::backdrop` pseudo-element - MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/::backdrop)
- [Four new CSS features for smooth entry and exit animations - Chrome for Developers](https://developer.chrome.com/blog/entry-exit-animations/)
- [Now in Baseline: animating entry effects - web.dev](https://web.dev/blog/baseline-entry-animations)
- [Element: transitionend event (not fired when transition removed) - MDN](https://developer.mozilla.org/en-US/docs/Web/API/Element/transitionend_event)
- [Element: transitioncancel event - MDN](https://developer.mozilla.org/en-US/docs/Web/API/Element/transitioncancel_event)
- [Element: getAnimations() (.finished promise cleanup) - MDN](https://developer.mozilla.org/en-US/docs/Web/API/Element/getAnimations)
- [prefers-reduced-motion media feature - MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion)
- [Animation.finished - MDN (the promise rejects with AbortError when the animation is cancelled)](https://developer.mozilla.org/en-US/docs/Web/API/Animation/finished)
- [react-spectrum runAfterTransition.ts (transitioncancel + node-removal handling; commit-pinned — the file moved in the #9774 package consolidation)](https://github.com/adobe/react-spectrum/blob/01a53cfa626c8226e71efb07458fd7de5ffc370d/packages/@react-aria/utils/src/runAfterTransition.ts)
- [react-spectrum #7326: detached nodes retained when a multi-value transition is cancelled](https://github.com/adobe/react-spectrum/issues/7326)
