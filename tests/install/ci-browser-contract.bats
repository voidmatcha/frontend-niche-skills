#!/usr/bin/env bats

setup() {
  REPO_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  CHECKS_WORKFLOW="$REPO_ROOT/.github/workflows/checks.yml"
  LINK_CHECK_WORKFLOW="$REPO_ROOT/.github/workflows/link-check.yml"
}

@test "CI actions are pinned to reviewed commits with version comments" {
  run grep -F "uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4.4.0" \
    "$CHECKS_WORKFLOW" "$LINK_CHECK_WORKFLOW"
  [ "$status" -eq 0 ]
  [ "${#lines[@]}" -eq 2 ]

  run grep -F "uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065 # v5.6.0" \
    "$CHECKS_WORKFLOW" "$LINK_CHECK_WORKFLOW"
  [ "$status" -eq 0 ]
  [ "${#lines[@]}" -eq 2 ]

  run grep -F "uses: actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020 # v4.4.0" \
    "$CHECKS_WORKFLOW"
  [ "$status" -eq 0 ]

  run grep -F "uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02 # v4.6.2" \
    "$LINK_CHECK_WORKFLOW"
  [ "$status" -eq 0 ]
}

@test "CI checkout disables persisted credentials" {
  run grep -F "persist-credentials: false" "$CHECKS_WORKFLOW" "$LINK_CHECK_WORKFLOW"
  [ "$status" -eq 0 ]
  [ "${#lines[@]}" -eq 2 ]
}

@test "CI installs and verifies the exact Node and CLI versions" {
  run grep -F 'node-version: "22.20.0"' "$CHECKS_WORKFLOW"
  [ "$status" -eq 0 ]

  run grep -F 'test "$(node --version)" = "v22.20.0"' "$CHECKS_WORKFLOW"
  [ "$status" -eq 0 ]

  run grep -F 'test "$(playwright --version)" = "Version 1.62.1"' "$CHECKS_WORKFLOW"
  [ "$status" -eq 0 ]

  run grep -F 'test "$(skills --version)" = "1.5.21"' "$CHECKS_WORKFLOW"
  [ "$status" -eq 0 ]
}

@test "CI pins Playwright and installs every required browser engine" {
  run grep -F "npm install -g playwright@1.62.1 skills@1.5.21" "$CHECKS_WORKFLOW"
  [ "$status" -eq 0 ]

  run grep -F "playwright install --with-deps chromium firefox webkit" "$CHECKS_WORKFLOW"
  [ "$status" -eq 0 ]
}

@test "CI requires the full browser casebook matrix" {
  run grep -F "CASEBOOK_BROWSERS: chromium,firefox,webkit" "$CHECKS_WORKFLOW"
  [ "$status" -eq 0 ]
}

@test "CI fetches delivery history and passes explicit diff endpoints" {
  run grep -F "fetch-depth: 0" "$CHECKS_WORKFLOW"
  [ "$status" -eq 0 ]

  run grep -F "CHECK_DIFF_BASE:" "$CHECKS_WORKFLOW"
  [ "$status" -eq 0 ]

  run grep -F "CHECK_DIFF_HEAD:" "$CHECKS_WORKFLOW"
  [ "$status" -eq 0 ]
}

@test "iframe casebook honors an explicitly pinned Playwright CLI" {
  run grep -F 'playwright_cli="${PLAYWRIGHT_CLI:-}"' \
    "$REPO_ROOT/skills/iframe-embed-contracts/tests/iframe-contract.bats"

  [ "$status" -eq 0 ]
}
