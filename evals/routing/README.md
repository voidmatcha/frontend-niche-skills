# Routing benchmark

The static dataset uses schema v3 and tests metadata-level selection across the
complete public domain skill catalog. The live export, prediction, and manifest
protocol uses v4 provenance envelopes. Repository checks do not invoke a model;
they
validate the dataset schema, discover the current `skills/*/SKILL.md` catalog,
and fail when a domain skill lacks a representative smoke case, a clear
collision smoke case, or a hard collision case.

The original representative and clear collision cases are smoke coverage: they
catch missing or badly regressed metadata, but many contain strong diagnostic
evidence. Hard collisions are the stronger routing claim. A limited static
phrase lint rejects a small set of explicit sibling exclusions, routing
instructions, and generic success-control phrases; it cannot establish answer
neutrality or detect every equivalent formulation. Human or independent-agent
semantic review remains required.

`clusters` organize related skills for browsing only and do not contribute any
score or scoring denominator. `plausible_edges` is a curated denominator of
user-plausible directed `from -> to` confusions, not a claim that all plausible
boundaries have been enumerated. Every collision edge must appear in that
registry, and every `critical` registry edge must have a hard case. Standard
registry edges may remain untested so registry review and case construction do
not define each other. The dataset stores review notes, not reviewer identity or
an independently auditable review artifact; do not describe it as independently
reviewed without adding digest-bound provenance.

Validate the static dataset:

```bash
python3 evals/routing/routing_benchmark.py validate
```

To run a live evaluation, first export a blinded prompt pack. It contains only
case IDs, prompts, allowed skill slugs, and the response instruction; expected
labels, collision hints, and rationales remain hidden:

```bash
python3 evals/routing/routing_benchmark.py export \
  > /tmp/frontend-routing-prompts.json
```

By default, live provenance reads each expected skill's `name` and
`description` from repository frontmatter. To reproduce a run against a stored
metadata baseline without reconstructing skill directories, provide a catalog
before the subcommand:

```bash
python3 evals/routing/routing_benchmark.py \
  --metadata-catalog /path/to/metadata-catalog.json \
  export > /tmp/frontend-routing-prompts.json
```

The catalog file is a JSON array whose entries contain exactly `name` and
`description`. It must cover every skill targeted by the dataset exactly once;
unknown, duplicate, missing, blank, malformed, or extra fields are rejected.
Input order is normalized by skill name before hashing. The option changes only
the live metadata provenance input: static dataset catalog coverage is still
validated from `--root`.

The exporter first applies a stable digest-based permutation, then assigns
opaque sequential IDs such as `route-001`. This keeps alphabetical catalog
order, internal case IDs, expected skills, and representative/collision kinds
out of the model input. The scorer reconstructs the opaque-to-internal mapping
from the local labeled dataset; no mapping file is exported.

The v4 export also includes `dataset_id`, `dataset_sha256`, and
`metadata_catalog_sha256`. The dataset digest covers canonicalized semantic JSON
content. The metadata digest covers the exact sorted skill names and
frontmatter descriptions exposed for this catalog. Copy all three fields into
the prediction file and run manifest unchanged. The scorer rejects an artifact
after either input changes instead of silently interpreting an old
`route-NNN` against new labels.

Give that file to the model with the installed skill metadata available, run
each case independently to avoid cross-case leakage, and do not give the model
repository access to the labeled dataset or scorer. Save outputs without
editing them:

```json
{
  "schema_version": 4,
  "dataset_id": "frontend-niche-skills-routing-v3",
  "dataset_sha256": "<copy exactly from export>",
  "metadata_catalog_sha256": "<copy exactly from export>",
  "predictions": [
    {
      "case_id": "route-001",
      "predicted_skill": "a11y-contract-testing"
    }
  ]
}
```

Prediction files follow `prediction-schema.json`.

Predictions always contain exactly one slug. Cases default to
`routing_mode: "exclusive"`. A natural multi-domain report may instead declare
`routing_mode: "primary-owner"` and list secondary valid destinations in
`acceptable_skills`. The scorer therefore reports exact-primary and acceptable
accuracy separately; an acceptable secondary choice never becomes the exact
primary label.

Copy `live-run-manifest.template.json` beside a live prediction file and record
the three exported provenance fields, exact model and role, UTC timestamp,
batch boundaries, prompt protocol, and independence caveat. A manifest
documents the run; it does not turn batched cases into independent
observations. `case_isolation: true` is valid only when every batch contains
exactly one case and `context_reset_between_cases` is also true. If a provider
reuses hidden state, caches, or conversation context across cases, record that
limitation.

Use ISO 8601 UTC timestamps ending in `Z`, or the explicit `not_captured`
sentinel when timing evidence was unavailable. `metadata_source` is
`installed_skill_metadata` when the runtime exposes installed metadata,
`inline_metadata_catalog` when the exact digest-bound catalog is placed in the
prompt, or `repository_skill_metadata` when the model reads repository files.
The first two require `model_repo_access: false`; the last requires `true` and
must not be reported as independent metadata-only routing.

Validate the manifest before scoring:

```bash
python3 evals/routing/routing_benchmark.py validate-run \
  --manifest /path/to/run-manifest.json
```

When the export used a stored catalog, validate with the same file:

```bash
python3 evals/routing/routing_benchmark.py \
  --metadata-catalog /path/to/metadata-catalog.json \
  validate-run --manifest /path/to/run-manifest.json
```

Validation resolves `predictions_path` relative to the manifest, requires that
file to exist, checks unique batch IDs and case membership, and requires the
union of batch case IDs to equal the prediction case IDs exactly. It also
requires the manifest and predictions to echo the same current dataset and
metadata digests.

Score a complete prediction file:

```bash
python3 evals/routing/routing_benchmark.py score \
  --predictions /path/to/predictions.json
```

Score a stored-catalog run against that same provenance input:

```bash
python3 evals/routing/routing_benchmark.py \
  --metadata-catalog /path/to/metadata-catalog.json \
  score --predictions /path/to/predictions.json
```

Complete coverage is required by default. `--allow-partial` is available for
exploratory batches, and `--min-accuracy 0.9` can turn an agreed threshold into
a failing exit status.

Live protocol v4 is intentionally fail-closed and is not file-compatible with
v3 predictions or manifests. The `validate`, `export`, `validate-run`, and
`score` CLI commands keep the same interface, but old live artifacts must be
regenerated from a fresh v4 export. Static `cases.json` remains schema v3.

The scorer reports:

- representative smoke accuracy;
- all-collision and hard-collision accuracy;
- per-skill recall and overall accuracy;
- exact-primary and acceptable accuracy, including separate primary-owner
  metrics;
- accuracy for each tested directed `expected -> confusable` edge;
- registered, tested-registered, and critical edge counts and coverage;
- unregistered tested-edge count, which must remain zero for a valid dataset;
- confusion counts.

For the current catalog, there are 138 cases: 40 representative smoke cases,
42 collision smoke cases, and 56 hard collision cases. The curated registry
contains 100 directed edges. Cases test 98 of those edges, so registered-edge
coverage is intentionally incomplete at `98 / 100`; all 56 critical edges have
hard cases. These are dataset-coverage facts, not results from a live model
run.

Schema v2 reported `78 / 184` or about 42.4% cluster-pair coverage. That value
used the Cartesian product of broad cluster members. Schema v3 uses a curated
plausible-boundary denominator, with `98 / 100` edges tested in the current
dataset. The two schema versions are not comparable and must not be presented as a
performance improvement or a completeness claim.

Use hard-collision, exact-primary, acceptable, and registered-edge results for
discrimination claims. Never commit fabricated predictions. The recorded
[2026-07-31 targeted metadata comparison](./results/2026-07-31-targeted-metadata-comparison/README.md)
covers 16 cases and reports both its observed delta and its limits; it is not a
catalog-wide score.
