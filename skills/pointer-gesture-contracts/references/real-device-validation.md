# Real device validation protocol

Use this reference when a pointer finding depends on physical touch, active pen,
or operating-system interruption behavior. Automated browser fixtures can
exercise event ownership and cleanup paths, but physical input coverage requires
a real device and a recorded event trace from that device.

Do not treat Playwright mouse input, Playwright `touchscreen.tap()`, legacy touch
event dispatch, or synthetic `PointerEvent` objects as proof of physical touch,
active pen, palm rejection, orientation changes, or OS/app interruption behavior.
Those tools are useful regression aids only.

## Contents

- [Scope](#scope)
- [Device matrix](#device-matrix)
- [Instrumentation](#instrumentation)
- [Manual scenarios](#manual-scenarios)
- [Evidence packet](#evidence-packet)
- [Pass / fail rule](#pass--fail-rule)
- [Sources](#sources)

## Scope

This protocol validates single-pointer direct-manipulation flows covered by
`pointer-gesture-contracts`: drag handles, sliders, resize grips, swipe
controls, canvas tools, and similar one-active-pointer interactions.

Out of scope:

- multi-contact pinch, rotate, or geometry calculations;
- generic click or keyboard activation;
- HTML Drag and Drop / file ingest;
- accessibility semantics;
- performance diagnosis.

## Device matrix

Run the smallest matrix that matches the product support claim. Do not mark an
untested pointer type as covered.

| Input path | Required when | Minimum checks |
| --- | --- | --- |
| Physical touch | The UI supports phones, tablets, touch laptops, or touchscreens | contact drag, rapid boundary exit, browser pan axis, browser zoom path if supported |
| Active pen contact | The UI advertises or must tolerate pen/stylus input | contact drag, hover re-entry, barrel/secondary-button state when supported by the product |
| Active pen hover | The UI runs on pen hardware that emits hover | hover move before contact, hover after cancellation, hover with no pressed buttons |
| Mouse control | The UI also supports desktop pointer input | primary-button drag, boundary exit, release, zero-buttons recovery |

Record the device category, browser, OS version, viewport size, input path, and
whether the run used physical hardware or emulation.

## Instrumentation

Add temporary logging around the real component or a production-equivalent
harness. The log must be redacted but complete enough to reconstruct the
contract:

- event type;
- `pointerId`;
- `pointerType`;
- `isPrimary`;
- `button` and `buttons`;
- client coordinates or normalized component value;
- active owner/session id;
- `hasPointerCapture(pointerId)` when available;
- terminal reason: `pointerup`, `pointercancel`, `lostpointercapture`,
  zero-buttons recovery, teardown, app/background interruption, or navigation;
- final value and active visual state;
- computed `touch-action` on the start target and relevant ancestors.

Screenshots or video should show the gesture surface, final UI state, and any
browser/OS interruption UI needed to explain the sequence. Redact user data,
device identifiers, notification content, and unrelated page content.

## Manual scenarios

### 1. Normal ownership

1. Start on the intended hit target with the supported input path.
2. Move within the control and then beyond the original element boundary.
3. Release normally.
4. Confirm one commit or cancel result according to the product contract.
5. Confirm active styling, capture state, and temporary listeners are cleared.

Pass when the final value matches the intended commit/cancel semantics and no
active pointer state remains. Fail when movement is lost at the boundary, a late
event commits another interaction, capture remains held, or active styling stays
stuck.

### 2. Browser gesture arbitration

1. Start a component-owned gesture on its supported axis.
2. Start browser-owned pan/scroll on the axis the component should preserve.
3. Exercise browser zoom if the product claims zoom remains available.
4. Record `pointercancel` or continued pointer delivery.

Pass when component-owned gestures work and preserved browser gestures still
work. Fail when broad `touch-action: none` blocks required browser behavior, or
when browser pan/zoom cancels the component without the required cleanup.

### 3. Touch interruption

Run the applicable interruptions for the target browser/OS:

- orientation change during an active drag;
- app switch or browser backgrounding during an active drag;
- system gesture from the screen edge or browser UI;
- page navigation, route replacement, or component unmount while active;
- accidental second contact when the contract is single-pointer only.

Pass when the interaction reaches exactly one terminal state, does not commit a
disposed preview, and leaves no active styling or listeners. Fail when the UI
stays active, commits after disposal, or lets an unrelated pointer finish the
original interaction.

### 4. Active pen interruption

Run the applicable pen-specific checks:

- contact drag and release;
- hover before contact;
- hover re-entry after release;
- hover or move with `buttons === 0` after a missed release;
- palm rejection or accidental touch while the pen owns the interaction;
- barrel/secondary-button state when the product supports it.

Pass when pen contact owns only its active `pointerId`, hover does not revive or
terminate another interaction, and palm/secondary input follows the documented
contract. Fail when hover is treated as a pressed drag, palm input steals the
active pen interaction without cleanup, or an unrelated pointer commits the
value.

## Evidence packet

Attach or summarize:

- test date and tester role;
- browser, OS, device category, viewport, and input path;
- redacted event log covering start, move, terminal event, and cleanup;
- short video or screenshots for each failing or fixed scenario;
- final value/state assertions;
- list of scenarios not run and why.

Do not include raw device labels, account names, notification text, camera/mic
indicators, or unrelated page data unless explicitly permitted by the test
environment.

## Pass / fail rule

Mark physical-device coverage as **pass** only when every required pointer type
in the declared support matrix has a real-device log and the product reaches the
right terminal state with cleanup. Mark it **partial** when mouse or emulation
passed but physical touch/pen coverage is missing. Mark it **fail** when any
required physical input path loses ownership, blocks required browser behavior,
or leaves transient state after interruption.

## Sources

- Playwright, Emulation: browser contexts can emulate device properties,
  permissions, viewport, touch support, and other environment state:
  <https://playwright.dev/docs/emulation>
- Playwright, Touchscreen: `touchscreen.tap()` dispatches touch events and is
  limited to tap gestures in contexts initialized with `hasTouch`:
  <https://playwright.dev/docs/api/class-touchscreen>
- Playwright, Touch events: legacy touch gesture examples manually dispatch
  touch events from page code:
  <https://playwright.dev/docs/touch-events>
- MDN, `pointercancel`: fired when the browser determines there will likely be
  no more pointer events, including viewport manipulation such as panning,
  zooming, or scrolling:
  <https://developer.mozilla.org/en-US/docs/Web/API/Element/pointercancel_event>
- MDN, Pointer events: pointer events cover mouse, pen/stylus, and touch input
  devices:
  <https://developer.mozilla.org/en-US/docs/Web/API/Pointer_events>
