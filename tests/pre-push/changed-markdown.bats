#!/usr/bin/env bats

setup() {
  export REPO_ROOT
  REPO_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export TEST_REPO="$BATS_TEST_TMPDIR/repo"

  mkdir -p "$TEST_REPO"
  git -C "$TEST_REPO" init -q
  git -C "$TEST_REPO" config user.email "test@example.invalid"
  git -C "$TEST_REPO" config user.name "Test"
  printf 'baseline\n' >"$TEST_REPO/committed.md"
  printf 'baseline\n' >"$TEST_REPO/staged.md"
  printf 'baseline\n' >"$TEST_REPO/unstaged.md"
  git -C "$TEST_REPO" add committed.md staged.md unstaged.md
  git -C "$TEST_REPO" commit -qm "baseline"
}

@test "collects committed, staged, unstaged, and untracked markdown once" {
  printf 'committed change\n' >>"$TEST_REPO/committed.md"
  git -C "$TEST_REPO" add committed.md
  git -C "$TEST_REPO" commit -qm "committed change"

  printf 'staged change\n' >>"$TEST_REPO/staged.md"
  git -C "$TEST_REPO" add staged.md
  printf 'unstaged change\n' >>"$TEST_REPO/unstaged.md"
  printf 'untracked\n' >"$TEST_REPO/untracked.md"

  run env LC_ALL=C LC_CTYPE=C LANG=C bash -c \
    'cd "$1" && while IFS= read -r -d "" path; do printf "%s\n" "$path"; done < <("$2/scripts/list-changed-markdown.sh" "HEAD~1...HEAD")' \
    _ "$TEST_REPO" "$REPO_ROOT"

  [ "$status" -eq 0 ]
  [ "$output" = $'committed.md\nstaged.md\nunstaged.md\nuntracked.md' ]
}

@test "excludes deleted markdown and non-markdown files" {
  rm "$TEST_REPO/committed.md"
  printf 'not markdown\n' >"$TEST_REPO/untracked.txt"

  run env LC_ALL=C LC_CTYPE=C LANG=C bash -c \
    'cd "$1" && while IFS= read -r -d "" path; do printf "%s\n" "$path"; done < <("$2/scripts/list-changed-markdown.sh" "HEAD...HEAD")' \
    _ "$TEST_REPO" "$REPO_ROOT"

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "no-upstream fallback scans every committed markdown file" {
  printf 'first commit\n' >"$TEST_REPO/first.md"
  git -C "$TEST_REPO" add first.md
  git -C "$TEST_REPO" commit -qm "first change"

  printf 'second commit\n' >"$TEST_REPO/second.md"
  git -C "$TEST_REPO" add second.md
  git -C "$TEST_REPO" commit -qm "second change"

  run env LC_ALL=C LC_CTYPE=C LANG=C bash -c \
    'cd "$1" && while IFS= read -r -d "" path; do printf "%s\n" "$path"; done < <("$2/scripts/list-changed-markdown.sh")' \
    _ "$TEST_REPO" "$REPO_ROOT"

  [ "$status" -eq 0 ]
  [ "$output" = $'committed.md\nfirst.md\nsecond.md\nstaged.md\nunstaged.md' ]
}

@test "detached depth-one checkout falls back without requiring HEAD parent" {
  printf 'latest\n' >"$TEST_REPO/latest.md"
  git -C "$TEST_REPO" add latest.md
  git -C "$TEST_REPO" commit -qm "latest"

  local shallow_repo="$BATS_TEST_TMPDIR/shallow"
  git clone -q --depth 1 "file://$TEST_REPO" "$shallow_repo"
  git -C "$shallow_repo" checkout -q --detach

  run env LC_ALL=C LC_CTYPE=C LANG=C bash -c \
    'cd "$1" && while IFS= read -r -d "" path; do printf "%s\n" "$path"; done < <("$2/scripts/list-changed-markdown.sh")' \
    _ "$shallow_repo" "$REPO_ROOT"

  [ "$status" -eq 0 ]
  [[ "$output" == *"latest.md"* ]]
}

@test "explicit base and head include a multi-commit delivery range" {
  local base
  base="$(git -C "$TEST_REPO" rev-parse HEAD)"

  printf 'first commit\n' >"$TEST_REPO/first.md"
  git -C "$TEST_REPO" add first.md
  git -C "$TEST_REPO" commit -qm "first change"

  printf 'second commit\n' >"$TEST_REPO/second.md"
  git -C "$TEST_REPO" add second.md
  git -C "$TEST_REPO" commit -qm "second change"
  local head
  head="$(git -C "$TEST_REPO" rev-parse HEAD)"

  run env LC_ALL=C LC_CTYPE=C LANG=C \
    CHECK_DIFF_BASE="$base" CHECK_DIFF_HEAD="$head" \
    bash -c 'cd "$1" && while IFS= read -r -d "" path; do printf "%s\n" "$path"; done < <("$2/scripts/list-changed-markdown.sh")' \
    _ "$TEST_REPO" "$REPO_ROOT"

  [ "$status" -eq 0 ]
  [ "$output" = $'first.md\nsecond.md' ]
}

@test "preserves a Unicode markdown path as one record" {
  git -C "$TEST_REPO" config core.quotePath true
  printf '[source](https://example.invalid/source)\n' >"$TEST_REPO/한글.md"
  git -C "$TEST_REPO" add "한글.md"
  git -C "$TEST_REPO" commit -qm "add Unicode markdown"

  run env LC_ALL=C LC_CTYPE=C LANG=C bash -c \
    'cd "$1" && while IFS= read -r -d "" path; do printf "%s\n" "$path"; done < <("$2/scripts/list-changed-markdown.sh" "HEAD~1...HEAD")' \
    _ "$TEST_REPO" "$REPO_ROOT"

  [ "$status" -eq 0 ]
  [ "$output" = "한글.md" ]
}
