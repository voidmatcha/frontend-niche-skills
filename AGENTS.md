# Agent contract for frontend-niche-skills

This repository is a published pack of frontend edge-case skills consumed by
coding agents. Everything here is agent-facing documentation, so a wrong or
unsourced sentence is the product defect.

## Non-negotiables

- **Every externally verifiable claim needs a citation.** Put it in the skill's
  `## Sources` section or a `references/*.md` entry. Never invent a URL, and
  never cite a page you have not opened — a `200` proves the page exists, not
  that it says what you claim.
- **Verify version- and behavior-sensitive claims against primary sources**
  (MDN, caniuse, specs, release notes, library docs) before writing them, and
  prefer time-safe phrasing over pinned support matrices, which rot.
- **Do not bypass the pre-push checks** (`--no-verify`, `SKIP_LINK_CHECK=1` for
  anything other than genuinely being offline). If the link check fails, follow
  the triage steps it prints.
- **Keep the pack universal.** No company, product, customer, or personal-tooling
  names; no internal URLs; no examples that only make sense inside one codebase.
- **`skills/` content is English** — skill names, commands, and paths stay
  English everywhere so agent skill-matching works, even in translated READMEs.

## Before you finish

```bash
./scripts/pre-push-checks.sh    # audit + manifests + Bats + links you changed
```

Run this even if you are only committing (not pushing) — the git hook fires on
push, but most agent sessions end at a commit, so the hook alone will not catch
you. Before a release, also run the full sweep:

```bash
python3 scripts/audit-skill-pack.py --check-links
```

## Repo-specific rules

- **Frontmatter `description` is capped at 1024 characters** by the skill spec;
  the audit errors above the cap and warns at 950. Descriptions state *when to
  use* the skill (symptoms, triggers) — not a summary of its workflow.
- **README parity:** `README.md`, `README.ko.md`, `README.ja.md`, and
  `README.zh-cn.md` share badge counts, table structure, and skill links. A
  change to one is a change to all four.
- **New skill checklist:** satisfy `docs/skill-quality-standard.md`, add at
  least three realistic eval cases, add a row to
  `docs/skill-evidence-coverage.md`, the routing table in
  `skills/frontend-report-triage/SKILL.md`, all four READMEs, and both plugin
  manifests. The audit enforces the structural parts.
- **Preserve the gates.** Each skill's PR-worthiness gate and "reject weak
  findings" list are the pack's main value — never trim them for brevity.
- **Non-trivial commits carry the trailer block** (`Constraint:`, `Rejected:`,
  `Confidence:`, `Scope-risk:`, `Not-tested:`) so `git log` stays a decision log.
