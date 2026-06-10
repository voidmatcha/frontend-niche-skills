---
name: cjk-text-and-input
description: "Use when a page must handle CJK (Korean, Japanese, Chinese) text or input — mid-word line breaks in Korean, word-break/keep-all/line-break decisions, IME composition breaking controlled inputs, Enter firing during composition, duplicate keydown with keyCode 229, or string length counting Hangul wrong."
---

# CJK text & IME input

Two families of bugs that English-only testing never surfaces: **line breaking**
(CJK text wraps differently) and **IME composition** (characters are composed across
multiple keystrokes, so key events lie).

## Line breaking

- East Asian text lines can break **between almost any two characters** by default
  (UAX #14 ideographic line-breaking class; UAX #14 itself notes Korean is commonly
  tailored to space-based breaking) — in CSS, English-style word integrity for
  Korean is opt-in via `word-break: keep-all`, not the default.
- **Korean**: `word-break: keep-all` prevents intra-word breaks for CJK text so
  space-separated Korean words wrap as units (MDN: "Word breaks should not be used
  for Chinese/Japanese/Korean (CJK) text"). Pair with `overflow-wrap: break-word` as
  the escape hatch for long unbreakable tokens (URLs).
- `word-break: break-all` solves the opposite problem — inserting breaks between any
  two characters of **non-CJK** text to prevent overflow (CJK behavior is unchanged
  by it, per MDN); don't apply it to body text in mixed-language UIs.
- `line-break: strict|loose` tunes Japanese/Chinese punctuation-adjacent breaking
  (kinsoku); it does not control Korean word integrity — that's `keep-all`.
- Headlines/buttons: test with real Korean copy — label widths differ wildly from
  English and mid-word breaks read as typos to native speakers. W3C *klreq* (Korean
  Layout Requirements) is the canonical reference for Korean typography rules.

## IME composition (the part that breaks controlled inputs)

- IMEs compose text across keystrokes; the DOM fires
  `compositionstart` → `compositionupdate`* → `compositionend` (MDN CompositionEvent).
- **During composition, key events are unreliable for shortcuts**: `keydown` fires
  with `KeyboardEvent.isComposing === true`, and legacy browsers/engines report
  `keyCode 229` (UI Events spec documents 229 as the IME-processing code). The
  classic bug: pressing Enter to commit the IME buffer ALSO triggers the form's
  Enter handler — submitting half-composed text. Guard:

  ```js
  input.addEventListener('keydown', (e) => {
    if (e.isComposing || e.keyCode === 229) return; // IME is composing — not a command
    if (e.key === 'Enter') submit();
  });
  ```

- **Controlled inputs (React etc.)**: transforming/filtering `value` on every change
  while `isComposing` breaks the composition buffer (characters duplicate or split,
  e.g. 한글 자모 분리) — community-documented across React issue threads rather than
  any spec, but consistently reproducible. Apply sanitization/uppercase/masking on
  `compositionend` or blur, not mid-composition.
- **Search-as-you-type**: each composition update fires `input` events with partial
  syllables (ㅅ → 스 → 슽 → 스킬). Debounce alone still queries garbage intermediate
  states; gate dispatch on `compositionend` (plus a normal path for non-IME input).
- Browser order differences exist between engines for `compositionend` vs the final
  `input` event — never assume one fixed sequence; branch on `event.isComposing`
  rather than event order.

## Counting and slicing

- `String.length` counts UTF-16 code units, not user-perceived characters. Hangul
  syllables in NFC are 1 unit, but decomposed jamo (NFD — e.g. file names from
  macOS HFS+-era tooling, which stored strings decomposed) are 2-3; emoji are 2+.
  For user-facing length limits and cursor-safe slicing use `Intl.Segmenter`
  (grapheme granularity) and normalize (`.normalize('NFC')`) before comparing
  strings from mixed sources.

## Sources

- MDN: `word-break`, `line-break`, `overflow-wrap`, CompositionEvent,
  `KeyboardEvent.isComposing`, `String.prototype.normalize`, `Intl.Segmenter`
- W3C UAX #14 (Unicode Line Breaking Algorithm); W3C klreq (Korean Layout Requirements)
- UI Events spec — `keyCode` 229 / IME composition processing
