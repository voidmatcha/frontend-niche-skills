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
BAT_TESTS=()
while IFS= read -r test_file; do
  BAT_TESTS+=("$test_file")
done < <(find skills -type f -path '*/tests/*.bats' | sort)
if command -v bats >/dev/null 2>&1 && [ "${#BAT_TESTS[@]}" -gt 0 ]; then
  bats --print-output-on-failure "${BAT_TESTS[@]}"
else
  echo "bats not installed or no Bats tests found; skipping optional Bats tests"
fi

echo "==> Git diff whitespace"
git diff --check

# Source links in the markdown being pushed. Scoped to changed files so this
# stays ~2s instead of ~30s for the whole pack, and skipped entirely when
# offline so a flight or a captive portal cannot block a push. Rot in files you
# did not touch is the scheduled job's problem (.github/workflows/link-check.yml).
echo "==> Changed-file source links"
if [ "${SKIP_LINK_CHECK:-0}" = "1" ]; then
  echo "SKIP_LINK_CHECK=1; skipping"
elif ! curl -sS -m 4 -o /dev/null https://www.google.com/generate_204 2>/dev/null; then
  echo "offline; skipping (run --check-links later)"
else
  if RANGE_BASE="$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null)"; then
    DIFF_RANGE="$RANGE_BASE...HEAD"
  else
    # No upstream yet: fall back to the newest commit so the check still sees
    # links added in it, instead of diffing the entire history.
    DIFF_RANGE="HEAD~1...HEAD"
  fi
  CHANGED_MD=()
  while IFS= read -r changed_file; do
    [ -n "$changed_file" ] && [ -f "$changed_file" ] && CHANGED_MD+=("$changed_file")
  done < <(git diff --name-only --diff-filter=d "$DIFF_RANGE" -- '*.md' 2>/dev/null | sort -u)
  if [ "${#CHANGED_MD[@]}" -eq 0 ]; then
    echo "no changed markdown in $DIFF_RANGE; skipping"
  elif ! python3 scripts/audit-skill-pack.py --check-links --link-paths "${CHANGED_MD[@]}"; then
    cat >&2 <<'GUIDE'

A citation above is dead (404/410). Do not push past this and do not delete the
link to silence it. Triage it, in this order:

  1. Moved, same content   -> swap in the successor URL, keep the annotation.
  2. Gone but historical   -> pin a commit-SHA permalink (repo files) or a Web
                              Archive snapshot, and say why in the annotation.
  3. Source now disagrees  -> this is a claim bug, not a link bug: re-verify the
                              claim against current primary sources and update
                              or remove the claim together with its citation.
  4. No honest replacement -> remove the claim along with the link.

A replacement must resolve AND actually state the claim: open it and read it, a
200 is not evidence. Then rerun this check and record old -> new in the commit
message. Full procedure: docs/skill-evidence-coverage.md (Source link
maintenance). SKIP_LINK_CHECK=1 exists for offline work, not for skipping this.
GUIDE
    exit 1
  fi
fi

echo "pre-push checks passed"
