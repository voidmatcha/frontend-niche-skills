# Storage & computation

Decide, for every datetime value, which of two kinds it is — and never let the two mix:

- **Instant** — one point on the global timeline (a UTC/epoch moment). "When did this
  happen." Comparable and orderable across the world.
- **Date-only / wall-clock** — a calendar date or a clock reading with **no** zone
  (a birthday, a 09:00 store-opening rule, a `datetime-local` field). Not an instant until
  you pair it with a zone.

## Store instants as UTC/epoch (or RFC 3339 with an offset)

- Persist an instant as epoch milliseconds (`Date.now()` / `date.getTime()`) or as an
  RFC 3339 / ISO 8601 string carrying an explicit offset (`...Z` or `...+09:00`). Both pin
  the moment unambiguously.
- A wall-clock string with **no** offset (`"2026-06-14 09:00"`) is not an instant. Storing
  it loses the information needed to place it on the timeline, and whoever reads it later
  guesses a zone — usually the server's, which is wrong for the user.
- Keep a genuinely date-only value (a birthday, an invoice date) as a date-only string
  (`"2026-06-14"`) or a dedicated date-only type. Promoting it to an instant invents a time
  and a zone you don't have.

## The parsing trap: date-only is UTC, date-time-without-offset is local

`new Date(string)` / `Date.parse` apply **opposite** default zones depending on the shape of
the string. Per MDN: *"When the time zone offset is absent, date-only forms are interpreted
as a UTC time and date-time forms are interpreted as local time."*

```js
new Date("2026-06-14")        // date-only → 2026-06-14T00:00:00 UTC
new Date("2026-06-14T09:00")  // date-time, no offset → 09:00 LOCAL time
```

So in `America/Los_Angeles` (UTC−07:00 in June):

```js
new Date("2026-06-14").toLocaleDateString("en-US")  // "6/13/2026" — the day BEFORE
```

The date-only string became UTC midnight, which is still June 13 in the western hemisphere.
This is the classic "my date picker shows yesterday" bug. Fixes:

- Don't round-trip a date-only value through `new Date(...)` for display. Split the string
  (`"2026-06-14".split("-")`) or use `Temporal.PlainDate.from("2026-06-14")`, which stays
  date-only and never acquires a zone.
- If you need a specific local midnight as an instant, build it with explicit local parts
  (`new Date(2026, 5, 14)` — month is 0-based) or `Temporal.PlainDate#toZonedDateTime(tz)`.
- Only non-offset **date-time** strings are parsed as local; anything with `Z`/offset is an
  instant. Make the offset explicit in stored data so reads don't depend on this rule.

## A day is not 24 hours: DST gaps and overlaps

On DST-observing zones, a calendar day can be 23 or 25 hours, and a wall-clock time can be
missing or doubled:

- **Spring forward** (gap): clocks jump, e.g. 02:00 → 03:00, so **02:30 does not exist** that
  day. Constructing or expecting that local time is ambiguous.
- **Fall back** (overlap): clocks repeat, e.g. 02:00 → 01:00, so the **01:00 hour occurs
  twice** and "01:30" maps to two different instants.

Adding `24 * 60 * 60 * 1000` ms to get "the same time tomorrow" is therefore wrong across a
transition — you land an hour off. Do calendar arithmetic in a zone-aware way:

```js
// WRONG across a DST boundary:
const tomorrow = new Date(now.getTime() + 86_400_000);

// Right (Temporal): add a calendar day in a zone; DST is handled, and an
// impossible/ambiguous wall time is resolved by the `disambiguation` option.
const zdt = Temporal.Now.zonedDateTimeISO("America/New_York");
const tomorrow2 = zdt.add({ days: 1 });
```

"Start of day", "add one month", and "is this the same calendar date" are all calendar
operations — compute them on zoned/plain types, not on epoch millisecond arithmetic.

## Mapping the invariants onto Temporal

Temporal makes the instant-vs-wall-clock split a type distinction, so the traps above become
hard to express by accident:

- `Temporal.Instant` — an exact moment (epoch), no calendar/zone. Use for storage/ordering.
- `Temporal.ZonedDateTime` — an instant **plus** an IANA time zone and calendar; the only
  type that knows about DST. Use for "9am in Seoul on this date."
- `Temporal.PlainDate` / `PlainTime` / `PlainDateTime` — calendar/clock values with **no**
  zone; a `PlainDateTime` is not an instant until you call `.toZonedDateTime(timeZone)`.
- `Temporal.Now.instant()` / `Temporal.Now.zonedDateTimeISO(tz)` for the current moment.

Temporal objects are immutable and keep the instant/wall-clock split in the type system:
`Temporal.PlainDate.from` keeps only the date and **ignores** any time or offset in the
string (so it never silently produces an instant from a wall-clock value — but it does *not*
reject the extra parts), while `Temporal.ZonedDateTime.from` is the strict one — it requires
a bracketed `[Area/City]` zone and throws `RangeError` without it. Gap/overlap times resolve
via an explicit `disambiguation` option (`'compatible'` | `'earlier'` | `'later'` |
`'reject'`).
Where Temporal isn't available yet, a polyfill or Luxon / date-fns-tz can hold the same
discipline — the point is the distinction, not the library.

## Find these in your codebase

A grep is a fast first pass — every hit is a review point, not an automatic bug:

```sh
# Date-arithmetic by milliseconds — wrong across DST; prefer zone-aware calendar math
rg -n '\* *24 *\* *60 *\* *60 *\* *1000|86400000|getTime\(\) *[-+]' src/
# new Date(<string>) — check for date-only off-by-one and no-offset local parsing
rg -n 'new Date\((["'\''`])' src/
# Manual offset/zone assumptions
rg -n 'getTimezoneOffset|setHours\(0, *0, *0|UTC\+|GMT[+-]' src/
```

## Sources

- MDN — [`Date.parse()`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Date/parse)
  ("date-only forms are interpreted as a UTC time and date-time forms are interpreted as
  local time"; non-standard string parsing is implementation-dependent)
- MDN — [`Date()` constructor](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Date/Date)
  (`dateString` parsing; month argument is 0-indexed)
- MDN — [Date and time formats / ISO 8601](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Date#date_time_string_format)
- MDN — [`Temporal`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Temporal)
  (`Instant`, `ZonedDateTime`, `PlainDate`/`PlainDateTime`; `disambiguation` for DST
  gaps/overlaps)
- TC39 — [Temporal proposal](https://tc39.es/proposal-temporal/docs/)
  (instant vs plain vs zoned model; ambiguity & disambiguation)
- IETF — [RFC 3339](https://www.rfc-editor.org/rfc/rfc3339) (date-time on the Internet:
  offsets, `Z`)
