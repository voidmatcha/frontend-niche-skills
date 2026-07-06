#!/usr/bin/env bats

setup() {
  REPO_ROOT="${BATS_TEST_DIRNAME}/../../.."
  SCRIPT="$REPO_ROOT/skills/design-to-code-fidelity/scripts/figma-export.sh"
  TMPDIR_TEST="$(mktemp -d)"
}

teardown() {
  rm -rf "$TMPDIR_TEST"
}

@test "figma-export requires a token" {
  run env -u FIGMA_TOKEN -u FIGMA_API_KEY "$SCRIPT" file 1-2 "$TMPDIR_TEST/out"
  [ "$status" -eq 2 ]
  [[ "$output" == *"set FIGMA_TOKEN or FIGMA_API_KEY"* ]]
}

@test "figma-export reports 429 without waiting on Retry-After" {
  mkdir -p "$TMPDIR_TEST/bin"
  cat > "$TMPDIR_TEST/bin/curl" <<'SH'
#!/usr/bin/env bash
out=""
hdr=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    -o) out="$2"; shift 2 ;;
    -D) hdr="$2"; shift 2 ;;
    -w) shift 2 ;;
    *) shift ;;
  esac
done
printf 'HTTP/2 429\nretry-after: 129899\nx-figma-rate-limit-type: low\nx-figma-plan-tier: org\n' > "$hdr"
printf '{"status":429,"err":"Rate limit exceeded"}' > "$out"
printf '429'
SH
  chmod +x "$TMPDIR_TEST/bin/curl"

  run env PATH="$TMPDIR_TEST/bin:$PATH" FIGMA_API_KEY=fake "$SCRIPT" file 1-2 "$TMPDIR_TEST/out"
  [ "$status" -eq 2 ]
  [[ "$output" == *"Figma Images API HTTP 429"* ]]
  [[ "$output" == *"retry-after: 129899"* ]]
}

@test "figma-export downloads returned image URLs" {
  mkdir -p "$TMPDIR_TEST/bin"
  printf 'png-bytes' > "$TMPDIR_TEST/source.png"
  cat > "$TMPDIR_TEST/bin/curl" <<SH
#!/usr/bin/env bash
out=""
hdr=""
while [ "\$#" -gt 0 ]; do
  case "\$1" in
    -o) out="\$2"; shift 2 ;;
    -D) hdr="\$2"; shift 2 ;;
    -w) shift 2 ;;
    *) shift ;;
  esac
done
printf 'HTTP/2 200\n' > "\$hdr"
printf '{"images":{"1:2":"file://$TMPDIR_TEST/source.png"}}' > "\$out"
printf '200'
SH
  chmod +x "$TMPDIR_TEST/bin/curl"

  run env PATH="$TMPDIR_TEST/bin:$PATH" FIGMA_API_KEY=fake "$SCRIPT" file 1-2 "$TMPDIR_TEST/out"
  [ "$status" -eq 0 ]
  [[ "$output" == *"saved $TMPDIR_TEST/out/1_2.png"* ]]
  cmp "$TMPDIR_TEST/source.png" "$TMPDIR_TEST/out/1_2.png"
}
