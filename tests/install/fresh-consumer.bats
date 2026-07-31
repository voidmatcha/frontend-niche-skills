#!/usr/bin/env bats

# This smoke uses the public skills CLI because its --copy mode proves that a
# downstream project receives independent skill files. A local `codex plugin`
# marketplace install is not equivalent evidence: Codex registers the checkout
# path and creates an empty plugin cache directory for that local source.
#
# The CLI must already be installed (or supplied with SKILLS_CLI). The test
# never invokes npx, so an offline CI run cannot trigger an implicit download.

install_skill_source() {
  local source_path="$1"
  local project_path="$2"
  local log_path="$3"

  if ! (
    cd "$project_path"
    CI=1 NO_COLOR=1 "$SKILLS_CLI" add "$source_path" \
      --skill '*' \
      --agent claude-code codex \
      --copy \
      --yes
  ) >"$log_path" 2>&1; then
    cat "$log_path" >&2
    return 1
  fi
}

setup_file() {
  export REPO_ROOT
  REPO_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"

  export SKILLS_CLI="${SKILLS_CLI:-}"
  if [[ -z "$SKILLS_CLI" ]]; then
    SKILLS_CLI="$(command -v skills || true)"
    export SKILLS_CLI
  fi

  if [[ -z "$SKILLS_CLI" || ! -x "$SKILLS_CLI" ]]; then
    if [[ "${CI:-}" == "true" || "${CI:-}" == "1" ]]; then
      echo "skills CLI is required in CI; install the pinned workflow version or set SKILLS_CLI" >&2
      return 1
    fi
    skip "skills CLI is not installed; set SKILLS_CLI to run the offline consumer smoke"
  fi

  export SMOKE_ROOT="$BATS_FILE_TMPDIR/fresh-consumer"
  export CONSUMER_PROJECT="$SMOKE_ROOT/project"
  export WRAPPER_CONSUMER_PROJECT="$SMOKE_ROOT/plugin-wrapper-project"
  export HOME="$SMOKE_ROOT/home"
  export CODEX_HOME="$SMOKE_ROOT/codex-home"
  export XDG_CONFIG_HOME="$SMOKE_ROOT/xdg-config"
  export XDG_CACHE_HOME="$SMOKE_ROOT/xdg-cache"
  export XDG_DATA_HOME="$SMOKE_ROOT/xdg-data"

  mkdir -p \
    "$CONSUMER_PROJECT" \
    "$WRAPPER_CONSUMER_PROJECT" \
    "$HOME" \
    "$CODEX_HOME" \
    "$XDG_CONFIG_HOME" \
    "$XDG_CACHE_HOME" \
    "$XDG_DATA_HOME"

  install_skill_source "$REPO_ROOT" "$CONSUMER_PROJECT" "$SMOKE_ROOT/install.log"
  install_skill_source \
    "$REPO_ROOT/plugins/frontend-niche-skills" \
    "$WRAPPER_CONSUMER_PROJECT" \
    "$SMOKE_ROOT/plugin-wrapper-install.log"
}

teardown_file() {
  if [[ -n "${SMOKE_ROOT:-}" && "$SMOKE_ROOT" == "$BATS_FILE_TMPDIR/"* ]]; then
    find "$SMOKE_ROOT" -depth -delete
  fi
}

skill_names() {
  local skills_root="$1"

  find "$skills_root" \
    -mindepth 2 \
    -maxdepth 2 \
    -type f \
    -name SKILL.md \
    -print |
    sed 's#/SKILL\.md$##; s#^.*/##' |
    sort
}

skill_files() {
  local skills_root="$1"

  find "$skills_root" \
    -mindepth 2 \
    -type f \
    -print |
    sed "s#^$skills_root/##" |
    sort
}

@test "copies every source skill into the Codex project skill surface" {
  run diff \
    <(skill_names "$REPO_ROOT/skills") \
    <(skill_names "$CONSUMER_PROJECT/.agents/skills")

  [[ "$status" -eq 0 ]]
}

@test "copies every source skill into the Claude Code project skill surface" {
  run diff \
    <(skill_names "$REPO_ROOT/skills") \
    <(skill_names "$CONSUMER_PROJECT/.claude/skills")

  [[ "$status" -eq 0 ]]
}

@test "preserves every skill file byte-for-byte on both consumer surfaces" {
  local relative_path

  run diff \
    <(skill_files "$REPO_ROOT/skills") \
    <(skill_files "$CONSUMER_PROJECT/.agents/skills")
  [[ "$status" -eq 0 ]]

  run diff \
    <(skill_files "$REPO_ROOT/skills") \
    <(skill_files "$CONSUMER_PROJECT/.claude/skills")
  [[ "$status" -eq 0 ]]

  while IFS= read -r relative_path; do
    cmp \
      "$REPO_ROOT/skills/$relative_path" \
      "$CONSUMER_PROJECT/.agents/skills/$relative_path"
    cmp \
      "$REPO_ROOT/skills/$relative_path" \
      "$CONSUMER_PROJECT/.claude/skills/$relative_path"
  done < <(skill_files "$REPO_ROOT/skills")
}

@test "installs independent files instead of symlinks or source aliases" {
  local linked_paths
  local source_skill="$REPO_ROOT/skills/frontend-report-triage/SKILL.md"
  local codex_skill="$CONSUMER_PROJECT/.agents/skills/frontend-report-triage/SKILL.md"
  local claude_skill="$CONSUMER_PROJECT/.claude/skills/frontend-report-triage/SKILL.md"

  linked_paths="$(
    find \
      "$CONSUMER_PROJECT/.agents/skills" \
      "$CONSUMER_PROJECT/.claude/skills" \
      -type l \
      -print
  )"

  [[ -z "$linked_paths" ]]
  [[ -f "$codex_skill" ]]
  [[ -f "$claude_skill" ]]
  [[ ! "$source_skill" -ef "$codex_skill" ]]
  [[ ! "$source_skill" -ef "$claude_skill" ]]
}

@test "keeps installation state inside the isolated consumer project" {
  [[ -f "$CONSUMER_PROJECT/skills-lock.json" ]]
  [[ -z "$(find "$HOME" "$CODEX_HOME" "$XDG_CONFIG_HOME" "$XDG_CACHE_HOME" "$XDG_DATA_HOME" -type f -print)" ]]
}

@test "plugin wrapper source copies every skill into both consumer skill surfaces" {
  run diff \
    <(skill_names "$REPO_ROOT/skills") \
    <(skill_names "$WRAPPER_CONSUMER_PROJECT/.agents/skills")

  [[ "$status" -eq 0 ]]

  run diff \
    <(skill_names "$REPO_ROOT/skills") \
    <(skill_names "$WRAPPER_CONSUMER_PROJECT/.claude/skills")

  [[ "$status" -eq 0 ]]
}

@test "plugin wrapper source preserves every skill file without symlinks" {
  local relative_path
  local linked_paths

  linked_paths="$(
    find \
      "$WRAPPER_CONSUMER_PROJECT/.agents/skills" \
      "$WRAPPER_CONSUMER_PROJECT/.claude/skills" \
      -type l \
      -print
  )"
  [[ -z "$linked_paths" ]]

  run diff \
    <(skill_files "$REPO_ROOT/skills") \
    <(skill_files "$WRAPPER_CONSUMER_PROJECT/.agents/skills")
  [[ "$status" -eq 0 ]]

  run diff \
    <(skill_files "$REPO_ROOT/skills") \
    <(skill_files "$WRAPPER_CONSUMER_PROJECT/.claude/skills")
  [[ "$status" -eq 0 ]]

  while IFS= read -r relative_path; do
    cmp \
      "$REPO_ROOT/skills/$relative_path" \
      "$WRAPPER_CONSUMER_PROJECT/.agents/skills/$relative_path"
    cmp \
      "$REPO_ROOT/skills/$relative_path" \
      "$WRAPPER_CONSUMER_PROJECT/.claude/skills/$relative_path"
  done < <(skill_files "$REPO_ROOT/skills")
}
