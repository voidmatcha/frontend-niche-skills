#!/usr/bin/env bats

run_browser_smoke() {
  local browser_name="$1"
  local playwright_cli
  playwright_cli="${PLAYWRIGHT_CLI:-}"
  if [ -z "$playwright_cli" ]; then
    playwright_cli="$(command -v playwright)" || return 127
  fi
  PLAYWRIGHT_CLI="$playwright_cli" node \
    "$BATS_TEST_DIRNAME/browser_smoke.cjs" "$browser_name"
}

@test "same-document history restores entry-specific offsets after async layout without a second jump" {
  if [ -z "${PLAYWRIGHT_CLI:-}" ] && ! command -v playwright >/dev/null 2>&1; then
    if [ -n "${CASEBOOK_BROWSERS:-}" ]; then
      echo "Playwright CLI not installed; requested engines: $CASEBOOK_BROWSERS" >&2
      false
    fi
    skip "Playwright CLI not installed"
  fi

  local browsers="${CASEBOOK_BROWSERS:-chromium}"
  local browser_name
  local -a requested_browsers
  IFS=',' read -r -a requested_browsers <<< "$browsers"

  for browser_name in "${requested_browsers[@]}"; do
    browser_name="${browser_name#"${browser_name%%[![:space:]]*}"}"
    browser_name="${browser_name%"${browser_name##*[![:space:]]}"}"
    [ -n "$browser_name" ]

    run run_browser_smoke "$browser_name"
    if [ "$status" -ne 0 ]; then
      printf 'history casebook failed for %s:\n%s\n' "$browser_name" "$output" >&2
    fi

    [ "$status" -eq 0 ]
    [[ "$output" == *"\"browserName\":\"$browser_name\""* ]]
    [[ "$output" == *'"status":"pass"'* ]]
    [[ "$output" == *'"entrySpecific":true'* ]]
    [[ "$output" == *'"readyBeforeEveryWrite":true'* ]]
    [[ "$output" == *'"noSecondJump":true'* ]]
    [[ "$output" == *'"sameDocumentOnly":true'* ]]
    [[ "$output" == *'"bfcacheResumes":0'* ]]
  done
}
