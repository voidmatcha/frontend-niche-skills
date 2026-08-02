# Behavioral run: ambiguous stale-page report — 2026-08-01

Second observation, run because the first one
([IME Enter double-submit](../2026-08-01-ime-enter-double-submit/)) tested the
wrong thing. That case was a well-documented bug the model already knew, so it
measured recall. A 41-skill pack is for deciding which boundary owns a symptom,
and a report with one correct answer cannot measure that.

This case has no single obvious answer. It is kept whatever it shows.

## The report given to both conditions

> After a deploy, some users see an old version of the page, and a draft they
> were writing disappears. Refreshing usually fixes it. It is not everyone and
> we cannot reproduce it on staging.

At least four boundaries in this pack could own that, and the report contains
no evidence that separates them:

- a service worker serving cached bundles, `pwa-offline-cache-contracts`
- a page restored from back/forward cache with stale state,
  `browser-page-lifecycle-bfcache-contracts`
- a failed or aborted IndexedDB write losing the draft,
  `browser-storage-durability-contracts`
- an optimistic update that rolled back without surfacing it,
  `optimistic-update-rollback-contracts`

## Conditions

| Condition | Context supplied |
| --- | --- |
| A, without skill | The report only. |
| B, with skill | The report plus the full text of `skills/frontend-report-triage/SKILL.md`. |

`frontend-report-triage` is the pack's declared entry point for exactly this
shape of report, so this tests the routing claim rather than recall of one
failure mode. Both conditions are told not to read this repository.

## Protocol

- Run date: 2026-08-01.
- Each condition was a separate agent invocation with no shared context, so
  neither saw the other's answer.
- Both were instructed not to read this repository. Condition B received the
  skill as text pasted into its prompt; condition A received nothing beyond the
  report.
- Each condition wrote its own answer directly to `condition-a.md` and
  `condition-b.md`. Those files are verbatim output, not summaries, and were
  not edited afterwards.
- Scoring was done by reading both files against the rubric above, by hand.

The model identifier was not pinned or recorded, which is a real gap. The
routing comparison under `evals/routing/results/` records its model and process
isolation; this run does not, so a reader cannot tell whether the tie was
against a frontier model or a small one, and those mean opposite things. Any
further case should pin the model before it runs.

## Rubric

Fixed before either condition ran, and committed before the runs.

Unlike the first case, the rubric does not reward naming a cause. A report with
this little evidence has no determinable cause yet, so committing to one is the
failure mode being tested.

| ID | Criterion |
| --- | --- |
| R1 | Keeps at least three distinct candidate causes alive rather than settling on one. |
| R2 | For each candidate, names the observation that would confirm or eliminate it, not just the candidate. |
| R3 | Names at least one discriminator that separates two specific candidates, so the evidence requested is ordered by what it rules out. |
| R4 | Does not propose a code change before the cause is narrowed, or states explicitly that any fix offered is provisional. |
| R5 | Treats "refreshing usually fixes it" and "cannot reproduce on staging" as evidence that constrains the candidate set, rather than as background colour. |

A criterion counts as met only if the response states it.

## Result

Both conditions met all five criteria. Second case, second tie.

| Criterion | A, no skill | B, with skill |
| --- | :---: | :---: |
| R1 three or more candidates kept alive | met | met |
| R2 confirming or eliminating observation per candidate | met | met |
| R3 a discriminator between two specific candidates | met | met |
| R4 no premature fix, or fixes marked provisional | met | met |
| R5 "refresh fixes it" and "not on staging" used as constraints | met | met |

Condition A listed five mechanisms, asked for the service worker registration,
the document cache headers, the deploy's asset-retention behaviour, the draft's
storage location, and error telemetry filtered to the deploy window. It gave an
explicit discriminator: long-lived sessions spanning the deploy rule in the
chunk and service-worker mechanisms and rule out most CDN theories. It flagged
that DevTools with cache disabled hides this entire class of bug, which is part
of why staging looks clean.

Condition B produced the pack's declared output shape, ranked hypotheses with
evidence gaps and named follow-up skills, and refused a root cause outright in
its first line.

## The difference the rubric did not catch

One substantive difference showed up outside the criteria, and it goes to
condition B.

Both conditions recommended persisting the draft outside component state as
mitigation. Condition A put it first: "I would do this first, since it converts
the worst part of the user impact into a non-issue while you diagnose."
Condition B flagged the opposite: shipping that mitigation "would also hide the
evidence you need for H3," because if the draft is silently failing to persist,
adding a second persistence path masks the failing one.

B is right. A's advice would have destroyed the evidence for one of its own
hypotheses.

This is recorded because it happened, not because it rescues the result. It was
noticed after reading both outputs, which is exactly the position the
pre-registration exists to guard against. A criterion written after seeing the
answers is not evidence. If a third case is run, "does the proposed mitigation
destroy evidence for a live hypothesis" belongs in the rubric before it starts.

B was also sharper in three smaller places: it asked whether the stale-page and
lost-draft reports name the same users or are two merged reports, it ranked the
evidence gaps by how much each one narrows rather than listing them flat, and it
told the reader not to send screenshots because they would not distinguish any
hypothesis. None of that is scored.

## Limits

- One report, one skill, one model, one run per condition.
- This design favours the pack more than the first case did. Asking for
  discriminating evidence before committing to a cause is the behaviour the
  skill teaches, so a win here is close to measuring whether the model followed
  an instruction it was just given. That is worth less than it looks.
- The skill is supplied inline rather than installed, so the routing that would
  select `frontend-report-triage` in a real session is still untested here.
- The rubric was written by the author of the skill.
