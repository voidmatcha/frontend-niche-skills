# Copy: plurals, sentences, formatting

The words and values themselves. Grammar and number/date/currency conventions vary per
locale — English-only string handling mistranslates or misformats.

## Plurals are not singular-vs-plural

`count === 1 ? "item" : "items"` is an English-only assumption. Unicode CLDR defines
**six** plural categories — `zero`, `one`, `two`, `few`, `many`, `other` — and languages
use different subsets:

- English: `one`, `other`. CJK (Japanese, Korean, Chinese): `other` only (no count
  agreement). Russian/Polish: `one`, `few`, `many`, `other` (by last digits).
  **Arabic: all six.** `other` is the only category guaranteed to exist.
- The category names are **mnemonics, not literal** — selection is defined by which
  numbers force a phrase change (CLDR "minimal pairs"), not by the obvious meaning of
  "two"/"few". Don't reason about them from the English label.
- **Never branch on the number yourself.** Select the form at runtime with
  `Intl.PluralRules` (or an ICU `plural` message that pulls the same CLDR data):

  ```js
  new Intl.PluralRules('ru').select(21);   // 'one'  — not what English intuition says
  new Intl.PluralRules('ar').select(0);    // 'zero'
  // ICU MessageFormat: the translator supplies the right set of forms per locale
  // {count, plural, =0 {No files} one {# file} other {# files}}
  ```

  `=0`/`=1` are exact-value selectors; `#` is the formatted number; the `other` arm is
  mandatory. The set of arms a translator needs differs per language — let the message
  format carry that, don't hardcode two branches.

## Don't build sentences by concatenation

`"You have " + count + " new " + type` is untranslatable: word order, gender agreement,
and article forms differ per language, and the translator can't move the pieces.

- **Use one full-sentence template with named placeholders** so the translator can
  reorder the variable to wherever the target grammar needs it. OpenStack's I18n guide
  gives a concrete example: `"The %(name)s image is too large for this volume."` becomes
  `"L'image %(name)s est trop volumineuse…"` — the placeholder moved. Concatenation makes
  that impossible.
- **Interpolation alone still isn't enough** for words that inflect. Substituting a noun
  doesn't fix the article/adjective around it (German: the word for "the" before
  `{paymentType}` changes with the noun's gender). For gendered/variant text use an ICU
  `select` arm rather than gluing a chosen word in:

  ```
  {gender, select, female {her} male {his} other {their}} reservation
  ```

- Placeholders are for **values** (numbers, names, dates) — not for several words of a
  sentence, and not for adjectives whose form depends on the noun. If concatenation is
  truly unavoidable, ship rich translator context describing the full sentence.

## Numbers, dates, currency — never hardcode the format

Format with `Intl`, keyed by the user's locale; don't string-build or hardcode symbols.

- **Decimal & grouping separators are locale-specific**: `1,234.56` (en) vs `1.234,56`
  (de) vs `١٬٢٣٤٫٥٦` (ar); grouping isn't always every 3 digits (India: `1,23,456`).
  Use `Intl.NumberFormat`.
- **Currency**: `Intl.NumberFormat(locale, {style:'currency', currency:'EUR'})` — the
  `currency` is a required **ISO 4217** code; symbol vs code vs name is `currencyDisplay`;
  symbol *position* and spacing are locale-dependent (`$123.46` vs `123,46 €`). Don't
  prepend a hardcoded `$`.
- **Dates**: `Intl.DateTimeFormat` — order (MM/DD vs DD.MM.YYYY), month as number vs
  word, and calendar all vary. Don't template `${m}/${d}/${y}`.
- `Intl` formats but **does not parse** (ECMA-402 omits parsing by design) — for parsing
  user-entered numbers/dates you need a separate locale-aware path.

## Sources

- Unicode CLDR — [Plural Rules spec](https://cldr.unicode.org/index/cldr-spec/plural-rules);
  [Language Plural Rules chart](https://www.unicode.org/cldr/charts/48/supplemental/language_plural_rules.html)
  (six categories; names are mnemonics; per-language subsets)
- ICU User Guide — [Formatting Messages](https://unicode-org.github.io/icu/userguide/format_parse/messages/)
  (`plural`, `select`, `=0`, `#`, mandatory `other`; `select` for gender)
- W3C i18n — best practices on not concatenating (full-sentence templates so translators
  can reorder; gender/article failure modes), echoed across localization tooling
- OpenStack — [I18n/TranslatableStrings](https://wiki.openstack.org/wiki/I18n/TranslatableStrings)
  (the "image is too large for this volume" reorderable-placeholder example)
- W3C i18n — [ECMAScript Internationalization API guide](https://www.w3.org/International/articles/intl/index);
  ECMA-402 ([spec](https://tc39.es/ecma402/)); MDN
  [`Intl.NumberFormat`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/NumberFormat),
  [`Intl.PluralRules`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/PluralRules)
