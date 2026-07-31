#!/usr/bin/env bats

run_eval_check() {
  local evals_json="$1"

  python3 - "$BATS_TEST_DIRNAME/../../scripts/audit-skill-pack.py" "$evals_json" <<'PY'
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

module_path = Path(sys.argv[1])
evals = json.loads(sys.argv[2])
spec = importlib.util.spec_from_file_location("audit_skill_pack", module_path)
audit = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(audit)

with tempfile.TemporaryDirectory() as temp_dir:
    root = Path(temp_dir)
    skill = root / "skills" / "example-skill"
    (skill / "evals").mkdir(parents=True)
    (skill / "evals" / "evals.json").write_text(
        json.dumps({"skill_name": "example-skill", "evals": evals}),
        encoding="utf-8",
    )
    result = {"summary": {}, "errors": [], "warnings": []}
    audit.check_skill_evals(root, result, [skill])
    print(json.dumps(result))
    raise SystemExit(0 if not result["errors"] else 1)
PY
}

@test "optional eval expectations accept unique non-empty assertions" {
  run run_eval_check '[
    {
      "id": 1,
      "prompt": "A realistic prompt",
      "expected_output": "A verifiable output",
      "expectations": ["Reports the failed boundary", "Names a focused regression"]
    },
    {"id": 2, "prompt": "Another prompt", "expected_output": "Another output"},
    {"id": 3, "prompt": "Third prompt", "expected_output": "Third output"}
  ]'

  [ "$status" -eq 0 ]
}

@test "eval expectations reject empty and duplicate assertions" {
  run run_eval_check '[
    {
      "id": 1,
      "prompt": "A realistic prompt",
      "expected_output": "A verifiable output",
      "expectations": ["Same assertion", "Same assertion"]
    },
    {"id": 2, "prompt": "Another prompt", "expected_output": "Another output"},
    {"id": 3, "prompt": "Third prompt", "expected_output": "Third output"}
  ]'

  [ "$status" -eq 1 ]
  [[ "$output" == *"expectations must not contain duplicates"* ]]
}

@test "a new non-legacy skill cannot omit evals" {
  run python3 - "$BATS_TEST_DIRNAME/../../scripts/audit-skill-pack.py" <<'PY'
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

module_path = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("audit_skill_pack", module_path)
audit = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(audit)

with tempfile.TemporaryDirectory() as temp_dir:
    root = Path(temp_dir)
    skill = root / "skills" / "new-contract-skill"
    skill.mkdir(parents=True)
    result = {"summary": {}, "errors": [], "warnings": []}
    audit.check_skill_evals(root, result, [skill])
    print(json.dumps(result))
    raise SystemExit(0 if result["errors"] else 1)
PY

  [ "$status" -eq 0 ]
  [[ "$output" == *"new skills must include evals/evals.json"* ]]
}

@test "a skill with evals cannot remain on the legacy exemption list" {
  run python3 - "$BATS_TEST_DIRNAME/../../scripts/audit-skill-pack.py" <<'PY'
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

module_path = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("audit_skill_pack", module_path)
audit = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(audit)
audit.LEGACY_EVAL_EXEMPTIONS = frozenset({"example-skill"})

with tempfile.TemporaryDirectory() as temp_dir:
    root = Path(temp_dir)
    skill = root / "skills" / "example-skill"
    (skill / "evals").mkdir(parents=True)
    (skill / "evals" / "evals.json").write_text(
        json.dumps(
            {
                "skill_name": "example-skill",
                "evals": [
                    {"id": 1, "prompt": "First prompt", "expected_output": "First output"},
                    {"id": 2, "prompt": "Second prompt", "expected_output": "Second output"},
                    {"id": 3, "prompt": "Third prompt", "expected_output": "Third output"},
                ],
            }
        ),
        encoding="utf-8",
    )
    result = {"summary": {}, "errors": [], "warnings": []}
    audit.check_skill_evals(root, result, [skill])
    print(json.dumps(result))
    raise SystemExit(0 if result["errors"] else 1)
PY

  [ "$status" -eq 0 ]
  [[ "$output" == *"legacy eval exemption is stale"* ]]
}

@test "OpenAI agent metadata is required for every public skill" {
  run python3 - "$BATS_TEST_DIRNAME/../../scripts/audit-skill-pack.py" <<'PY'
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

module_path = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("audit_skill_pack", module_path)
audit = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(audit)

with tempfile.TemporaryDirectory() as temp_dir:
    root = Path(temp_dir)
    skill = root / "skills" / "example-skill"
    skill.mkdir(parents=True)
    result = {"summary": {}, "errors": [], "warnings": []}
    audit.check_agent_metadata(root, result, [skill])
    print(json.dumps(result))
    raise SystemExit(0 if result["errors"] else 1)
PY

  [ "$status" -eq 0 ]
  [[ "$output" == *"agents/openai.yaml missing"* ]]
}

@test "repository source-file citations require a full commit SHA" {
  run python3 - "$BATS_TEST_DIRNAME/../../scripts/audit-skill-pack.py" <<'PY'
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

module_path = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("audit_skill_pack", module_path)
audit = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(audit)

with tempfile.TemporaryDirectory() as temp_dir:
    root = Path(temp_dir)
    docs = root / "docs"
    docs.mkdir()
    (docs / "evidence.md").write_text(
        "Canary: https://github.com/example/project/blob/canary/docs/claim.md\n"
        "Develop: https://github.com/example/project/blob/develop/docs/claim.md\n"
        "Trunk: https://github.com/example/project/tree/trunk/packages/example\n"
        "Arbitrary: https://github.com/example/project/blob/feature-branch/src/example.ts\n"
        "Raw branch: https://raw.githubusercontent.com/example/project/develop/src/example.ts\n"
        "Gitiles branch: https://chromium.googlesource.com/example/project/+/trunk/src/example.cc\n"
        "Pinned: https://github.com/example/project/blob/0123456789abcdef0123456789abcdef01234567/docs/claim.md\n"
        "Pinned raw: https://raw.githubusercontent.com/example/project/0123456789abcdef0123456789abcdef01234567/src/example.ts\n"
        "Pinned Gitiles: https://chromium.googlesource.com/example/project/+/0123456789abcdef0123456789abcdef01234567/src/example.cc\n"
        "Repository: https://github.com/example/project\n"
        "Issue: https://github.com/example/project/issues/123\n"
        "Release: https://github.com/example/project/releases/tag/v1.0.0\n"
        "Docs: https://example.github.io/project/docs/claim\n",
        encoding="utf-8",
    )
    result = {"summary": {}, "errors": [], "warnings": []}
    audit.check_mutable_repository_links(root, result)
    print(json.dumps(result))
    messages = [error["message"] for error in result["errors"]]
    assert len(messages) == 6, messages
    assert result["summary"]["mutable_repository_links_found"] == 6
    assert all("full 40-character SHA" in message for message in messages)
PY

  [ "$status" -eq 0 ]
}

@test "routing evaluation documentation participates in Markdown link audit" {
  run python3 - "$BATS_TEST_DIRNAME/../../scripts/audit-skill-pack.py" <<'PY'
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

module_path = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("audit_skill_pack", module_path)
audit = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(audit)

with tempfile.TemporaryDirectory() as temp_dir:
    root = Path(temp_dir)
    routing = root / "evals" / "routing"
    routing.mkdir(parents=True)
    (routing / "README.md").write_text(
        "[missing result](./results/missing.json)\n",
        encoding="utf-8",
    )
    result = {"summary": {}, "errors": [], "warnings": []}
    audit.check_markdown_links(root, result)
    print(json.dumps(result))
    assert result["summary"]["local_markdown_refs_checked"] == 1
    assert len(result["errors"]) == 1
    assert "missing local markdown target" in result["errors"][0]["message"]
PY

  [ "$status" -eq 0 ]
}
