---
name: datetime-correctness
description: "Use when date/time behavior depends on timezone, DST, date-only parsing, floating local inputs, SSR/server zone differences, or instant-vs-wall-clock boundaries — wall-clock values stored with no zone, `new Date(\"2026-06-14\")` parsed as UTC and printing the previous day, `datetime-local input` floating values with no zone, adding 24h across a DST boundary, or `toLocaleString` rendering the server's zone. Correctness/storage scope; for which locale format to show (grouping, currency, format string) see i18n-copy-and-layout; for in-render `Date` causing server/client divergence see ssr-hydration-mismatch."
---

# Datetime correctness

The expensive datetime bugs aren't formatting — they're **correctness assumptions baked in
on a UTC dev box**: storing a wall-clock value with no zone, parsing a date-only string as
an instant, formatting against the runtime's ambient zone, or adding milliseconds across a
DST boundary. None of them reproduce when the server, the CI box, and the developer are all
in UTC. Core rule: every value is either an **instant** (one point on the global timeline,
e.g. epoch/UTC) **or** a **date-only / wall-clock** value (not an instant until you supply a
zone) — never conflate the two, and make the zone explicit at every boundary.

For *which* locale format to show (digit grouping, currency, `MM/DD` vs `DD/MM`), use
**i18n-copy-and-layout** — it owns display formatting and notes `Intl` formats but does not
parse. For in-render `new Date()` (or zone-dependent text) causing a server/client mismatch,
see **ssr-hydration-mismatch**.

## Checklist (lead with the trap; details in references/)

**Storage & computation** → [storage-and-math](./references/storage-and-math.md)

1. Store an instant as **UTC/epoch** or RFC 3339 **with an explicit offset**. A wall-clock
   string with no zone (`"2026-06-14 09:00"`) can't be placed on the timeline — that's data
   loss, not a format choice.
2. `new Date("2026-06-14")` parses the **date-only** ISO form as **UTC** midnight, so it
   prints as the *previous* day in any negative-offset zone (off-by-one). Date-only ISO is
   UTC; a date-*time* without an offset (`"2026-06-14T09:00"`) is **local** — opposite
   defaults. Keep date-only values date-only; parse explicitly.
3. A day is not 24h. Across a DST transition local midnight may not exist (spring-forward
   gap) or occur twice (fall-back overlap). Do calendar math ("add a day", "start of day")
   **zone-aware** — never by adding `86_400_000` ms.
4. Where targetable, reach for **Temporal**: `Instant` (epoch), `PlainDate`/`PlainDateTime`
   (no zone), `ZonedDateTime` (instant + zone) make these distinctions un-skippable.
   Temporal is Stage 4 but, as of mid-2026, not yet universal across evergreen targets
   (Firefox, Chromium, and Node ship it; Safari/iOS lag) — check MDN BCD for current
   support instead of trusting a pinned version matrix. Feature-detect and polyfill with
   `@js-temporal/polyfill`, or use Luxon / date-fns-tz with the same discipline.

**Display & input** → [display-and-input](./references/display-and-input.md)

5. Pin `Intl.DateTimeFormat`'s `timeZone` explicitly for any user-facing time. The default
   is the runtime's ambient zone, so the server and the user's phone render different clocks
   from the *same* instant.
6. `<input type="datetime-local">` / `date` / `time` values are **floating local** strings
   with no zone attached. Attach the intended zone explicitly on read/write and round-trip
   through it — don't `new Date(input.value)` and hope.
7. Don't compute zone- or locale-dependent text during render: it diverges between the
   server's zone and the client's (→ **ssr-hydration-mismatch**). Send a stable serialized
   instant and render it in one fixed, explicit zone on both sides.

## PR-worthiness gate

A date/time finding is PR-worthy only when it changes rendered, stored, or compared behavior for a
real user or timezone — an instant stored with no zone, `new Date("2026-06-14")` printing the
previous day in a negative-offset zone, 24h arithmetic across a DST boundary, or output rendered in
the runtime's ambient zone — not a cosmetic format nit.

Reject weak findings: dev-only logs or UTC-only test fixtures, a value that never crosses a zone/DST
boundary, or pure locale display formatting (grouping, `MM/DD` vs `DD/MM`) — that is
`i18n-copy-and-layout`'s.

Minimal useful PR: make the zone explicit at the boundary (store epoch/offset, keep date-only
date-only, pin `Intl` `timeZone`) and add a test that runs in a non-UTC zone or across a DST transition.

## Output shape

Report the value type (instant, zoned wall clock, floating local date-time, or
date-only), the parse/store/render boundary, failing zone or DST example,
smallest representation fix, and a pinned-zone regression.

## References

| File | Covers |
|------|--------|
| [storage-and-math](./references/storage-and-math.md) | UTC/epoch storage, date-only vs instant, ISO 8601 / RFC 3339 parsing rules, DST gaps & overlaps, zone-aware arithmetic, Temporal types |
| [display-and-input](./references/display-and-input.md) | `Intl.DateTimeFormat` `timeZone` pinning + `formatToParts`, `datetime-local`/`date`/`time` floating round-trip, server-vs-client zone, SSR |

Sources are listed in each reference file.
