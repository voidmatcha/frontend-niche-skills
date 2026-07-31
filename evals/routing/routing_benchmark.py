#!/usr/bin/env python3
"""Validate the routing dataset and score externally produced predictions."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 3
LIVE_PROTOCOL_VERSION = 4
CASE_KINDS = {"representative", "collision"}
DIFFICULTIES = {"smoke", "hard"}
ROUTING_MODES = {"exclusive", "primary-owner"}
EDGE_PRIORITIES = {"standard", "critical"}
HARD_PROMPT_CUES = (
    " not ",
    "not the adjacent",
    "rather than",
    "instead of",
    "route to",
    "route this",
    "belongs to",
    "owns the bug",
    "owns this",
    "the failure is",
    "the problem is",
    "the defect is",
    "is healthy",
    "remains healthy",
    "works correctly",
    "working correctly",
    "keeps user activation active",
    "completes correctly",
    "complete correctly",
    "behaves correctly",
    "builds the correct",
    "handles clipboard rejection truthfully",
    "is correct",
    "are correct",
    "is reliable",
    "are reliable",
    "focus on",
    "keep diagnosis",
)
REQUIRED_CASE_FIELDS = {
    "id",
    "kind",
    "difficulty",
    "prompt",
    "expected_skill",
    "confusable_with",
    "rationale",
}
OPTIONAL_CASE_FIELDS = {"routing_mode", "acceptable_skills"}
REQUIRED_EDGE_FIELDS = {"from", "to", "priority", "basis", "review_note"}
REQUIRED_PREDICTION_FIELDS = {"case_id", "predicted_skill"}
REQUIRED_PREDICTION_ROOT_FIELDS = {
    "schema_version",
    "dataset_id",
    "dataset_sha256",
    "metadata_catalog_sha256",
    "predictions",
}
REQUIRED_MANIFEST_FIELDS = {
    "benchmark_schema_version",
    "dataset_id",
    "dataset_sha256",
    "metadata_catalog_sha256",
    "run_id",
    "created_at_utc",
    "model",
    "prompt_protocol",
    "batches",
    "predictions_path",
    "independence_caveat",
}
MODEL_FIELDS = {"provider", "name", "version", "role"}
PROTOCOL_FIELDS = {
    "metadata_source",
    "selection_instruction",
    "case_isolation",
    "context_reset_between_cases",
    "model_repo_access",
    "temperature",
    "notes",
}
BATCH_FIELDS = {
    "id",
    "case_ids",
    "started_at_utc",
    "completed_at_utc",
}
METADATA_ACCESS = {
    "installed_skill_metadata": False,
    "inline_metadata_catalog": False,
    "repository_skill_metadata": True,
}
METADATA_CATALOG_FIELDS = {"name", "description"}
INDEPENDENCE_CAVEAT_PLACEHOLDERS = {
    (
        "Record any hidden-state, cache, conversation-context, retry, or "
        "provider behavior that may make case outcomes statistically dependent."
    ),
}


def catalog_skills(root: Path) -> list[str]:
    """Return skill directory names from the repository's public catalog."""
    return sorted(
        path.parent.name
        for path in (root / "skills").glob("*/SKILL.md")
        if path.is_file()
    )


def _canonical_json_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def dataset_sha256(dataset: dict[str, Any]) -> str:
    """Bind a run to the semantic JSON content of the labeled dataset."""
    return _canonical_json_sha256(dataset)


def _frontmatter_scalar(value: str, skill_file: Path, field: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] == '"':
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"skill metadata has invalid quoted {field}: {skill_file}"
            ) from exc
    elif len(value) >= 2 and value[0] == value[-1] == "'":
        value = value[1:-1].replace("''", "'")
    if not value:
        raise ValueError(f"skill metadata has empty {field}: {skill_file}")
    return value


def _frontmatter_metadata(skill_file: Path) -> dict[str, str]:
    try:
        text = skill_file.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"cannot read skill metadata from {skill_file}: {exc}") from exc
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"skill metadata has no YAML frontmatter: {skill_file}")
    metadata: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        field, value = line.split(":", 1)
        if field in {"name", "description"}:
            metadata[field] = _frontmatter_scalar(value, skill_file, field)
    missing = sorted({"name", "description"} - set(metadata))
    if missing:
        raise ValueError(
            f"skill metadata missing {', '.join(missing)}: {skill_file}"
        )
    return metadata


def _normalized_metadata_catalog(
    dataset: dict[str, Any],
    root: Path,
    metadata_catalog: Path | None = None,
) -> list[dict[str, str]]:
    expected_names = sorted(
        {case["expected_skill"] for case in dataset["cases"]}
    )
    if metadata_catalog is None:
        raw_catalog: Any = [
            _frontmatter_metadata(root / "skills" / skill / "SKILL.md")
            for skill in expected_names
        ]
    else:
        raw_catalog = _read_json(metadata_catalog)

    if not isinstance(raw_catalog, list):
        raise ValueError("metadata catalog root must be an array")

    errors: list[str] = []
    names: list[str] = []
    normalized: list[dict[str, str]] = []
    for index, entry in enumerate(raw_catalog):
        prefix = f"metadata catalog entry {index + 1}"
        if not isinstance(entry, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if set(entry) != METADATA_CATALOG_FIELDS:
            errors.append(f"{prefix} must contain only name and description")
        name = entry.get("name")
        description = entry.get("description")
        if not _is_nonempty_string(name):
            errors.append(f"{prefix} name must be a non-empty string")
        else:
            names.append(name)
        if not _is_nonempty_string(description):
            errors.append(f"{prefix} description must be a non-empty string")
        if _is_nonempty_string(name) and _is_nonempty_string(description):
            normalized.append({"name": name, "description": description})

    duplicate_names = _duplicates(names)
    if duplicate_names:
        errors.append(
            "duplicate metadata catalog skills: " + ", ".join(duplicate_names)
        )
    expected_set = set(expected_names)
    supplied_set = set(names)
    unknown_names = sorted(supplied_set - expected_set)
    if unknown_names:
        errors.append(
            "metadata catalog has unknown skills: " + ", ".join(unknown_names)
        )
    missing_names = sorted(expected_set - supplied_set)
    if missing_names:
        errors.append(
            "metadata catalog is missing skills: " + ", ".join(missing_names)
        )
    if errors:
        raise ValueError("; ".join(errors))
    return sorted(normalized, key=lambda entry: entry["name"])


def metadata_catalog_sha256(
    dataset: dict[str, Any],
    root: Path,
    metadata_catalog: Path | None = None,
) -> str:
    """Bind a run to the exact name/description catalog exposed to the model."""
    return _canonical_json_sha256(
        _normalized_metadata_catalog(dataset, root, metadata_catalog)
    )


def _provenance_fields(
    dataset: dict[str, Any],
    root: Path,
    metadata_catalog: Path | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": LIVE_PROTOCOL_VERSION,
        "dataset_id": dataset["dataset_id"],
        "dataset_sha256": dataset_sha256(dataset),
        "metadata_catalog_sha256": metadata_catalog_sha256(
            dataset, root, metadata_catalog
        ),
    }


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _duplicates(values: list[str]) -> list[str]:
    return sorted(name for name, count in Counter(values).items() if count > 1)


def validate_dataset(dataset: Any, root: Path) -> list[str]:
    """Return deterministic validation errors; an empty list means valid."""
    errors: list[str] = []
    if not isinstance(dataset, dict):
        return ["dataset root must be an object"]

    required_top = {
        "schema_version",
        "dataset_id",
        "catalog",
        "clusters",
        "plausible_edges",
        "cases",
    }
    missing_top = sorted(required_top - set(dataset))
    unknown_top = sorted(set(dataset) - required_top)
    if missing_top:
        errors.append(f"dataset missing fields: {', '.join(missing_top)}")
    if unknown_top:
        errors.append(f"dataset has unknown fields: {', '.join(unknown_top)}")
    if dataset.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if not _is_nonempty_string(dataset.get("dataset_id")):
        errors.append("dataset_id must be a non-empty string")

    catalog = dataset.get("catalog")
    excluded: list[str] = []
    if not isinstance(catalog, dict):
        errors.append("catalog must be an object")
    else:
        if set(catalog) != {"excluded_skills"}:
            errors.append("catalog must contain only excluded_skills")
        raw_excluded = catalog.get("excluded_skills")
        if not isinstance(raw_excluded, list) or not all(
            _is_nonempty_string(item) for item in raw_excluded
        ):
            errors.append("catalog.excluded_skills must be an array of non-empty strings")
        else:
            excluded = raw_excluded
            duplicate_exclusions = _duplicates(excluded)
            if duplicate_exclusions:
                errors.append(
                    "duplicate excluded skills: " + ", ".join(duplicate_exclusions)
                )

    all_skills = catalog_skills(root)
    unknown_exclusions = sorted(set(excluded) - set(all_skills))
    if unknown_exclusions:
        errors.append("excluded skills not in catalog: " + ", ".join(unknown_exclusions))
    domain_skills = sorted(set(all_skills) - set(excluded))
    domain_set = set(domain_skills)

    clusters = dataset.get("clusters")
    cluster_ids: list[str] = []
    if not isinstance(clusters, list) or not clusters:
        errors.append("clusters must be a non-empty array")
        clusters = []
    for index, cluster in enumerate(clusters):
        prefix = f"cluster {index + 1}"
        if not isinstance(cluster, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if set(cluster) != {"id", "description", "members"}:
            errors.append(f"{prefix} must contain only id, description, and members")
        cluster_id = cluster.get("id")
        description = cluster.get("description")
        members = cluster.get("members")
        if not _is_nonempty_string(cluster_id):
            errors.append(f"{prefix} id must be a non-empty string")
            continue
        cluster_ids.append(cluster_id)
        if not _is_nonempty_string(description):
            errors.append(f"cluster {cluster_id} description must be a non-empty string")
        if (
            not isinstance(members, list)
            or len(members) < 2
            or not all(_is_nonempty_string(member) for member in members)
        ):
            errors.append(f"cluster {cluster_id} members must contain at least two skill names")
            continue
        duplicate_members = _duplicates(members)
        if duplicate_members:
            errors.append(
                f"cluster {cluster_id} has duplicate members: {', '.join(duplicate_members)}"
            )
        unknown_members = sorted(set(members) - domain_set)
        if unknown_members:
            errors.append(
                f"cluster {cluster_id} references unknown skills: {', '.join(unknown_members)}"
            )
    duplicate_cluster_ids = _duplicates(cluster_ids)
    if duplicate_cluster_ids:
        errors.append("duplicate cluster ids: " + ", ".join(duplicate_cluster_ids))

    plausible_edges = dataset.get("plausible_edges")
    registered_edges: set[tuple[str, str]] = set()
    critical_edges: set[tuple[str, str]] = set()
    if not isinstance(plausible_edges, list) or not plausible_edges:
        errors.append("plausible_edges must be a non-empty array")
        plausible_edges = []
    for index, edge in enumerate(plausible_edges):
        prefix = f"plausible edge {index + 1}"
        if not isinstance(edge, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if set(edge) != REQUIRED_EDGE_FIELDS:
            errors.append(
                f"{prefix} must contain only from, to, priority, basis, and review_note"
            )
        source = edge.get("from")
        target = edge.get("to")
        priority = edge.get("priority")
        if source not in domain_set:
            errors.append(f"{prefix} from references unknown skill: {source!r}")
        if target not in domain_set:
            errors.append(f"{prefix} to references unknown skill: {target!r}")
        if source == target and source in domain_set:
            errors.append(f"{prefix} cannot be a self edge: {source}")
        pair = (source, target)
        if source in domain_set and target in domain_set and source != target:
            if pair in registered_edges:
                errors.append(f"duplicate plausible edge: {source} -> {target}")
            registered_edges.add(pair)
            if priority == "critical":
                critical_edges.add(pair)
        if priority not in EDGE_PRIORITIES:
            errors.append(f"{prefix} priority must be standard or critical")
        if not _is_nonempty_string(edge.get("basis")):
            errors.append(f"{prefix} basis must be a non-empty string")
        if (
            not _is_nonempty_string(edge.get("review_note"))
            or len(edge["review_note"]) < 40
        ):
            errors.append(f"{prefix} review_note must record the reviewed boundary")

    cases = dataset.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append("cases must be a non-empty array")
        cases = []
    case_ids: list[str] = []
    coverage: dict[str, set[tuple[str, str]]] = defaultdict(set)
    collision_edges: set[tuple[str, str]] = set()
    hard_collision_edges: set[tuple[str, str]] = set()
    for index, case in enumerate(cases):
        prefix = f"case {index + 1}"
        if not isinstance(case, dict):
            errors.append(f"{prefix} must be an object")
            continue
        missing = sorted(REQUIRED_CASE_FIELDS - set(case))
        unknown = sorted(set(case) - REQUIRED_CASE_FIELDS - OPTIONAL_CASE_FIELDS)
        if missing:
            errors.append(f"{prefix} missing fields: {', '.join(missing)}")
        if unknown:
            errors.append(f"{prefix} has unknown fields: {', '.join(unknown)}")
        case_id = case.get("id")
        kind = case.get("kind")
        difficulty = case.get("difficulty")
        prompt = case.get("prompt")
        expected = case.get("expected_skill")
        confusable = case.get("confusable_with")
        rationale = case.get("rationale")
        routing_mode = case.get("routing_mode", "exclusive")
        acceptable = case.get("acceptable_skills", [])
        if not _is_nonempty_string(case_id):
            errors.append(f"{prefix} id must be a non-empty string")
        else:
            case_ids.append(case_id)
        if kind not in CASE_KINDS:
            errors.append(f"{prefix} kind must be representative or collision")
        if difficulty not in DIFFICULTIES:
            errors.append(f"{prefix} difficulty must be smoke or hard")
        if kind == "representative" and difficulty == "hard":
            errors.append(f"{prefix} representative cases must use smoke difficulty")
        if routing_mode not in ROUTING_MODES:
            errors.append(f"{prefix} routing_mode must be exclusive or primary-owner")
        if not isinstance(acceptable, list) or not all(
            _is_nonempty_string(skill) for skill in acceptable
        ):
            errors.append(f"{prefix} acceptable_skills must be an array of skill names")
            acceptable = []
        else:
            duplicate_acceptable = _duplicates(acceptable)
            if duplicate_acceptable:
                errors.append(
                    f"{prefix} has duplicate acceptable skills: "
                    + ", ".join(duplicate_acceptable)
                )
            unknown_acceptable = sorted(set(acceptable) - domain_set)
            if unknown_acceptable:
                errors.append(
                    f"{prefix} acceptable_skills has unknown skills: "
                    + ", ".join(unknown_acceptable)
                )
            if expected in acceptable:
                errors.append(
                    f"{prefix} expected_skill cannot also be acceptable_skills"
                )
        if routing_mode == "exclusive" and acceptable:
            errors.append(f"{prefix} exclusive case must have empty acceptable_skills")
        if routing_mode == "primary-owner" and not acceptable:
            errors.append(
                f"{prefix} primary-owner case requires acceptable_skills"
            )
        if not _is_nonempty_string(prompt):
            errors.append(f"{prefix} prompt must be a non-empty string")
        elif len(prompt.split()) < 12 or len(prompt) < 80:
            errors.append(f"{prefix} prompt is too short to be a realistic routing report")
        elif any(skill in prompt for skill in all_skills):
            errors.append(f"{prefix} prompt must not name a skill slug")
        elif difficulty == "hard" and any(
            cue in f" {prompt.lower()} " for cue in HARD_PROMPT_CUES
        ):
            errors.append(f"{prefix} hard prompt must remain answer-neutral")
        if expected not in domain_set:
            errors.append(f"{prefix} expected_skill is not a domain catalog skill: {expected!r}")
        elif kind in CASE_KINDS and difficulty in DIFFICULTIES:
            coverage[expected].add((kind, difficulty))
        if not isinstance(confusable, list) or not all(
            _is_nonempty_string(skill) for skill in confusable
        ):
            errors.append(f"{prefix} confusable_with must be an array of skill names")
            confusable = []
        else:
            duplicate_confusables = _duplicates(confusable)
            if duplicate_confusables:
                errors.append(
                    f"{prefix} has duplicate confusable skills: {', '.join(duplicate_confusables)}"
                )
            unknown_confusables = sorted(set(confusable) - domain_set)
            if unknown_confusables:
                errors.append(
                    f"{prefix} confusable_with has unknown skills: {', '.join(unknown_confusables)}"
                )
            if expected in confusable:
                errors.append(f"{prefix} expected_skill cannot also be confusable_with")
        if kind == "representative" and confusable:
            errors.append(f"{prefix} representative case must have empty confusable_with")
        if kind == "collision":
            if not confusable:
                errors.append(f"{prefix} collision case requires confusable_with")
            elif difficulty == "hard" and len(confusable) != 1:
                errors.append(
                    f"{prefix} hard collision must test exactly one confusable edge"
                )
            elif expected in domain_set:
                for skill in confusable:
                    if skill not in domain_set:
                        continue
                    edge = (expected, skill)
                    collision_edges.add(edge)
                    if edge not in registered_edges:
                        errors.append(
                            f"{prefix} collision edge is not in plausible_edges: "
                            f"{expected} -> {skill}"
                        )
                    if difficulty == "hard":
                        hard_collision_edges.add(edge)
        if not _is_nonempty_string(rationale) or len(rationale) < 40:
            errors.append(f"{prefix} rationale must explain the routing boundary")

    duplicate_case_ids = _duplicates(case_ids)
    if duplicate_case_ids:
        errors.append("duplicate case id: " + ", ".join(duplicate_case_ids))
    required_shapes = {
        ("representative", "smoke"),
        ("collision", "smoke"),
        ("collision", "hard"),
    }
    for skill in domain_skills:
        missing_shapes = sorted(required_shapes - coverage[skill])
        if missing_shapes:
            errors.append(
                f"catalog skill {skill} missing coverage: "
                + ", ".join(f"{kind}/{difficulty}" for kind, difficulty in missing_shapes)
            )
    missing_critical_hard = sorted(critical_edges - hard_collision_edges)
    for source, target in missing_critical_hard:
        errors.append(
            f"critical plausible edge lacks answer-neutral hard coverage: "
            f"{source} -> {target}"
        )
    stale_targets = sorted(set(coverage) - domain_set)
    if stale_targets:
        errors.append("cases target skills outside catalog: " + ", ".join(stale_targets))
    return errors


def score_predictions(
    dataset: dict[str, Any],
    predictions: Any,
    root: Path | None = None,
    metadata_catalog: Path | None = None,
    *,
    allow_partial: bool = False,
) -> tuple[dict[str, Any], list[str]]:
    """Score predictions after strict structural and coverage validation."""
    errors: list[str] = []
    if root is None:
        root = _default_root()
    if not isinstance(predictions, dict):
        return {}, ["predictions root must be an object"]
    if set(predictions) != REQUIRED_PREDICTION_ROOT_FIELDS:
        errors.append(
            "predictions root must contain only schema_version, dataset_id, "
            "dataset_sha256, metadata_catalog_sha256, and predictions"
        )
    try:
        expected_provenance = _provenance_fields(
            dataset, root, metadata_catalog
        )
    except ValueError as exc:
        return {}, [str(exc)]
    if predictions.get("schema_version") != LIVE_PROTOCOL_VERSION:
        errors.append(
            f"prediction schema_version must be {LIVE_PROTOCOL_VERSION}"
        )
    if predictions.get("dataset_id") != expected_provenance["dataset_id"]:
        errors.append("prediction dataset_id does not match the current dataset")
    for field in ("dataset_sha256", "metadata_catalog_sha256"):
        value = predictions.get(field)
        if not _is_sha256(value):
            errors.append(f"prediction {field} must be a lowercase SHA-256 digest")
        elif value != expected_provenance[field]:
            errors.append(f"prediction {field} does not match the current inputs")
    rows = predictions.get("predictions")
    if not isinstance(rows, list):
        return {}, errors + ["predictions must be an array"]

    cases = _prediction_case_map(dataset)
    catalog = {
        case["expected_skill"] for case in dataset["cases"]
    } | {
        skill for case in dataset["cases"] for skill in case["confusable_with"]
    } | {
        skill
        for case in dataset["cases"]
        for skill in case.get("acceptable_skills", [])
    }
    by_id: dict[str, str] = {}
    for index, row in enumerate(rows):
        prefix = f"prediction {index + 1}"
        if not isinstance(row, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if set(row) != REQUIRED_PREDICTION_FIELDS:
            errors.append(f"{prefix} must contain only case_id and predicted_skill")
        case_id = row.get("case_id")
        predicted = row.get("predicted_skill")
        if not _is_nonempty_string(case_id):
            errors.append(f"{prefix} case_id must be a non-empty string")
            continue
        if case_id in by_id:
            errors.append(f"duplicate prediction for case: {case_id}")
            continue
        if case_id not in cases:
            errors.append(f"prediction references unknown case: {case_id}")
        if predicted not in catalog:
            errors.append(
                f"{prefix} predicted_skill is not in the benchmark catalog: "
                f"{predicted!r}"
            )
        by_id[case_id] = predicted

    missing = sorted(set(cases) - set(by_id))
    if missing and not allow_partial:
        errors.append("missing predictions: " + ", ".join(missing))
    if errors:
        return {}, errors

    evaluated_ids = sorted(set(cases) & set(by_id))
    if not evaluated_ids:
        return {}, ["no predictions available to score"]
    exact_primary = {
        case_id: by_id[case_id] == cases[case_id]["expected_skill"]
        for case_id in evaluated_ids
    }
    acceptable = {
        case_id: by_id[case_id]
        in {
            cases[case_id]["expected_skill"],
            *cases[case_id].get("acceptable_skills", []),
        }
        for case_id in evaluated_ids
    }
    skill_scores: dict[str, list[bool]] = defaultdict(list)
    representative_results: list[bool] = []
    collision_results: list[bool] = []
    hard_collision_results: list[bool] = []
    exact_by_mode: dict[str, list[bool]] = defaultdict(list)
    acceptable_by_mode: dict[str, list[bool]] = defaultdict(list)
    directed_edge_exact_scores: dict[str, list[bool]] = defaultdict(list)
    directed_edge_acceptable_scores: dict[str, list[bool]] = defaultdict(list)
    confusions: Counter[str] = Counter()
    unacceptable_predictions: Counter[str] = Counter()
    for case_id in evaluated_ids:
        case = cases[case_id]
        exact_hit = exact_primary[case_id]
        acceptable_hit = acceptable[case_id]
        routing_mode = case.get("routing_mode", "exclusive")
        exact_by_mode[routing_mode].append(exact_hit)
        acceptable_by_mode[routing_mode].append(acceptable_hit)
        skill_scores[case["expected_skill"]].append(exact_hit)
        if case["kind"] == "representative":
            representative_results.append(exact_hit)
        if case["kind"] == "collision":
            collision_results.append(exact_hit)
            if case["difficulty"] == "hard":
                hard_collision_results.append(exact_hit)
            for confusable in case["confusable_with"]:
                directed_edge_exact_scores[
                    f'{case["expected_skill"]} -> {confusable}'
                ].append(exact_hit)
                directed_edge_acceptable_scores[
                    f'{case["expected_skill"]} -> {confusable}'
                ].append(acceptable_hit)
        if not exact_hit:
            confusions[
                f'{case["expected_skill"]} -> {by_id[case_id]}'
            ] += 1
        if not acceptable_hit:
            unacceptable_predictions[
                f'{case["expected_skill"]} -> {by_id[case_id]}'
            ] += 1

    total = len(evaluated_ids)
    exact_count = sum(exact_primary.values())
    acceptable_count = sum(acceptable.values())

    def rate(values: list[bool]) -> float | None:
        return sum(values) / len(values) if values else None

    registered_edges = {
        f"{edge['from']} -> {edge['to']}" for edge in dataset["plausible_edges"]
    }
    critical_edges = {
        f"{edge['from']} -> {edge['to']}"
        for edge in dataset["plausible_edges"]
        if edge["priority"] == "critical"
    }
    pairwise_exact_accuracy = {
        edge: sum(values) / len(values)
        for edge, values in sorted(directed_edge_exact_scores.items())
    }
    pairwise_acceptable_accuracy = {
        edge: sum(values) / len(values)
        for edge, values in sorted(directed_edge_acceptable_scores.items())
    }
    tested_edges = set(pairwise_exact_accuracy)
    tested_registered_edges = tested_edges & registered_edges
    tested_critical_edges = tested_edges & critical_edges
    unregistered_tested_edges = tested_edges - registered_edges
    result = {
        "dataset_id": expected_provenance["dataset_id"],
        "dataset_sha256": expected_provenance["dataset_sha256"],
        "metadata_catalog_sha256": expected_provenance[
            "metadata_catalog_sha256"
        ],
        "evaluated": total,
        "correct": exact_count,
        "incorrect": total - exact_count,
        "accuracy": exact_count / total,
        "exact_primary_correct": exact_count,
        "exact_primary_accuracy": exact_count / total,
        "acceptable_correct": acceptable_count,
        "acceptable_accuracy": acceptable_count / total,
        "exclusive_exact_primary_accuracy": rate(exact_by_mode["exclusive"]),
        "exclusive_acceptable_accuracy": rate(acceptable_by_mode["exclusive"]),
        "primary_owner_exact_primary_accuracy": rate(
            exact_by_mode["primary-owner"]
        ),
        "primary_owner_acceptable_accuracy": rate(
            acceptable_by_mode["primary-owner"]
        ),
        "macro_skill_recall": sum(
            sum(values) / len(values) for values in skill_scores.values()
        )
        / len(skill_scores),
        "representative_accuracy": rate(representative_results),
        "all_collision_accuracy": rate(collision_results),
        "hard_collision_accuracy": rate(hard_collision_results),
        "collision_accuracy": rate(collision_results),
        "per_skill_recall": {
            skill: sum(values) / len(values)
            for skill, values in sorted(skill_scores.items())
        },
        "pairwise_directed_edge_accuracy": pairwise_exact_accuracy,
        "pairwise_directed_edge_exact_primary_accuracy": pairwise_exact_accuracy,
        "pairwise_directed_edge_acceptable_accuracy": (
            pairwise_acceptable_accuracy
        ),
        "directed_edge_macro_accuracy": (
            sum(pairwise_exact_accuracy.values()) / len(pairwise_exact_accuracy)
            if pairwise_exact_accuracy
            else None
        ),
        "tested_directed_edge_count": len(tested_edges),
        "registered_edge_count": len(registered_edges),
        "tested_registered_edge_count": len(tested_registered_edges),
        "registered_edge_coverage": (
            len(tested_registered_edges) / len(registered_edges)
            if registered_edges
            else None
        ),
        "critical_edge_count": len(critical_edges),
        "tested_critical_edge_count": len(tested_critical_edges),
        "critical_edge_coverage": (
            len(tested_critical_edges) / len(critical_edges)
            if critical_edges
            else None
        ),
        "unregistered_tested_edge_count": len(unregistered_tested_edges),
        "confusions": dict(sorted(confusions.items())),
        "unacceptable_predictions": dict(sorted(unacceptable_predictions.items())),
    }
    return result, []


def _valid_timestamp(value: Any) -> bool:
    if value == "not_captured":
        return True
    if not isinstance(value, str) or not value.endswith("Z"):
        return False
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return False
    return parsed.utcoffset() is not None and parsed.utcoffset().total_seconds() == 0


def validate_run_manifest(
    dataset: dict[str, Any],
    manifest: Any,
    manifest_path: Path,
    root: Path | None = None,
    metadata_catalog: Path | None = None,
) -> list[str]:
    """Validate a live-run manifest and its referenced prediction file."""
    errors: list[str] = []
    if root is None:
        root = _default_root()
    if not isinstance(manifest, dict):
        return ["run manifest root must be an object"]
    missing = sorted(REQUIRED_MANIFEST_FIELDS - set(manifest))
    unknown = sorted(set(manifest) - REQUIRED_MANIFEST_FIELDS)
    if missing:
        errors.append("run manifest missing fields: " + ", ".join(missing))
    if unknown:
        errors.append("run manifest has unknown fields: " + ", ".join(unknown))
    try:
        expected_provenance = _provenance_fields(
            dataset, root, metadata_catalog
        )
    except ValueError as exc:
        return [str(exc)]
    if manifest.get("benchmark_schema_version") != LIVE_PROTOCOL_VERSION:
        errors.append(
            f"benchmark_schema_version must be {LIVE_PROTOCOL_VERSION}"
        )
    if manifest.get("dataset_id") != expected_provenance["dataset_id"]:
        errors.append("manifest dataset_id does not match the current dataset")
    for field in ("dataset_sha256", "metadata_catalog_sha256"):
        value = manifest.get(field)
        if not _is_sha256(value):
            errors.append(f"manifest {field} must be a lowercase SHA-256 digest")
        elif value != expected_provenance[field]:
            errors.append(f"manifest {field} does not match the current inputs")
    if not _is_nonempty_string(manifest.get("run_id")):
        errors.append("run_id must be a non-empty string")
    if not _valid_timestamp(manifest.get("created_at_utc")):
        errors.append(
            "created_at_utc must be ISO 8601 UTC ending in Z or not_captured"
        )

    model = manifest.get("model")
    if not isinstance(model, dict) or set(model) != MODEL_FIELDS:
        errors.append("model must contain only provider, name, version, and role")
    else:
        for field in sorted(MODEL_FIELDS):
            if not _is_nonempty_string(model.get(field)):
                errors.append(f"model.{field} must be a non-empty string")

    protocol = manifest.get("prompt_protocol")
    if not isinstance(protocol, dict) or set(protocol) != PROTOCOL_FIELDS:
        errors.append(
            "prompt_protocol must contain the documented protocol fields only"
        )
    else:
        metadata_source = protocol.get("metadata_source")
        repo_access = protocol.get("model_repo_access")
        if metadata_source not in METADATA_ACCESS:
            errors.append(
                "prompt_protocol.metadata_source must be "
                "inline_metadata_catalog, installed_skill_metadata, or "
                "repository_skill_metadata"
            )
        if not isinstance(repo_access, bool):
            errors.append("prompt_protocol.model_repo_access must be a boolean")
        elif metadata_source in METADATA_ACCESS:
            expected_access = METADATA_ACCESS[metadata_source]
            if repo_access != expected_access:
                errors.append(
                    "prompt_protocol metadata_source and model_repo_access "
                    "are inconsistent"
                )
        for field in ("case_isolation", "context_reset_between_cases"):
            if not isinstance(protocol.get(field), bool):
                errors.append(f"prompt_protocol.{field} must be a boolean")
        if not _is_nonempty_string(protocol.get("selection_instruction")):
            errors.append(
                "prompt_protocol.selection_instruction must be a non-empty string"
            )
        temperature = protocol.get("temperature")
        if temperature is not None and (
            isinstance(temperature, bool)
            or not isinstance(temperature, (int, float))
        ):
            errors.append("prompt_protocol.temperature must be a number or null")
        if not isinstance(protocol.get("notes"), str):
            errors.append("prompt_protocol.notes must be a string")

    batches = manifest.get("batches")
    batch_ids: list[str] = []
    batch_case_ids: list[str] = []
    if not isinstance(batches, list) or not batches:
        errors.append("batches must be a non-empty array")
        batches = []
    for index, batch in enumerate(batches, start=1):
        prefix = f"batch {index}"
        if not isinstance(batch, dict) or set(batch) != BATCH_FIELDS:
            errors.append(
                f"{prefix} must contain only id, case_ids, and UTC timestamps"
            )
            continue
        batch_id = batch.get("id")
        if not _is_nonempty_string(batch_id):
            errors.append(f"{prefix} id must be a non-empty string")
        else:
            batch_ids.append(batch_id)
        case_ids = batch.get("case_ids")
        if (
            not isinstance(case_ids, list)
            or not case_ids
            or not all(_is_nonempty_string(case_id) for case_id in case_ids)
        ):
            errors.append(f"{prefix} case_ids must be a non-empty string array")
        else:
            batch_case_ids.extend(case_ids)
        for field in ("started_at_utc", "completed_at_utc"):
            if not _valid_timestamp(batch.get(field)):
                errors.append(
                    f"{prefix} {field} must be ISO 8601 UTC ending in Z "
                    "or not_captured"
                )
    duplicate_batch_ids = _duplicates(batch_ids)
    if duplicate_batch_ids:
        errors.append("duplicate batch id: " + ", ".join(duplicate_batch_ids))
    duplicate_batch_cases = _duplicates(batch_case_ids)
    if duplicate_batch_cases:
        errors.append(
            "case ids appear in multiple batch entries: "
            + ", ".join(duplicate_batch_cases)
        )
    if isinstance(protocol, dict) and protocol.get("case_isolation") is True:
        if protocol.get("context_reset_between_cases") is not True:
            errors.append(
                "case_isolation requires context_reset_between_cases to be true"
            )
        for index, batch in enumerate(batches, start=1):
            if (
                isinstance(batch, dict)
                and isinstance(batch.get("case_ids"), list)
                and len(batch["case_ids"]) != 1
            ):
                errors.append(
                    f"batch {index} case_isolation requires exactly one case"
                )

    independence = manifest.get("independence_caveat")
    if not _is_nonempty_string(independence):
        errors.append("independence_caveat must be a non-empty string")
    elif independence.strip() in INDEPENDENCE_CAVEAT_PLACEHOLDERS:
        errors.append(
            "independence_caveat must contain run-specific evidence, not template text"
        )

    predictions_value = manifest.get("predictions_path")
    predictions: Any = None
    predictions_path: Path | None = None
    if not _is_nonempty_string(predictions_value):
        errors.append("predictions_path must be a non-empty string")
    else:
        predictions_path = Path(predictions_value)
        if not predictions_path.is_absolute():
            predictions_path = manifest_path.parent / predictions_path
        if not predictions_path.is_file():
            errors.append(f"predictions_path does not exist: {predictions_path}")
        else:
            try:
                predictions = _read_json(predictions_path)
            except ValueError as exc:
                errors.append(str(exc))

    if predictions is not None:
        _, prediction_errors = score_predictions(
            dataset,
            predictions,
            root,
            metadata_catalog,
            allow_partial=True,
        )
        errors.extend(f"predictions: {error}" for error in prediction_errors)
        if isinstance(predictions, dict):
            for field in (
                "dataset_id",
                "dataset_sha256",
                "metadata_catalog_sha256",
            ):
                if manifest.get(field) != predictions.get(field):
                    errors.append(
                        f"manifest {field} must match predictions {field}"
                    )
        if isinstance(predictions, dict) and isinstance(
            predictions.get("predictions"), list
        ):
            prediction_case_ids = [
                row.get("case_id")
                for row in predictions["predictions"]
                if isinstance(row, dict) and _is_nonempty_string(row.get("case_id"))
            ]
            if (
                set(batch_case_ids) != set(prediction_case_ids)
                or len(batch_case_ids) != len(prediction_case_ids)
            ):
                errors.append(
                    "batch case ids must exactly equal prediction case ids"
                )
    return errors


def build_blinded_prompt_pack(
    dataset: dict[str, Any],
    root: Path,
    metadata_catalog: Path | None = None,
) -> dict[str, Any]:
    """Build model input without expected labels, rationales, or collision hints."""
    skills = sorted({case["expected_skill"] for case in dataset["cases"]})
    prediction_cases = _prediction_case_map(dataset)
    return {
        **_provenance_fields(dataset, root, metadata_catalog),
        "instruction": (
            "For each case, select exactly one slug from skills. Return a prediction "
            f"object with schema_version {LIVE_PROTOCOL_VERSION}; echo dataset_id, "
            "dataset_sha256, and metadata_catalog_sha256 exactly; and return "
            "predictions containing case_id and predicted_skill only."
        ),
        "skills": skills,
        "cases": [
            {"case_id": opaque_id, "prompt": case["prompt"]}
            for opaque_id, case in prediction_cases.items()
        ],
    }


def _prediction_case_map(dataset: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Map opaque exported IDs to labeled cases after a stable permutation."""
    dataset_id = dataset["dataset_id"]
    permuted = sorted(
        dataset["cases"],
        key=lambda case: hashlib.sha256(
            f"{dataset_id}\0{case['id']}".encode()
        ).digest(),
    )
    width = max(3, len(str(len(permuted))))
    return {
        f"route-{index:0{width}d}": case
        for index, case in enumerate(permuted, start=1)
    }


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON from {path}: {exc}") from exc


def _default_root() -> Path:
    return Path(__file__).resolve().parents[2]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path(__file__).with_name("cases.json"),
        help="routing dataset JSON (default: evals/routing/cases.json)",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=_default_root(),
        help="repository root used for live catalog discovery",
    )
    parser.add_argument(
        "--metadata-catalog",
        type=Path,
        help=(
            "JSON array of exact name/description metadata objects used for "
            "live provenance instead of reading skill frontmatter"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate", help="validate schema and fail-closed catalog coverage")
    subparsers.add_parser(
        "export",
        help="print a blinded model-input pack without labels or rationales",
    )
    validate_run = subparsers.add_parser(
        "validate-run",
        help="validate a live-run manifest and referenced predictions",
    )
    validate_run.add_argument("--manifest", type=Path, required=True)
    score = subparsers.add_parser("score", help="score model predictions from JSON")
    score.add_argument("--predictions", type=Path, required=True)
    score.add_argument(
        "--allow-partial",
        action="store_true",
        help="score an incomplete exploratory run instead of requiring every case",
    )
    score.add_argument(
        "--min-accuracy",
        type=float,
        help="exit nonzero when accuracy is below this threshold",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        dataset = _read_json(args.dataset)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2
    errors = validate_dataset(dataset, args.root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    if args.command == "validate":
        domain_count = (
            len(catalog_skills(args.root))
            - len(dataset["catalog"]["excluded_skills"])
        )
        print(
            f"routing dataset valid: {len(dataset['cases'])} cases, "
            f"{len(dataset['clusters'])} clusters, "
            f"{len(dataset['plausible_edges'])} plausible edges, "
            f"{domain_count} domain skills"
        )
        return 0
    if args.command == "export":
        try:
            prompt_pack = build_blinded_prompt_pack(
                dataset, args.root, args.metadata_catalog
            )
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        print(
            json.dumps(
                prompt_pack,
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.command == "validate-run":
        try:
            manifest = _read_json(args.manifest)
        except ValueError as exc:
            print(exc, file=sys.stderr)
            return 2
        manifest_errors = validate_run_manifest(
            dataset,
            manifest,
            args.manifest.resolve(),
            args.root,
            args.metadata_catalog,
        )
        if manifest_errors:
            for error in manifest_errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        print(
            f"routing run manifest valid: {len(manifest['batches'])} batches, "
            f"{manifest['predictions_path']}"
        )
        return 0
    try:
        predictions = _read_json(args.predictions)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2
    result, scoring_errors = score_predictions(
        dataset,
        predictions,
        args.root,
        args.metadata_catalog,
        allow_partial=args.allow_partial,
    )
    if scoring_errors:
        for error in scoring_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.min_accuracy is not None and result["accuracy"] < args.min_accuracy:
        print(
            f"ERROR: accuracy {result['accuracy']:.4f} is below "
            f"{args.min_accuracy:.4f}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
