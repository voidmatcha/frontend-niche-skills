---
name: i18n-copy-and-layout
description: "Use when shipping UI copy in more than one language — text overflowing buttons/labels after translation, German/Finnish compound words too long to wrap, `count === 1 ? singular : plural` breaking in Russian/Arabic/Polish, sentences built by string concatenation mistranslating, hardcoded date/number/currency formats, or no RTL (Arabic/Hebrew) support. Excludes CJK glyph rendering & IME input — see cjk-text-and-input."
---

# i18n copy & layout

The expensive i18n bugs aren't missing translations — they're the **layout, grammar,
and formatting assumptions baked in while the app was English-only**, which surface only
when real translated copy lands. Core rule: treat copy as **variable-length,
variable-order, variable-form data**, never as fixed text measured once in English.
Two halves: **copy** (the words and values) and **layout** (the space they live in).

For East-Asian glyph rendering, line-breaking (`word-break: keep-all`), and IME
composition, use **cjk-text-and-input** — the two are deliberately split.

## Checklist (details in references/)

**Layout** → [layout](./references/layout.md)

1. No fixed-width or tight single-line containers for copy; design for reflow —
   translations run ~130–300% of the English length, and the *shortest* strings expand
   most.
2. Compound-noun languages (German/Finnish/Dutch) produce one long unbreakable word;
   leave room and don't rely on wrapping. Allow extra line height — Thai/Arabic/
   Devanagari/CJK glyphs are taller than Latin.
3. Set `lang` **and** `dir` on `<html>` — separate mechanisms; direction is not
   derivable from language, and `dir` is markup, not CSS-only.
4. Lay out with CSS logical properties (`margin-inline-start`, `inset-inline`), not
   `left`/`right`, so RTL mirrors automatically; watch `dir="ltr"` islands
   (email/URL/code).
5. Verify with real translated copy or pseudo-localization — never English/Lorem.

**Copy** → [copy](./references/copy.md)

6. Never `count === 1 ? singular : plural`. Select via `Intl.PluralRules` / ICU `plural`
   — CLDR has six categories (Arabic uses all; CJK only `other`).
7. Never concatenate sentence fragments. One full-sentence template + named placeholders
   so translators can reorder the variable.
8. Interpolation alone doesn't fix gender/article agreement — use ICU `select` for
   gendered/variant words.
9. Format numbers/dates/currency with `Intl` (locale separators, digit grouping, ISO
   4217 currency) — never hardcode `$`, `MM/DD/YYYY`, or `.`/`,`. `Intl` formats but
   does not parse.

## References

| File | Covers |
|------|--------|
| [layout](./references/layout.md) | Text expansion (W3C/IBM table), compound nouns, glyph height, RTL, `lang`/`dir`, CSS logical properties |
| [copy](./references/copy.md) | CLDR plural categories, `Intl.PluralRules`/ICU `plural`, no-concatenation + ICU `select`, `Intl` number/date/currency |

Sources are listed in each reference file.
