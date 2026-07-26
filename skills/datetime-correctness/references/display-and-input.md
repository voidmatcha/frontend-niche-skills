# Display & input

## Contents

- [Pin `Intl.DateTimeFormat`'s `timeZone`](#pin-intldatetimeformats-timezone)
- [`datetime-local` / `date` / `time` inputs are floating, zoneless](#datetime-local--date--time-inputs-are-floating-zoneless)
- [Rendering on the server and the client (SSR)](#rendering-on-the-server-and-the-client-ssr)
- [Find these in your codebase](#find-these-in-your-codebase)
- [Sources](#sources)

Showing a time and reading one back from a form are the two places a correct instant gets
silently re-zoned. Both hinge on one fact: **the runtime's ambient time zone is not the
user's intent.**

## Pin `Intl.DateTimeFormat`'s `timeZone`

`Intl.DateTimeFormat` (and `Date#toLocaleString`, which uses it) defaults the `timeZone`
option to the **runtime's** zone. So the same instant renders as a different clock on the
server, in CI, and on each user's device:

```js
const instant = new Date("2026-06-14T00:30:00Z");
instant.toLocaleString("en-US");                              // depends on the runtime zone
new Intl.DateTimeFormat("en-US", {
  timeZone: "Asia/Seoul",                                     // pin it explicitly
  dateStyle: "medium", timeStyle: "short",
}).format(instant);                                            // always Seoul wall time
```

- Always pass an explicit IANA `timeZone` for user-facing times — the user's stored
  preference, the event's zone, or `"UTC"`. Don't rely on the default.
- To read the runtime's actual zone (e.g. to store a default), use
  `Intl.DateTimeFormat().resolvedOptions().timeZone`.
- When you need the individual pieces (to build a custom layout, or feed another control),
  use `formatToParts()` rather than slicing the formatted string — the order and separators
  are locale-dependent and not safe to parse back.

```js
const parts = new Intl.DateTimeFormat("en-US", { timeZone: "Asia/Seoul", hour: "2-digit",
  minute: "2-digit" }).formatToParts(instant);
const hour = parts.find(p => p.type === "hour").value;
```

(Which format to choose — `dateStyle`, 12h vs 24h, currency-adjacent number formatting — is
**i18n-copy-and-layout**'s scope. This file is only about *which instant and which zone*.)

## `datetime-local` / `date` / `time` inputs are floating, zoneless

The value of `<input type="datetime-local">` is a string like `"2026-06-14T09:00"` that
represents a **local date and time with no time-zone information** (MDN). Likewise
`type="date"` is a date-only string and `type="time"` is a clock-only string. The browser
does not know, and does not tell you, which zone the user meant.

```html
<input type="datetime-local" value="2026-06-14T09:00">
```

```js
// WRONG: new Date() parses a no-offset date-time as the RUNTIME's local zone,
// which may not be the zone the value was meant for.
const wrong = new Date(input.value);

// Right: pair the floating value with the INTENDED zone explicitly.
const zdt = Temporal.PlainDateTime
  .from(input.value)                       // floating, no zone
  .toZonedDateTime("Asia/Seoul");          // now an instant in the intended zone
const instant = zdt.toInstant();           // store this
```

- On read: combine the floating value with the zone you actually mean (the user's profile
  zone, the venue's zone, etc.), then convert to an instant for storage.
- On write: convert your stored instant **into the same intended zone**, then emit the
  `YYYY-MM-DDTHH:mm` (no offset) string the input expects. Round-tripping through the
  runtime zone instead will drift the value for any user not in that zone.
- Note the opposite default for the **date-only** `type="date"` value (`"2026-06-14"`):
  `new Date(value)` parses *that* as UTC midnight (the off-by-one in
  [SKILL.md](../SKILL.md) item 2), whereas the no-offset date-*time* `datetime-local` value
  in the `WRONG` example above parses as local. Keep date-only values date-only either way.
- A spring-forward gap means a user can't pick a non-existent local time; a fall-back
  overlap means a picked time is ambiguous — resolve it with Temporal's `disambiguation`
  option rather than guessing.

## Rendering on the server and the client (SSR)

A server-rendered page that formats a time in the ambient zone (or calls `new Date()` /
`Date.now()` during render) is a classic hydration-mismatch trigger — that mechanism and its
containment are **ssr-hydration-mismatch**'s scope. The datetime-specific fix:

- Compute the **instant** on the server, serialize it as epoch/ISO-with-offset, and send
  that — not a pre-formatted local string.
- Format on **one fixed, explicit zone** on both sides (a pinned `timeZone`), or defer
  user-local formatting to a client-only effect after hydration.

## Find these in your codebase

A grep is a fast first pass — every hit is a review point, not an automatic bug:

```sh
# Locale formatting with no pinned timeZone — renders the runtime's zone
rg -n 'toLocaleString|toLocaleDateString|toLocaleTimeString|DateTimeFormat\(' src/ \
  | rg -v 'timeZone'
# Reading a datetime-local/date/time field straight into Date (drops the intended zone)
rg -n 'new Date\([^)]*\.value' src/
```

## Sources

- MDN — [`Intl.DateTimeFormat`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/DateTimeFormat/DateTimeFormat)
  (`timeZone` option defaults to the runtime's zone; IANA names)
- MDN — [`Intl.DateTimeFormat.prototype.formatToParts()`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/DateTimeFormat/formatToParts)
- MDN — [`resolvedOptions()`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/DateTimeFormat/resolvedOptions)
  (read the runtime's resolved `timeZone`)
- MDN — [`<input type="datetime-local">`](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/input/datetime-local)
  (value is a local date-time string with no time-zone information)
- MDN — [`<input type="date">`](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/input/date)
  / [`type="time"`](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/input/time)
- MDN — [`Temporal.PlainDateTime#toZonedDateTime`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Temporal/PlainDateTime/toZonedDateTime)
