# Behavioral run: folder drop empty after an await — 2026-09-25

One observation, not a benchmark. It compares what an agent says about a
single bug report with and without the relevant skill in context. It does not
measure accuracy across cases, models, or skills.

This file is committed before either condition runs, so the report, the
rubric, and the limits below are pre-registered. The result section is added
afterwards and nothing above it changes.

## How the case was chosen

The two earlier runs taught two things: a well-known bug tests recall rather
than the skill, and picking cases until the pack wins is not allowed. So the
skill was drawn, not chosen:

- Excluded: the two skills already tested here (`cjk-text-and-input`,
  `frontend-report-triage`) and the 14 skills whose eval cases were rewritten
  and graded on the same day, because those gradings showed where a model
  without the skill went wrong.
- Drawn: `random.Random(20260925).choice(pool)` over the remaining 26 domain
  skills, sorted by name. The draw returned `file-ingest-contracts`.
- Within that skill, the two most widely documented traps (drop-zone highlight
  flicker and a missing `dragover` cancel) were set aside as recall tests. The
  report below combines a less common trap with a common misconception.

The report was written by the same author who maintains the skill, after
reading it. That is a bias this format cannot remove.

## The report given to both conditions

> Users can drag files onto our upload area, and dragging a whole folder used
> to show zero files. A teammate switched the drop handler from
> `e.dataTransfer.files` to looping over `e.dataTransfer.items`, and folders
> started working in local testing. Then we added a storage-quota check at the
> top of the drop handler (`await checkQuota()`), and now every drop shows an
> empty list, folders and single files alike. Separately, product wants the
> uploader limited to images, and the plan is to add `accept="image/*"` to the
> file input so drops of other files are refused too. What is going on, and
> what is the smallest safe fix?

The report never names the drag data store, protected mode, directory
entries, or what `accept` does.

## Conditions

| Condition | Context supplied |
| --- | --- |
| A, without skill | The report only. |
| B, with skill | The report plus the full text of `skills/file-ingest-contracts/SKILL.md` at the commit that adds this file. |

Both conditions get identical instructions otherwise and are told not to read
this repository, so condition A cannot reach the skill indirectly.

## Protocol

- Model: Anthropic Claude Opus (`claude-opus-5-5`), each condition a separate
  Claude Code subagent with no shared context. Temperature was not exposed.
- Condition B receives the skill as text pasted into its prompt; condition A
  receives nothing beyond the report. Neither may open files in this
  repository; that is enforced by instruction, not by a sandbox.
- Each condition writes its answer verbatim to `condition-a.md` or
  `condition-b.md`. Those files are not edited afterwards.
- Scoring: one grader agent scores both answers against the rubric without
  being told which condition wrote which (the answers are presented as X and
  Y in a random order), and the maintainer checks each verdict against the
  answer text. Disagreements are reported, not silently resolved.

## Rubric

| ID | Criterion |
| --- | --- |
| R1 | Names the new `await` as the cause of the regression: the drag data store is readable only during the `drop` handler (protected mode afterwards), so `items` read after `await checkQuota()` yields nothing. Says to capture the items or entries synchronously before the first `await`. |
| R2 | Explains that folders need `DataTransfer.items` with `webkitGetAsEntry()` (or a feature-detected `getAsFileSystemHandle()`) and recursive directory reading, because `DataTransfer.files` has no directory support. |
| R3 | Says a directory reader must call `readEntries()` repeatedly until it returns an empty list, because each call can return only part of the directory. |
| R4 | Says `accept` only filters the OS file picker, does not apply to drag-and-drop, and is not validation; a real type check needs server-side validation, with `file.type` and client checks as hints at most. |
| R5 | Keeps the fix at the drop handler (synchronous capture, then the quota check and recursion) instead of rewriting the uploader, adding a library, or adding delays or retries. |

A criterion counts as met only if the response states it, not if it can be
inferred charitably. R3 is not in the skill; it checks whether the skill's
presence crowds out knowledge the model already has, or the reverse.

Sources for the criteria:

- MDN, `DataTransferItem.webkitGetAsEntry()`: "this method can only read data
  in the handlers for the dragstart and drop events, because those are the only
  times the drag data store is readable. Calling it from any other drag event
  returns null."
  <https://developer.mozilla.org/en-US/docs/Web/API/DataTransferItem/webkitGetAsEntry>
- MDN, Drag data store: "Outside of dragstart and drop events, the data store
  is in protected mode, disallowing code from accessing any payload."
  <https://developer.mozilla.org/en-US/docs/Web/API/HTML_Drag_and_Drop_API/Drag_data_store>
- WICG File and Directory Entries API, `readEntries()` steps: each call
  produces "a non-zero number of entries ... that have not yet been produced",
  the done flag is set when a call returns an empty list, and the spec's
  example reads batches until `entries.length === 0`.
  <https://wicg.github.io/entries-api/#dom-filesystemdirectoryreader-readentries>
- MDN, `accept` attribute: a hint for the file picker, not validation; back it
  with server-side checks.
  <https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/accept>
- MDN, `Blob.type`: assumed from the file extension, not a sole validation
  scheme. <https://developer.mozilla.org/en-US/docs/Web/API/Blob/type>

## Limits

- One report, one skill, one model, one run per condition. Run-to-run variance
  is unmeasured.
- The skill is supplied inline rather than installed, so this measures the
  skill's content, not whether routing would select it.
- The rubric and the report were written by the skill's maintainer after
  reading the skill.
- A result favourable to the pack is weak evidence; an unfavourable one is
  strong evidence, since the conditions are chosen to suit the pack.
- Repository isolation and grader blinding are instructions, not sandboxes.
