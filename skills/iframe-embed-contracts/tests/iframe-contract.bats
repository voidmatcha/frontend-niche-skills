#!/usr/bin/env bats

setup() {
  SERVER_INFO="$BATS_TEST_TMPDIR/server.json"
  SERVER_LOG="$BATS_TEST_TMPDIR/server.log"
  python3 "$BATS_TEST_DIRNAME/fixture_server.py" >"$SERVER_INFO" 2>"$SERVER_LOG" &
  SERVER_PID=$!

  local attempt
  for attempt in {1..100}; do
    if [ -s "$SERVER_INFO" ] && grep -q 'allowed_url' "$SERVER_INFO"; then
      return 0
    fi
    sleep 0.05
  done
  cat "$SERVER_LOG" >&2
  return 1
}

teardown() {
  if [ -n "${SERVER_PID:-}" ]; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
    wait "$SERVER_PID" >/dev/null 2>&1 || true
  fi
}

run_browser_smoke() {
  local mode="$1"
  local playwright_cli
  playwright_cli="${PLAYWRIGHT_CLI:-}"
  if [ -z "$playwright_cli" ]; then
    playwright_cli="$(command -v playwright)" || return 127
  fi
  PLAYWRIGHT_CLI="$playwright_cli" node "$BATS_TEST_DIRNAME/browser_smoke.cjs" "$SERVER_INFO" "$mode"
}

@test "two-origin iframe contract authenticates, resizes, and tears down" {
  if [ -z "${PLAYWRIGHT_CLI:-}" ] && ! command -v playwright >/dev/null 2>&1; then
    skip "Playwright CLI not installed"
  fi

  run run_browser_smoke allowed
  if [ "$status" -ne 0 ]; then
    printf '%s\n' "$output" >&2
  fi
  [ "$status" -eq 0 ]
  [[ "$output" == *'"status":"pass"'* ]]
  [[ "$output" == *'"initSent":1'* ]]
  [[ "$output" == *'"maxAppliedHeight":500'* ]]
  [[ "$output" == *'"finalHeight":180'* ]]
  [[ "$output" == *'"crossOriginBlocked":true'* ]]
  [[ "$output" == *'"teardownSilent":true'* ]]
}

@test "frame-ancestors blocks the same fixture from a disallowed parent origin" {
  if [ -z "${PLAYWRIGHT_CLI:-}" ] && ! command -v playwright >/dev/null 2>&1; then
    skip "Playwright CLI not installed"
  fi

  run run_browser_smoke blocked
  if [ "$status" -ne 0 ]; then
    printf '%s\n' "$output" >&2
  fi
  [ "$status" -eq 0 ]
  [[ "$output" == *'"status":"pass"'* ]]
  [[ "$output" == *'"frameAncestorsBlocked":true'* ]]
  [[ "$output" == *'"acceptedReady":0'* ]]
}
