#!/usr/bin/env bats

@test "repo routing benchmark validator and scorer tests pass" {
  repo_root="${BATS_TEST_DIRNAME}/../../.."

  run python3 -m unittest discover \
    -s "$repo_root/evals/routing/tests" \
    -p "test_*.py" \
    -v

  [ "$status" -eq 0 ]
}

@test "routing registry validates the curated 138-case contract" {
  repo_root="${BATS_TEST_DIRNAME}/../../.."

  run python3 "$repo_root/evals/routing/routing_benchmark.py" validate

  [ "$status" -eq 0 ]
  [[ "$output" == *"138 cases"* ]]
  [[ "$output" == *"100 plausible edges"* ]]
  [[ "$output" == *"40 domain skills"* ]]
}

@test "recorded targeted comparison manifests validate and scores reproduce" {
  repo_root="${BATS_TEST_DIRNAME}/../../.."
  benchmark="$repo_root/evals/routing/routing_benchmark.py"
  result_dir="$repo_root/evals/routing/results/2026-07-31-targeted-metadata-comparison"

  for variant in baseline current-before current-after; do
    run python3 "$benchmark" \
      --metadata-catalog "$result_dir/${variant}-metadata.json" \
      validate-run --manifest "$result_dir/${variant}-run-manifest.json"

    [ "$status" -eq 0 ]

    run bash -c \
      'python3 "$1" --metadata-catalog "$2" score --predictions "$3" --allow-partial | cmp - "$4"' \
      _ \
      "$benchmark" \
      "$result_dir/${variant}-metadata.json" \
      "$result_dir/${variant}-predictions.json" \
      "$result_dir/${variant}-score.json"

    [ "$status" -eq 0 ]
  done
}
