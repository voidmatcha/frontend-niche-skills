# Condition A — no skill in context

## Short version

This is almost certainly an IME composition bug, not a general double-click or race condition. When a Korean IME has an uncommitted syllable in the buffer, the Enter key does two jobs: it commits the composition, and it acts as Enter. Depending on the OS, the IME, and the browser engine, your keydown handler can see that single physical keypress as two separate events, or your keydown handler and the browser's native form submission can both fire from it.

The debounce reduced the symptom because the two fires are usually only a few milliseconds apart. That is the strongest signal in your report: a bug that a 300ms debounce almost-but-not-quite fixes is a bug where the duplicate arrives immediately, not one where the user genuinely acted twice.

The smallest safe fix is to stop submitting from a key handler and let the native form do it, or, if you must keep the key handler, gate it on composition state. Then delete the debounce.

## What is actually happening

There are three variants and you may have more than one of them.

**1. The IME emits two keydown events for the commit Enter.**

On Windows with the Microsoft Korean IME (and on several Android keyboards), pressing Enter while a syllable is still composing produces a keydown that closes the composition, followed by a second keydown that is the "real" Enter. The first one carries `keyCode === 229` and `isComposing === true`. If your handler checks only `e.key === 'Enter'`, it runs on both. The gap is typically 0 to 15ms.

**2. Your keydown handler and the browser's implicit form submission both fire.**

If the input lives in a `<form>` and you also handle Enter in `onKeyDown` without calling `preventDefault()` on every path, one keypress produces your handler's search plus the form's native submit. This is not IME-specific on its own, but composition makes it intermittent: browsers suppress implicit form submission while a composition is active, so the double fire appears only on the keypress where the composition happens to have already ended.

**3. Event ordering differs across engines.**

Blink and Gecko generally fire `keydown` (isComposing true) then `compositionend`. WebKit has historically fired `compositionend` before the `keydown`, which means the same physical keypress arrives with `isComposing === false` in Safari and `true` in Chrome. Any hand-rolled "am I composing" flag that is set on `compositionstart` and cleared on `compositionend` will therefore behave differently per browser, and a flag cleared with a `setTimeout` will behave differently per machine load.

## Why only some users

Three variables, and your affected users are the intersection of them:

- **Typing habit.** The bug only fires when the last syllable is still uncommitted. A user who types `한국어 ` with a trailing space, or who clicks the search button, or who presses an arrow key before Enter, has already committed the composition and will never see it. A user who types `한국어` and hits Enter immediately sees it every time.
- **OS and IME.** Windows MS Korean IME, macOS 2-set Korean, Android Samsung/Google keyboards, and iOS all differ. Windows and Android are the usual offenders.
- **Browser engine.** See ordering above.

This is why it does not reproduce for you. If you develop on macOS in Chrome and type a trailing space out of habit, you are in the safe cell of the matrix.

## The smallest safe fix

**Preferred: let the form submit, remove the key handler entirely.**

```jsx
<form onSubmit={(e) => { e.preventDefault(); runSearch(query); }}>
  <input value={query} onChange={(e) => setQuery(e.target.value)} />
  <button type="submit">검색</button>
</form>
```

Native implicit submission is specified to be suppressed while a composition is active, and every current engine honors that. You get exactly one submit per Enter, with the composition already committed, for free. No debounce, no flags, no IME branching. This is the smallest correct change if your markup already has a real `<form>`.

**If you cannot use a form, gate the key handler on composition state.**

```jsx
function onKeyDown(e) {
  if (e.key !== 'Enter') return;
  // React's synthetic event does not expose isComposing; read the native one.
  if (e.nativeEvent.isComposing || e.keyCode === 229) return;
  e.preventDefault();
  runSearch(query);
}
```

Check both. `isComposing` covers the spec-compliant path; the `keyCode === 229` check covers older Android WebViews and a few IMEs where `isComposing` is not set on the commit keydown. `keyCode` is deprecated but it is still the only reliable signal on those targets, and reading it costs nothing.

Do not add a `compositionstart` / `compositionend` ref flag on top of this unless you find a specific target where the two checks above fail. That flag is where most teams introduce the WebKit ordering bug, and clearing it on a timer makes the behavior load-dependent, which is exactly the kind of intermittency you are trying to remove.

**Then remove the 300ms debounce.** It is masking the real defect, it adds 300ms of latency to every search for every user, and it will keep leaking duplicates whenever the two events happen to straddle the window. If you want a backstop, make it a correctness guard rather than a timing guard: drop a submit whose query string equals the in-flight request's query string, and clear that on response. That is deterministic and does not slow anyone down.

## Also check: a suggestion dropdown

Korean search boxes usually have an autocomplete list under them. If you are using a combobox component (Downshift, MUI Autocomplete, Ant Design Select/AutoComplete, react-select), that component has its own Enter handler that selects the highlighted item and typically calls your `onSearch` or `onSelect`. Combined with your own submit path, that is a clean double fire with no IME involvement at all, and it will also be intermittent because it depends on whether an item happens to be highlighted.

If you have such a component, check whether both its selection callback and your submit handler end up calling the search. That is worth ruling out before you change anything else.

## What I would ask you for

**Environment data from the affected users.** For each report: OS and version, browser and version, IME (Windows MS Korean vs. macOS 2-set vs. third-party like 날개셋, or the Android keyboard app). If the reports cluster on Windows or Android, variant 1 is confirmed.

**The timestamp delta between the two requests.** Pull a HAR or check your server logs for the duplicate pairs. This one number identifies the variant:

- under ~20ms: IME double keydown (variant 1) or two handlers on one event (variant 2 or the dropdown case)
- around 300ms or just over: your debounce's trailing edge is letting the second one through
- hundreds of ms with no pattern: not this bug, look at the user genuinely pressing twice or at a retry in your fetch layer

**A repro attempt with this exact recipe,** on Windows Chrome if you have access to one:

1. Focus the input, switch to Korean input.
2. Type `한국어` and stop. Do not press space, do not press an arrow key, do not click elsewhere. The final syllable must still be composing (usually shown with an underline).
3. Press Enter once.
4. Watch the Network panel.

If that does not fire twice, repeat on Android Chrome with the Samsung keyboard.

**Event instrumentation,** if the recipe above still does not reproduce. Paste this into the console on the search page and type the recipe:

```js
const input = document.querySelector('input[type=search], input');
['compositionstart','compositionupdate','compositionend','keydown','keyup','input']
  .forEach(type => input.addEventListener(type, (e) => {
    console.log(
      performance.now().toFixed(1), type,
      'key=', e.key, 'keyCode=', e.keyCode,
      'isComposing=', e.isComposing,
      'data=', e.data, 'value=', input.value
    );
  }, true));
```

The log tells you unambiguously whether one physical Enter produces one keydown or two, and what `isComposing` reads on each. Ask an affected user to run it and send you the output if you cannot reproduce locally. That single log resolves the whole question.

## One more thing to verify after the fix

Confirm that Enter still submits correctly in the *non*-composing cases, since the `isComposing` guard returns early:

- English/Latin input, Enter submits
- Korean text followed by a space, then Enter, submits
- Korean text, Enter to commit the composition, then Enter again, submits on the second press

That third case is the expected behavior with an IME and is what Korean users already anticipate from every other search box on the platform. It is not a regression, and it is the behavior you get from the native form path as well.
