# Full-catalog routing run and boundary edit — 2026-09-25

Five blinded, full-catalog runs of the 138-case dataset: before and after one boundary edit, after a second review pass, after an ssr/datetime boundary fix, and after the release-gate review fixes. It is evidence for these metadata iterations, not a stable model score: each run was made once, and cases inside a batch shared context.

## Result

| Catalog | Overall | Hard collision | Observed confusions |
| --- | ---: | ---: | --- |
| Name-only baseline (descriptions replaced by names) | 134/138 (97.1%) | 52/56 (92.9%) | `a11y-contract-testing -> js-form-validation-contracts`, `browser-storage-durability-contracts -> browser-page-lifecycle-bfcache-contracts`, `download-export-safety -> user-activation-contracts`, `frontend-security-baseline -> payment-page-client-security` |
| Before the boundary edit | 136/138 (98.6%) | 54/56 (96.4%) | `frontend-security-baseline -> payment-page-client-security`, `media-capture-device-contracts -> webview-bridge-pages` |
| After the boundary edit | 138/138 (100%) | 56/56 (100%) | none |
| After a second review pass | 137/138 (99.3%) | 55/56 (98.2%) | `ssr-hydration-mismatch -> datetime-correctness` |
| After the ssr/datetime boundary fix | 138/138 (100%) | 56/56 (100%) | none |
| After the release-gate review fixes | 138/138 (100%) | 56/56 (100%) | none |

Between the first two runs, only two frontmatter descriptions changed; the other 38 are byte-identical across the two metadata files:

- `media-capture-device-contracts` now sends only the native app's permission grant and bridge timing to `webview-bridge-pages`, and keeps track acquisition, replacement, and teardown inside a WebView.
- `payment-page-client-security` now sends auth-token storage, XSS, opener, and return-URL checks to `frontend-security-baseline` even on a checkout page. Its body previously limited that route to "outside payment context", which contradicted its own description.

Both misses were hard-collision cases that the old wording pointed the wrong way. The after-run fixed both and changed no other decision's correctness. This is an observed one-run delta, not proof that the edit alone caused it.

A third run followed a second review pass that changed seven descriptions (`browser-page-lifecycle-bfcache-contracts`, `frontend-auth-flow-contracts`, `history-scroll-restoration-contracts`, `js-form-validation-contracts`, `media-capture-device-contracts`, `semantic-markup-contracts`, `webview-bridge-pages`). It missed one hard collision, a zoned appointment whose server and first client render differ. Both involved descriptions (`ssr-hydration-mismatch`, `datetime-correctness`) were identical in all three runs, and the first two runs routed that case correctly, so the miss is not a regression from the seven edited descriptions. It did expose a real ambiguity: each of those two descriptions pointed zone-driven server/client divergence at the other, and the router cited that. After this run both were rewritten so `ssr-hydration-mismatch` owns the server-versus-first-render divergence and `datetime-correctness` owns whether the stored value and zone are right. A fourth run with only those two descriptions changed routed that case to `ssr-hydration-mismatch` and scored 138/138. A fifth run followed the release-gate review, which reworded five descriptions (`frontend-data-fetching-cache-contracts`, `frontend-security-baseline`, `iframe-embed-contracts`, `media-capture-device-contracts`, `user-activation-contracts`) so both sides of several boundaries agree; it also scored 138/138. One batched run per catalog still does not measure stability.

The name-only baseline is a metadata ablation run against the final catalog: every description is replaced by the skill name, and nothing else changes. All 40 representative cases still routed correctly; the four misses are hard collisions on boundaries whose descriptions were sharpened in this release. So on this dataset the descriptions matter mainly for overlapping boundaries, and the gap is four cases in one run, not a measured effect size.

## Protocol

- Model: Anthropic Claude Opus (`claude-opus-5-5`), run as Claude Code subagents; temperature was not exposed.
- The exported prompt pack was split into six batches of 23 opaque cases. Each batch went to one fresh subagent whose input file held the exact digest-bound name/description catalog and the blinded prompts.
- Subagents were instructed to read only their batch file. Repository access was withheld by instruction, not by a sandbox, so `model_repo_access: false` reflects the instruction rather than an enforced boundary.
- Cases in a batch shared one context (`case_isolation: false`). Provider cache and hidden-state reuse were not observable.

The dataset digest is `c0160a3364d2ce8ffdafeb94b03b777652c2397f8459c1187e03febd54f6cd18`.

## Reproduce validation and scoring

From the repository root:

```bash
RESULT=evals/routing/results/2026-09-25-full-catalog-boundary-edit

for run in name-only before after second-pass ssr-datetime-fix release-gate; do
  python3 evals/routing/routing_benchmark.py \
    --metadata-catalog "$RESULT/$run-metadata.json" \
    validate-run --manifest "$RESULT/$run-run-manifest.json"
  python3 evals/routing/routing_benchmark.py \
    --metadata-catalog "$RESULT/$run-metadata.json" \
    score --predictions "$RESULT/$run-predictions.json"
done
```

The saved scorer outputs are:

- [name-only-score.json](./name-only-score.json)
- [before-score.json](./before-score.json)
- [after-score.json](./after-score.json)
- [second-pass-score.json](./second-pass-score.json)
- [ssr-datetime-fix-score.json](./ssr-datetime-fix-score.json)
- [release-gate-score.json](./release-gate-score.json)
