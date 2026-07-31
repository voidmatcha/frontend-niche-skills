#!/usr/bin/env bash
set -euo pipefail

# Print every Markdown file that can be part of the next delivered change as a
# NUL-delimited record: committed range, staged work, unstaged work, and
# untracked files.
#
# Resolution order for the committed portion:
#   1. CHECK_DIFF_BASE and CHECK_DIFF_HEAD (CI/push delivery endpoints)
#   2. one explicit git diff range argument
#   3. two explicit git diff endpoint arguments
#   4. the current branch upstream and HEAD
#   5. the empty tree and HEAD (safe for first pushes and detached/shallow work)
#
# Usage:
#   scripts/list-changed-markdown.sh
#   scripts/list-changed-markdown.sh <git-diff-range>
#   scripts/list-changed-markdown.sh <base> <head>

if [ "$#" -gt 2 ]; then
  echo "usage: $0 [git-diff-range] | [base head]" >&2
  exit 2
fi

COMMITTED_DIFF_ARGS=()
if [ -n "${CHECK_DIFF_BASE:-}" ]; then
  diff_head="${CHECK_DIFF_HEAD:-HEAD}"
  if [[ "$CHECK_DIFF_BASE" =~ ^0{40}$ ]]; then
    empty_tree="$(git hash-object -t tree /dev/null)"
    COMMITTED_DIFF_ARGS=("$empty_tree" "$diff_head")
  else
    if ! git rev-parse --verify "${CHECK_DIFF_BASE}^{commit}" >/dev/null 2>&1; then
      echo "CHECK_DIFF_BASE is not available: $CHECK_DIFF_BASE" >&2
      exit 2
    fi
    if ! git rev-parse --verify "${diff_head}^{commit}" >/dev/null 2>&1; then
      echo "CHECK_DIFF_HEAD is not available: $diff_head" >&2
      exit 2
    fi
    COMMITTED_DIFF_ARGS=("$CHECK_DIFF_BASE" "$diff_head")
  fi
elif [ "$#" -eq 1 ]; then
  COMMITTED_DIFF_ARGS=("$1")
elif [ "$#" -eq 2 ]; then
  COMMITTED_DIFF_ARGS=("$1" "$2")
elif upstream_commit="$(git rev-parse --verify '@{u}^{commit}' 2>/dev/null)"; then
  COMMITTED_DIFF_ARGS=("$upstream_commit" "HEAD")
elif git rev-parse --verify 'HEAD^{commit}' >/dev/null 2>&1; then
  empty_tree="$(git hash-object -t tree /dev/null)"
  COMMITTED_DIFF_ARGS=("$empty_tree" "HEAD")
fi

{
  if [ "${#COMMITTED_DIFF_ARGS[@]}" -gt 0 ]; then
    git diff --name-only -z --diff-filter=d "${COMMITTED_DIFF_ARGS[@]}" -- '*.md'
  fi
  git diff --name-only -z --diff-filter=d -- '*.md'
  git diff --cached --name-only -z --diff-filter=d -- '*.md'
  git ls-files --others --exclude-standard -z -- '*.md'
} | sort -zu
