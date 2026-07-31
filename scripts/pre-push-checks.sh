#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

is_ci() {
  [ "${CI:-}" = "1" ] || [ "${CI:-}" = "true" ]
}

run_link_check() {
  local result_json
  result_json="$(mktemp)"

  if ! python3 scripts/audit-skill-pack.py --check-links --link-paths "$@" --json >"$result_json"; then
    cat "$result_json" >&2
    rm -f "$result_json"
    return 1
  fi

  if is_ci; then
    if ! python3 - "$result_json" <<'PY'
import json
import sys

path = sys.argv[1]
data = json.load(open(path, encoding="utf-8"))
summary = data.get("summary", {})
checked = int(summary.get("external_urls_checked") or 0)
unverified = summary.get("external_urls_unverified") or []
if checked and len(unverified) >= checked:
    print(f"CI link check failed: all {checked} external URLs were unverified.", file=sys.stderr)
    for item in unverified[:20]:
        print(f"- {item}", file=sys.stderr)
    if len(unverified) > 20:
        print(f"... {len(unverified) - 20} more", file=sys.stderr)
    raise SystemExit(1)
PY
    then
      rm -f "$result_json"
      return 1
    fi
  fi
  rm -f "$result_json"
}

echo "==> Python syntax"
python3 -m py_compile scripts/audit-skill-pack.py

echo "==> Skill pack audit"
python3 scripts/audit-skill-pack.py

echo "==> Plugin manifest JSON"
python3 -m json.tool .codex-plugin/plugin.json >/dev/null
python3 -m json.tool .claude-plugin/plugin.json >/dev/null
python3 -m json.tool .claude-plugin/marketplace.json >/dev/null

echo "==> Bats tests"
BAT_TESTS=()
while IFS= read -r test_file; do
  BAT_TESTS+=("$test_file")
done < <(find skills tests -type f -name '*.bats' | sort)
BATS_BIN="${BATS_BIN:-}"
if [ -z "$BATS_BIN" ]; then
  BATS_BIN="$(command -v bats || true)"
fi
if [ -n "$BATS_BIN" ] && [ -x "$BATS_BIN" ] && [ "${#BAT_TESTS[@]}" -gt 0 ]; then
  "$BATS_BIN" --print-output-on-failure "${BAT_TESTS[@]}"
elif [ "${#BAT_TESTS[@]}" -gt 0 ]; then
  if is_ci; then
    echo "bats is required in CI because ${#BAT_TESTS[@]} Bats test file(s) exist" >&2
    exit 1
  fi
  echo "pre-push checks partial: bats is missing, so ${#BAT_TESTS[@]} Bats test file(s) did not run" >&2
  exit 2
else
  echo "no Bats tests found; skipping"
fi

echo "==> Git diff whitespace"
git diff --check

echo "==> Git deliverable audit"
python3 scripts/check-git-deliverable.py

# Source links in the Markdown being delivered. CI supplies explicit endpoints,
# a normal local branch uses its upstream, and a no-upstream or detached
# checkout safely scans the full committed tree. Staged, unstaged, and untracked
# Markdown is always included. The scheduled job still catches rot in untouched
# files between deliveries (.github/workflows/link-check.yml).
echo "==> Delivery source links"
if [ "${SKIP_LINK_CHECK:-0}" = "1" ]; then
  if is_ci; then
    echo "SKIP_LINK_CHECK=1 is not allowed in CI" >&2
    exit 1
  fi
  echo "SKIP_LINK_CHECK=1; skipping"
elif ! curl -sS -m 4 -o /dev/null https://www.google.com/generate_204 2>/dev/null; then
  if is_ci; then
    echo "CI network probe failed; running source-link check fail-closed"
  else
    echo "offline; skipping (run --check-links later)"
    exit 0
  fi
else
  echo "network probe passed; checking source links"
fi

if [ "${SKIP_LINK_CHECK:-0}" != "1" ]; then
  CHANGED_MD=()
  CHANGED_MD_FILE="$(mktemp)"
  trap 'rm -f "$CHANGED_MD_FILE"' EXIT
  scripts/list-changed-markdown.sh >"$CHANGED_MD_FILE"
  while IFS= read -r -d '' changed_file; do
    [ -n "$changed_file" ] && [ -f "$changed_file" ] && CHANGED_MD+=("$changed_file")
  done <"$CHANGED_MD_FILE"
  if [ "${#CHANGED_MD[@]}" -eq 0 ]; then
    echo "no committed, staged, unstaged, or untracked markdown; skipping"
  elif ! run_link_check "${CHANGED_MD[@]}"; then
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
