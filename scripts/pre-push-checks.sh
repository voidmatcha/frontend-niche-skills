#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> Python syntax"
python3 -m py_compile scripts/audit-skill-pack.py

echo "==> Skill pack audit"
python3 scripts/audit-skill-pack.py

echo "==> Plugin manifest JSON"
python3 -m json.tool .codex-plugin/plugin.json >/dev/null
python3 -m json.tool .claude-plugin/plugin.json >/dev/null
python3 -m json.tool .claude-plugin/marketplace.json >/dev/null

echo "==> Skill count consistency"
python3 - <<'PY'
import json
import re
from pathlib import Path

skills = sorted(path.parent.name for path in Path("skills").glob("*/SKILL.md"))
readme = Path("README.md").read_text(encoding="utf-8")
links = sorted(set(re.findall(r"\./skills/([^/]+)/SKILL\.md", readme)))
badge_match = re.search(r"Agent_Skills-(\d+)-", readme)
claude = sorted(Path(path).name for path in json.loads(Path(".claude-plugin/plugin.json").read_text(encoding="utf-8"))["skills"])

if badge_match is None:
    raise SystemExit("README Agent_Skills badge missing")
badge_count = int(badge_match.group(1))
if badge_count != len(skills):
    raise SystemExit(f"README badge count {badge_count} != skill count {len(skills)}")
if links != skills:
    raise SystemExit(f"README skill links mismatch: links={links} skills={skills}")
if claude != skills:
    raise SystemExit(f"Claude manifest skills mismatch: claude={claude} skills={skills}")
if "frontend-report-triage" not in skills:
    raise SystemExit("frontend-report-triage missing")
if "skill-pack-auditor" in skills:
    raise SystemExit("skill-pack-auditor should not be a public skill")
print(f"skill_count={len(skills)}")
PY

echo "==> Optional Bats tests"
if command -v bats >/dev/null 2>&1 && [ -d skills/design-to-code-fidelity/tests ]; then
  bats skills/design-to-code-fidelity/tests
else
  echo "bats not installed or tests missing; skipping optional Bats tests"
fi

echo "==> Git diff whitespace"
git diff --check

echo "pre-push checks passed"
