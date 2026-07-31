import copy
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO_ROOT / "evals" / "routing" / "routing_benchmark.py"
DATASET_PATH = REPO_ROOT / "evals" / "routing" / "cases.json"


def load_module():
    spec = importlib.util.spec_from_file_location("routing_benchmark", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def metadata_catalog_document(benchmark, dataset, root):
    return [
        benchmark._frontmatter_metadata(
            root / "skills" / skill / "SKILL.md"
        )
        for skill in sorted(
            {case["expected_skill"] for case in dataset["cases"]}
        )
    ]


def prediction_document(
    benchmark, dataset, root, rows, metadata_catalog=None
):
    prompt_pack = benchmark.build_blinded_prompt_pack(
        dataset, root, metadata_catalog
    )
    return {
        "schema_version": prompt_pack["schema_version"],
        "dataset_id": prompt_pack["dataset_id"],
        "dataset_sha256": prompt_pack["dataset_sha256"],
        "metadata_catalog_sha256": prompt_pack["metadata_catalog_sha256"],
        "predictions": rows,
    }


class RoutingBenchmarkValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.benchmark = load_module()
        cls.dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))

    def test_current_catalog_has_complete_benchmark_coverage(self):
        errors = self.benchmark.validate_dataset(self.dataset, REPO_ROOT)
        self.assertEqual([], errors)

    def test_new_catalog_skill_fails_closed_until_cases_are_added(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for skill in self.benchmark.catalog_skills(REPO_ROOT):
                (root / "skills" / skill).mkdir(parents=True)
                (root / "skills" / skill / "SKILL.md").write_text("---\n", encoding="utf-8")
            (root / "skills" / "new-browser-contract").mkdir(parents=True)
            new_skill_file = root / "skills" / "new-browser-contract" / "SKILL.md"
            new_skill_file.write_text("---\n", encoding="utf-8")

            errors = self.benchmark.validate_dataset(self.dataset, root)

        self.assertTrue(any("new-browser-contract" in error for error in errors))

    def test_duplicate_case_id_is_rejected(self):
        dataset = copy.deepcopy(self.dataset)
        dataset["cases"][1]["id"] = dataset["cases"][0]["id"]

        errors = self.benchmark.validate_dataset(dataset, REPO_ROOT)

        self.assertTrue(any("duplicate case id" in error for error in errors))

    def test_collision_case_requires_a_declared_confusable_skill(self):
        dataset = copy.deepcopy(self.dataset)
        collision = next(case for case in dataset["cases"] if case["kind"] == "collision")
        collision["confusable_with"] = []

        errors = self.benchmark.validate_dataset(dataset, REPO_ROOT)

        self.assertTrue(any("confusable_with" in error for error in errors))

    def test_clusters_are_organizational_and_do_not_gate_edges(self):
        dataset = copy.deepcopy(self.dataset)
        target = dataset["clusters"][0]["members"][0]
        for cluster in dataset["clusters"]:
            cluster["members"] = [member for member in cluster["members"] if member != target]

        errors = self.benchmark.validate_dataset(dataset, REPO_ROOT)

        self.assertEqual([], errors)

    def test_every_domain_skill_has_representative_smoke_and_hard_coverage(self):
        skills = set(self.benchmark.catalog_skills(REPO_ROOT)) - set(
            self.dataset["catalog"]["excluded_skills"]
        )

        for skill in skills:
            cases = [
                case for case in self.dataset["cases"]
                if case["expected_skill"] == skill
            ]
            shapes = {(case["kind"], case["difficulty"]) for case in cases}
            self.assertIn(("representative", "smoke"), shapes)
            self.assertIn(("collision", "smoke"), shapes)
            self.assertIn(("collision", "hard"), shapes)

    def test_every_collision_edge_is_in_curated_registry(self):
        registered = {
            (edge["from"], edge["to"])
            for edge in self.dataset["plausible_edges"]
        }
        tested = {
            (case["expected_skill"], confusable)
            for case in self.dataset["cases"]
            if case["kind"] == "collision"
            for confusable in case["confusable_with"]
        }

        self.assertTrue(tested <= registered)

    def test_curated_registry_includes_untested_edges(self):
        registered = {
            (edge["from"], edge["to"])
            for edge in self.dataset["plausible_edges"]
        }
        tested = {
            (case["expected_skill"], confusable)
            for case in self.dataset["cases"]
            if case["kind"] == "collision"
            for confusable in case["confusable_with"]
        }

        self.assertEqual(
            {
                ("a11y-contract-testing", "js-form-validation-contracts"),
                ("iframe-embed-contracts", "user-activation-contracts"),
            },
            registered - tested,
        )

    def test_duplicate_self_and_stale_registry_edges_are_rejected(self):
        duplicate = copy.deepcopy(self.dataset)
        duplicate["plausible_edges"].append(
            copy.deepcopy(duplicate["plausible_edges"][0])
        )
        self.assertTrue(
            any(
                "duplicate plausible edge" in error
                for error in self.benchmark.validate_dataset(duplicate, REPO_ROOT)
            )
        )

        self_edge = copy.deepcopy(self.dataset)
        self_edge["plausible_edges"][0]["to"] = (
            self_edge["plausible_edges"][0]["from"]
        )
        self.assertTrue(
            any(
                "self edge" in error
                for error in self.benchmark.validate_dataset(self_edge, REPO_ROOT)
            )
        )

        stale = copy.deepcopy(self.dataset)
        stale["plausible_edges"][0]["to"] = "removed-browser-contract"
        self.assertTrue(
            any(
                "unknown skill" in error
                for error in self.benchmark.validate_dataset(stale, REPO_ROOT)
            )
        )

    def test_collision_edge_outside_registry_is_rejected(self):
        dataset = copy.deepcopy(self.dataset)
        case = next(case for case in dataset["cases"] if case["kind"] == "collision")
        edge = (case["expected_skill"], case["confusable_with"][0])
        dataset["plausible_edges"] = [
            item
            for item in dataset["plausible_edges"]
            if (item["from"], item["to"]) != edge
        ]

        errors = self.benchmark.validate_dataset(dataset, REPO_ROOT)

        self.assertTrue(any("not in plausible_edges" in error for error in errors))

    def test_critical_edge_requires_answer_neutral_hard_coverage(self):
        dataset = copy.deepcopy(self.dataset)
        critical = next(
            edge for edge in dataset["plausible_edges"]
            if edge["priority"] == "critical"
        )
        dataset["cases"] = [
            case
            for case in dataset["cases"]
            if not (
                case["difficulty"] == "hard"
                and case["expected_skill"] == critical["from"]
                and critical["to"] in case["confusable_with"]
            )
        ]

        errors = self.benchmark.validate_dataset(dataset, REPO_ROOT)

        self.assertTrue(
            any("critical plausible edge lacks" in error for error in errors)
        )

    def test_cross_cluster_registered_edge_is_valid(self):
        edge = next(
            edge for edge in self.dataset["plausible_edges"]
            if edge["from"] == "css-transition-animation-contracts"
            and edge["to"] == "view-transitions-contracts"
        )
        cluster_by_skill = {
            member: cluster["id"]
            for cluster in self.dataset["clusters"]
            for member in cluster["members"]
        }

        self.assertNotEqual(
            cluster_by_skill[edge["from"]],
            cluster_by_skill[edge["to"]],
        )
        self.assertEqual(
            [], self.benchmark.validate_dataset(self.dataset, REPO_ROOT)
        )

    def test_pointer_media_contextual_edges_are_not_registered(self):
        registered = {
            (edge["from"], edge["to"])
            for edge in self.dataset["plausible_edges"]
        }

        self.assertNotIn(
            ("pointer-gesture-contracts", "media-capture-device-contracts"),
            registered,
        )
        self.assertNotIn(
            ("media-capture-device-contracts", "pointer-gesture-contracts"),
            registered,
        )

    def test_hard_collision_rejects_answer_cue_phrasing(self):
        cue_phrases = (
            "not the adjacent workflow",
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
            "remains healthy",
        )
        for cue_phrase in cue_phrases:
            with self.subTest(cue_phrase=cue_phrase):
                dataset = copy.deepcopy(self.dataset)
                hard_case = next(
                    case for case in dataset["cases"]
                    if case["difficulty"] == "hard"
                )
                hard_case["prompt"] = (
                    f"The adjacent mechanism {cue_phrase}. "
                    "The report otherwise contains enough realistic symptom words "
                    "for the hard collision prompt length requirement."
                )

                errors = self.benchmark.validate_dataset(dataset, REPO_ROOT)

                self.assertTrue(
                    any("answer-neutral" in error for error in errors)
                )


class RoutingBenchmarkProvenanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.benchmark = load_module()
        cls.dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
        cls.prediction_cases = cls.benchmark._prediction_case_map(cls.dataset)

    def test_export_binds_dataset_and_metadata_catalog_digests(self):
        prompt_pack = self.benchmark.build_blinded_prompt_pack(
            self.dataset, REPO_ROOT
        )

        self.assertEqual(self.dataset["dataset_id"], prompt_pack["dataset_id"])
        self.assertEqual(
            self.benchmark.dataset_sha256(self.dataset),
            prompt_pack["dataset_sha256"],
        )
        self.assertEqual(
            self.benchmark.metadata_catalog_sha256(self.dataset, REPO_ROOT),
            prompt_pack["metadata_catalog_sha256"],
        )

    def test_metadata_catalog_override_is_valid_and_order_independent(self):
        catalog = metadata_catalog_document(
            self.benchmark, self.dataset, REPO_ROOT
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            catalog_path = Path(temp_dir) / "metadata-catalog.json"
            catalog_path.write_text(
                json.dumps(list(reversed(catalog))), encoding="utf-8"
            )

            overridden = self.benchmark.metadata_catalog_sha256(
                self.dataset, REPO_ROOT, catalog_path
            )

        self.assertEqual(
            self.benchmark.metadata_catalog_sha256(
                self.dataset, REPO_ROOT
            ),
            overridden,
        )

    def test_metadata_catalog_override_rejects_invalid_catalogs(self):
        catalog = metadata_catalog_document(
            self.benchmark, self.dataset, REPO_ROOT
        )
        invalid_catalogs = {
            "malformed root": {"skills": catalog},
            "missing skill": catalog[1:],
            "duplicate skill": catalog + [copy.deepcopy(catalog[0])],
            "stale skill": [
                {**catalog[0], "name": "removed-domain-skill"},
                *catalog[1:],
            ],
            "extra field": [{**catalog[0], "summary": "not allowed"}, *catalog[1:]],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            for label, document in invalid_catalogs.items():
                with self.subTest(label=label):
                    catalog_path = Path(temp_dir) / f"{label}.json"
                    catalog_path.write_text(
                        json.dumps(document), encoding="utf-8"
                    )
                    with self.assertRaises(ValueError):
                        self.benchmark.metadata_catalog_sha256(
                            self.dataset, REPO_ROOT, catalog_path
                        )

    def test_metadata_catalog_override_rejects_missing_or_invalid_json_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_path = Path(temp_dir) / "missing.json"
            invalid_path = Path(temp_dir) / "invalid.json"
            invalid_path.write_text("{", encoding="utf-8")
            for catalog_path in (missing_path, invalid_path):
                with self.subTest(catalog_path=catalog_path):
                    with self.assertRaisesRegex(
                        ValueError, "cannot read JSON"
                    ):
                        self.benchmark.metadata_catalog_sha256(
                            self.dataset, REPO_ROOT, catalog_path
                        )

    def test_score_binds_metadata_catalog_override(self):
        rows = [
            {"case_id": case_id, "predicted_skill": case["expected_skill"]}
            for case_id, case in self.prediction_cases.items()
        ]
        catalog = metadata_catalog_document(
            self.benchmark, self.dataset, REPO_ROOT
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            catalog_path = Path(temp_dir) / "metadata-catalog.json"
            catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
            predictions = prediction_document(
                self.benchmark,
                self.dataset,
                REPO_ROOT,
                rows,
                catalog_path,
            )
            catalog[0]["description"] += " Changed after the run."
            catalog_path.write_text(json.dumps(catalog), encoding="utf-8")

            _, errors = self.benchmark.score_predictions(
                self.dataset,
                predictions,
                REPO_ROOT,
                catalog_path,
            )

        self.assertTrue(
            any("metadata_catalog_sha256" in error for error in errors)
        )

    def test_predictions_from_changed_dataset_are_rejected_as_stale(self):
        predictions = prediction_document(
            self.benchmark,
            self.dataset,
            REPO_ROOT,
            [
                {"case_id": case_id, "predicted_skill": case["expected_skill"]}
                for case_id, case in self.prediction_cases.items()
            ],
        )
        changed_dataset = copy.deepcopy(self.dataset)
        changed_dataset["cases"][0]["prompt"] += " Added after the recorded run."

        _, errors = self.benchmark.score_predictions(
            changed_dataset, predictions, REPO_ROOT
        )

        self.assertTrue(any("dataset_sha256" in error for error in errors))

    def test_predictions_with_changed_metadata_digest_are_rejected_as_stale(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skills = sorted(
                {case["expected_skill"] for case in self.dataset["cases"]}
            )
            for skill in skills:
                target = root / "skills" / skill / "SKILL.md"
                target.parent.mkdir(parents=True)
                target.write_text(
                    (REPO_ROOT / "skills" / skill / "SKILL.md").read_text(
                        encoding="utf-8"
                    ),
                    encoding="utf-8",
                )
            predictions = prediction_document(
                self.benchmark,
                self.dataset,
                root,
                [
                    {
                        "case_id": case_id,
                        "predicted_skill": case["expected_skill"],
                    }
                    for case_id, case in self.prediction_cases.items()
                ],
            )
            changed_skill = root / "skills" / skills[0] / "SKILL.md"
            changed_skill.write_text(
                changed_skill.read_text(encoding="utf-8").replace(
                    'description: "', 'description: "Changed metadata. ', 1
                ),
                encoding="utf-8",
            )

            _, errors = self.benchmark.score_predictions(
                self.dataset, predictions, root
            )

        self.assertTrue(
            any("metadata_catalog_sha256" in error for error in errors)
        )

    def test_legacy_v3_prediction_without_provenance_is_rejected(self):
        case_id, case = next(iter(self.prediction_cases.items()))
        predictions = {
            "schema_version": 3,
            "predictions": [
                {"case_id": case_id, "predicted_skill": case["expected_skill"]}
            ],
        }

        _, errors = self.benchmark.score_predictions(
            self.dataset, predictions, REPO_ROOT, allow_partial=True
        )

        self.assertTrue(any("schema_version must be 4" in error for error in errors))
        self.assertTrue(any("dataset_sha256" in error for error in errors))

    def test_missing_metadata_returns_an_error_instead_of_crashing(self):
        predictions = prediction_document(
            self.benchmark,
            self.dataset,
            REPO_ROOT,
            [
                {"case_id": case_id, "predicted_skill": case["expected_skill"]}
                for case_id, case in self.prediction_cases.items()
            ],
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            _, errors = self.benchmark.score_predictions(
                self.dataset, predictions, Path(temp_dir)
            )

        self.assertTrue(any("cannot read skill metadata" in error for error in errors))


class RoutingBenchmarkScoringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.benchmark = load_module()
        cls.dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
        cls.prediction_cases = cls.benchmark._prediction_case_map(cls.dataset)

    def test_perfect_predictions_score_one_for_all_metrics(self):
        predictions = prediction_document(
            self.benchmark,
            self.dataset,
            REPO_ROOT,
            [
                {"case_id": case_id, "predicted_skill": case["expected_skill"]}
                for case_id, case in self.prediction_cases.items()
            ],
        )

        result, errors = self.benchmark.score_predictions(self.dataset, predictions)

        self.assertEqual([], errors)
        self.assertEqual(1.0, result["accuracy"])
        self.assertEqual(1.0, result["macro_skill_recall"])
        self.assertEqual(1.0, result["representative_accuracy"])
        self.assertEqual(1.0, result["all_collision_accuracy"])
        self.assertEqual(1.0, result["hard_collision_accuracy"])
        self.assertEqual(1.0, result["collision_accuracy"])
        self.assertNotIn("cluster_macro_accuracy", result)
        self.assertNotIn("per_cluster_accuracy", result)
        self.assertEqual(1.0, result["exact_primary_accuracy"])
        self.assertEqual(1.0, result["acceptable_accuracy"])
        self.assertEqual(1.0, result["primary_owner_exact_primary_accuracy"])
        self.assertEqual(1.0, result["primary_owner_acceptable_accuracy"])

    def test_primary_owner_exact_and_acceptable_metrics_are_separate(self):
        primary_case_id, primary_case = next(
            (case_id, case)
            for case_id, case in self.prediction_cases.items()
            if case.get("routing_mode") == "primary-owner"
        )
        exclusive_case_id, exclusive_case = next(
            (case_id, case)
            for case_id, case in self.prediction_cases.items()
            if case.get("routing_mode", "exclusive") == "exclusive"
            and case["kind"] == "collision"
        )
        predictions = prediction_document(
            self.benchmark,
            self.dataset,
            REPO_ROOT,
            [
                {
                    "case_id": case_id,
                    "predicted_skill": (
                        primary_case["acceptable_skills"][0]
                        if case_id == primary_case_id
                        else exclusive_case["confusable_with"][0]
                        if case_id == exclusive_case_id
                        else case["expected_skill"]
                    ),
                }
                for case_id, case in self.prediction_cases.items()
            ],
        )

        result, errors = self.benchmark.score_predictions(self.dataset, predictions)

        self.assertEqual([], errors)
        self.assertEqual(136 / 138, result["exact_primary_accuracy"])
        self.assertEqual(137 / 138, result["acceptable_accuracy"])
        self.assertLess(
            result["primary_owner_exact_primary_accuracy"],
            result["primary_owner_acceptable_accuracy"],
        )
        self.assertEqual(1.0, result["primary_owner_acceptable_accuracy"])
        self.assertLess(result["exclusive_acceptable_accuracy"], 1.0)

    def test_missing_prediction_fails_closed_by_default(self):
        predictions = prediction_document(
            self.benchmark,
            self.dataset,
            REPO_ROOT,
            [
                {"case_id": case_id, "predicted_skill": case["expected_skill"]}
                for case_id, case in list(self.prediction_cases.items())[1:]
            ],
        )

        _, errors = self.benchmark.score_predictions(self.dataset, predictions)

        self.assertTrue(any("missing predictions" in error for error in errors))

    def test_wrong_skill_is_reported_in_confusion_counts(self):
        cases = list(self.prediction_cases.items())
        wrong_skill = next(
            case["expected_skill"]
            for _, case in cases[1:]
            if case["expected_skill"] != cases[0][1]["expected_skill"]
        )
        predictions = prediction_document(
            self.benchmark,
            self.dataset,
            REPO_ROOT,
            [
                {
                    "case_id": case_id,
                    "predicted_skill": (
                        wrong_skill if index == 0 else case["expected_skill"]
                    ),
                }
                for index, (case_id, case) in enumerate(cases)
            ],
        )

        result, errors = self.benchmark.score_predictions(self.dataset, predictions)

        self.assertEqual([], errors)
        self.assertEqual(1, result["incorrect"])
        self.assertEqual(1, sum(result["confusions"].values()))

    def test_label_bearing_internal_case_id_is_rejected(self):
        internal_case = self.dataset["cases"][0]
        predictions = prediction_document(
            self.benchmark,
            self.dataset,
            REPO_ROOT,
            [
                {
                    "case_id": internal_case["id"],
                    "predicted_skill": internal_case["expected_skill"],
                }
            ],
        )

        _, errors = self.benchmark.score_predictions(
            self.dataset, predictions, allow_partial=True
        )

        self.assertTrue(any("unknown case" in error for error in errors))

    def test_difficulty_and_pairwise_metrics_isolate_three_misses(self):
        cases = list(self.prediction_cases.items())
        selected = {
            "representative": next(
                case_id for case_id, case in cases
                if case["kind"] == "representative"
            ),
            "smoke_collision": next(
                case_id for case_id, case in cases
                if case["kind"] == "collision" and case["difficulty"] == "smoke"
            ),
            "hard_collision": next(
                case_id for case_id, case in cases
                if case["kind"] == "collision" and case["difficulty"] == "hard"
            ),
        }
        predictions = prediction_document(
            self.benchmark,
            self.dataset,
            REPO_ROOT,
            [
                {
                    "case_id": case_id,
                    "predicted_skill": (
                        next(
                            candidate["expected_skill"]
                            for _, candidate in cases
                            if candidate["expected_skill"] != case["expected_skill"]
                        )
                        if case_id in selected.values()
                        else case["expected_skill"]
                    ),
                }
                for case_id, case in cases
            ],
        )

        result, errors = self.benchmark.score_predictions(self.dataset, predictions)

        self.assertEqual([], errors)
        self.assertEqual(39 / 40, result["representative_accuracy"])
        self.assertEqual(96 / 98, result["all_collision_accuracy"])
        self.assertEqual(55 / 56, result["hard_collision_accuracy"])
        self.assertEqual(98, result["tested_directed_edge_count"])
        self.assertEqual(100, result["registered_edge_count"])
        self.assertEqual(98, result["tested_registered_edge_count"])
        self.assertEqual(98 / 100, result["registered_edge_coverage"])
        self.assertEqual(56, result["critical_edge_count"])
        self.assertEqual(56, result["tested_critical_edge_count"])
        self.assertEqual(1.0, result["critical_edge_coverage"])
        self.assertEqual(0, result["unregistered_tested_edge_count"])
        self.assertNotIn("declared_cluster_directed_pair_count", result)
        self.assertNotIn("declared_cluster_pair_coverage", result)
        self.assertEqual(
            0.0,
            result["pairwise_directed_edge_accuracy"][
                self._edge_for_case(selected["hard_collision"])
            ],
        )

    def test_partial_representative_run_reports_unobserved_collision_metrics(self):
        case_id, case = next(
            (case_id, case)
            for case_id, case in self.prediction_cases.items()
            if case["kind"] == "representative"
        )
        predictions = prediction_document(
            self.benchmark,
            self.dataset,
            REPO_ROOT,
            [
                {"case_id": case_id, "predicted_skill": case["expected_skill"]}
            ],
        )

        result, errors = self.benchmark.score_predictions(
            self.dataset, predictions, allow_partial=True
        )

        self.assertEqual([], errors)
        self.assertEqual(1.0, result["representative_accuracy"])
        self.assertIsNone(result["all_collision_accuracy"])
        self.assertIsNone(result["hard_collision_accuracy"])
        self.assertIsNone(result["directed_edge_macro_accuracy"])
        self.assertEqual(0, result["tested_directed_edge_count"])
        self.assertEqual(0.0, result["registered_edge_coverage"])
        self.assertEqual(0.0, result["critical_edge_coverage"])

    def test_blinded_prompt_pack_does_not_expose_expected_labels(self):
        prompt_pack = self.benchmark.build_blinded_prompt_pack(
            self.dataset, REPO_ROOT
        )

        serialized = json.dumps(prompt_pack)
        self.assertNotIn("expected_skill", serialized)
        self.assertNotIn("rationale", serialized)
        self.assertEqual(len(self.dataset["cases"]), len(prompt_pack["cases"]))

    def test_blinded_prompt_pack_uses_opaque_case_ids(self):
        prompt_pack = self.benchmark.build_blinded_prompt_pack(
            self.dataset, REPO_ROOT
        )
        forbidden = {
            "representative",
            "collision",
            *(case["expected_skill"] for case in self.dataset["cases"]),
        }

        for case in prompt_pack["cases"]:
            case_id = case["case_id"]
            self.assertRegex(case_id, r"^route-[0-9]{3,}$")
            self.assertFalse(any(token in case_id for token in forbidden))

    def test_blinded_prompt_pack_order_does_not_match_labeled_dataset_order(self):
        prompt_pack = self.benchmark.build_blinded_prompt_pack(
            self.dataset, REPO_ROOT
        )

        exported_prompts = [case["prompt"] for case in prompt_pack["cases"]]
        labeled_prompts = [case["prompt"] for case in self.dataset["cases"]]

        self.assertNotEqual(labeled_prompts, exported_prompts)

    def test_blinded_prompt_pack_is_deterministic(self):
        first = self.benchmark.build_blinded_prompt_pack(self.dataset, REPO_ROOT)
        second = self.benchmark.build_blinded_prompt_pack(self.dataset, REPO_ROOT)

        self.assertEqual(first, second)

    def _edge_for_case(self, case_id):
        case = self.prediction_cases[case_id]
        return f"{case['expected_skill']} -> {case['confusable_with'][0]}"


class RoutingBenchmarkManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.benchmark = load_module()
        cls.dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
        cls.prediction_cases = cls.benchmark._prediction_case_map(cls.dataset)

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.run_dir = Path(self.temp_dir.name)
        self.predictions_path = self.run_dir / "predictions.json"
        self.predictions = prediction_document(
            self.benchmark,
            self.dataset,
            REPO_ROOT,
            [
                {"case_id": case_id, "predicted_skill": case["expected_skill"]}
                for case_id, case in self.prediction_cases.items()
            ],
        )
        self.predictions_path.write_text(
            json.dumps(self.predictions), encoding="utf-8"
        )
        case_ids = list(self.prediction_cases)
        self.manifest_path = self.run_dir / "run-manifest.json"
        self.manifest = {
            "benchmark_schema_version": self.benchmark.LIVE_PROTOCOL_VERSION,
            "dataset_id": self.predictions["dataset_id"],
            "dataset_sha256": self.predictions["dataset_sha256"],
            "metadata_catalog_sha256": self.predictions[
                "metadata_catalog_sha256"
            ],
            "run_id": "routing-live-2026-08-01",
            "created_at_utc": "2026-08-01T01:02:03Z",
            "model": {
                "provider": "provider",
                "name": "model",
                "version": "version",
                "role": "router",
            },
            "prompt_protocol": {
                "metadata_source": "installed_skill_metadata",
                "selection_instruction": "Select exactly one allowed skill slug.",
                "case_isolation": True,
                "context_reset_between_cases": True,
                "model_repo_access": False,
                "temperature": None,
                "notes": "",
            },
            "batches": [
                {
                    "id": f"batch-{index:03d}",
                    "case_ids": [case_id],
                    "started_at_utc": "not_captured",
                    "completed_at_utc": "not_captured",
                }
                for index, case_id in enumerate(case_ids, start=1)
            ],
            "predictions_path": "predictions.json",
            "independence_caveat": "Provider cache behavior was not observable.",
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_valid_manifest_matches_prediction_cases(self):
        errors = self.benchmark.validate_run_manifest(
            self.dataset, self.manifest, self.manifest_path
        )

        self.assertEqual([], errors)

    def test_manifest_accepts_inline_metadata_without_repo_access(self):
        self.manifest["prompt_protocol"]["metadata_source"] = (
            "inline_metadata_catalog"
        )

        errors = self.benchmark.validate_run_manifest(
            self.dataset, self.manifest, self.manifest_path
        )

        self.assertEqual([], errors)

    def test_validate_run_cli_accepts_valid_manifest(self):
        self.manifest_path.write_text(
            json.dumps(self.manifest), encoding="utf-8"
        )

        result = subprocess.run(
            [
                "python3",
                str(MODULE_PATH),
                "validate-run",
                "--manifest",
                str(self.manifest_path),
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("routing run manifest valid", result.stdout)

    def test_validate_run_cli_accepts_and_binds_metadata_catalog_override(self):
        catalog_path = self.run_dir / "metadata-catalog.json"
        catalog = metadata_catalog_document(
            self.benchmark, self.dataset, REPO_ROOT
        )
        catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
        self.manifest_path.write_text(
            json.dumps(self.manifest), encoding="utf-8"
        )

        valid_result = subprocess.run(
            [
                "python3",
                str(MODULE_PATH),
                "--metadata-catalog",
                str(catalog_path),
                "validate-run",
                "--manifest",
                str(self.manifest_path),
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        catalog[0]["description"] += " Changed after the run."
        catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
        stale_errors = self.benchmark.validate_run_manifest(
            self.dataset,
            self.manifest,
            self.manifest_path,
            REPO_ROOT,
            catalog_path,
        )

        self.assertEqual(0, valid_result.returncode, valid_result.stderr)
        self.assertTrue(
            any("metadata_catalog_sha256" in error for error in stale_errors)
        )

    def test_manifest_rejects_duplicate_batch_id(self):
        self.manifest["batches"][1]["id"] = self.manifest["batches"][0]["id"]

        errors = self.benchmark.validate_run_manifest(
            self.dataset, self.manifest, self.manifest_path
        )

        self.assertTrue(any("duplicate batch id" in error for error in errors))

    def test_manifest_rejects_batch_prediction_case_mismatch(self):
        self.manifest["batches"][0]["case_ids"].pop()

        errors = self.benchmark.validate_run_manifest(
            self.dataset, self.manifest, self.manifest_path
        )

        self.assertTrue(any("must exactly equal prediction case ids" in error for error in errors))

    def test_manifest_rejects_invalid_timestamp(self):
        self.manifest["created_at_utc"] = "August 1st"

        errors = self.benchmark.validate_run_manifest(
            self.dataset, self.manifest, self.manifest_path
        )

        self.assertTrue(any("created_at_utc" in error for error in errors))

    def test_manifest_rejects_blank_or_template_independence_caveat(self):
        invalid_caveats = (
            "",
            "   ",
            (
                "Record any hidden-state, cache, conversation-context, retry, or "
                "provider behavior that may make case outcomes statistically dependent."
            ),
        )
        for caveat in invalid_caveats:
            with self.subTest(caveat=caveat):
                self.manifest["independence_caveat"] = caveat

                errors = self.benchmark.validate_run_manifest(
                    self.dataset, self.manifest, self.manifest_path
                )

                self.assertTrue(
                    any("independence_caveat" in error for error in errors)
                )

    def test_manifest_rejects_boolean_temperature(self):
        for temperature in (False, True):
            with self.subTest(temperature=temperature):
                self.manifest["prompt_protocol"]["temperature"] = temperature

                errors = self.benchmark.validate_run_manifest(
                    self.dataset, self.manifest, self.manifest_path
                )

                self.assertTrue(any("temperature" in error for error in errors))

    def test_manifest_accepts_explicit_not_captured_timestamp(self):
        self.manifest["created_at_utc"] = "not_captured"

        errors = self.benchmark.validate_run_manifest(
            self.dataset, self.manifest, self.manifest_path
        )

        self.assertEqual([], errors)

    def test_manifest_rejects_missing_predictions_path(self):
        self.manifest["predictions_path"] = "missing.json"

        errors = self.benchmark.validate_run_manifest(
            self.dataset, self.manifest, self.manifest_path
        )

        self.assertTrue(any("predictions_path does not exist" in error for error in errors))

    def test_manifest_rejects_repo_metadata_without_repo_access(self):
        self.manifest["prompt_protocol"]["metadata_source"] = (
            "repository_skill_metadata"
        )

        errors = self.benchmark.validate_run_manifest(
            self.dataset, self.manifest, self.manifest_path
        )

        self.assertTrue(any("metadata_source" in error for error in errors))

    def test_manifest_rejects_installed_metadata_with_repo_access(self):
        self.manifest["prompt_protocol"]["model_repo_access"] = True

        errors = self.benchmark.validate_run_manifest(
            self.dataset, self.manifest, self.manifest_path
        )

        self.assertTrue(any("metadata_source" in error for error in errors))

    def test_manifest_rejects_stale_dataset_digest(self):
        self.manifest["dataset_sha256"] = "0" * 64

        errors = self.benchmark.validate_run_manifest(
            self.dataset, self.manifest, self.manifest_path
        )

        self.assertTrue(any("dataset_sha256" in error for error in errors))

    def test_manifest_rejects_multi_case_batch_when_case_isolation_is_true(self):
        self.manifest["batches"][0]["case_ids"].extend(
            self.manifest["batches"][1]["case_ids"]
        )
        del self.manifest["batches"][1]

        errors = self.benchmark.validate_run_manifest(
            self.dataset, self.manifest, self.manifest_path
        )

        self.assertTrue(
            any("case_isolation requires exactly one case" in error for error in errors)
        )

    def test_manifest_rejects_case_isolation_without_context_reset(self):
        self.manifest["batches"] = [
            {
                "id": f"batch-{index:03d}",
                "case_ids": [case_id],
                "started_at_utc": "not_captured",
                "completed_at_utc": "not_captured",
            }
            for index, case_id in enumerate(self.prediction_cases, start=1)
        ]
        self.manifest["prompt_protocol"]["context_reset_between_cases"] = False

        errors = self.benchmark.validate_run_manifest(
            self.dataset, self.manifest, self.manifest_path
        )

        self.assertTrue(
            any("case_isolation requires context_reset_between_cases" in error
                for error in errors)
        )


if __name__ == "__main__":
    unittest.main()
