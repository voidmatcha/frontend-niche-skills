# Layout: expansion & direction

## Contents

- [Text expands](#text-expands)
- [RTL & language markup](#rtl--language-markup)
- [RTL retrofit in a codebase that already ships an RTL locale](#rtl-retrofit-in-a-codebase-that-already-ships-an-rtl-locale)
- [Sources](#sources)

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

## RTL retrofit in a codebase that already ships an RTL locale

Setting `dir` and using logical properties is the greenfield answer. A codebase
that already shipped Arabic or Hebrew usually did it a different way, with
per-language CSS overrides that mirror each component by hand, and the questions
there are different.

- **Check whether the locale ships but `dir` never does.** The signal is an RTL
  locale bundle in the build alongside no `dir` anywhere in the rendered markup.
  Mirroring done purely in CSS can look right while the bidi algorithm still runs
  with an LTR base, so mixed-direction runs, trailing punctuation, and text field
  editing resolve wrong even on a screen that visually mirrors.
- **CSS `direction` is not a substitute for the `dir` attribute.** Direction is
  normally defined in the document rather than through the `direction` property,
  and the two do not behave identically: `dir` inherits from table columns into
  cells, `direction` does not, because CSS inheritance follows the document tree.
  Styles can also fail to load or be overridden; markup travels with the content.
- **Language-scoped override blocks fail by omission.** A `[lang="ar"] .card { ... }`
  block, or the preprocessor mixin equivalent, mirrors only the components someone
  remembered to write a block for. A new component inherits its physical
  properties and renders unmirrored with no error, no failing build, and no
  console warning. Nothing surfaces it except rendering that locale.
- **Count before proposing a migration.** Physical `margin-left`/`margin-right`,
  `padding-left`/`padding-right`, bare `left:`/`right:` offsets, and
  `text-align: left`/`right` against existing logical-property usage. The ratio is
  the difference between a bounded edit and a rewrite, and it decides whether a
  full conversion is even the right recommendation.
- **Order the retrofit by what pays first.** Set `dir` on the document root first:
  it fixes bidi resolution for text, form fields, and selection regardless of what
  the stylesheet does. Then convert only the components that genuinely mirror:
  containers, icon-adjacent spacing, positioned overlays. Symmetric spacing does
  not need touching, and logical properties are the destination rather than a
  prerequisite.
- **Watch for `direction` used as a layout trick.** Setting `direction: rtl` to
  push an ellipsis to the start of a string, or to truncate from the other end,
  borrows a text-direction mechanism for a visual effect. It changes bidi
  resolution inside that element, reordering punctuation and embedded LTR runs,
  and it collides with a real RTL retrofit later.

The regression that catches this class is rendering in the RTL locale itself.
A snapshot taken in English exercises none of the mirroring paths.

## Sources

- W3C i18n — [Text size in translation](https://www.w3.org/International/articles/article-text-size.en.html)
  (IBM expansion table, compound nouns, character/line height); [Authoring HTML: text
  expansion](https://www.w3.org/International/techniques/authoring-html#textexpansion)
- W3C i18n — [Handling RTL scripts](https://www.w3.org/International/geo/html-tech/tech-bidi.html);
  [Declaring language in HTML](https://www.w3.org/International/questions/qa-html-language-declarations)
  (`lang` ≠ `dir`; direction not derivable from language; `dir` as markup; font selection)
- MDN — [CSS logical properties for margins, borders, padding](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_logical_properties_and_values)
- W3C i18n — [Structural markup and right-to-left text in HTML](https://www.w3.org/International/questions/qa-html-dir)
  (where `dir` belongs, and why inline markup is not enough)
- MDN — [`dir` global attribute](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Global_attributes/dir);
  [CSS `direction`](https://developer.mozilla.org/en-US/docs/Web/CSS/direction)
  (direction is normally defined in the document rather than via the property;
  `dir` inherits from table columns into cells while `direction` does not)
