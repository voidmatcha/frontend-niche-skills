---
name: overlay-focus-scroll-contracts
description: "Use when reviewing or implementing modal, dialog, drawer, sheet, popover, menu, command palette, or overlay behavior where focus trap/restoration, background inert/aria-hidden, ESC/backdrop dismissal, nested overlay stacks, animation timing, or body scroll-lock cleanup can regress. Overlay runtime scope; use a11y-contract-testing for role/name/state assertions and semantic-markup-contracts for native element choice."
---

# Overlay focus scroll contracts

Use this skill for overlays whose runtime behavior depends on focus, background interactivity, scroll state, dismissal, or nested stacks. The goal is not a generic accessibility audit; it is to make overlay lifecycle behavior explicit and regression-testable.

## Boundary with sibling skills

- Use **overlay-focus-scroll-contracts** for modal/drawer/sheet/popover/menu runtime: focus trap, focus restore, background inertness, `aria-hidden` timing, scroll lock, ESC/backdrop, nested overlays, and animation/unmount cleanup.
- Use **a11y-contract-testing** for rendered role/name/state/focus tests once the expected overlay contract is known.
- Use **semantic-markup-contracts** to decide whether trigger/content should use native button, link, dialog, list, heading, or form structure.
- Use **webview-bridge-pages** when the overlay is inside a native WebView and safe-area, keyboard, host back button, or bridge lifecycle is part of the failure.
- Use **frontend-security-baseline** for clickjacking, opener, CSP, or XSS traps around overlay content.
- Use **css-transition-animation-contracts** when a trap or scroll lock stays stuck because cleanup is gated on a `transitionend` that never fires (cancelled or interrupted exit animation).

## Review workflow

1. **Classify overlay modality** — modal dialog, non-modal popover, menu, drawer, command palette, tooltip, nested overlay, or mobile sheet. Do not impose modal behavior on intentionally non-modal controls. Then ask whether a native primitive already covers the contract before wiring a custom trap/`inert` stack: `<dialog>.showModal()` provides top-layer, focus containment, ESC, and `::backdrop` (but **not** body scroll lock); `popover` provides non-modal top-layer with light dismiss.
2. **Trace open sequence** — trigger activates overlay, focus moves to the right element, background becomes non-interactive if modal, and scroll lock starts only when needed.
3. **Trace close/unmount sequence** — ESC/backdrop/action closes overlay, focus returns to a sensible target, scroll lock restores prior body styles, listeners detach, and delayed animations do not keep stale traps active.
4. **Check `aria-hidden`/`inert` timing** — never hide a still-focused descendant from assistive tech. Prefer `inert` or a library-managed modal strategy when supported; if using `aria-hidden`, move focus before applying it and restore carefully.
5. **Check nested stacks** — opening a child dialog/menu should pause or layer parent traps and scroll locks; closing the child should not unlock the page or return focus behind the parent.
6. **Check scroll behavior** — save previous body overflow/padding, account for scrollbar compensation, and cleanup on unmount, route change, exception, and repeated open/close.
7. **Lock with a narrow test** — keyboard Tab/Shift+Tab, Escape, backdrop, focus restore, body overflow cleanup, nested overlay close order, or console warning absence.

## Defect patterns

| Pattern | Why it matters | Better direction |
| --- | --- | --- |
| Apply `aria-hidden` to a parent while focus remains inside | Browser/AT can report blocked hidden-focus warnings and users lose the active control. | Move focus first, or use `inert`/library modal handling that manages focus and background. |
| Modal opens but focus stays on page behind it | Keyboard users can continue interacting with background or miss dialog content. | Focus initial dialog element, title, or least destructive action according to UX contract. |
| Modal closes but focus disappears to `body` | Keyboard workflow restarts from top or wrong page position. | Store trigger/previous active element and restore if it still exists and is appropriate. |
| Body scroll lock overwrites existing overflow/padding | Nested overlays or pages with prior styles restore incorrectly. | Save prior values, ref-count locks, and restore only when the last lock closes. |
| Event listeners remain after unmount | ESC/backdrop handlers fire on later pages or closed overlays. | Add cleanup in unmount/effect teardown; test the route/unmount path. |
| Non-modal menu gets modal trap by default | Selection menus or editor popovers can block page interactions unexpectedly. | Keep `modal=false` but add the specific scroll/focus behavior needed. |
| Animation delay keeps focus trap active after visually closed | Users tab into invisible content or scroll remains locked. | Tie trap/lock lifecycle to state and animation completion intentionally. |

## Quick probes

Use probes as leads, then inspect runtime behavior:

```sh
rg -n 'aria-hidden|\binert\b|role="dialog"|aria-modal|trapFocus|FocusTrap|focus-trap|RemoveScroll' src/ app/ packages/ 2>/dev/null
rg -n 'document\.activeElement|\.focus\(|returnFocus|restoreFocus|initialFocus|fallbackFocus' src/ app/ packages/ 2>/dev/null
rg -n 'document\.body\.style|body\.style\.overflow|overflow\s*=\s*["'"']hidden|scrollLock|lockScroll|unlockScroll' src/ app/ packages/ 2>/dev/null
rg -n 'keydown|Escape|onEscape|backdrop|outsideClick|clickOutside|onBeforeUnmount|removeEventListener' src/ app/ packages/ 2>/dev/null
```

## PR-worthiness gate

Count an overlay finding only when all are true:

1. The overlay can be opened by a real user path.
2. The issue affects keyboard focus, background interaction, scroll state, dismissal, or nested overlay stack.
3. Evidence includes runtime state on a realistic code path, not only a grep hit.
4. The proposed change is narrow and testable.

Reject weak findings:

- Decorative `aria-hidden` icons are not overlay focus defects by themselves.
- Libraries such as Radix, Headless UI, Element Plus, Melt UI, or `focus-trap` may already manage part of the contract; inspect configuration and rendered behavior before filing.
- Non-modal popovers should not be forced into modal dialog semantics unless the product contract says background interaction must stop.
- Body scroll lock is not wrong by itself; the issue is missing cleanup or broken nested restore.

## References

Read [overlay-contracts](./references/overlay-contracts.md) for official references and evidence framing.

## Output shape

Return compact findings:

- **Overlay contract**: modal/non-modal, focus, background interactivity, scroll lock, dismissal, stack.
- **Evidence**: file/line plus runtime path or test gap.
- **Risk**: keyboard trap, hidden focused element, page scroll leak/lock, stale listener, wrong focus restore.
- **Fix**: smallest lifecycle or library configuration change.
- **Verification**: keyboard/browser test that would catch regression.
