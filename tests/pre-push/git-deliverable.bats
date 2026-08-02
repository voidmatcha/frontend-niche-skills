#!/usr/bin/env bats

setup() {
  # The CI step exports these for the real checkout. Each test builds its
  # own repository in a temp dir where those revisions do not exist, so
  # inheriting them makes the script take its CI branch and fail. Tests
  # that need them set them explicitly.
  unset CHECK_DIFF_BASE CHECK_DIFF_HEAD CHECK_DELIVERABLE_REF

  export REPO_ROOT
  REPO_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export TEST_REPO="$BATS_TEST_TMPDIR/repo"

  mkdir -p "$TEST_REPO/scripts"
  git -C "$TEST_REPO" init -q
  git -C "$TEST_REPO" config user.email "test@example.invalid"
  git -C "$TEST_REPO" config user.name "Test"
  cat >"$TEST_REPO/scripts/audit-skill-pack.py" <<'PY'
#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[-1])
if not (root / "required.txt").exists():
    print("missing required.txt")
    raise SystemExit(1)
print("fixture audit passed")
PY
  git -C "$TEST_REPO" add scripts/audit-skill-pack.py
  git -C "$TEST_REPO" commit -qm "baseline"
}

@test "audits the exact Git archive instead of untracked working-tree files" {
  printf 'exists only in the working tree\n' >"$TEST_REPO/required.txt"

  run env LC_ALL=C LC_CTYPE=C LANG=C \
    "$REPO_ROOT/scripts/check-git-deliverable.py" \
      --repo "$TEST_REPO" \
      --audit-script "$TEST_REPO/scripts/audit-skill-pack.py"

  [ "$status" -eq 1 ]
  [[ "$output" == *"missing required.txt"* ]]
  [[ "$output" == *"exact Git archive does not pass"* ]]
}

@test "passes once the required deliverable file is committed" {
  printf 'committed deliverable\n' >"$TEST_REPO/required.txt"
  git -C "$TEST_REPO" add required.txt
  git -C "$TEST_REPO" commit -qm "add deliverable"

  run env LC_ALL=C LC_CTYPE=C LANG=C \
    "$REPO_ROOT/scripts/check-git-deliverable.py" \
      --repo "$TEST_REPO" \
      --audit-script "$TEST_REPO/scripts/audit-skill-pack.py"

  [ "$status" -eq 0 ]
  [[ "$output" == *"fixture audit passed"* ]]
  [[ "$output" == *"Git deliverable audit passed for ref HEAD"* ]]
}

@test "skips non-git consumer directories by default" {
  local consumer_dir="$BATS_TEST_TMPDIR/non-git"
  mkdir -p "$consumer_dir"

  run env LC_ALL=C LC_CTYPE=C LANG=C \
    "$REPO_ROOT/scripts/check-git-deliverable.py" --repo "$consumer_dir"

  [ "$status" -eq 0 ]
  [[ "$output" == *"Git deliverable audit skipped"* ]]
}
