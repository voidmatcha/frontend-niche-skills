# Design — `datetime-correctness` skill

Status: approved 2026-06-14. Part of the `frontend-niche-skills` collection (skill #8).

## Purpose

A skill for the bug class where a date or time silently shifts — by a day, an hour,
or a whole DST transition — because the code stored a wall-clock value without a zone,
parsed a date-only string as an instant, or formatted against the runtime's ambient
timezone. These bugs never reproduce on a UTC dev box with English testing, which is
exactly the collection's thesis.

Scope is **correctness / storage / computation / round-trip**, NOT locale display
formatting (that is `i18n-copy-and-layout`).

## Conventions (inherited from the collection)

- Compact `SKILL.md` (trap-first checklist + boundary + sources) plus per-skill
  `references/`.
- Strict-YAML frontmatter: `name` matches the directory; single-line quoted `description`
  that doubles as the trigger + boundary.
- Every factual claim verified against an official source before release; `## Sources`
  lists them.
- Cross-references mark boundaries with neighboring skills.

## Frontmatter

- `name: datetime-correctness`
- `description`: "Use when storing, computing, or displaying dates/times that must stay
  correct across timezones, DST transitions, server-vs-client environments, and date-only
  vs instant boundaries — UTC/epoch storage, the `new Date("2026-06-14")` date-only-parsed-
  as-UTC off-by-one, `datetime-local` floating values with no zone, DST gaps/overlaps, and
  pinning `Intl.DateTimeFormat`'s `timeZone`. Correctness/storage scope; for locale display
  formatting (which format, grouping, currency) see i18n-copy-and-layout; for in-render
  `Date` causing server/client divergence see ssr-hydration-mismatch."

## `SKILL.md` — trap-first checklist (7 items)

1. Store instants as UTC/epoch (or RFC 3339 with an explicit offset); never persist a
   wall-clock value with no zone.
2. **date-only ≠ instant**: `new Date("2026-06-14")` parses as UTC midnight → off-by-one
   day in negative-offset zones. Parse date-only values explicitly / keep them as a
   date-only type.
3. Display: pin `Intl.DateTimeFormat`'s `timeZone` explicitly; never rely on the runtime's
   ambient zone for user-facing times.
4. `<input type="datetime-local">` (and `date`/`time`) values are **floating local** with
   NO zone — attach the intended zone explicitly on read/write and round-trip carefully.
5. **DST**: a day is not always 24h — local midnight may not exist (spring-forward gap) or
   occur twice (fall-back overlap). Do calendar math zone-aware, not by adding milliseconds.
6. Don't compute zone/locale-dependent text during render (→ `ssr-hydration-mismatch`);
   pass a stable serialized instant plus a fixed render zone.
7. Where targetable, use **Temporal** (`PlainDate` / `ZonedDateTime` / `Instant` make the
   distinctions explicit); otherwise a polyfill or Luxon / date-fns-tz with the same
   discipline.

## `references/`

- `storage-and-math.md` — UTC/epoch storage; date-only vs instant; ISO 8601 / RFC 3339
  parsing pitfalls (`Date.parse` behaviors, date-only-as-UTC vs date-time-as-local); DST
  gap/overlap and zone-aware arithmetic; mapping the invariants onto Temporal types.
- `display-and-input.md` — `Intl.DateTimeFormat` `timeZone` pinning + `formatToParts`;
  `datetime-local`/`date`/`time` input round-trip (floating time, no zone); server-vs-client
  zone divergence; cross-reference to `ssr-hydration-mismatch` for the render-time angle.

## Boundaries / cross-references

- `i18n-copy-and-layout` — owns *which* locale format (grouping, currency, format string,
  "Intl formats but does not parse"). This skill owns instant/day correctness, DST math,
  and form round-trip. Add a reverse pointer when convenient.
- `ssr-hydration-mismatch` — owns the general server/client divergence mechanism. This skill
  owns the datetime-specific fix (serialize a stable instant; render in a fixed zone). The
  reverse pointer is added when that skill is built (next in this batch).

## Sources (to verify against during build)

MDN: `Date`, `Date.parse`, `Date.UTC`, `Intl.DateTimeFormat` (+ `timeZone`, `formatToParts`),
`<input type="datetime-local">`, `Temporal` (`PlainDate`, `ZonedDateTime`, `Instant`). TC39
Temporal proposal. ECMA-402. Unicode CLDR / tz database notes as needed.

## Build checklist (this serves as the implementation plan)

1. Create `skills/datetime-correctness/SKILL.md` (frontmatter + intro + boundary + 7-item
   checklist + references pointer + Sources).
2. Create `skills/datetime-correctness/references/storage-and-math.md`.
3. Create `skills/datetime-correctness/references/display-and-input.md`.
4. Run a focused web-verification workflow (MDN/TC39/ECMA-402) over every non-trivial claim;
   apply corrections.
5. Register: `.claude-plugin/plugin.json` skills[], `.claude-plugin/marketplace.json`
   (description + keywords), `.codex-plugin/plugin.json` (description/longDescription +
   keywords + defaultPrompt), README skill table + references prose, CHANGELOG Added entry,
   version bump.
6. Verify (JSON valid, links resolve, frontmatter name matches) and commit.

## Verification plan

After drafting, run a hardened web-verification workflow (WebSearch/exa only) that quotes
each claim, finds the official source, and emits findings for anything overstated/outdated;
adversarially verify findings; apply confirmed corrections before commit — same gate the
existing skills passed.
