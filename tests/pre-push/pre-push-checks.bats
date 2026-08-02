#!/usr/bin/env bats

setup() {
  export REPO_ROOT
  REPO_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export TEST_REPO="$BATS_TEST_TMPDIR/repo"
  export TOOL_BIN="$BATS_TEST_TMPDIR/bin"

  mkdir -p "$TEST_REPO/scripts" "$TEST_REPO/skills" "$TEST_REPO/tests" "$TEST_REPO/.codex-plugin" "$TEST_REPO/.claude-plugin" "$TOOL_BIN"
  cp "$REPO_ROOT/scripts/pre-push-checks.sh" "$TEST_REPO/scripts/pre-push-checks.sh"
  cat >"$TEST_REPO/scripts/audit-skill-pack.py" <<'PY'
#!/usr/bin/env python3
import json
import sys

if "--check-links" in sys.argv:
    expected = __import__("os").environ.get("EXPECT_LINK_PATH")
    if expected and expected not in sys.argv:
        print(f"missing expected link path: {expected}", file=sys.stderr)
        raise SystemExit(3)
    print(json.dumps({
        "ok": True,
        "summary": {
            "external_urls_checked": 2,
            "external_urls_unverified": [
                "doc.md — network/timeout: https://example.invalid/a",
                "doc.md — network/timeout: https://example.invalid/b",
            ],
        },
        "errors": [],
        "warnings": [],
    }))
else:
    print("fixture audit passed")
PY
  cat >"$TEST_REPO/scripts/check-git-deliverable.py" <<'PY'
#!/usr/bin/env python3
print("fixture deliverable passed")
PY
cat >"$TEST_REPO/scripts/list-changed-markdown.sh" <<'SH'
#!/usr/bin/env bash
printf 'doc.md\0'
SH
  chmod +x \
    "$TEST_REPO/scripts/pre-push-checks.sh" \
    "$TEST_REPO/scripts/audit-skill-pack.py" \
    "$TEST_REPO/scripts/check-git-deliverable.py" \
    "$TEST_REPO/scripts/list-changed-markdown.sh"
  printf '{}\n' >"$TEST_REPO/.codex-plugin/plugin.json"
  printf '{}\n' >"$TEST_REPO/.claude-plugin/plugin.json"
  printf '{}\n' >"$TEST_REPO/.claude-plugin/marketplace.json"
  printf '[link](https://example.invalid/a)\n' >"$TEST_REPO/doc.md"
  git -C "$TEST_REPO" init -q
  git -C "$TEST_REPO" config user.email "test@example.invalid"
  git -C "$TEST_REPO" config user.name "Test"
  git -C "$TEST_REPO" add .
  git -C "$TEST_REPO" commit -qm "fixture"
}

@test "CI fails when Bats tests exist but bats is missing" {
  mkdir -p "$TEST_REPO/tests"
  printf '#!/usr/bin/env bats\n@test "x" { true; }\n' >"$TEST_REPO/tests/example.bats"

  run env BATS_BIN="$TOOL_BIN/missing-bats" CI=1 LC_ALL=C LC_CTYPE=C LANG=C \
    /bin/bash "$TEST_REPO/scripts/pre-push-checks.sh"

  [ "$status" -eq 1 ]
  [[ "$output" == *"bats is required in CI because 1 Bats test file(s) exist"* ]]
}

@test "local missing Bats tests exits partial instead of claiming success" {
  mkdir -p "$TEST_REPO/tests"
  printf '#!/usr/bin/env bats\n@test "x" { true; }\n' >"$TEST_REPO/tests/example.bats"

  run env -u CI BATS_BIN="$TOOL_BIN/missing-bats" LC_ALL=C LC_CTYPE=C LANG=C \
    /bin/bash "$TEST_REPO/scripts/pre-push-checks.sh"

  [ "$status" -eq 2 ]
  [[ "$output" == *"pre-push checks partial: bats is missing"* ]]
}

@test "CI does not skip source links when the network probe fails" {
  cat >"$TOOL_BIN/curl" <<'SH'
#!/usr/bin/env bash
exit 7
SH
  chmod +x "$TOOL_BIN/curl"
  mkdir -p "$TEST_REPO/skills" "$TEST_REPO/tests"

  run env PATH="$TOOL_BIN:$PATH" CI=1 LC_ALL=C LC_CTYPE=C LANG=C \
    /bin/bash "$TEST_REPO/scripts/pre-push-checks.sh"

  [ "$status" -eq 1 ]
  [[ "$output" == *"CI network probe failed; running source-link check fail-closed"* ]]
  [[ "$output" == *"CI link check failed: all 2 external URLs were unverified"* ]]
}

@test "passes a NUL-delimited Unicode markdown path to the link checker" {
  cat >"$TOOL_BIN/curl" <<'SH'
#!/usr/bin/env bash
exit 0
SH
  cat >"$TEST_REPO/scripts/list-changed-markdown.sh" <<'SH'
#!/usr/bin/env bash
printf '한글.md\0'
SH
  chmod +x "$TOOL_BIN/curl" "$TEST_REPO/scripts/list-changed-markdown.sh"
  printf '[link](https://example.invalid/a)\n' >"$TEST_REPO/한글.md"

  run env -u CI PATH="$TOOL_BIN:$PATH" EXPECT_LINK_PATH="한글.md" LC_ALL=C LC_CTYPE=C LANG=C \
    /bin/bash "$TEST_REPO/scripts/pre-push-checks.sh"

  [ "$status" -eq 0 ]
  [[ "$output" == *"pre-push checks passed"* ]]
}
