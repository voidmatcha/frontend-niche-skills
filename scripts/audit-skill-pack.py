#!/usr/bin/env python3
"""Audit an Agent Skills bundle for publication consistency.

Standard-library only so it can run in fresh agent sandboxes.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

OVERCLAIM_RE = re.compile(
    r"\b(guarantee(?:d|s)?|prove|proves|proving|complete security|"
    r"any runtime|every agent|PCI compliant|compliance verdict|"
    r"stays closed|stays in place|no single open-source)\b",
    re.IGNORECASE,
)
LOCAL_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
README_SKILL_RE = re.compile(r"\./skills/([^/]+)/SKILL\.md")
BADGE_RE = re.compile(r"Agent_Skills-(\d+)")
URL_RE = re.compile(r"https?://[^\s)>\]\"']+")
REPOSITORY_SOURCE_LINK_RE = re.compile(
    r"https?://(?:"
    r"github\.com/[^/\s)>]+/[^/\s)>]+/(?:blob|tree)/(?P<github_ref>[^/\s)>]+)(?:/[^\s)>]*)?|"
    r"raw\.githubusercontent\.com/[^/\s)>]+/[^/\s)>]+/(?P<raw_ref>[^/\s)>]+)(?:/[^\s)>]*)?|"
    r"chromium\.googlesource\.com/[^\s)>]+/\+/(?P<gitiles_ref>[^/\s)>]+)(?:/[^\s)>]*)?"
    r")"
)
FULL_COMMIT_SHA_RE = re.compile(r"[0-9a-fA-F]{40}")
SOURCE_HEADING_RE = re.compile(r"^#{1,3}\s+Sources\b", re.IGNORECASE)
HEADING_RE = re.compile(r"^#{1,6}\s+")
WEAK_TRAILING_WORDS = {"a", "an", "and", "at", "for", "in", "of", "on", "or", "the", "to", "with"}

# Every skill now ships evals/evals.json, so this exemption set is empty and
# must stay that way: a name added back here would let a skill bypass the
# evaluation contract. The audit also errors if a listed skill has evals.
LEGACY_EVAL_EXEMPTIONS: frozenset[str] = frozenset()

# Claude.ai caps the frontmatter description at 200 characters while the Agent
# Skills specification allows 1024. The pack targets the spec limit, so the
# Claude.ai upload path needs the short variant in docs/.
CLAUDEAI_DESCRIPTION_LIMIT = 200


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def add(result: dict[str, Any], level: str, path: str, line: int | None, message: str) -> None:
    result[level].append({"path": path, "line": line, "message": message})


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def is_external(target: str) -> bool:
    return bool(re.match(r"^[a-z][a-z0-9+.-]*:", target)) or target.startswith("#")


def markdown_files(root: Path) -> list[Path]:
    return [
        path
        for path in [
            *root.glob("README*.md"),
            root / "CHANGELOG.md",
            root / "SECURITY.md",
            *root.glob("docs/**/*.md"),
            *root.glob("evals/**/*.md"),
            *root.glob("skills/**/*.md"),
        ]
        if path.exists() and path.is_file()
    ]


def markdown_lines(text: str) -> list[str]:
    """Return source lines with fenced-code contents blanked out."""
    lines: list[str] = []
    fence_char: str | None = None
    fence_length = 0
    for line in text.splitlines():
        if fence_char is None:
            opener = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
            if opener:
                marker = opener.group(1)
                fence_char = marker[0]
                fence_length = len(marker)
                lines.append("")
            else:
                lines.append(line)
        else:
            lines.append("")
            closer = re.match(
                rf"^\s{{0,3}}{re.escape(fence_char)}{{{fence_length},}}\s*$",
                line,
            )
            if closer:
                fence_char = None
                fence_length = 0
    return lines


def yaml_scalar_without_comment(value: str) -> str:
    """Strip a YAML plain-scalar comment while preserving quoted hashes."""
    quote: str | None = None
    escaped = False
    for index, char in enumerate(value):
        if quote == '"':
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
        elif quote == "'":
            if char == quote:
                quote = None
        elif char in "\"'":
            quote = char
        elif char == "#" and (index == 0 or value[index - 1].isspace()):
            return value[:index].rstrip()
    return value.rstrip()


def yaml_plain_scalar_is_non_string(value: str) -> bool:
    """Recognize YAML core scalars that are not strings when unquoted."""
    lowered = value.lower()
    if lowered in {
        "yes",
        "no",
        "true",
        "false",
        "on",
        "off",
        ".inf",
        "+.inf",
        "-.inf",
        ".nan",
    }:
        return True
    if value.startswith(("*", "&", "!")):
        return True
    number = re.fullmatch(
        r"[-+]?(?:"
        r"[0-9][0-9_]*|0b[01_]+|0o[0-7_]+|0x[0-9a-fA-F_]+|"
        r"[0-9][0-9_]*\.[0-9_]*(?:[eE][-+]?[0-9]+)?|"
        r"\.[0-9][0-9_]*(?:[eE][-+]?[0-9]+)?|"
        r"[0-9][0-9_]*[eE][-+]?[0-9]+|"
        r"[1-9][0-9_]*(?::[0-5]?[0-9])+(?:\.[0-9_]*)?"
        r")",
        value,
    )
    timestamp = re.fullmatch(r"\d{4}-\d{1,2}-\d{1,2}(?:[Tt ]\S+)?", value)
    return number is not None or timestamp is not None


def manifest_files(root: Path) -> list[Path]:
    return [
        path
        for path in [
            root / ".claude-plugin" / "marketplace.json",
            root / ".claude-plugin" / "plugin.json",
            root / ".codex-plugin" / "plugin.json",
            root / ".agents" / "plugins" / "marketplace.json",
            root / "plugins" / "frontend-niche-skills" / ".codex-plugin" / "plugin.json",
        ]
        if path.exists() and path.is_file()
    ]


def check_frontmatter(root: Path, result: dict[str, Any], skill_dirs: list[Path]) -> None:
    compatibility_checked = 0
    for skill_dir in skill_dirs:
        skill_file = skill_dir / "SKILL.md"
        skill_name = skill_dir.name
        if not skill_file.exists():
            add(result, "errors", rel(skill_file, root), None, "SKILL.md missing")
            continue
        lines = skill_file.read_text(encoding="utf-8", errors="ignore").splitlines()
        if not lines or lines[0].strip() != "---":
            add(result, "errors", rel(skill_file, root), 1, "YAML frontmatter missing")
            continue
        try:
            end = lines[1:].index("---") + 1
        except ValueError:
            add(result, "errors", rel(skill_file, root), 1, "YAML frontmatter terminator missing")
            continue
        frontmatter = "\n".join(lines[1:end])
        if not re.search(rf"^name:\s*{re.escape(skill_name)}\s*$", frontmatter, re.MULTILINE):
            add(result, "errors", rel(skill_file, root), 1, f"frontmatter name must match folder {skill_name}")

        # Spec: name is kebab-case, <=64 chars, and cannot contain the reserved
        # words "anthropic" or "claude".
        if len(skill_name) > 64:
            add(result, "errors", rel(skill_file, root), 1, f"name exceeds the 64-char skill-spec cap ({len(skill_name)} chars)")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", skill_name):
            add(result, "errors", rel(skill_file, root), 1, f"name must be kebab-case (lowercase letters, digits, hyphens): {skill_name}")
        for reserved in ("anthropic", "claude"):
            if reserved in skill_name:
                add(result, "errors", rel(skill_file, root), 1, f"name cannot contain the reserved word {reserved!r}")

        # Spec: only these frontmatter keys are read; anything else is ignored
        # silently, which hides typos like "descripton" behind a passing audit.
        allowed_keys = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
        for match in re.finditer(r"^([A-Za-z0-9_-]+):", frontmatter, re.MULTILINE):
            key = match.group(1)
            if key not in allowed_keys:
                add(result, "errors", rel(skill_file, root), 1, f"unsupported frontmatter key {key!r} (allowed: {', '.join(sorted(allowed_keys))})")

        # Spec: keep the SKILL.md body under 500 lines; longer bodies belong in
        # reference files that load only when needed.
        body_lines = len(lines[end + 1:])
        if body_lines > 500:
            add(result, "errors", rel(skill_file, root), 1, f"SKILL.md body exceeds the 500-line guidance ({body_lines} lines); move detail into references/")
        elif body_lines > 450:
            add(result, "warnings", rel(skill_file, root), 1, f"SKILL.md body is approaching the 500-line guidance ({body_lines} lines)")
        desc_match = re.search(r"^description:\s*(.+)$", frontmatter, re.MULTILINE)
        if not desc_match:
            add(result, "errors", rel(skill_file, root), 1, "frontmatter description missing")
        else:
            description = desc_match.group(1).strip()
            if description.startswith('"') and description.endswith('"'):
                description = description[1:-1]
            if len(description) > 1024:
                add(result, "errors", rel(skill_file, root), 1, f"description exceeds the 1024-char skill-spec cap ({len(description)} chars)")
            elif len(description) > 950:
                add(result, "warnings", rel(skill_file, root), 1, f"description is close to the 1024-char skill-spec cap ({len(description)} chars)")

            # Spec: the description is injected into the system prompt verbatim,
            # so it cannot contain XML tags and must stay in third person —
            # a shifting point of view degrades trigger accuracy.
            if re.search(r"[<>]", description):
                add(result, "errors", rel(skill_file, root), 1, "description cannot contain XML tags or angle brackets")
            person = re.search(r"\b(?:I can|I will|I help|you can use this|use me to)\b", description, re.IGNORECASE)
            if person:
                add(result, "errors", rel(skill_file, root), 1, f"description must be third person, found {person.group(0)!r}")

        compatibility_match = re.search(r"^compatibility:\s*(.*)$", frontmatter, re.MULTILINE)
        if compatibility_match:
            compatibility_checked += 1
            compatibility = yaml_scalar_without_comment(compatibility_match.group(1).strip())
            quoted = False
            if compatibility in {"|", "|-", "|+", ">", ">-", ">+"}:
                block = []
                for line in frontmatter[compatibility_match.end() :].splitlines():
                    if line and not line[0].isspace():
                        break
                    block.append(line.strip())
                compatibility = ("\n" if compatibility.startswith("|") else " ").join(block).strip()
            elif len(compatibility) >= 2 and compatibility[0] == compatibility[-1] and compatibility[0] in "\"'":
                quoted = True
                compatibility = compatibility[1:-1]
            null_value = not quoted and compatibility.lower() in {"~", "null"}
            collection_value = not quoted and compatibility.startswith(("[", "{"))
            scalar_value = not quoted and yaml_plain_scalar_is_non_string(compatibility)
            if not compatibility.strip() or null_value:
                add(result, "errors", rel(skill_file, root), 1, "frontmatter compatibility must not be empty")
            elif collection_value or scalar_value:
                add(result, "errors", rel(skill_file, root), 1, "frontmatter compatibility must be a string")
            elif len(compatibility) > 500:
                add(result, "errors", rel(skill_file, root), 1, f"compatibility exceeds the 500-char skill-spec cap ({len(compatibility)} chars)")
    result["summary"]["compatibility_fields_checked"] = compatibility_checked


def check_skill_contracts(root: Path, result: dict[str, Any], skill_dirs: list[Path]) -> None:
    checked = 0
    for skill_dir in skill_dirs:
        if skill_dir.name == "frontend-report-triage":
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue
        checked += 1
        lines = markdown_lines(skill_file.read_text(encoding="utf-8", errors="ignore"))
        for heading in ("## PR-worthiness gate", "## Output shape"):
            if heading not in lines:
                add(result, "errors", rel(skill_file, root), None, f"exact heading missing: {heading}")
        if "## PR-worthiness gate" not in lines:
            continue
        start = lines.index("## PR-worthiness gate") + 1
        end = next((index for index in range(start, len(lines)) if lines[index].startswith("## ")), len(lines))
        section = "\n".join(lines[start:end])
        if "Reject weak findings:" not in section:
            add(
                result,
                "errors",
                rel(skill_file, root),
                start,
                "PR-worthiness gate must include 'Reject weak findings:'",
            )
    result["summary"]["skill_contracts_checked"] = checked


def check_skill_evals(root: Path, result: dict[str, Any], skill_dirs: list[Path]) -> None:
    files_checked = 0
    evals_checked = 0
    for skill_dir in skill_dirs:
        path = skill_dir / "evals" / "evals.json"
        if not path.exists():
            if skill_dir.name not in LEGACY_EVAL_EXEMPTIONS:
                add(
                    result,
                    "errors",
                    rel(path, root),
                    None,
                    "new skills must include evals/evals.json",
                )
            continue
        if skill_dir.name in LEGACY_EVAL_EXEMPTIONS:
            add(
                result,
                "errors",
                rel(path, root),
                None,
                "legacy eval exemption is stale; remove this skill from LEGACY_EVAL_EXEMPTIONS",
            )
        files_checked += 1
        try:
            data = read_json(path)
        except Exception as exc:  # noqa: BLE001
            add(result, "errors", rel(path, root), None, f"cannot parse JSON: {exc}")
            continue
        if not isinstance(data, dict):
            add(result, "errors", rel(path, root), None, "evals.json root must be an object")
            continue
        if data.get("skill_name") != skill_dir.name:
            add(result, "errors", rel(path, root), None, f"skill_name must match folder {skill_dir.name}")
        evals = data.get("evals")
        if not isinstance(evals, list):
            add(result, "errors", rel(path, root), None, "evals must be an array")
            continue
        evals_checked += len(evals)
        if len(evals) < 3:
            add(result, "errors", rel(path, root), None, f"evals must contain at least 3 cases; found {len(evals)}")
        seen_ids: set[str] = set()
        for index, case in enumerate(evals, start=1):
            if not isinstance(case, dict):
                add(result, "errors", rel(path, root), None, f"eval {index} must be an object")
                continue
            eval_id = case.get("id")
            if "id" not in case or isinstance(eval_id, (list, dict)):
                add(result, "errors", rel(path, root), None, f"eval {index} id must be a scalar")
            else:
                id_key = json.dumps(eval_id, ensure_ascii=False, sort_keys=True)
                if id_key in seen_ids:
                    add(result, "errors", rel(path, root), None, f"eval {index} has duplicate id {eval_id!r}")
                seen_ids.add(id_key)
            for field in ("prompt", "expected_output"):
                value = case.get(field)
                if not isinstance(value, str) or not value.strip():
                    add(result, "errors", rel(path, root), None, f"eval {index} {field} must be a non-empty string")
            expectations = case.get("expectations")
            if expectations is not None:
                if not isinstance(expectations, list) or not expectations:
                    add(
                        result,
                        "errors",
                        rel(path, root),
                        None,
                        f"eval {index} expectations must be a non-empty array when present",
                    )
                elif not all(
                    isinstance(expectation, str) and expectation.strip()
                    for expectation in expectations
                ):
                    add(
                        result,
                        "errors",
                        rel(path, root),
                        None,
                        f"eval {index} expectations must contain only non-empty strings",
                    )
                elif len(set(expectations)) != len(expectations):
                    add(
                        result,
                        "errors",
                        rel(path, root),
                        None,
                        f"eval {index} expectations must not contain duplicates",
                    )
    result["summary"]["eval_files_checked"] = files_checked
    result["summary"]["eval_cases_checked"] = evals_checked


def check_claudeai_descriptions(root: Path, result: dict[str, Any], skill_dirs: list[Path]) -> None:
    path = root / "docs" / "claudeai-short-descriptions.json"
    if not path.exists():
        add(result, "errors", "docs/claudeai-short-descriptions.json", None, "missing Claude.ai short description map")
        return
    try:
        data = read_json(path)
    except Exception as exc:  # noqa: BLE001
        add(result, "errors", rel(path, root), None, f"cannot parse JSON: {exc}")
        return
    descriptions = data.get("descriptions") if isinstance(data, dict) else None
    if not isinstance(descriptions, dict):
        add(result, "errors", rel(path, root), None, "descriptions must be an object")
        return
    names = {skill_dir.name for skill_dir in skill_dirs}
    for missing in sorted(names - set(descriptions)):
        add(result, "errors", rel(path, root), None, f"missing short description for {missing}")
    for extra in sorted(set(descriptions) - names):
        add(result, "errors", rel(path, root), None, f"short description for unknown skill {extra!r}")
    seen: dict[str, str] = {}
    for name, text in sorted(descriptions.items()):
        if not isinstance(text, str) or not text.strip():
            add(result, "errors", rel(path, root), None, f"{name} short description must be a non-empty string")
            continue
        if len(text) > CLAUDEAI_DESCRIPTION_LIMIT:
            add(result, "errors", rel(path, root), None, f"{name} short description is {len(text)} chars; Claude.ai limit is {CLAUDEAI_DESCRIPTION_LIMIT}")
        if text in seen:
            add(result, "errors", rel(path, root), None, f"{name} short description duplicates {seen[text]}")
        else:
            seen[text] = name
    result["summary"]["claudeai_descriptions_checked"] = len(descriptions)


def check_reference_links(root: Path, result: dict[str, Any], skill_dirs: list[Path]) -> None:
    checked = 0
    for skill_dir in skill_dirs:
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue
        text = "\n".join(markdown_lines(skill_file.read_text(encoding="utf-8", errors="ignore")))
        linked = {
            (skill_file.parent / match.group(1).split("#", 1)[0].strip("<>")).resolve()
            for match in LOCAL_LINK_RE.finditer(text)
            if match.group(1).split("#", 1)[0] and not is_external(match.group(1))
        }
        for path in sorted((skill_dir / "references").glob("*.md")):
            checked += 1
            if path.resolve() not in linked:
                add(result, "errors", rel(path, root), None, "reference file must be linked directly from this skill's SKILL.md")
    result["summary"]["reference_files_checked"] = checked


def check_readmes(root: Path, result: dict[str, Any], skill_names: list[str]) -> None:
    readmes = sorted(root.glob("README*.md"))
    if not readmes:
        add(result, "warnings", "README.md", None, "README.md missing")
        return
    canonical = root / "README.md"
    canonical_order = README_SKILL_RE.findall(canonical.read_text(encoding="utf-8")) if canonical.exists() else []
    order_checked = 0
    for readme in readmes:
        rel_path = rel(readme, root)
        text = readme.read_text(encoding="utf-8")
        badge = BADGE_RE.search(text)
        if badge and int(badge.group(1)) != len(skill_names):
            add(result, "errors", rel_path, None, f"badge count {badge.group(1)} != skill count {len(skill_names)}")
        if not badge:
            add(result, "warnings", rel_path, None, "Agent_Skills badge count not found")
        ordered_links = README_SKILL_RE.findall(text)
        links = sorted(set(ordered_links))
        duplicates = sorted(name for name in links if ordered_links.count(name) > 1)
        for name in duplicates:
            add(result, "errors", rel_path, None, f"duplicate README skill link for {name}")
        missing = sorted(set(skill_names) - set(links))
        extra = sorted(set(links) - set(skill_names))
        for name in missing:
            add(result, "errors", rel_path, None, f"missing README skill link for {name}")
        for name in extra:
            add(result, "errors", rel_path, None, f"README links skill without folder: {name}")
        if canonical_order:
            order_checked += 1
            if ordered_links != canonical_order:
                add(result, "errors", rel_path, None, "README skill links must match README.md order")
    result["summary"]["readme_skill_order_checked"] = order_checked


def check_reference_toc(root: Path, result: dict[str, Any], skill_dirs: list[Path]) -> None:
    """Reference files over 100 lines need a contents list.

    Claude previews long files with partial reads (for example `head -100`), so a
    long reference with no contents list can be acted on without the agent ever
    seeing what it missed.
    """
    threshold = 100
    for skill_dir in skill_dirs:
        for path in sorted(skill_dir.rglob("*.md")):
            if path.name == "SKILL.md":
                continue
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
            if len(lines) <= threshold:
                continue
            head = "\n".join(lines[:40])
            has_heading = re.search(r"^#{1,3}\s*(?:table of contents|contents)\s*$", head, re.IGNORECASE | re.MULTILINE)
            has_anchor_list = len(re.findall(r"^\s*-\s*\[[^\]]+\]\(#", head, re.MULTILINE)) >= 3
            if not has_heading and not has_anchor_list:
                add(
                    result,
                    "errors",
                    rel(path, root),
                    1,
                    f"reference file is {len(lines)} lines and has no contents list; partial reads will miss sections",
                )


def check_reference_anchors(root: Path, result: dict[str, Any], skill_dirs: list[Path]) -> None:
    """Same-page anchor links must resolve to a real heading in that file."""
    fence = re.compile(r"^\s*(?:```|~~~)")
    heading = re.compile(r"^(#{1,6})\s+(.*?)\s*$")

    def slug(text: str) -> str:
        return re.sub(r"[^\w\s-]", "", text.lower()).replace(" ", "-")

    for skill_dir in skill_dirs:
        for path in sorted(skill_dir.rglob("*.md")):
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
            in_fence = False
            anchors: set[str] = set()
            for line in lines:
                if fence.match(line):
                    in_fence = not in_fence
                    continue
                if in_fence:
                    continue
                match = heading.match(line)
                if match:
                    anchors.add(slug(match.group(2)))
            for number, line in enumerate(lines, start=1):
                for target in re.findall(r"\]\(#([^)]+)\)", line):
                    if target not in anchors:
                        add(result, "errors", rel(path, root), number, f"anchor link #{target} has no matching heading")


def check_markdown_links(root: Path, result: dict[str, Any]) -> None:
    checked = 0
    for path in markdown_files(root):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for match in LOCAL_LINK_RE.finditer(text):
            target = match.group(1).split("#", 1)[0].strip("<>")
            if not target or is_external(target):
                continue
            checked += 1
            if not (path.parent / target).resolve().exists():
                line = text[: match.start()].count("\n") + 1
                add(result, "errors", rel(path, root), line, f"missing local markdown target: {match.group(1)}")
    result["summary"]["local_markdown_refs_checked"] = checked


def check_source_urls(root: Path, result: dict[str, Any]) -> None:
    checked = 0
    for path in markdown_files(root):
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for idx, line in enumerate(lines):
            if not SOURCE_HEADING_RE.match(line):
                continue
            block: list[str] = []
            for next_line in lines[idx + 1 :]:
                if HEADING_RE.match(next_line):
                    break
                block.append(next_line)
            if not any(item.lstrip().startswith("-") for item in block):
                continue
            checked += 1
            if not any(URL_RE.search(item) for item in block):
                add(result, "warnings", rel(path, root), idx + 1, "Sources section has no direct URL")
    result["summary"]["sources_sections_checked"] = checked


def check_manifests(root: Path, result: dict[str, Any], skill_names: list[str]) -> None:
    parsed: dict[Path, Any] = {}
    for path in manifest_files(root):
        try:
            parsed[path] = read_json(path)
        except Exception as exc:  # noqa: BLE001
            add(result, "errors", rel(path, root), None, f"cannot parse JSON: {exc}")

    claude = root / ".claude-plugin" / "plugin.json"
    if claude in parsed:
        data = parsed[claude]
        manifest_names = sorted(Path(item).name for item in data.get("skills", []))
        if manifest_names != sorted(skill_names):
            add(result, "errors", rel(claude, root), None, "Claude manifest skills must exactly match skills/*")
        result["summary"]["claude_manifest_skill_count"] = len(manifest_names)

    codex_paths = [root / ".codex-plugin" / "plugin.json", root / "plugins" / "frontend-niche-skills" / ".codex-plugin" / "plugin.json"]
    for codex in codex_paths:
        if codex not in parsed:
            continue
        data = parsed[codex]
        skills_path = data.get("skills")
        if not isinstance(skills_path, str):
            add(result, "errors", rel(codex, root), None, "Codex manifest skills must be a string path")
        else:
            candidates = [(codex.parent / skills_path).resolve(), (root / skills_path).resolve()]
            if not any(candidate.exists() for candidate in candidates):
                add(result, "errors", rel(codex, root), None, f"Codex skills path does not exist: {skills_path}")
        prompts = (data.get("interface") or {}).get("defaultPrompt")
        if prompts is not None:
            if not isinstance(prompts, list) or not all(isinstance(item, str) for item in prompts):
                add(result, "errors", rel(codex, root), None, "Codex interface.defaultPrompt must be a string list")
            elif len(prompts) > 3:
                add(result, "warnings", rel(codex, root), None, "Codex interface.defaultPrompt should stay concise (<= 3 prompts, matching e2e-skills pattern)")

    agents_marketplace = root / ".agents" / "plugins" / "marketplace.json"
    if agents_marketplace in parsed:
        data = parsed[agents_marketplace]
        plugins = data.get("plugins")
        if data.get("name") != "frontend-niche-skills":
            add(result, "errors", rel(agents_marketplace, root), None, "Agents marketplace name must be frontend-niche-skills")
        if not isinstance(plugins, list) or len(plugins) != 1:
            add(result, "errors", rel(agents_marketplace, root), None, "Agents marketplace must expose exactly one plugin")
        else:
            plugin = plugins[0]
            if plugin.get("name") != "frontend-niche-skills":
                add(result, "errors", rel(agents_marketplace, root), None, "Agents marketplace plugin name must be frontend-niche-skills")
            source = plugin.get("source") or {}
            source_path = source.get("path")
            if source.get("source") != "local" or not isinstance(source_path, str):
                add(result, "errors", rel(agents_marketplace, root), None, "Agents marketplace source must be local with a path")
            else:
                candidates = [(agents_marketplace.parent / source_path).resolve(), (root / source_path).resolve()]
                if not any(candidate.exists() for candidate in candidates):
                    add(result, "errors", rel(agents_marketplace, root), None, f"Agents marketplace source path does not exist: {source_path}")
        result["summary"]["agents_marketplace_plugin_count"] = len(plugins) if isinstance(plugins, list) else 0

    versions: dict[str, str] = {}
    for path, data in parsed.items():
        if path.name == "marketplace.json" and isinstance(data.get("plugins"), list):
            for plugin in data["plugins"]:
                if plugin.get("name") == "frontend-niche-skills" and plugin.get("version"):
                    versions[rel(path, root)] = str(plugin["version"])
        elif isinstance(data, dict) and data.get("name") == "frontend-niche-skills" and data.get("version"):
            versions[rel(path, root)] = str(data["version"])
    if len(set(versions.values())) > 1:
        add(result, "errors", "manifest versions", None, f"manifest version mismatch: {versions}")
    result["summary"]["manifest_versions"] = versions

    codex = root / ".codex-plugin" / "plugin.json"
    claude_marketplace = root / ".claude-plugin" / "marketplace.json"
    if codex in parsed and claude_marketplace in parsed:
        codex_keywords = parsed[codex].get("keywords")
        marketplace_plugins = parsed[claude_marketplace].get("plugins")
        claude_keywords = marketplace_plugins[0].get("keywords") if isinstance(marketplace_plugins, list) and marketplace_plugins else None
        if not isinstance(codex_keywords, list) or not isinstance(claude_keywords, list):
            add(result, "errors", "manifest keywords", None, "Codex and Claude marketplace keywords must both be arrays")
        elif codex_keywords != claude_keywords:
            add(result, "errors", "manifest keywords", None, "Codex and Claude marketplace keywords must match in order")

    # Pre-release guard: manifests should not point at a currently unpublished public repo.
    for path, data in parsed.items():
        text = json.dumps(data, ensure_ascii=False)
        if "github.com/voidmatcha/frontend-niche-skills" in text:
            add(result, "warnings", rel(path, root), None, "manifest references unpublished public GitHub URL")


def check_backlog_snapshot(root: Path, result: dict[str, Any]) -> None:
    path = root / "docs" / "oss-maintainer-candidate-backlog.md"
    if not path.exists():
        return
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    sections = [
        "core-web-vitals-performance-contracts",
        "frontend-data-fetching-cache-contracts",
        "async-effect-race-contracts",
        "pwa-offline-cache-contracts",
        "large-list-data-grid-contracts",
    ]
    for section in sections:
        heading = f"## `{section}`"
        try:
            start = lines.index(heading)
        except ValueError:
            add(result, "warnings", rel(path, root), None, f"missing backlog section {section}")
            continue
        end = start + 1
        while end < len(lines) and not lines[end].startswith("## "):
            end += 1
        items = [line for line in lines[start + 1 : end] if re.match(r"^\d+\. \*\*", line)]
        nums = [int(re.match(r"^(\d+)\.", line).group(1)) for line in items]
        if nums != list(range(1, 11)):
            add(result, "errors", rel(path, root), start + 1, f"section {section} must have 10 numbered candidates; found {nums}")


def check_evidence_coverage(root: Path, result: dict[str, Any], skill_names: list[str]) -> None:
    path = root / "docs" / "skill-evidence-coverage.md"
    if not path.exists():
        add(result, "warnings", rel(path, root), None, "skill evidence coverage doc missing")
        return
    text = path.read_text(encoding="utf-8", errors="ignore")
    covered = sorted(set(re.findall(r"^\| `([^`]+)` \|", text, re.MULTILINE)))
    missing = sorted(set(skill_names) - set(covered))
    extra = sorted(set(covered) - set(skill_names))
    for name in missing:
        add(result, "errors", rel(path, root), None, f"missing evidence coverage row for {name}")
    for name in extra:
        add(result, "errors", rel(path, root), None, f"evidence coverage row has no skill folder: {name}")
    result["summary"]["evidence_coverage_rows"] = len(covered)


def check_triage_coverage(root: Path, result: dict[str, Any], skill_names: list[str]) -> None:
    path = root / "skills" / "frontend-report-triage" / "SKILL.md"
    if not path.exists():
        add(result, "errors", rel(path, root), None, "frontend-report-triage skill missing")
        return
    text = path.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"^## Failure class map\s*$([\s\S]*?)(?=^## )", text, re.MULTILINE)
    if not match:
        add(result, "errors", rel(path, root), None, "Failure class map section missing")
        return
    routed: list[str] = []
    for line in match.group(1).splitlines():
        columns = line.split("|")
        if len(columns) < 4:
            continue
        skill_match = re.fullmatch(r"\s*`([a-z0-9-]+)`\s*", columns[2])
        if skill_match:
            routed.append(skill_match.group(1))
    routed = sorted(set(routed))
    expected = sorted(name for name in skill_names if name != "frontend-report-triage")
    missing = sorted(set(expected) - set(routed))
    extra = sorted(set(routed) - set(expected))
    for name in missing:
        add(result, "errors", rel(path, root), None, f"triage failure map missing route for {name}")
    for name in extra:
        add(result, "errors", rel(path, root), None, f"triage failure map routes unknown skill: {name}")
    result["summary"]["triage_skill_routes"] = len(routed)


def quoted_yaml_value(text: str, key: str) -> str | None:
    match = re.search(rf"^\s*{re.escape(key)}:\s*([\"'])(.*?)\1\s*$", text, re.MULTILINE)
    return match.group(2) if match else None


def check_agent_metadata(root: Path, result: dict[str, Any], skill_dirs: list[Path]) -> None:
    checked = 0
    for skill_dir in skill_dirs:
        path = skill_dir / "agents" / "openai.yaml"
        if not path.exists():
            add(
                result,
                "errors",
                rel(path, root),
                None,
                "agents/openai.yaml missing",
            )
            continue
        checked += 1
        text = path.read_text(encoding="utf-8", errors="ignore")
        description = quoted_yaml_value(text, "short_description")
        default_prompt = quoted_yaml_value(text, "default_prompt")
        if not description:
            add(result, "errors", rel(path, root), None, "OpenAI metadata short_description missing")
        else:
            if not 25 <= len(description) <= 64:
                add(result, "errors", rel(path, root), None, f"OpenAI metadata short_description must be 25-64 characters; found {len(description)}")
            last_word = re.sub(r"[^a-z]+", "", description.lower().split()[-1])
            if last_word in WEAK_TRAILING_WORDS:
                add(result, "warnings", rel(path, root), None, "OpenAI metadata short_description appears truncated")
        if not default_prompt or f"${skill_dir.name}" not in default_prompt:
            add(result, "errors", rel(path, root), None, f"OpenAI metadata default_prompt must invoke ${skill_dir.name}")
    result["summary"]["openai_agent_metadata_checked"] = checked


def check_overclaims(root: Path, result: dict[str, Any]) -> None:
    allowed_phrases = (
        "review claims",
        "not guarantee",
        "not guaranteed",
        "not proof",
        "do not",
        "must not",
        "not as pci certification",
        "not qsa/legal pci compliance verdict",
        'not "compliance verdict"',
        "not a list of confirmed bugs",
        "not list of confirmed bugs",
        "never claim more",
        "not secrets",
        "this site is/is not pci compliant",
    )
    for path in markdown_files(root):
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for idx, line in enumerate(lines, 1):
            context = " ".join(lines[max(0, idx - 2) : min(len(lines), idx + 1)]).lower()
            context = re.sub(r"\s+", " ", context)
            if any(phrase in context for phrase in allowed_phrases):
                continue
            if OVERCLAIM_RE.search(line):
                add(result, "warnings", rel(path, root), idx, "review strong claim/overclaim wording")


def check_mutable_repository_links(root: Path, result: dict[str, Any]) -> None:
    checked = 0
    for path in markdown_files(root):
        for index, line in enumerate(
            markdown_lines(path.read_text(encoding="utf-8", errors="ignore")),
            start=1,
        ):
            for match in REPOSITORY_SOURCE_LINK_RE.finditer(line):
                ref = next(value for value in match.groupdict().values() if value is not None)
                if FULL_COMMIT_SHA_RE.fullmatch(ref):
                    continue
                checked += 1
                add(
                    result,
                    "errors",
                    rel(path, root),
                    index,
                    "commit-pin repository file citations with a full 40-character SHA: "
                    f"{match.group(0)}",
                )
    result["summary"]["mutable_repository_links_found"] = checked


def check_script_syntax(root: Path, result: dict[str, Any]) -> None:
    checked: list[str] = []
    script_paths = [
        *root.glob("scripts/*"),
        *root.glob("skills/**/scripts/*"),
        *root.glob("skills/**/tests/*"),
    ]
    for path in sorted(script_paths):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        if path.suffix == ".sh":
            proc = subprocess.run(["bash", "-n", str(path)], cwd=root, text=True, capture_output=True)
            checked.append(rel(path, root))
            if proc.returncode != 0:
                add(result, "errors", rel(path, root), None, f"bash -n failed: {proc.stderr.strip()}")
        elif path.suffix in {".cjs", ".mjs", ".js"}:
            proc = subprocess.run(["node", "--check", str(path)], cwd=root, text=True, capture_output=True)
            checked.append(rel(path, root))
            if proc.returncode != 0:
                add(result, "errors", rel(path, root), None, f"node --check failed: {proc.stderr.strip()}")
        elif path.suffix == ".py":
            checker = "import pathlib,sys; compile(pathlib.Path(sys.argv[1]).read_text(), sys.argv[1], 'exec')"
            proc = subprocess.run([sys.executable, "-c", checker, str(path)], cwd=root, text=True, capture_output=True)
            checked.append(rel(path, root))
            if proc.returncode != 0:
                add(result, "errors", rel(path, root), None, f"python syntax check failed: {proc.stderr.strip()}")
    result["summary"]["scripts_syntax_checked"] = checked


def check_external_links(root: Path, result: dict[str, Any], only: list[Path] | None = None) -> None:
    """Opt-in network check: external URLs in tracked markdown must still resolve.

    Only 404/410 fail the run — a dead citation is a real defect. Everything
    else (timeouts, DNS, bot-blocking 403/429) is reported as unverified but
    does not fail, because transient failures are common enough to make a
    strict gate flap between runs.

    Pass `only` to limit the scan to specific files (pre-push checks the files
    being pushed; the scheduled job checks everything).
    """
    import urllib.error
    import urllib.request
    from concurrent.futures import ThreadPoolExecutor

    skip_hosts = ("example.com", "example.org", "example.test", "localhost", "127.0.0.1")
    if only is not None:
        files = {path for path in only if path.exists() and path.suffix == ".md"}
    else:
        files = set(root.glob("README*.md"))
        for extra in (root / "CHANGELOG.md",):
            if extra.exists():
                files.add(extra)
        for tree in (root / "docs", root / "skills"):
            if tree.exists():
                files.update(tree.rglob("*.md"))
    first_seen: dict[str, Path] = {}
    for path in sorted(files):
        for match in URL_RE.finditer(path.read_text(encoding="utf-8")):
            url = match.group(0).split("`")[0].rstrip(".,;:").split("#")[0]
            host = url.split("://", 1)[-1].split("/", 1)[0]
            if (
                "<" in url
                or "(" in url  # URL_RE stops at ")", truncating paren-bearing URLs
                or any(ch in url for ch in "…*")
                or "." not in host
                or "@" in host
                or host.endswith((".example", ".test", ".invalid"))
                or any(skip in url for skip in skip_hosts)
            ):
                continue
            first_seen.setdefault(url, path)

    def status_of(url: str) -> int:
        headers = {"User-Agent": "Mozilla/5.0 (skill-pack-audit link check)"}
        for method, timeout in (("HEAD", 10), ("GET", 15)):
            try:
                request = urllib.request.Request(url, method=method, headers=headers)
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    return response.status
            except urllib.error.HTTPError as error:
                # Some hosts (rfc-editor, some CDNs) 404 or block HEAD but serve GET.
                if method == "GET" or error.code not in (403, 404, 405, 410, 429, 501):
                    return error.code
            except Exception:
                if method == "GET":
                    return -1
        return -1

    if not first_seen:
        result["summary"]["external_urls_checked"] = 0
        return
    with ThreadPoolExecutor(max_workers=8) as pool:
        statuses = dict(zip(first_seen, pool.map(status_of, first_seen)))
    unverified: list[str] = []
    for url, status in sorted(statuses.items()):
        rel_path = rel(first_seen[url], root)
        if status in (404, 410):
            add(result, "errors", rel_path, None, f"dead external link ({status}): {url}")
        elif status == -1 or status >= 400:
            label = "network/timeout" if status == -1 else f"status {status}"
            unverified.append(f"{rel_path} — {label}: {url}")
    result["summary"]["external_urls_checked"] = len(first_seen)
    if unverified:
        result["summary"]["external_urls_unverified"] = unverified


def audit(root: Path, check_links: bool = False, link_paths: list[Path] | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "root": str(root),
        "summary": {},
        "errors": [],
        "warnings": [],
    }
    skills_root = root / "skills"
    if not skills_root.exists():
        add(result, "errors", "skills", None, "skills directory missing")
        result["ok"] = False
        return result
    skill_dirs = sorted(path for path in skills_root.iterdir() if path.is_dir())
    skill_names = [path.name for path in skill_dirs]
    result["summary"]["skill_count"] = len(skill_names)
    result["summary"]["skill_names"] = skill_names
    # Maintainer-only tooling must not ship as a public skill.
    if "skill-pack-auditor" in skill_names:
        add(result, "errors", "skills/skill-pack-auditor", None, "skill-pack-auditor must not be published as a public skill")
    check_frontmatter(root, result, skill_dirs)
    check_skill_contracts(root, result, skill_dirs)
    check_skill_evals(root, result, skill_dirs)
    check_claudeai_descriptions(root, result, skill_dirs)
    check_reference_links(root, result, skill_dirs)
    check_readmes(root, result, skill_names)
    check_reference_toc(root, result, skill_dirs)
    check_reference_anchors(root, result, skill_dirs)
    check_markdown_links(root, result)
    check_source_urls(root, result)
    check_manifests(root, result, skill_names)
    check_backlog_snapshot(root, result)
    check_evidence_coverage(root, result, skill_names)
    check_triage_coverage(root, result, skill_names)
    check_agent_metadata(root, result, skill_dirs)
    check_overclaims(root, result)
    check_mutable_repository_links(root, result)
    check_script_syntax(root, result)
    if check_links:
        check_external_links(root, result, only=link_paths)
    result["ok"] = not result["errors"] and not result["warnings"]
    return result


def print_text(result: dict[str, Any]) -> None:
    print(f"Skill pack audit: {'PASS' if result['ok'] else 'FAIL'}")
    print(f"Root: {result['root']}")
    print(f"Skills: {result['summary'].get('skill_count', 0)}")
    print(f"Local markdown refs checked: {result['summary'].get('local_markdown_refs_checked', 0)}")
    print(f"Sources sections checked: {result['summary'].get('sources_sections_checked', 0)}")
    print(f"Compatibility fields checked: {result['summary'].get('compatibility_fields_checked', 0)}")
    print(f"Skill contracts checked: {result['summary'].get('skill_contracts_checked', 0)}")
    print(f"Eval files checked: {result['summary'].get('eval_files_checked', 0)}")
    print(f"Eval cases checked: {result['summary'].get('eval_cases_checked', 0)}")
    print(f"Reference files checked: {result['summary'].get('reference_files_checked', 0)}")
    print(f"README skill orders checked: {result['summary'].get('readme_skill_order_checked', 0)}")
    scripts = result["summary"].get("scripts_syntax_checked", [])
    print(f"Scripts syntax checked: {len(scripts)}")
    if "external_urls_checked" in result["summary"]:
        print(f"External URLs checked: {result['summary']['external_urls_checked']}")
    unverified = result["summary"].get("external_urls_unverified", [])
    if unverified:
        print(f"External URLs unverified (not a failure): {len(unverified)}")
        for item in unverified:
            print(f"- {item}")
    if result["errors"]:
        print("\nErrors:")
        for item in result["errors"]:
            loc = f"{item['path']}:{item['line']}" if item["line"] else item["path"]
            print(f"- {loc} — {item['message']}")
    if result["warnings"]:
        print("\nWarnings:")
        for item in result["warnings"][:80]:
            loc = f"{item['path']}:{item['line']}" if item["line"] else item["path"]
            print(f"- {loc} — {item['message']}")
        if len(result["warnings"]) > 80:
            print(f"... {len(result['warnings']) - 80} more warning(s)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print JSON output")
    parser.add_argument(
        "--check-links",
        action="store_true",
        help="also verify external URLs resolve (network; only 404/410 fail)",
    )
    parser.add_argument(
        "--link-paths",
        nargs="*",
        metavar="FILE",
        help="with --check-links, only check URLs in these files (e.g. the files being pushed)",
    )
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    link_paths = [Path(p).resolve() for p in args.link_paths] if args.link_paths is not None else None
    result = audit(root, check_links=args.check_links, link_paths=link_paths)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print_text(result)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
