#!/usr/bin/env python3
"""Audit the exact Git deliverable, not the dirty working tree.

The normal pack audit intentionally reads the current filesystem so local and
pre-release checkouts can be validated before they are committed. This guard is
separate: it extracts a Git ref/archive and runs the pack audit against that
snapshot, catching manifests that only pass because untracked files exist.
"""
from __future__ import annotations

import argparse
import io
import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path


def run(command: list[str], cwd: Path, *, capture: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def git_stdout(repo: Path, args: list[str]) -> str:
    proc = run(["git", *args], repo)
    if proc.returncode != 0:
        message = proc.stderr.strip() or proc.stdout.strip()
        raise RuntimeError(message or f"git {' '.join(args)} failed")
    return proc.stdout.strip()


def choose_ref(repo: Path, explicit_ref: str | None) -> str:
    if explicit_ref:
        return explicit_ref
    for name in ("CHECK_DELIVERABLE_REF", "CHECK_DIFF_HEAD"):
        value = os.environ.get(name)
        if value:
            return value
    return "HEAD"


def is_git_repo(repo: Path) -> bool:
    proc = run(["git", "rev-parse", "--is-inside-work-tree"], repo)
    return proc.returncode == 0 and proc.stdout.strip() == "true"


def extract_archive(repo: Path, ref: str, destination: Path) -> None:
    archive = subprocess.run(
        ["git", "archive", "--format=tar", ref],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if archive.returncode != 0:
        message = archive.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(message or f"git archive failed for {ref}")
    with tarfile.open(fileobj=io.BytesIO(archive.stdout), mode="r:") as tar:
        tar.extractall(destination)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Git repository root to archive")
    parser.add_argument("--ref", help="Git ref to audit; defaults to CHECK_DELIVERABLE_REF, CHECK_DIFF_HEAD, or HEAD")
    parser.add_argument(
        "--audit-script",
        help="Audit script to run against the extracted archive; defaults to <repo>/scripts/audit-skill-pack.py",
    )
    parser.add_argument("--require-git", action="store_true", help="Fail instead of skipping when --repo is not a Git worktree")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not is_git_repo(repo):
        message = f"Git deliverable audit skipped: {repo} is not a Git worktree"
        if args.require_git:
            print(message, file=sys.stderr)
            return 2
        print(message)
        return 0

    try:
        root = Path(git_stdout(repo, ["rev-parse", "--show-toplevel"]))
        ref = choose_ref(root, args.ref)
        git_stdout(root, ["rev-parse", "--verify", f"{ref}^{{commit}}"])
    except RuntimeError as exc:
        print(f"Git deliverable audit failed before archive: {exc}", file=sys.stderr)
        return 2

    audit_script = Path(args.audit_script).resolve() if args.audit_script else root / "scripts" / "audit-skill-pack.py"
    if not audit_script.exists():
        print(f"Git deliverable audit failed: audit script not found: {audit_script}", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="frontend-skill-deliverable-") as temp_dir:
        archive_root = Path(temp_dir) / "archive"
        archive_root.mkdir()
        try:
            extract_archive(root, ref, archive_root)
        except RuntimeError as exc:
            print(f"Git deliverable audit failed before audit: {exc}", file=sys.stderr)
            return 2

        proc = subprocess.run(
            [sys.executable, str(audit_script), str(archive_root)],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(proc.stdout, end="")
        if proc.returncode != 0:
            print(
                f"Git deliverable audit failed for ref {ref}: the exact Git archive does not pass the current pack audit. "
                "Commit the missing deliverable files or pass an explicit committed ref, then re-run.",
                file=sys.stderr,
            )
            return proc.returncode

    print(f"Git deliverable audit passed for ref {ref}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
