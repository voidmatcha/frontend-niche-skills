#!/usr/bin/env python3
"""Emit a Claude.ai-compatible variant of the skill pack.

Claude.ai caps the SKILL.md frontmatter `description` at 200 characters, while
the Agent Skills specification allows 1024. This pack spends the larger budget
on routing triggers, so the canonical skills cannot be uploaded to Claude.ai
unchanged. This script copies each skill and swaps in the short description
from docs/claudeai-short-descriptions.json. The canonical SKILL.md files are
never modified; the variant is build output.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

CLAUDEAI_DESCRIPTION_LIMIT = 200
SHORT_DESCRIPTIONS = Path("docs/claudeai-short-descriptions.json")
DEFAULT_OUT = Path("dist/claudeai")

FRONTMATTER_RE = re.compile(r"\A---\n(?P<body>.*?)\n---\n", re.DOTALL)
DESCRIPTION_RE = re.compile(r"^description:.*(?:\n[ \t]+.*)*$", re.MULTILINE)


def yaml_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def build(root: Path, out_dir: Path) -> int:
    mapping_path = root / SHORT_DESCRIPTIONS
    if not mapping_path.exists():
        print(f"missing {SHORT_DESCRIPTIONS}", file=sys.stderr)
        return 1
    descriptions = json.loads(mapping_path.read_text(encoding="utf-8"))["descriptions"]

    skill_dirs = sorted(p for p in (root / "skills").iterdir() if (p / "SKILL.md").is_file())
    errors: list[str] = []

    if out_dir.exists():
        shutil.rmtree(out_dir)

    for skill_dir in skill_dirs:
        name = skill_dir.name
        short = descriptions.get(name)
        if short is None:
            errors.append(f"{name}: no entry in {SHORT_DESCRIPTIONS}")
            continue
        if len(short) > CLAUDEAI_DESCRIPTION_LIMIT:
            errors.append(f"{name}: description is {len(short)} chars, limit is {CLAUDEAI_DESCRIPTION_LIMIT}")
            continue

        text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        match = FRONTMATTER_RE.match(text)
        if match is None:
            errors.append(f"{name}: SKILL.md has no frontmatter")
            continue
        frontmatter = match.group("body")
        if not DESCRIPTION_RE.search(frontmatter):
            errors.append(f"{name}: SKILL.md frontmatter has no description")
            continue

        rewritten = DESCRIPTION_RE.sub(f"description: {yaml_quote(short)}", frontmatter, count=1)
        target = out_dir / name
        shutil.copytree(skill_dir, target)
        (target / "SKILL.md").write_text(
            f"---\n{rewritten}\n---\n{text[match.end():]}", encoding="utf-8"
        )

    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1

    print(f"Wrote {len(skill_dirs)} skills to {out_dir}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    root = args.root.resolve()
    return build(root, args.out.resolve() if args.out else root / DEFAULT_OUT)


if __name__ == "__main__":
    raise SystemExit(main())
