# Layout: expansion & direction

The space copy lives in. Translated text changes length, height, and reading
direction — layouts measured once in English break on all three axes.

## Text expands

Translated text is usually **longer** than English, and the shorter the source string,
the larger the expansion — exactly the strings squeezed into buttons, tabs, and labels.
W3C publishes IBM's average expansion rates (English → European languages):

| English source length | Average expansion |
|-----------------------|-------------------|
| up to 10 chars | 200–300% |
| 11–20 | 180–200% |
| 21–30 | 160–180% |
| 31–50 | 140–160% |
| 51–70 | 131–140% |
| over 70 | 130% |

- **Design for reflow** — no fixed-width containers or tight single-line squeezes for
  copy; let text wrap and grow. A button sized to fit "Save" will clip "Speichern".
- **Compound nouns don't wrap** — German/Finnish/Dutch fuse phrases into one long word
  ("Input processing features" → "Eingabeverarbeitungsfunktionen") with no break
  opportunity, so it overflows narrow columns/tabs instead of wrapping.
- **Height, not just width** — many scripts (Thai, Arabic, Devanagari, CJK) need taller
  glyphs and more line spacing than Latin; fixed-height rows clip them even when the
  character count is equal or smaller. (This is *why* the Japanese-text-overflow class
  of bug appears in real apps.)
- **Test with real translated copy**, not Lorem Ipsum or English. Pseudo-localization
  (padding + accents) is a cheap stand-in to catch clipping before translations land.

## RTL & language markup

- **Set `lang` and `dir` on `<html>` — they're separate mechanisms.** `lang` drives
  language-aware rendering, screen-reader pronunciation, indexing, and font selection;
  `dir` gives the Unicode bidirectional algorithm its base direction. Conflating them is
  a documented mistake.
- **You cannot derive `dir` from `lang`.** Some languages use both RTL and LTR scripts
  (Azerbaijani), and BCP-47 suppresses the script subtag for languages like Hebrew — so
  the language tag alone doesn't tell you the direction. Set `dir` explicitly; it's
  *markup*, because the data may travel without its CSS.
- **Lay out with CSS logical properties**, not physical ones: `margin-inline-start`,
  `padding-inline`, `inset-inline-start`, `border-inline` map to the correct physical
  side per `dir`/`writing-mode`, so the UI mirrors automatically in Arabic/Hebrew.
  `margin-left` does not.
- Watch **`dir="ltr"` islands** inside RTL pages — email addresses, URLs, phone numbers,
  code — and ensure fonts cover every script you ship (font selection is more than
  first-in-the-stack).

## Sources

- W3C i18n — [Text size in translation](https://www.w3.org/International/articles/article-text-size.en.html)
  (IBM expansion table, compound nouns, character/line height); [Authoring HTML: text
  expansion](https://www.w3.org/International/techniques/authoring-html#textexpansion)
- W3C i18n — [Handling RTL scripts](https://www.w3.org/International/geo/html-tech/tech-bidi.html);
  [Declaring language in HTML](https://www.w3.org/International/questions/qa-html-language-declarations)
  (`lang` ≠ `dir`; direction not derivable from language; `dir` as markup; font selection)
- MDN — [CSS logical properties for margins, borders, padding](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_logical_properties_and_values)
