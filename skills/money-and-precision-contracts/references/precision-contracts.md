# Money & precision contracts reference

Use this reference only after `money-and-precision-contracts` triggers and the task computes,
rounds, sums, stores, or parses monetary or quantity values in the browser.

## Why floats break money

- JavaScript `number` is an IEEE-754 double. Most terminating decimals (0.1, 0.2, 0.20, 29.99)
  have no exact binary representation, so `0.1 + 0.2 === 0.30000000000000004` and the error
  accumulates as you sum line items. This is a representation limit, not a bug you can round away.
- Integer minor units (store `2999`, not `29.99`) are exact — as long as they stay within
  `Number.MAX_SAFE_INTEGER` (2^53 − 1 = 9007199254740991, ≈ $90T at 2 decimal places). Past that,
  addition silently loses the low bits; use `BigInt` or a bigint-backed decimal.
- Not every currency has 2 minor digits: JPY/KRW have 0, BHD/KWD/OMR have 3. Hard-coding `* 100`
  or `.toFixed(2)` is wrong for those. `Intl.NumberFormat` currency style pulls the digit count
  from the ISO 4217 minor-unit list (2 when unknown).

## The three rounding surfaces disagree

| Surface | Half-way behavior | Example |
| --- | --- | --- |
| `Math.round` | ties toward **+∞** | `Math.round(-2.5) === -2`, `Math.round(2.5) === 3` |
| `Number.prototype.toFixed` | rounds the **stored binary value**, no defined half rule | `(2.55).toFixed(1) === "2.5"`, `(1.005).toFixed(2) === "1.00"` |
| `Intl.NumberFormat` | `roundingMode` default `"halfExpand"` (ties **away from 0**) | `654321.987` → `"$654,321.99"` |
| accounting/banker's | `roundingMode: "halfEven"` (ties to nearest even) | not any JS default; opt in |

`toFixed` and `Math.round(x*100)/100` are not a reliable money-rounding rule because the input is
already a binary approximation. Round on integer minor units or a decimal type, and set the mode
explicitly.

## Sum, tax, and allocation order

- Rounding each line then summing vs summing then rounding once produce different totals (penny
  drift). Pick one order, document it, and test it.
- Splitting a total (invoice into installments, bill among people) must distribute the remainder
  so parts sum back to the whole — a naive `total / n` rounded per part loses or gains pennies.
  Dinero.js `allocate` and most decimal libs provide this.

## Parsing localized amounts

- `Intl.NumberFormat` **formats but does not parse** — there is no standard reverse API.
- `Number("1.234,56")` is `NaN`; `parseFloat("1.234,56")` is `1.234`. Grouping separators and
  comma decimal marks vary by locale, so `Number(userInput)`/`parseFloat` mis-reads foreign input.
- Derive the locale's group and decimal separators from `Intl.NumberFormat(...).formatToParts(...)`,
  strip/normalize them, then convert — or constrain input to a canonical, unambiguous format.

## Test shapes

- Drift: assert `0.1 + 0.2` handling, a 3+ line-item sum, and a running total match the
  integer/decimal result, not the float.
- Rounding: `1.005`, `2.55`, `-2.5`, and a `halfEven` vs `halfExpand` case round as the chosen mode.
- Minor units: an amount near `Number.MAX_SAFE_INTEGER`, plus a 0-digit (JPY) and 3-digit (BHD)
  currency.
- Parse: `"1.234,56"` (de-DE), `"1,234.56"` (en-US), and `"₩1,234"` normalize to the same value.
- Allocation: split 1000 minor units 3 ways sums back to exactly 1000.

## Official references

- MDN, Numbers and strings (IEEE-754 float precision): <https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Numbers_and_strings>
- MDN, `Number.prototype.toFixed()` (rounds the stored binary value): <https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Number/toFixed>
- MDN, `Math.round()` (ties toward +∞): <https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Math/round>
- MDN, `Number.MAX_SAFE_INTEGER`: <https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Number/MAX_SAFE_INTEGER>
- MDN, `Intl.NumberFormat()` constructor (`roundingMode` default `halfExpand`, currency minor-unit digits): <https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/NumberFormat/NumberFormat>
- MDN, `Intl.NumberFormat.prototype.formatToParts()` (derive locale separators): <https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/NumberFormat/formatToParts>
- TC39 Decimal proposal (Stage 1, exact decimal): <https://github.com/tc39/proposal-decimal>
- Dinero.js v2 amount (integer minor units, `allocate`, bigint variant): <https://v2.dinerojs.com/docs/core-concepts/amount>
- decimal.js (arbitrary-precision Decimal type): <https://github.com/MikeMcl/decimal.js>
