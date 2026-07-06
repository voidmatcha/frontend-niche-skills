# Overlay contracts reference

Use this reference only after `overlay-focus-scroll-contracts` triggers and the task involves modal, drawer, sheet, popover, menu, command palette, or overlay lifecycle behavior.

## Official references

- MDN `aria-hidden`: `aria-hidden="true"` removes an element and its children from the accessibility tree and should not be used on focusable elements or ancestors of focusable elements. <https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Attributes/aria-hidden>
- MDN `inert`: an inert element and its flat-tree descendants cannot receive focus or be clicked. <https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Global_attributes/inert>
- WAI-ARIA APG Modal Dialog Pattern: windows under a modal dialog are inert, and modal dialogs contain their own tab sequence. <https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/>

## Evidence framing

- Treat `aria-hidden`, `inert`, and `body.style.overflow` hits as **leads**, not findings.
- For hidden-focus issues, show focus can remain inside the hidden subtree or cite a test/console warning that reproduces it.
- For focus-trap issues, test Tab, Shift+Tab, Escape, and focus restore from the actual trigger.
- For scroll-lock issues, test repeated open/close, nested overlays, route unmount, and previous body overflow/padding styles.
- For library-managed overlays, inspect configuration (`modal`, `trapFocus`, `returnFocus`, `initialFocus`, `allowOutsideClick`, `RemoveScroll`, etc.) before proposing custom code.

## Test shapes

- Open a dialog from a button; assert focus moves into the dialog and returns to the button on close.
- Open a modal; assert background controls are not reachable by Tab/click while open.
- Close with Escape/backdrop; assert listeners do not fire after unmount.
- Open two nested overlays; close the child; assert the parent remains trapped/scroll-locked and focus stays in the parent.
- Start with `document.body.style.overflow = "clip"` or existing padding; open/close the overlay; assert previous values restore.
- If using `aria-hidden`, assert no focused element is contained in the hidden subtree during each state transition.
