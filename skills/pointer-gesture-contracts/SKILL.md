---
name: pointer-gesture-contracts
description: "Use when a single-pointer drag, resize handle, slider, canvas tool, or swipe interaction stops outside its hit area, stays active after release or interruption, commits after pointer cancellation, loses touch or pen input, or blocks browser pan/zoom because active-pointer state, event delivery, capture, or touch-action is wrong. Single-pointer direct-manipulation runtime scope; true multi-pointer gesture geometry is out of scope. Use file-ingest-contracts for HTML/file drag-and-drop, a11y-contract-testing for generic click/keyboard semantics, user-activation-contracts for gesture-gated APIs, and core-web-vitals-performance-contracts for pointer-handler performance."
---

# Pointer gesture contracts

A single-pointer direct-manipulation interaction owns one active pointer from
start through commit, cancellation, or teardown. Pointer capture is one event
delivery strategy; it does not decide whether the product should commit,
revert, or cancel, and it does not replace explicit state cleanup.

## Checklist

1. Identify the manipulated value, start target, active `pointerId`, supported
   pointer types, and the exact states for idle, previewing, committed, and
   cancelled. Do not infer a valid drag from generic `pointermove` events.
2. Start ownership from the intended `pointerdown`. Ignore unrelated pointers
   while one interaction is active, and decide explicitly whether secondary
   mouse buttons are supported. This skill does not own pinch, rotate, or
   other true multi-pointer geometry/state; route those systems to a dedicated
   multi-touch gesture workflow.
3. Map the actual event-delivery path before changing it: handlers on an
   element with pointer capture, a window capture-phase listener, or a
   document/window listener with its propagation and teardown behavior. When
   movement must continue outside the hit area, verify which path loses events
   and why. Element capture is a complete ownership path only when move and
   terminal events are consumed on the capturing element, or otherwise before
   the known propagation blocker. Capture retargeting can still bubble through
   an ancestor that stops propagation, so adding capture while leaving a
   document bubble listener downstream does not repair that path. When
   element-local ownership is the smallest demonstrated fix, capture the active
   `pointerId` and place or confirm consumption on that path. Otherwise use an
   appropriate window capture-phase/global path with explicit cleanup. Do not
   replace a working, correctly cleaned-up global path merely because capture
   is absent.
4. End the active state on the normal `pointerup` path and release capture when
   still held. Also handle `pointercancel` and `lostpointercapture`; classify
   each as commit, revert, or cancel from the product contract, but always
   clear transient state exactly once.
5. For button-driven drags, treat an active `pointermove` with
   `event.buttons === 0` as recovery evidence that no button remains pressed.
   Do not confuse `buttons`, the current bitmask, with `button`, the button
   whose state changed. Keep the active `pointerId` guard so pen hover or an
   unrelated pointer cannot end another interaction.
6. Choose `touch-action` from the gesture axis the component truly owns.
   Preserve browser panning and zooming that the component does not replace;
   do not apply `touch-action: none` broadly to silence `pointercancel`.
   Configure it before the gesture starts, then verify the real scroll and
   zoom behavior.
7. Make teardown idempotent. On unmount, disable, owner replacement, or other
   supported interruption, remove non-declarative listeners, clear active
   pointer/value state, and release capture when possible. Never let a late
   event commit a disposed interaction.
8. Test normal and interrupted sequences with mouse, touch, and pen where the
   product supports them. Verify final value, active styling, capture state,
   page pan/zoom, and listener/state counts rather than checking only that
   handlers exist.

## Quick probes

- Log `pointerId`, `pointerType`, event type, `button`, `buttons`, active owner,
  and `hasPointerCapture(pointerId)` for one focused reproduction.
- Drag rapidly beyond a narrow handle or thumb. If movement stops at the hit
  boundary, compare the current element/global and capture/bubble path,
  propagation stops, handler location, and listener lifetime before selecting
  a repair. If testing element capture, assert that move and terminal handlers
  actually consume the retargeted events before any blocker.
- During an active mouse drag, omit `pointerup` in a synthetic regression and
  deliver a later matching `pointermove` with `buttons === 0`; the preview and
  active styling must not remain stuck.
- On touch, start from the custom surface and from its surrounding page.
  Confirm the intended gesture works while preserved page pan and pinch zoom
  still work.
- Interrupt with `pointercancel`, capture loss, component unmount, and owner
  replacement. Assert one terminal transition and no late commit.

## Focused browser regression

Use a real rendered component, not handler-unit tests alone:

1. **Mouse:** press the primary button, cross the element boundary, release,
   and cover the missing-release recovery with a matching move whose
   `buttons` is zero.
2. **Touch:** drag quickly from a narrow handle, then exercise the browser pan
   axis and a cancellation sequence. Assert both the component result and the
   preserved browser behavior.
3. **Pen:** when pen input is supported, test contact drag, hover re-entry with
   no buttons, and cancellation. A hover move must not revive or terminate
   another pointer's interaction.

Record the terminal reason (`up`, zero-buttons recovery, cancel, capture loss,
or teardown), final value, active owner, and capture state. Device emulation is
useful for repeatability, but do not claim physical touch or pen coverage when
only emulation ran. When the support claim depends on hardware or OS
interruption, use the evidence contract in
[`references/real-device-validation.md`](references/real-device-validation.md).

## Boundary with sibling skills

- `file-ingest-contracts` owns HTML Drag and Drop, `DataTransfer`, dropped
  files/directories, and upload intake. This skill owns custom pointer-driven
  manipulation, not `dragstart`/`drop`.
- `a11y-contract-testing` owns names, roles, keyboard access, and generic click
  activation. Route there when the defect is an inaccessible alternative
  rather than a broken pointer stream.
- `user-activation-contracts` owns APIs that must run during a trusted gesture.
  Pointer ownership does not preserve or manufacture transient activation.
- `core-web-vitals-performance-contracts` owns page responsiveness and handler
  cost. This skill can identify a pointer sequence but does not diagnose INP.
- `browser-page-lifecycle-bfcache-contracts` owns document restoration. This
  skill owns clearing a direct-manipulation state once a supported teardown or
  interruption signal reaches the component.
- True multi-pointer gesture systems that calculate pinch, rotation, scale, or
  multi-contact geometry are outside this single-pointer skill. Do not
  partially repair them with a one-`pointerId` state machine.

## Boundary with public prior art

The public `pointer-drag-release` skill already covers normal `pointerup`,
`buttons === 0` recovery, `lostpointercapture`, active-`pointerId` guards,
cancel handling, and mouse/touch/pen release paths. This skill intentionally
overlaps those runtime exit checks and extends the review surface to compare
event-delivery ownership alternatives, negotiate `touch-action`, verify
teardown, and route accessibility, file intake, activation, performance, and
lifecycle findings to their owning skills. The broader public `touch-pointer`
skill owns accessibility and WCAG guidance rather than this narrow runtime
state investigation.

## PR-worthiness gate

Require a reproducible direct-manipulation failure tied to event ownership,
capture, terminal-state handling, `buttons` recovery, `touch-action`, or
teardown. Record the pointer sequence and type, expected commit/cancel result,
actual final value and active/capture state, and the smallest mouse/touch/pen
browser regression that fails before the change.

The bundled Playwright fixture runs its trusted mouse boundary-drag and cleanup
contract in the bundled Chromium, Firefox, and WebKit engines. A separate
`hasTouch` plus `touchscreen.tap()` lane confirms emulated touch down/up
delivery and cleanup in those engines. Its `pointercancel` and zero-buttons
paths use synthetic pointer events, and capture loss is programmatic; none of
these lanes is physical touch, pen, pressure/tilt, palm-rejection, or
device/OS-level cancellation evidence.

Reject weak findings: the presence or absence of `setPointerCapture` without a
demonstrated event-delivery or teardown failure; a working global listener path
rejected only because element capture is possible; capture added without
moving or confirming event consumption before a known propagation blocker;
`touch-action: none` without demonstrated lost browser behavior; a
`pointercancel` handler whose product-specific commit/revert semantics were not
established; a source-only claim that teardown leaks; a true multi-pointer
geometry system; an ordinary click or keyboard defect; HTML file drag-and-drop;
a gesture-gated API failure; or a slow pointer handler with no ownership/state
defect.

## Output shape

Start with a disposition: confirmed, candidate/needs evidence, reject, or
route. Report the component and manipulated value, pointer type and active
`pointerId` contract, event/capture sequence, terminal reason, observed final
value and active/capture state, `touch-action` and preserved browser behavior,
smallest warranted fix, sibling boundary, and the focused browser regression.
For missing physical-device coverage or an unspecified cancel/commit contract,
state the verification gap instead of presenting a confirmed fix.

## Sources

- W3C, Pointer Events Level 3, including pointer event types, button state,
  direct-manipulation behavior, and pointer capture:
  <https://www.w3.org/TR/pointerevents3/>
- MDN, Pointer events overview and pointer capture:
  <https://developer.mozilla.org/en-US/docs/Web/API/Pointer_events>
- MDN, `Element.setPointerCapture()` behavior and active-pointer error:
  <https://developer.mozilla.org/en-US/docs/Web/API/Element/setPointerCapture>
- MDN, `touch-action` and browser gesture negotiation:
  <https://developer.mozilla.org/en-US/docs/Web/CSS/touch-action>
- MDN, `addEventListener()` listener phases, options, and removal:
  <https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/addEventListener>
- Playwright, browser installation and bundled engine builds:
  <https://playwright.dev/docs/browsers>
- Playwright, device and touch-capability emulation:
  <https://playwright.dev/docs/emulation>
- Playwright, `touchscreen.tap()` and its tap-only scope:
  <https://playwright.dev/docs/api/class-touchscreen>
- Public issue showing drag state stuck after an interrupted iOS navigation
  sequence: <https://github.com/pmndrs/use-gesture/issues/349>
- Public issue showing a race where capture is attempted after the pointer is
  no longer active: <https://github.com/pmndrs/use-gesture/issues/701>
- Public slider issue showing document-level movement tracking disrupted by
  ancestor event propagation handling:
  <https://github.com/mui/material-ui/issues/35887>
- Public grid issue with a touch reproduction where a narrow resize handle
  loses movement without pointer capture:
  <https://github.com/sv-grid/sv-grid/issues/59>
- Public prior-art skill covering pointer release recovery, active-pointer
  guards, cancellation, and mouse/touch/pen paths:
  <https://github.com/lennondotw/agent-skills/blob/09ed7cd81bf2855d1e7b64c74078d77ac83ec6e8/skills/web/pointer-drag-release/SKILL.md>
- Public prior-art skill covering broad pointer and touch accessibility:
  <https://github.com/mgifford/accessibility-skills/blob/cb9af604e08e3656b96676a3c731bff7945bef46/skills/touch-pointer/SKILL.md>
