# Condition B — cjk-text-and-input in context

## What is going on

This is almost certainly IME composition, not a click/event-handler race. The debounce didn't fix it because there is no bug to debounce — there are two legitimately distinct Enter keydowns, and your handler treats both as commands.

When a Korean user types 검색 and presses Enter, the first Enter is not "submit". It is the keystroke that commits the IME's composition buffer — the underlined, not-yet-final syllable. The browser still delivers a `keydown` for it, but that keydown is flagged as belonging to the IME:

- `KeyboardEvent.isComposing === true`
- legacy engines and many Android WebViews report `keyCode === 229` (the UI Events spec's "IME is processing this" code)

So the sequence for an affected user is:

```
compositionstart / compositionupdate ...   (ㄱ → 거 → 검 → 검ㅅ → 검사 → 검색)
keydown  key="Enter"  isComposing=true  keyCode=229   ← commits the buffer, your handler ALSO fires
compositionend
input                                                  ← value settles to "검색"
keydown  key="Enter"  isComposing=false                ← the user's real submit (their second press,
                                                          or the same press re-delivered post-commit)
```

Two submits, identical text, because by the time the second one fires the buffer has already committed to the same string.

This explains every part of your report:

**"Only some users."** Only users whose last character was still mid-composition when they hit Enter. If a Korean user types a trailing space, clicks away, or pauses long enough for the IME to auto-commit, the composition is already closed and Enter behaves normally. English-typing users and QA testing in English never hit it at all — that is why it doesn't reproduce.

**"Debounce reduced it a lot but not completely."** The gap between commit-Enter and submit-Enter is human keystroke timing plus the browser's compositionend→keydown latency. Usually under 300ms, so the debounce swallows it. On a slow device, a loaded main thread, or a user who taps Enter twice deliberately (a very common Korean typing habit — one to confirm, one to go), the gap exceeds 300ms and both get through. A debounce is a race you win most of the time, not a guard.

**"Same text."** Diagnostic confirmation. A genuine double-fire from, say, a click plus a submit would usually differ in some way; identical payloads point at the buffer already being final for both dispatches.

Note also that `isComposing` is **false** on the `keyup` for that same Enter — the composition has already ended by then. If your handler is on `keyup` (or `keypress`), that is an additional reason you see the ghost submit, and moving the guard to `keyup` will not help.

## The smallest safe fix

**Case 1 — you handle Enter yourself in a key handler.** Add the composition guard and delete the debounce:

```js
input.addEventListener('keydown', (e) => {
  if (e.isComposing || e.keyCode === 229) return; // IME is composing — not a command
  if (e.key === 'Enter' && !e.repeat) submit();
});
```

React, where the synthetic event does not reliably carry `isComposing` — read it off the native event:

```jsx
<input
  onKeyDown={(e) => {
    if (e.nativeEvent.isComposing || e.keyCode === 229) return;
    if (e.key === 'Enter' && !e.repeat) submit();
  }}
/>
```

Keep both conditions. `isComposing` is the correct modern signal; `keyCode === 229` is the fallback for Android WebViews and older Safari builds that leave `isComposing` false on the commit keydown. Keep the guard on `keydown` — not `keyup`, not `keypress`.

**Case 2 — the input is inside a `<form>` and you have *both* an Enter keydown handler and an `onSubmit`.** Then the smallest fix is smaller still: delete the keydown handler and let the form's `submit` event do the work. Browsers suppress implicit form submission for an Enter that commits a composition, so form-level submit sidesteps the problem entirely. (Some older Android WebViews are unreliable here, so if your matrix includes embedded WebViews, keep the `isComposing` guard on whatever handler survives.)

Either way the debounce goes. If you want a safety net, replace it with something that is actually a correctness guarantee rather than a timing bet: dedupe in the request layer — drop a new query if an identical one is already in flight, or attach a request id and ignore stale responses. That is idempotency, not a timer, so it holds regardless of how far apart the two events land.

**While you're in there:** if this search box also does search-as-you-type, check that it isn't querying partial syllables. Every composition update fires an `input` event, so a Korean user typing 스킬 generates queries for ㅅ, 스, 슥, 스키, 스킬. Debouncing narrows that but still fires on whatever partial state the pause lands on. Gate the as-you-type dispatch on `compositionend`, with the normal `input` path for non-IME typing. Similarly, if you sanitize, uppercase, trim, or mask the value on every change, skip that work while `isComposing` is true — transforming the value mid-composition corrupts the IME buffer and produces the classic 한글 자모 분리 (jamo splitting apart) symptom.

## Reproduction steps

Set up a real Korean input method — this cannot be reproduced by pasting Korean text or by `type()`ing it in a test, because neither goes through composition.

- **macOS**: System Settings → Keyboard → Input Sources → add Korean → 2-Set Korean. Switch with Caps Lock or Ctrl+Space.
- **Windows**: Microsoft IME Korean, Hangul mode.
- **Android**: Gboard with Korean (10-key or 2-Bulsik) — test in your actual WebView, not just Chrome.
- **iOS**: Korean keyboard in Safari.

Then: focus the search box, type `검색` (or any Korean word), and **without typing a trailing space or clicking away**, press Enter once. Watch the network tab for two identical requests.

The contrast case that should stay clean: type `검색`, press space, then Enter. One request. If that difference shows up, the diagnosis is confirmed.

## Verification instrumentation

Before you change anything, log the raw sequence so you have evidence rather than a plausible story:

```js
for (const type of ['compositionstart','compositionupdate','compositionend','keydown','keyup','input']) {
  input.addEventListener(type, (e) => {
    console.log(type, {
      t: Math.round(performance.now()),
      key: e.key,
      isComposing: e.isComposing,
      keyCode: e.keyCode,
      value: input.value,
    });
  });
}
```

and log every submit dispatch with a timestamp and a trace id. The signature you're looking for is a submit dispatched from a keydown where `isComposing === true` or `keyCode === 229`, followed by a second submit a few dozen to a few hundred milliseconds later. After the fix, the same sequence should show the composing keydown logged but no submit attached to it — exactly one dispatch.

Don't assume a fixed ordering between `compositionend` and the final `input` event; engines differ on which comes first. Branch on `event.isComposing`, never on event order.

## Browser / device matrix worth covering

Chrome and Safari on macOS with 2-Set Korean; Chrome and Edge on Windows with MS-IME; Chrome on Android and your embedded WebView with Gboard (this is where `keyCode 229` still earns its place); Safari on iOS. Android WebView is the most likely source of the "some users" tail — if your usage skews mobile, test it there first.

## Regression test

Add one test that drives real composition rather than plain typing. Options, roughly in order of fidelity:

- **Chromium via CDP**: `Input.imeSetComposition` to build the syllable, then dispatch the Enter keydown with `isComposing: true`, then `Input.insertText` for the commit. This is the only approach that exercises the true browser path.
- **Synthetic DOM events** as a cheaper unit-level guard: dispatch `compositionstart` → `compositionupdate` → a `KeyboardEvent('keydown', { key: 'Enter', isComposing: true, keyCode: 229 })` → `compositionend` → a second `KeyboardEvent('keydown', { key: 'Enter' })`, and assert your submit callback fired exactly once.

Assert on the count of submit dispatches, not on timing — a test that passes because a debounce swallowed the second call is the bug you already have. And use a real Korean string (`검색`, `스킬`) in the fixture; the test is meaningless with ASCII.
