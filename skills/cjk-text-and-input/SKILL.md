---
name: cjk-text-and-input
description: "Use when CJK (Korean, Japanese, Chinese) line-breaking, IME composition, Enter/keyCode 229 behavior, or grapheme counting is failing — mid-word line breaks in Korean, word-break/keep-all/line-break decisions, IME composition breaking controlled inputs, Enter firing during composition, duplicate keydown with keyCode 229, or string length counting Hangul wrong. East-Asian glyph-rendering & IME-input scope; for translation length, plurals, RTL, and Intl number/date formatting see i18n-copy-and-layout."
---

# CJK text & IME input

Two families of bugs that English-only testing never surfaces: **line breaking** (CJK text wraps differently) and **IME composition** (characters are composed across multiple keystrokes, so key events lie).

This skill is East-Asian glyph rendering + input. For the broader multi-language copy layer — text expansion breaking layout, CLDR plural categories, `Intl` number/date/currency formatting, RTL and `lang`/`dir` markup — use **i18n-copy-and-layout**.

## Line breaking

- East Asian text lines can break **between almost any two characters** by default (UAX #14: ideographs are class ID, Hangul syllables and jamo have their own H2/H3/JL/JV/JT classes, and UAX #14 notes Korean uses both styles — per-syllable breaking for justified text, space-based breaking for ragged, non-justified text) — in CSS, English-style word integrity for Korean is opt-in via `word-break: keep-all`, not the default.
- **Korean**: `word-break: keep-all` prevents intra-word breaks for CJK text so space-separated Korean words wrap as units (MDN: "Word breaks should not be used for Chinese/Japanese/Korean (CJK) text"). Pair with `overflow-wrap: break-word` as the escape hatch for long unbreakable tokens (URLs). Don't apply `keep-all` to Japanese or Chinese running text: those languages don't separate words with spaces, and CSS Text says that in this style "sequences of CJK characters do not break", so a whole sentence can become one unbreakable run.
- `word-break: break-all` solves the opposite problem — inserting breaks between any two characters of **non-CJK** text to prevent overflow (CJK behavior is unchanged by it, per MDN); don't apply it to body text in mixed-language UIs.
- `line-break: strict|loose` tunes Japanese/Chinese punctuation-adjacent breaking (kinsoku); it does not control Korean word integrity — that's `keep-all`.
- **Japanese phrase-aware wrapping**: Japanese breaks between characters by default. `word-break: auto-phrase` (MDN marks it experimental) behaves like `normal` but runs language-specific analysis so breaks avoid "the middle of natural phrases"; treat it as progressive enhancement and check current support before relying on it.
- Headlines/buttons: test with real Korean copy — label widths differ wildly from English and mid-word breaks read as typos to native speakers. W3C *klreq* (Korean Layout Requirements) is the canonical reference for Korean typography rules.

## IME composition (the part that breaks controlled inputs)

- IMEs compose text across keystrokes; the DOM fires `compositionstart` → `compositionupdate`* → `compositionend` (MDN CompositionEvent).
- **During composition, key events are unreliable for shortcuts**: `keydown` fires with `KeyboardEvent.isComposing === true` and `keyCode 229` (UI Events spec documents 229 as the IME-processing code). `isComposing` alone is not enough: MDN notes that `compositionend` may fire before the `keydown` of the key that closes the IME, so that event has `isComposing === false` while `keyCode` is still 229. Safari has shipped exactly this order for the IME-committing Enter (mdn/browser-compat-data#29998; a WebKit fix existed only behind an unstable flag when that issue was discussed in July 2026), so the 229 check is load-bearing, not legacy. The classic bug: pressing Enter to commit the IME buffer ALSO triggers the form's Enter handler — submitting half-composed text. Guard:

  ```js
  input.addEventListener('keydown', (e) => {
    if (e.isComposing || e.keyCode === 229) return; // IME is composing — not a command
    if (e.key === 'Enter') submit();
  });
  ```

- **Controlled inputs (React etc.)**: transforming/filtering `value` on every change while `isComposing` breaks the composition buffer (characters duplicate or split, e.g. 한글 자모 분리) — community-documented in React issue threads (react/react#3926, `onChange` firing before composition ends, still open when checked 2026-09-25; #8683 on controlled inputs) rather than any spec, but consistently reproducible. Apply sanitization/uppercase/masking on `compositionend` or blur, not mid-composition.
- **Search-as-you-type**: each composition update fires `input` events with partial syllables (ㅅ → 스 → 슼 → 스키 → 스킬). Debounce alone still queries garbage intermediate states; gate dispatch on `compositionend` (plus a normal path for non-IME input).
- Browser order differences exist between engines for `compositionend` vs the surrounding `keydown`/`input` events (MDN `keydown`: `compositionstart` may fire after `keydown`, and `compositionend` before it) — never assume one fixed sequence; branch on `event.isComposing` *plus* the `keyCode === 229` check rather than on event order.

## Counting and slicing

- `String.length` counts UTF-16 code units, not user-perceived characters. Hangul syllables in NFC are 1 unit, but decomposed jamo are 2-3 (NFD; also file names from macOS HFS+-era tooling — HFS+ stored names in a frozen canonical decomposition similar to, but not identical to, standard NFD); emoji are 2+. For user-facing length limits and cursor-safe slicing use `Intl.Segmenter` (grapheme granularity) and normalize (`.normalize('NFC')`) before comparing strings from mixed sources. Feature-detect `Intl.Segmenter`; for older WebViews or browsers, fall back to a tested grapheme-splitter library or a conservative "validate after input, do not slice mid-string" policy rather than pretending `String.length` is a character count.

## PR-worthiness gate

Require a real CJK string or IME sequence and a user-visible failure: a broken composition buffer, premature shortcut/submit, incorrect grapheme limit, or layout that makes actual copy unreadable. Add the smallest native-input or rendered-text regression.

Reject weak findings: `keyCode === 229` used only as a compatibility guard (say what would change that verdict: a real composition sequence where Enter still submits partial text, or a supported browser or WebView where the guard misfires), `String.length` on protocol bytes or internal identifiers, a generic narrow container with no CJK reproduction, or translation expansion that belongs to `i18n-copy-and-layout`. Results that flicker between older and newer queries, or a request per keystroke with no cancellation, are async ordering, not composition: route raw fetch-in-effect races to `async-effect-race-contracts` (or `frontend-data-fetching-cache-contracts` when a data library owns the read); this skill keeps only when composition input should trigger the query.

## Output shape

Report the language/input method, composition or layout sequence, event and rendered evidence, smallest guard/style/segmentation fix, browser or WebView matrix, and the regression that uses real CJK text.

## Sources

- MDN `word-break`: <https://developer.mozilla.org/en-US/docs/Web/CSS/word-break>
- CSS Text Module Level 3, `word-break: keep-all` ("implicit soft wrap opportunities between typographic letter units … are suppressed"; "In this style, sequences of CJK characters do not break"): <https://drafts.csswg.org/css-text-3/#valdef-word-break-keep-all>
- MDN `line-break`: <https://developer.mozilla.org/en-US/docs/Web/CSS/line-break>
- MDN `overflow-wrap`: <https://developer.mozilla.org/en-US/docs/Web/CSS/overflow-wrap>
- MDN `CompositionEvent`: <https://developer.mozilla.org/en-US/docs/Web/API/CompositionEvent>
- MDN `KeyboardEvent.isComposing`: <https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent/isComposing>
- MDN `keydown` event ("compositionend may fire before keydown when typing the last character that closes the IME … KeyboardEvent.keyCode is still 229 in these cases, so it's still advisable to check keyCode as well"): <https://developer.mozilla.org/en-US/docs/Web/API/Element/keydown_event>
- mdn/browser-compat-data#29998, Safari `isComposing` event-order bug (Enter that accepts IME input is sent with `isComposing === false` because `keydown` arrives after `compositionend`; WebKit fix behind a flag still marked unstable in the July 2026 discussion; checked 2026-09-24): <https://github.com/mdn/browser-compat-data/issues/29998>
- react/react#3926 (formerly facebook/react), "Change event fires extra times before IME composition ends" (open, checked 2026-09-25): <https://github.com/react/react/issues/3926>
- react/react#8683, "Composition Events(Chinese, Japanese IME) problem in controlled components(input, textarea)": <https://github.com/react/react/issues/8683>
- Unicode Standard Annex #14, Unicode Line Breaking Algorithm (Korean: "When Korean text is justified, the second style is commonly used … when ragged margins are used, the Western style (relying on spaces) is commonly used"): <https://www.unicode.org/reports/tr14/>
- W3C Korean Layout Requirements: <https://www.w3.org/TR/klreq/>
- Apple Technical Note TN1150, HFS Plus Volume Format ("HFS Plus stores strings fully decomposed and in canonical order"; its decomposition "cannot evolve because such evolution would invalidate existing HFS Plus volumes", and U+2000–U+2FFF and CJK compatibility ideographs U+F900–U+FAFF are left undecomposed): <https://developer.apple.com/library/archive/technotes/tn/tn1150.html>
- UI Events spec, keyCode 229 / IME composition processing: <https://www.w3.org/TR/uievents/#determine-keydown-keyup-keyCode>
