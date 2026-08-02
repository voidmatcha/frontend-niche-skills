# Behavioral run: IME Enter double-submit — 2026-08-01

One observation, not a benchmark. It compares what an agent says about a
single bug report with and without the relevant skill in context. It does not
measure accuracy across cases, models, or skills.

This exists because everything else in the repository measures something
adjacent to the central claim. The routing benchmark measures which skill gets
selected. The audit measures metadata hygiene. The eval cases state desired
behaviour rather than record observed behaviour. None of them show an agent
producing a better diagnosis, which is what the pack claims to cause.

## The report given to both conditions

> Our Korean search box sometimes runs the search twice when the user presses
> Enter. The query fires, then fires again with the same text. It only happens
> for some users and we cannot reproduce it reliably. We added a 300ms debounce
> on the submit handler, which reduced it a lot, but it still happens
> occasionally. What is going on and what is the smallest safe fix?

The report is written the way a real one arrives: a symptom, an unreliable
repro, and a mitigation already applied that partly works. It never mentions
IME, composition, Korean input method, or key codes.

## Conditions

| Condition | Context supplied |
| --- | --- |
| A, without skill | The report only. |
| B, with skill | The report plus the full text of `skills/cjk-text-and-input/SKILL.md`. |

Both conditions get identical instructions otherwise and are told not to read
this repository, so condition A cannot reach the skill indirectly.

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

Fixed before either condition ran. This file was committed before the runs so
the criteria are verifiable as pre-registered rather than fitted to the output.

| ID | Criterion |
| --- | --- |
| R1 | Names IME composition as the mechanism, rather than debounce timing, a double-bound listener, a framework double-render, or event bubbling. |
| R2 | Gives the concrete guard: `KeyboardEvent.isComposing`, or `keyCode === 229` for legacy engines. |
| R3 | Treats the existing 300ms debounce as masking rather than fixing, and says why it partly worked. |
| R4 | Names evidence that discriminates: reproducing with an actual IME, or observing `keydown` while composition is active, rather than inferring from the intermittency. |
| R5 | Keeps the fix at the handler boundary instead of restructuring form state, adding a submit lock, or rewriting the search pipeline. |

A criterion counts as met only if the response states it, not if it can be
inferred charitably.

## Result

Both conditions met all five criteria. The skill did not change the diagnosis
on this case.

| Criterion | A, no skill | B, with skill |
| --- | :---: | :---: |
| R1 IME composition named as the mechanism | met | met |
| R2 `isComposing` or `keyCode === 229` given | met | met |
| R3 debounce called masking | met | met |
| R4 discriminating evidence named | met | met |
| R5 fix kept at the handler boundary | met | met |

Condition A reached the diagnosis unaided, in its first sentence, from a report
that never says IME, composition, or Korean input method. It then supplied both
guards, rejected the debounce as a timing bet, and proposed a request-level
dedupe in its place.

It also produced two things the skill does not contain: a combobox variant
where an autocomplete component's own Enter handler double-fires with no IME
involvement at all, and a timing table that reads the gap between the duplicate
requests as a discriminator, under about 20ms for a double keydown, around
300ms for the debounce's trailing edge, hundreds of milliseconds for a genuine
double press.

Condition B was more specific in three places: it wrote out the composition
event trace, it warned that pasting Korean text or driving the field with a
test runner's `type()` bypasses composition entirely so the bug cannot
reproduce that way, and it named a CDP path, `Input.imeSetComposition`, for a
regression that exercises the real browser sequence. It also carried the
skill's adjacent guidance on search-as-you-type firing on partial syllables and
on mid-composition value transforms causing jamo splitting.

None of that is in the rubric, and none of it changed the diagnosis or the fix.

## Reading this honestly

This is a null result for the claim the run was built to test. The
pre-registered limits say a favourable result would be weak evidence and an
unfavourable one strong; a tie is not favourable.

The most likely explanation is that the case was too easy. The IME Enter
double-submit is well documented and a capable model has seen it many times, so
the report's one unstated clue, a Korean search box, was enough. A case a model
already knows tests recall, not routing, and routing is what a 41-skill pack is
for. Picking this bug was a design error.

What it does not show is that the pack is useless, and what it must not become
is a search for a case that wins. Re-running until the pack looks good is the
behaviour this repository exists to argue against. Any further case goes in
beside this one, whatever it shows.

The honest reading is narrower than either side would like: on a well-known
failure with a strong model, the skill's content was redundant. Whether it
helps where the model is unsure, or where the report is ambiguous enough that
picking the right boundary is the hard part, is untested.

## Limits

- One report, one skill, one model, one run per condition. No repetition, so
  run-to-run variance is unmeasured.
- The skill is supplied inline rather than installed, so this measures the
  effect of the skill's content, not of the routing that would select it in a
  real session. Whether the right skill loads at all is what the routing
  benchmark measures, separately.
- The rubric was written by the same person who wrote the skill, which is a
  bias this format cannot remove. It is stated in advance so a reader can
  disagree with the criteria rather than only with the verdict.
- A result favourable to the pack would be weak evidence. A result unfavourable
  to it would be strong evidence, since the conditions are chosen to suit the
  pack.
