#!/usr/bin/env bats

setup() {
  REPO_ROOT="${BATS_TEST_DIRNAME}/../../.."
  SCRIPT="$REPO_ROOT/skills/design-to-code-fidelity/scripts/visual-diff.sh"

  if command -v magick >/dev/null 2>&1; then
    MK=(magick)
  elif command -v convert >/dev/null 2>&1; then
    MK=(convert)
  else
    skip "ImageMagick (magick/convert) not installed"
  fi

  TMPDIR_TEST="$(mktemp -d)"
  REF="$TMPDIR_TEST/ref.png"
  SAME="$TMPDIR_TEST/same.png"
  DRIFT="$TMPDIR_TEST/drift.png"
  SMALL="$TMPDIR_TEST/small.png"

  # Two identical 200x200 white frames (PASS), one with a large black block
  # (DRIFT), and one smaller frame (dimension mismatch).
  "${MK[@]}" -size 200x200 xc:white "$REF"
  "${MK[@]}" -size 200x200 xc:white "$SAME"
  "${MK[@]}" -size 200x200 xc:white -fill black -draw "rectangle 20,20 120,120" "$DRIFT"
  "${MK[@]}" -size 120x120 xc:white "$SMALL"
}

teardown() {
  rm -rf "$TMPDIR_TEST"
}

@test "visual-diff PASS on identical frames (exit 0)" {
  run bash "$SCRIPT" "$REF" "$SAME"
  [ "$status" -eq 0 ]
  [[ "$output" == *"STATUS=PASS"* ]]
}

@test "visual-diff DRIFT on a large diff block under STRUCT_GATE (exit 1)" {
  run env AE_FUZZ=10% STRUCT_GATE=1 bash "$SCRIPT" "$REF" "$DRIFT" "$TMPDIR_TEST/diff.png"
  [ "$status" -eq 1 ]
  [[ "$output" == *"STRUCT=DRIFT"* ]]
  [[ "$output" == *"STRUCT_GATE: FAIL"* ]]
}

@test "visual-diff flags dimension mismatch and fails (exit 1)" {
  run bash "$SCRIPT" "$REF" "$SMALL"
  [ "$status" -eq 1 ]
  [[ "$output" == *"SIZE_DELTA="* ]]
  [[ "$output" == *"dimension mismatch"* ]]
}

@test "visual-diff reports missing render file (exit 2)" {
  run bash "$SCRIPT" "$REF" "$TMPDIR_TEST/does-not-exist.png"
  [ "$status" -eq 2 ]
  [[ "$output" == *"render not found"* ]]
}

@test "visual-diff reports missing reference file (exit 2)" {
  run bash "$SCRIPT" "$TMPDIR_TEST/does-not-exist.png" "$SAME"
  [ "$status" -eq 2 ]
  [[ "$output" == *"reference not found"* ]]
}

@test "visual-diff cleans temporary structural images" {
  run env TMPDIR="$TMPDIR_TEST" STRUCT_GATE=1 bash "$SCRIPT" "$REF" "$SAME" "$TMPDIR_TEST/diff-cleanup.png"
  [ "$status" -eq 0 ]
  [ -z "$(find "$TMPDIR_TEST" -maxdepth 1 -name 'visual-diff-*' -print)" ]
}
