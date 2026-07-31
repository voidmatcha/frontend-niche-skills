# Skill quality standard

This pack treats a skill as a small routing-and-execution product, not as a
topic note. A useful skill must be discoverable from its metadata, narrow
enough to select without loading the whole catalog, explicit enough to produce
a verifiable result, and honest about weak evidence.

## Portable baseline and pack policy

Every skill must satisfy the portable Agent Skills frontmatter requirements:

- `name` matches the directory, uses lowercase letters, digits, and hyphens,
  and stays within 64 characters.
- `description` is non-empty and stays within 1,024 characters.
- `compatibility`, when present, states real environment requirements and stays
  within 500 characters.

This pack adds authoring policies on top of that portable shape:

- `description` says both what the skill does and when to use it.
- `SKILL.md` stays below 500 lines. Move detailed material into
  directly linked `references/` files and give reference files over 100 lines a
  contents list. These are maintainability policies informed by public authoring
  guidance, not portable-format requirements.

The frontmatter limits are portability constraints; the remaining bullets are
pack policies. Neither category is evidence that the workflow itself is good.

## Pack quality contract

Before adding or materially expanding a skill, require all of the following:

1. **One recognizable job.** The skill has one trigger family, one evidence
   model, and one success criterion. Split workflows when their inputs,
   failure modes, or completion checks differ.
2. **Front-loaded routing.** The description begins with the user-visible
   symptom or task. It names close siblings and exclusions when keyword
   overlap could route the same report to multiple skills. In this pack,
   `agents/openai.yaml` keeps `short_description` within 25-64 characters and
   its default prompt explicitly invokes the skill.
3. **Executable workflow.** The body identifies the evidence to inspect, the
   decision sequence, the smallest useful verification, and the output the
   user should receive. It says which facts must not be inferred.
4. **Progressive disclosure.** `SKILL.md` contains the core workflow. Each
   reference file is linked directly from it, and the link says when the agent
   should read that file.
5. **Evidence discipline.** Every externally verifiable claim has an opened
   source in `## Sources` or a linked reference. Version-sensitive claims use
   primary sources and time-safe wording. Repository file citations use a full
   commit SHA rather than any mutable branch or tag name; living official docs
   and issue trackers carry an explicit checked date when their current state
   matters.
6. **Finding quality.** Every defect-review skill has a `## PR-worthiness gate`,
   a list that rejects weak findings or likely false positives, and a minimal
   regression or reproduction shape.
7. **Output contract.** `## Output shape` tells the agent how to report the
   evidence, impact, boundary, smallest fix, and verification gap without
   inflating a grep hit into a defect.
8. **Evaluation cases.** New skills include at least three realistic cases:
   a representative positive case, an edge or false-positive case, and a
   boundary case that should route elsewhere. Each case states the expected
   output and, when graded, uses a short list of observable binary expectations
   rather than one keyword-presence check. Run comparative agent evaluations
   when a change is meant to improve behavior, not only wording; record a
   no-delta result instead of inventing skill value.
9. **Scripts earn their cost.** Bundle code only for deterministic or fragile
   work. State whether to run or read it, document dependencies, handle errors,
   and keep destructive or network behavior unsurprising.

## New-skill admission gate

Add a new public skill only when all six answers are yes:

| Question | Evidence required |
| --- | --- |
| Is the failure recurring? | Primary documentation plus a reproduced case, upstream issue pattern, or repeated user evidence. |
| Is it cross-framework or host-specific for a real shipped surface? | The contract is not tied to one private product or one component implementation. |
| Is it difficult for a general coding agent? | A plausible default fix can miss the browser/host/data boundary or create a false positive. |
| Is it distinct from existing skills? | The triage route, evidence type, and success criterion do not already belong to a sibling. |
| Is it testable? | A focused reproduction or regression can distinguish the bug from a harmless pattern. |
| Can weak findings be rejected? | The skill can name positive controls, false positives, and evidence that is insufficient to file or patch. |

If any answer is no, improve an existing sibling, record a research candidate,
or leave the topic out. Catalog size is not a quality metric.

## Maintenance loop

1. Capture direct, indirect, edge, and negative prompts.
2. Run the current skill and a no-skill or previous-skill baseline.
3. Grade routing and output against observable assertions.
4. Change the smallest instruction or metadata field that explains the miss.
5. Re-run the same cases and record remaining gaps.

The catalog-level routing benchmark in `evals/routing/` requires every public
domain skill to have one realistic representative smoke prompt, one clear
near-neighbor collision, one answer-neutral hard collision using a distinct
directed edge where the cluster permits it, and membership in a declared
collision cluster. Repository checks validate this coverage without invoking a
model. Live routing runs use the blinded export and external prediction scorer;
record batch/model/isolation limits in a run manifest, and never commit
fabricated predictions or call a model from the deterministic CI path.

The repository audit checks portable metadata, required quality sections,
direct reference reachability, and the shape of bundled eval files. It cannot
validate that a prompt routes correctly or that the advice fixes a browser bug;
those claims still require agent evaluation and runtime evidence.

## Sources

- Agent Skills specification, frontmatter, body, resources, and progressive
  disclosure (verified 2026-07-31): <https://agentskills.io/specification>
- OpenAI, Build skills, including focused jobs, front-loaded descriptions,
  explicit inputs/outputs, supporting resources, and activation tests:
  <https://learn.chatgpt.com/docs/build-skills>
- OpenAI, plugin skill authoring and workflow boundaries:
  <https://developers.openai.com/plugins/build/skills>
- OpenAI, plugin/tool metadata golden prompt sets and precision/recall
  iteration, adapted here for skill routing:
  <https://developers.openai.com/plugins/guides/optimize-metadata>
- Anthropic, Skill authoring best practices, including progressive disclosure,
  feedback loops, script guidance, and evaluation-driven iteration:
  <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices>
- Anthropic, Agent Skills overview and security considerations:
  <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview>
