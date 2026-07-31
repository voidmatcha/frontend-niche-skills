# Targeted metadata comparison — 2026-07-31

This is a blinded, partial routing comparison for the eight newly added domain
skills and eight of their hard near-neighbor boundaries. It is evidence for one
metadata iteration, not a catalog-wide model score.

## Result

| Catalog | Overall | Representative | Hard collision | Observed confusion |
| --- | ---: | ---: | ---: | --- |
| Name-only baseline | 15/16 (93.75%) | 8/8 | 7/8 | `download-export-safety -> user-activation-contracts` |
| Current metadata before the boundary edit | 15/16 (93.75%) | 8/8 | 7/8 | `download-export-safety -> user-activation-contracts` |
| Current metadata after the boundary edit | 16/16 (100%) | 8/8 | 8/8 | none |

The first comparison produced no delta: the name-only baseline and current
metadata both missed the same answer-neutral export/activation case. The only
instruction change then made was to the two frontmatter descriptions:

- keep `download-export-safety` primary for observed payload leakage, stale
  fallback content, or success-before-settlement;
- use `user-activation-contracts` as primary when inactive or consumed
  activation is the evidenced gated-call failure.

The second current run selected `download-export-safety` for that case and kept
the other 15 decisions unchanged. This is an observed one-run delta, not proof
that the metadata change alone caused the improvement.

## Protocol

- Model: OpenAI `gpt-5.5`; exact backend version and temperature were not
  exposed.
- Each prediction used a fresh `codex exec --ephemeral` process, one opaque case
  per process, an empty read-only working directory, and a strict one-field JSON
  output schema.
- User config, rules, plugins, remote plugins, memories, workspace
  dependencies, and all discovered ambient skills were disabled. The exact
  digest-bound metadata catalog was supplied inline.
- Temporary execution logs showed 16 unique session IDs per run and no tool
  calls. The logs are not committed because they repeat the complete prompt
  catalog and are not required to rescore the saved predictions.
- Provider cache and hidden-state reuse were not observable.

The selected set and opaque IDs are in [selection.json](./selection.json). The
dataset digest is
`c0160a3364d2ce8ffdafeb94b03b777652c2397f8459c1187e03febd54f6cd18`.

## Reproduce validation and scoring

From the repository root:

```bash
RESULT=evals/routing/results/2026-07-31-targeted-metadata-comparison

python3 evals/routing/routing_benchmark.py \
  --metadata-catalog "$RESULT/baseline-metadata.json" \
  validate-run --manifest "$RESULT/baseline-run-manifest.json"
python3 evals/routing/routing_benchmark.py \
  --metadata-catalog "$RESULT/baseline-metadata.json" \
  score --predictions "$RESULT/baseline-predictions.json" --allow-partial

python3 evals/routing/routing_benchmark.py \
  --metadata-catalog "$RESULT/current-before-metadata.json" \
  validate-run --manifest "$RESULT/current-before-run-manifest.json"
python3 evals/routing/routing_benchmark.py \
  --metadata-catalog "$RESULT/current-before-metadata.json" \
  score --predictions "$RESULT/current-before-predictions.json" --allow-partial

python3 evals/routing/routing_benchmark.py \
  --metadata-catalog "$RESULT/current-after-metadata.json" \
  validate-run --manifest "$RESULT/current-after-run-manifest.json"
python3 evals/routing/routing_benchmark.py \
  --metadata-catalog "$RESULT/current-after-metadata.json" \
  score --predictions "$RESULT/current-after-predictions.json" --allow-partial
```

The saved scorer outputs are:

- [baseline-score.json](./baseline-score.json)
- [current-before-score.json](./current-before-score.json)
- [current-after-score.json](./current-after-score.json)

## Limits

- This covers 16 of 138 cases and 8 of 100 registered directed edges.
- Each catalog/case pair has one scored observation; no confidence interval or
  repeated-run stability claim follows from it.
- The name-only baseline is a metadata ablation, not the previously published
  pack.
- The run measures routing selection only. It does not grade whether a loaded
  skill produces a correct diagnosis or fix.
- A full paired 138-case run is still required before making a catalog-wide
  routing-performance claim.
