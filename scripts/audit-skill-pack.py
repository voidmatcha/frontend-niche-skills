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
SOURCE_HEADING_RE = re.compile(r"^#{1,3}\s+Sources\b", re.IGNORECASE)
HEADING_RE = re.compile(r"^#{1,6}\s+")


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
            root / "README.md",
            root / "CHANGELOG.md",
            root / "SECURITY.md",
            *root.glob("docs/**/*.md"),
            *root.glob("skills/**/*.md"),
        ]
        if path.exists() and path.is_file()
    ]


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


def check_readme(root: Path, result: dict[str, Any], skill_names: list[str]) -> None:
    readme = root / "README.md"
    if not readme.exists():
        add(result, "warnings", "README.md", None, "README.md missing")
        return
    text = readme.read_text(encoding="utf-8")
    badge = BADGE_RE.search(text)
    if badge and int(badge.group(1)) != len(skill_names):
        add(result, "errors", "README.md", None, f"badge count {badge.group(1)} != skill count {len(skill_names)}")
    if not badge:
        add(result, "warnings", "README.md", None, "Agent_Skills badge count not found")
    links = sorted(set(README_SKILL_RE.findall(text)))
    missing = sorted(set(skill_names) - set(links))
    extra = sorted(set(links) - set(skill_names))
    for name in missing:
        add(result, "errors", "README.md", None, f"missing README skill link for {name}")
    for name in extra:
        add(result, "errors", "README.md", None, f"README links skill without folder: {name}")


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
        for idx, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            lowered = line.lower()
            if any(phrase in lowered for phrase in allowed_phrases):
                continue
            if OVERCLAIM_RE.search(line):
                add(result, "warnings", rel(path, root), idx, "review strong claim/overclaim wording")


def check_script_syntax(root: Path, result: dict[str, Any]) -> None:
    checked: list[str] = []
    script_paths = [*root.glob("scripts/*"), *root.glob("skills/**/scripts/*")]
    for path in sorted(script_paths):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        if path.suffix == ".sh":
            proc = subprocess.run(["bash", "-n", str(path)], cwd=root, text=True, capture_output=True)
            checked.append(rel(path, root))
            if proc.returncode != 0:
                add(result, "errors", rel(path, root), None, f"bash -n failed: {proc.stderr.strip()}")
        elif path.suffix in {".mjs", ".js"}:
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


def audit(root: Path) -> dict[str, Any]:
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
    check_frontmatter(root, result, skill_dirs)
    check_readme(root, result, skill_names)
    check_markdown_links(root, result)
    check_source_urls(root, result)
    check_manifests(root, result, skill_names)
    check_backlog_snapshot(root, result)
    check_overclaims(root, result)
    check_script_syntax(root, result)
    result["ok"] = not result["errors"] and not result["warnings"]
    return result


def print_text(result: dict[str, Any]) -> None:
    print(f"Skill pack audit: {'PASS' if result['ok'] else 'FAIL'}")
    print(f"Root: {result['root']}")
    print(f"Skills: {result['summary'].get('skill_count', 0)}")
    print(f"Local markdown refs checked: {result['summary'].get('local_markdown_refs_checked', 0)}")
    print(f"Sources sections checked: {result['summary'].get('sources_sections_checked', 0)}")
    scripts = result["summary"].get("scripts_syntax_checked", [])
    print(f"Scripts syntax checked: {len(scripts)}")
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
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    result = audit(root)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print_text(result)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
