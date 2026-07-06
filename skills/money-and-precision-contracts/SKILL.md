---
name: money-and-precision-contracts
description: "Use when money or quantity arithmetic runs in the browser and the result is off by a fraction or a penny — a total that shows 0.30000000000000004 or $19.999999999999996, summed line items or tax that don't reconcile, `toFixed`/`Math.round` producing surprising rounding (`(1.005).toFixed(2)` is `\"1.00\"`), a price stored as a float, `parseFloat`/`Number` mangling a localized amount (`\"1.234,56\"` → 1.234 or NaN), or amounts that overflow past exact integer range. Arithmetic/precision/storage scope; for which locale format to display (grouping, currency symbol, decimal mark) see i18n-copy-and-layout, for timezone/DST value correctness see the sibling datetime-correctness, and for numeric input field validity/error state see js-form-validation-contracts."
---

# Money and precision contracts

In the browser, money is not a `number`: IEEE-754 doubles can't represent most decimal fractions,
so amounts drift and rounding disagrees across `toFixed`, `Math.round`, and `Intl`. Core rule —
compute and store in **integer minor units or a decimal type**, round **once** with an
**explicit** mode, and let `Intl.NumberFormat` touch the value only at the display edge.

For *which* locale format to show (digit grouping, currency symbol, `1,234.56` vs `1.234,56`) use
**i18n-copy-and-layout** — it owns display formatting and notes `Intl` but does not own the math.
For the same "correct on a round-number/UTC dev box" trap in date/time values, see the sibling
value-correctness skill **datetime-correctness**. For the numeric *field's* validity lifecycle,
error, and submit state, use **js-form-validation-contracts**; this skill owns what the parsed
value means, not the field UI.

## Checklist (lead with the trap; details in references/)

→ [precision-contracts](./references/precision-contracts.md)

1. **`0.1 + 0.2` is `0.30000000000000004` — don't do money math in binary floats.** Doubles can't
   hold most decimals, and the error compounds as you sum line items. Store and compute in integer
   minor units (cents: `2999`, not `29.99`) or a decimal library (decimal.js / big.js / Dinero.js).
2. **`toFixed` rounds the stored binary value, not your decimal literal.** `(1.005).toFixed(2)` is
   `"1.00"` and `(2.55).toFixed(1)` is `"2.5"` — neither reliable half-up nor banker's rounding.
   `Math.round(x*100)/100` has the same flaw. Round on the integer/decimal value, not the float.
3. **The three rounding surfaces disagree — choose a mode on purpose.** `Math.round` ties toward
   **+∞** (`Math.round(-2.5) === -2`); `Intl.NumberFormat`'s default `roundingMode` is
   `"halfExpand"` (ties **away from 0**); accounting usually wants `"halfEven"` (banker's). State
   which the money math uses and set `roundingMode` explicitly rather than inheriting a default.
4. **Sum and tax on integers, and round once.** Rounding each line then summing vs summing then
   rounding once give different totals (penny drift). Splitting a total (installments, bill split)
   must distribute the remainder so parts sum back to the whole — use an allocate helper, not
   `total / n` rounded per part.
5. **Integer minor units have a ceiling, and 2 digits isn't universal.** Cents in a `number` are
   exact only to `Number.MAX_SAFE_INTEGER` (2^53−1, ≈ $90T at 2 dp); beyond that use `BigInt` or a
   bigint-backed decimal. JPY/KRW have 0 minor digits, BHD/KWD have 3 — hard-coded `* 100` /
   `.toFixed(2)` is wrong for them.
6. **`Intl.NumberFormat` formats but does not parse.** There is no standard reverse API, and
   `Number("1.234,56")` is `NaN` while `parseFloat("1.234,56")` is `1.234`. To read user-typed
   localized amounts, derive the locale's group/decimal separators from `formatToParts`, strip and
   normalize them, then convert — or constrain input to one canonical format.
7. **Format at the edge, from the exact value.** Convert the integer/decimal to a display string
   with `Intl.NumberFormat` only at render; never round-trip money back through a float afterward.

## Defect patterns

| Pattern | Why it matters | Better direction |
| --- | --- | --- |
| Prices held as `number` and added (`a + b`) | Float drift surfaces in totals (`19.999999999999996`) and reconciliation. | Integer minor units or a decimal type; floats only for display. |
| `(x).toFixed(2)` / `Math.round(x*100)/100` as the rounding rule | Rounds a binary approximation; half-way cases go the "wrong" way. | Round on the integer/decimal value with an explicit mode. |
| Rounding mode never stated | `Math.round` / `Intl` / banker's disagree on ties; totals differ by a cent. | Pick and set `roundingMode`; test a tie case. |
| Per-line round then sum (or vice versa) with no decision | Penny drift between total and sum of parts. | Decide the order, round once, test both paths. |
| `Number(userInput)` / `parseFloat` on a localized amount | `"1.234,56"` becomes `1.234` or `NaN`; silent wrong charge. | Parse via `formatToParts`-derived separators or a canonical input. |
| `* 100` / `toFixed(2)` assuming 2 minor digits | Wrong for JPY (0) and BHD (3); off by 100x. | Use the currency's ISO 4217 minor-unit digit count. |

## Quick probes

Use as leads, then trace the value from source to stored/displayed total:

```sh
rg -n '\.toFixed\(|Math\.round\([^)]*\*\s*100|/\s*100\b' src/ app/ packages/ 2>/dev/null
rg -n 'parseFloat\(|Number\(\s*[a-zA-Z_].*(value|input|amount|price)' src/ app/ packages/ 2>/dev/null
rg -n 'price|amount|total|subtotal|tax|discount' src/ app/ packages/ 2>/dev/null | rg -i 'number|float|parseFloat|\+|reduce'
rg -n 'Intl\.NumberFormat|roundingMode|dinero|decimal\.js|big\.js|currency' src/ app/ packages/ 2>/dev/null
```

## Boundary with sibling skills

- Use **money-and-precision-contracts** for the arithmetic/precision/rounding/storage contract:
  float drift, integer minor units vs decimal libraries, rounding mode, sum/tax/allocation order,
  minor-unit overflow, and parsing user-typed localized amounts.
- Use **i18n-copy-and-layout** for which locale format to *display* (grouping, currency symbol,
  decimal mark, `Intl` format options). Formatting display is i18n; this skill owns the math.
- Use **datetime-correctness** (sibling value-correctness skill) for timezone/DST/date-only value
  bugs — same class of dev-box-only trap, different value type.
- Use **js-form-validation-contracts** for the numeric input field's validity lifecycle, error
  display, and submit state; this skill owns the value's meaning once parsed, not the field UI.

## PR-worthiness gate

A finding is PR-worthy only when the imprecision reaches a stored, compared, or displayed money/
quantity value:

- Money computed or summed in binary floats where drift can change a total or a reconciliation.
- `toFixed`/`Math.round(x*100)/100` used as the rounding rule, or an unstated rounding mode on real
  currency where ties matter.
- Per-line vs total rounding order that produces penny drift, or a split that doesn't sum back.
- A localized amount parsed with `Number`/`parseFloat`, or `* 100`/`toFixed(2)` on a non-2-digit
  currency.

Reject weak findings: a lone float that never reaches a money output, integers/decimal library used
correctly end to end, pure display-format nits (→ **i18n-copy-and-layout**), or test fixtures only.

Minimal useful PR: move the computation to integer minor units or a decimal type, set an explicit
`roundingMode`, round once, and add a test with a known-drifty case (`0.1 + 0.2`, `(1.005).toFixed(2)`,
a de-DE `"1.234,56"` parse, or a 3-way split that must sum back).

## Output shape

Return compact findings:

- **Contract**: float-drift / rounding-mode / sum-order / minor-unit-overflow / localized-parse.
- **Evidence**: file/line and the value's path from source to total/display.
- **Risk**: wrong charge, unreconciled total, penny drift, overflow, or mis-parsed input.
- **Fix**: smallest change — minor-unit/decimal conversion, explicit `roundingMode`, round-once, or a `formatToParts` parser.
- **Verification**: a unit test on the drifty/tie/parse/split case above.

## Sources

- MDN, Numbers and strings (IEEE-754 float precision): <https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Numbers_and_strings>
- MDN, `Number.prototype.toFixed()` (rounds the stored binary value): <https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Number/toFixed>
- MDN, `Math.round()` (ties toward +∞): <https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Math/round>
- MDN, `Intl.NumberFormat()` constructor (`roundingMode` default `"halfExpand"`, currency minor-unit digits): <https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/NumberFormat/NumberFormat>
- MDN, `Intl.NumberFormat.prototype.formatToParts()` (derive locale separators to parse): <https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/NumberFormat/formatToParts>
- TC39 Decimal proposal (Stage 1, exact base-10 arithmetic): <https://github.com/tc39/proposal-decimal>
- Dinero.js v2 amount (integer minor units, `allocate`, bigint variant): <https://v2.dinerojs.com/docs/core-concepts/amount>
- decimal.js (arbitrary-precision Decimal type): <https://github.com/MikeMcl/decimal.js>
