# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2026-06-11

### Added

- `a11y-contract-testing` skill — accessibility semantics as testable contracts:
  dialog role/name requirements (WCAG 4.1.2, ARIA APG), role+name queries,
  sentinel specs, decorative-wrapper `role="presentation"` rules.
- `cjk-text-and-input` skill — CJK line breaking (`word-break: keep-all`,
  `line-break`, UAX #14), IME composition events (`isComposing`, legacy keyCode 229,
  Enter-during-composition guard), controlled-input composition pitfalls,
  grapheme-safe counting (`Intl.Segmenter`, NFC normalization).
- `deeplink-hydration` skill — deep links surviving SPA/SSR hydration:
  `router.isReady` gating, `window.location` as client-side source of truth,
  auth-bounce `returnTo`, direct-navigation e2e rule.

### Changed

- Renamed the collection from `webview-skills` to **`frontend-niche-skills`** —
  the scope is the long tail of frontend topics, not just webviews. Plugin and
  marketplace manifests updated (plugin `frontend-niche-skills` ships all skills;
  install command changed).

## [1.0.0] - 2026-06-10

### Added

- `webview-bridge-pages` skill: 12-item checklist plus a universal transport adapter
  for web pages running inside native app WebViews (React Native WebView, WKWebView,
  Android WebView, Flutter `webview_flutter`).
- `references/contract-design.md` — message contract, close/back ownership,
  actions with unobservable results (purchases), READY loading signal paired with an
  error/timeout policy, auth & session handoff, navigation & capabilities policy,
  A/B variants via query params.
- `references/page-implementation.md` — query parsing on SPA hydration, absolute-time
  timers, viewport/safe-area/keyboard/font-scale layout rules.
- Host references: `react-native.md`, `wkwebview.md`, `android-webview.md`,
  `flutter.md` (bridge APIs, version caveats, quirks).
- README curation of related bridge libraries, engineering write-ups, and
  compatibility references (all links live-verified 2026-06).
- Claude Code plugin packaging (`.claude-plugin/plugin.json`, `marketplace.json`),
  Apache-2.0 license, security policy.

### Notes

- All factual claims verified against official sources before release (93 claims
  checked; corrections incorporated). Community-sourced claims are labeled as such
  in the text.
- Incorporates an external Codex CLI review (auth/navigation/error-contract topics,
  framework-neutral adapter snippet, source-wording accuracy).

[Unreleased]: https://github.com/dididy/frontend-niche-skills/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/dididy/frontend-niche-skills/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/dididy/frontend-niche-skills/releases/tag/v1.0.0
