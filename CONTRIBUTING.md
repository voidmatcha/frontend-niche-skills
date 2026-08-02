# Contributing

Thanks for helping. This pack trades on being narrow and evidence-backed, so
most of the process below exists to protect those two properties rather than to
enforce style.

## Before opening a PR

Run the repo checks. They are the same ones CI runs.

```bash
./scripts/pre-push-checks.sh
```

That script runs Python syntax checks, the skill pack audit, plugin manifest
validation, Bats tests, `git diff --check`, the deliverable audit, and a source
link check on the markdown you are pushing. The link check is skipped when the
network probe fails locally but never in CI. To check every external URL in the
pack instead of only changed files:

```bash
python3 scripts/audit-skill-pack.py --check-links
```

`lefthook.yml` only delegates to the same script, so hooks are optional:

```bash
lefthook install
lefthook run pre-push
```

## Adding a skill

The gate is six questions in
[docs/skill-quality-standard.md](./docs/skill-quality-standard.md). Read it
rather than this summary, because that document is the authority:

1. Is the failure recurring?
2. Is it cross-framework or host-specific for a real shipped surface?
3. Is it difficult for a general coding agent?
4. Is it distinct from existing skills?
5. Is it testable?
6. Can weak findings be rejected?

Each question has an evidence column stating what answers it. A skill that
cannot answer 4 belongs inside an existing skill, and one that cannot answer 6
will generate false positives.

On top of the gate, three things are enforced mechanically and will fail the
audit if missing:

- **At least three evaluation cases** in `skills/<name>/evals/evals.json`. The
  established shape is one realistic failure the skill owns, one plausible but
  misrouted claim it must reject, and one where the obvious fix is blocked by a
  sibling skill.
- **A routing benchmark entry** in `evals/routing/cases.json` for any public
  domain skill.
- **A short description** in `docs/claudeai-short-descriptions.json`, covered
  below.

Every skill ships evals. `LEGACY_EVAL_EXEMPTIONS` in
`scripts/audit-skill-pack.py` is deliberately empty, and adding a name back to
it will not pass review.

## Things the audit will reject

- A reference file over 100 lines with no contents list, because partial reads
  would miss sections.
- Overclaim wording. The audit flags absolutes; say what the evidence supports.
- A skill added to one README but not the other three. All four must list skills
  in the same order.
- Frontmatter keys outside the specification's allowed set.
- A local markdown link with no target.

## Claude.ai

Claude.ai caps `description` at 200 characters while the specification allows
1024. The canonical skills target the specification, and
`docs/claudeai-short-descriptions.json` carries a short form per skill. If you
add a skill, add its entry there too, or the audit fails. Build the variant
with:

```bash
python3 scripts/build-claudeai-variant.py
```

## Evidence claims

Candidate open-source findings are not confirmed upstream bugs until the current
branch is re-checked, the issue is reproduced locally, and a maintainer accepts
it or a failing test supports it. Keep candidate and confirmed findings labelled
separately in [docs/skill-evidence-coverage.md](./docs/skill-evidence-coverage.md).

## Commit messages

Describe what changed and why. For anything beyond a typo, note the constraints
you worked under, the alternatives you rejected and why, and what you were not
able to test.
