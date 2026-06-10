# Security Policy

## Scope

This repository ships **documentation only** (agent skill markdown). There is no
executable or installable code; the transport-adapter snippet is copied into your own
codebase and reviewed there. Security-relevant guidance in the skill (bridge origin
validation, token handling, `addJavascriptInterface` caveats) is sourced from the
official platform documents cited in each reference file.

## Reporting

If you find guidance in this skill that would lead an implementation into a
vulnerability (e.g. unsafe bridge advice, incorrect origin-validation claims), please
report it privately via
[GitHub Security Advisories](https://github.com/dididy/webview-skills/security/advisories/new)
rather than a public issue. Inaccuracies without security impact can go to regular
issues.

## Supported versions

Only the latest `main` is maintained; the skill is versioned via CHANGELOG.md.
