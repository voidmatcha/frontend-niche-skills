# Copy: plurals, sentences, formatting

Grammar and number/date/currency conventions vary per locale — English-only string handling mistranslates or misformats.

## Plurals are not singular-vs-plural

**`count === 1 ? "item" : "items"` is an English-only assumption** — Unicode CLDR defines six plural categories (`zero`/`one`/`two`/`few`/`many`/`other`); languages use different subsets, and Arabic uses all six. Category names are mnemonics (CLDR "minimal pairs"), not literal meanings. Never branch on the number yourself — select the form at runtime with `Intl.PluralRules` or an ICU `plural` message:

```js
new Intl.PluralRules('ru').select(21);   // 'one'  — not what English intuition says
new Intl.PluralRules('ar').select(0);    // 'zero'
// ICU: {count, plural, =0 {No files} one {# file} other {# files}}
```

`=0`/`=1` select exact values; `#` is the formatted number; the `other` arm is mandatory — let the translator, not your code, decide which arms a language needs.

## Don't build sentences by concatenation

**`"You have " + count + " new " + type` is untranslatable** — word order, gender agreement, and article forms differ per language. Use one full-sentence template with named placeholders so the translator can move them: OpenStack's I18n guide shows `"The %(name)s image is too large for this volume."` becoming `"L'image %(name)s est trop volumineuse…"`.

- **Interpolation alone doesn't fix words that inflect** (German: "the" before `{paymentType}` changes with the noun's gender) — use an ICU `select` arm: `{gender, select, female {her} male {his} other {their}} reservation`.
- Placeholders carry **values** (numbers, names, dates), never sentence fragments or inflecting adjectives. If truly unavoidable, ship rich translator context describing the full sentence.

## Numbers, dates, currency — never hardcode the format

**Format with `Intl`, keyed by the user's locale** — separators, grouping, currency symbol position/spacing, date order, and calendar all vary; never string-build or prepend a hardcoded `$`.

- **Digits**: `1,234.56` (en) vs `1.234,56` (de) vs `١٬٢٣٤٫٥٦` (`ar-EG`; bare `ar` follows the CLDR default numbering system the runtime ships, which in recent data is Latin `1,234.56` — pin a Mashriq locale like `ar-EG` or the `ar-u-nu-arab` extension when Arabic-Indic digits are required); grouping isn't always every 3 digits (India: `1,23,456`).
- **Dates**: order and calendar vary (`6/14/2026` en-US vs `14.6.2026` de-DE; some locales default to non-Gregorian calendars) — format with `Intl.DateTimeFormat` keyed by the user's locale, never hand-assemble `MM/DD/YYYY`.
- **Currency**: `currency` is a required **ISO 4217** code; symbol vs code vs name is `currencyDisplay`.
- `Intl` formats but **does not parse** (ECMA-402 omits parsing by design) — parsing user-entered numbers/dates needs a separate locale-aware path.

## Sources

- Unicode CLDR — [Plural Rules spec](https://cldr.unicode.org/index/cldr-spec/plural-rules); [Language Plural Rules chart](https://www.unicode.org/cldr/charts/48/supplemental/language_plural_rules.html) (six categories; names are mnemonics; per-language subsets)
- Unicode CLDR — [Numbering Systems](https://cldr.unicode.org/translation/core-data/numbering-systems) ("The default numbering system for a locale is the numbering system that is normally used to represent numbers in that locale"; `arab` is Arabic-Indic digits, `latn` is Latin digits); CLDR 48 locale data (cldr-json `48.0.0` commit): [`ar`](https://github.com/unicode-org/cldr-json/blob/4d06be52b51bb2f75688d0abe55c52a66afed790/cldr-json/cldr-numbers-full/main/ar/numbers.json) has `"defaultNumberingSystem": "latn"` with `native` `arab`, and [`ar-EG`](https://github.com/unicode-org/cldr-json/blob/4d06be52b51bb2f75688d0abe55c52a66afed790/cldr-json/cldr-numbers-full/main/ar-EG/numbers.json) has `"defaultNumberingSystem": "arab"`
- ICU User Guide — [Formatting Messages](https://unicode-org.github.io/icu/userguide/format_parse/messages/) (`plural`, `select`, `=0`, `#`, mandatory `other`; `select` for gender)
- W3C i18n — [Working with Composite Messages](https://www.w3.org/International/articles/composite-messages/) (translators must be able to reorder message parts: "It must be possible to reorder variables in sentence-like arrangements and reposition them in any way relative to the text"; articles and adjectives change with "the gender and number of the subject")
- OpenStack — [I18n/TranslatableStrings](https://wiki.openstack.org/wiki/I18n/TranslatableStrings) (the "image is too large for this volume" reorderable-placeholder example)
- W3C i18n — [ECMAScript Internationalization API guide](https://www.w3.org/International/articles/intl/index); ECMA-402 ([spec](https://tc39.es/ecma402/)); MDN [`Intl.NumberFormat`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/NumberFormat), [`Intl.DateTimeFormat`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/DateTimeFormat), [`Intl.PluralRules`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/PluralRules)
