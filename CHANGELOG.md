# Changelog

All notable changes to this project are documented here. This project follows the general shape of [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- `contenteditable-selection-contracts` for editing-host selection ownership, `beforeinput`/`input` transaction boundaries, composition-safe DOM updates, undo/redo ownership, paste/drop insertion, focus, and teardown.
- `browser-storage-durability-contracts` for IndexedDB upgrade ownership,
  transaction activity and stale-write prevention, commit/abort evidence,
  StorageManager quota/persistence, and truthful browser-local recovery,
  backed by 13 evaluation cases including five hard competing-hypothesis and
  recovery-boundary cases.
- A catalog-complete routing benchmark with 138 representative, collision-smoke,
  and curated hard-collision cases; a limited static answer-cue lint; a curated
  100-edge plausible-domain denominator with 98 tested edges; a fail-closed
  validator; opaque deterministic export;
  exact-primary and acceptable-owner metrics; live-run manifest template; and
  CI-discovered tests. The registry is not a claim of exhaustive boundary
  coverage.
- A digest-bound 16-case `gpt-5.5` metadata comparison covering the eight new
  domains and eight hard boundaries. The name-only and pre-edit catalogs both
  scored 15/16; after narrowing the export/activation descriptions, the current
  catalog scored 16/16. The artifact records the single-run, partial-coverage,
  backend-version, and hidden-state limits and does not claim catalog-wide
  accuracy.
- Isolated fresh-consumer install smoke coverage that copies the complete skill
  pack from both repository and plugin-wrapper sources into temporary Codex and
  Claude project skill surfaces, then compares every delivered skill file
  without touching real user configuration.
- A Git-ref delivery audit that extracts the exact committed archive and applies
  the current pack standard, preventing untracked files from making a release
  candidate appear complete.
- Bundled Chromium/Firefox/WebKit casebooks for same-document scroll restoration,
  trusted-mouse pointer ownership, emulated touch delivery, and synthetic
  `MediaStream` application lifecycle; Chromium fake-device `getUserMedia`
  remains a separate lane, and physical-device/native-permission protocols are
  documented without claiming execution.
- `history-scroll-restoration-contracts` for SPA/same-document history-entry identity, native-vs-manual scroll restoration, async render readiness, double-scroll races, and fragment navigation.
- `pointer-gesture-contracts` for single active-pointer ownership, event delivery/capture, cancellation, `touch-action`, and direct-manipulation cleanup, while routing pinch/rotate/multi-contact geometry elsewhere.
- `media-capture-device-contracts` for camera/microphone permission transitions, device enumeration/change, track lifecycle, teardown, and reacquisition.
- `docs/public-skill-landscape.md` as an opened-source comparison of directly overlapping, near-match, and complementary public skill packs.
- `browser-page-lifecycle-bfcache-contracts` for distinguishing first loads from Back/Forward Cache restores, pausing and resuming resources, reconciling stale state, and diagnosing eligibility without blanket unload workarounds.
- `user-activation-contracts` for transient/sticky activation, async gesture boundaries, activation-consuming APIs, and blocked popup/clipboard/fullscreen/file-picker recovery.
- `resize-observer-layout-contracts` for pre-paint delivery, callback-induced resize cycles, box selection, stale targets, cleanup, and observer ownership boundaries.
- `docs/skill-quality-standard.md` as the evidence-backed admission and maintenance standard for focused, discoverable, operational, bounded, testable skills.
- `download-export-safety` for CSV/Excel exports, Blob/Object URL lifecycle, clipboard writes, and export filenames.
- `overlay-focus-scroll-contracts` for modal/drawer/sheet/popover focus, inert/aria-hidden timing, nested overlays, and scroll-lock cleanup.
- `semantic-markup-contracts` for native HTML structure, element choice, headings, landmarks, labels, tables/lists, invalid nesting, and native-before-ARIA review.
- `frontend-report-triage` as the public front door for vague or multi-domain frontend bug reports.
- `money-and-precision-contracts` for browser money/quantity arithmetic: IEEE-754 float drift, integer minor units vs decimal libraries, `toFixed`/`Math.round`/`Intl` rounding-mode surprises, line-item/tax summing order, and parsing localized amounts.
- `realtime-transport-contracts` for WebSocket/SSE client resilience: reconnect backoff+jitter, SSE `Last-Event-ID`/cursor resume, out-of-order/duplicate/gapped delta folding, heartbeat/zombie detection, `bufferedAmount` backpressure, and auth refresh on long-lived sockets.
- `optimistic-update-rollback-contracts` for optimistic UI: snapshot/rollback on failure, temp-to-server id swap, refetch reconcile, and ordering of concurrent mutations.
- `client-error-observability-contracts` for frontend error capture: `window.onerror`/`unhandledrejection`, error-boundary limits, the `Script error.` cross-origin blackout, ship-vs-upload source maps, grouping, and PII scrubbing.
- `file-ingest-contracts` for bringing files into the page: drag-drop event contract, `DataTransfer` items vs files, directory upload, `accept`/`file.type` trust vs magic bytes, paste-image, and object-URL preview lifecycle.
- `view-transitions-contracts` (review lens) for View Transitions API bugs: duplicate `view-transition-name` silent aborts, unpainted/stale snapshots (Suspense/decode), `prefers-reduced-motion` not auto-honored, React Transition-wrapping / stray `flushSync`, ghost names, and top-layer overlay stacking.
- `css-transition-animation-contracts` (review lens) for enter/exit transitions of dialogs/popovers/top-layer (`@starting-style`, `transition-behavior: allow-discrete`, `overlay`, `::backdrop`) and cleanup/focus gated on a transition that never fires (`transitionend` vs `getAnimations().finished`, `transitioncancel`, ESC/Firefox no-event).
- `responsive-image-contracts` (review lens) for `srcset`/`sizes` vs the real layout, honest intrinsic-width labels, LCP `eager`/`fetchpriority`, `picture` art-direction, and `width`/`height` for CLS (routes mechanical checks to RespImageLint / Markuplint).
- `core-web-vitals-performance-contracts` for attributing LCP, CLS, INP, and TTFB failures to concrete elements, shifts, and main-thread work before fixing.
- `frontend-data-fetching-cache-contracts` for client-cache staleness, query-key drift, request waterfalls, refetch storms, and pagination/revalidation bugs.
- `async-effect-race-contracts` for raw async effect races, missing cleanup/AbortController handling, StrictMode double-invoke traps, and stale closures.
- `pwa-offline-cache-contracts` for service-worker/offline cache update, stale-build, precache, eviction, navigation fallback, and authenticated-response caching risks.
- `large-list-data-grid-contracts` for virtualized list/data-grid scroll, accessibility totals, focus, find-in-page, pinned-column/header, and production-vs-test drift.
- `iframe-embed-contracts` for browser iframe/widget host-guest contracts: embeddability headers, sandbox/Permissions Policy, authenticated postMessage handshakes, dynamic sizing, partitioned storage, and teardown.
- `bff-proxy-security-contracts` for frontend-owned server proxies: target/path SSRF, route-method-auth capability allowlists, alternate ingress drift, multipart budgets/boundaries, redirect/error handling, and upstream-vs-gateway residual ownership.
- Repo maintainer checks in `scripts/audit-skill-pack.py`, with `lefthook.yml` delegating pre-push checks to `scripts/pre-push-checks.sh`.
- `AGENTS.md` repo contract: cite every externally verifiable claim, never cite an unopened page, run the pack checks before finishing even when only committing, keep the pack universal, and preserve each skill's PR-worthiness gate.
- Source-link checking in `audit-skill-pack.py`: `--check-links` verifies
  external URLs (`404`/`410` fail; unreachable-but-not-dead hosts are reported
  as unverified), and `--link-paths` scopes the check to specific files.
  `scripts/pre-push-checks.sh` checks the explicit CI delivery range when
  available, the upstream range locally, or the complete committed tree as a
  safe no-upstream fallback, plus staged, unstaged, and untracked Markdown.
  Local offline runs state the gap; CI forbids `SKIP_LINK_CHECK=1`, runs after a
  failed probe, and fails when every changed URL is unverified.
- Frontmatter description length check: an error above the 1024-character skill-spec cap, a warning at 950.
- GitHub Actions: `checks.yml` runs the pack checks on push/PR with Bats dependencies installed, and `link-check.yml` runs the full link sweep weekly, filing a `link-rot` issue when a citation dies.
- "Source link maintenance" procedure in `docs/skill-evidence-coverage.md` for triaging a dead citation: successor URL, commit-SHA/Web Archive pin, claim re-verification, or claim removal.

### Changed

- Live routing artifacts now bind predictions and run manifests to a dataset ID,
  canonical dataset digest, and metadata-catalog digest; stale artifacts and
  false per-case isolation declarations fail closed.
- `a11y-contract-testing` now has positive, false-positive, and
  `js-form-validation-contracts` boundary evals with observable expectations,
  reducing the legacy eval exemption set from 32 skills to 31. The audit rejects
  stale exemptions after an eval file is added.
- Repository file citations must use immutable commit links rather than mutable
  `main` or `master` paths. The WebView evidence dossier now distinguishes
  durable standards from dated engine, wrapper, and community observations.
- CI pins third-party actions to reviewed commit SHAs, disables persisted
  checkout credentials, fixes Node at 22.20.0, and asserts the invoked Node,
  Playwright, and skills CLI versions.
- The pack audit now validates optional eval `expectations` arrays as unique,
  non-empty assertions, and pre-push test discovery includes repository-level
  consumer/audit Bats suites in addition to skill-local browser fixtures.
- New, non-legacy skills now fail the audit when `evals/evals.json` is absent,
  every public skill requires `agents/openai.yaml`, and CI supplies full-history
  delivery endpoints so changed-link checks cover multi-commit pushes and PRs.
- The pack audit now requires a PR-worthiness gate, explicit weak-finding rejection, and an output shape for every domain skill; validates optional eval sets and compatibility metadata; rejects orphaned reference files; and enforces ordered README plus plugin-keyword parity.
- Existing skills now share the required quality contract, and auth routing no longer absorbs token-storage or CSRF findings owned by `frontend-security-baseline`.
- `a11y-contract-testing` now includes virtualized-widget and reduced-motion contract notes without becoming a broad audit checklist.
- `i18n-copy-and-layout` clarifies that mixed-direction user text may need `dir="auto"` rather than a standalone RTL skill.
- `component-extraction-judgment` now applies the same evidence gate to React, Vue, Svelte, Web Components, and similar component systems instead of declaring a React-only scope.
- `frontend-report-triage` now routes every public sibling skill, with a maintainer audit that fails closed when a new skill is omitted from its failure map.
- `iframe-embed-contracts` now records the closest public prior art and includes a live two-origin browser fixture for message authentication, replayable init, bounded grow/shrink sizing, teardown, and `frame-ancestors` rejection.
- README and plugin manifests now document 41 bundled skills, adding contenteditable/selection and browser-storage durability contracts alongside history/scroll restoration, pointer gesture, media-capture/device, page-lifecycle/bfcache, user-activation, and ResizeObserver/layout-cycle coverage.
- Publication wording stays evidence-framed around risks, candidates, positive controls, and local verification instead of certification or confirmed-bug claims.

### Fixed

- Corrected two legacy browser-contract claims: custom file drops require
  canceling `dragover` without relying on a universal default `dropEffect`, and
  native CSS nesting can express `&::backdrop`. Also separated WebKit
  overscroll evidence from iOS form-focus zoom guidance and removed unsupported
  universal WebView milestone claims.
- Made the iframe browser casebook honor an explicitly pinned
  `PLAYWRIGHT_CLI`, matching the other casebooks so local and CI runs load the
  browser revisions installed for that Playwright package.
- Corrected the stale English README body count, kept all four README tables and plugin discovery metadata in parity, and replaced a retired web.dev directory-drop citation with the current MDN API reference after re-verifying the claim.
- Closed audit bypasses for mixed Markdown fence delimiters and commented YAML null compatibility values, and normalized all OpenAI short descriptions to the enforced 25-64 character range.
- Corrected verified accuracy/currency errors found by an adversarial fact-check across skills: combobox `aria-selected` scope (`a11y-contract-testing`), the `tooLong`/`tooShort` dirty-value firing rule (`constraint-validation-contracts`), the Hangul composition example (`cjk-text-and-input`), `a[download]` filename sanitization vs server `Content-Disposition` (`download-export-safety`), the CSS-only scope of the animation kill-switch (`design-to-code-fidelity`), the event-stream classification and controls numbering (`frontend-security-baseline`), RHF `isValid` subscription / vee-validate defaults / Formik currency plus TanStack Form (`js-form-validation-contracts`), `autocomplete="one-time-code"` platform scope (`frontend-auth-flow-contracts`), the expansion-table row and Arabic `Intl.NumberFormat` digits (`i18n-copy-and-layout`), the removed "document outline" framing and softened SEO claim (`semantic-markup-contracts`), and a stale MDN link / library version (`overlay-focus-scroll-contracts`, `webview-bridge-pages`).
- Unified auxiliary section names across skills (`PR-worthiness gate`, `Boundary with sibling skills`, `Output shape`, `Defect patterns`) and filled missing gate, quick-probe, and sources sections.
- Added `## Sources` to the webview reference files so the "sources in each reference file" contract holds, and linked a previously orphaned reference.
- Normalized smart quotes to straight quotes across `SKILL.md` and reference files.
- Fixed `scripts/pre-push-checks.sh` to invoke `audit-skill-pack.py` without the unsupported `--format` flag.
- Corrected further errors found by a full-pack audit and an external cross-review: the removed Lighthouse PWA category and the Workbox precache-atomicity framing (`pwa-offline-cache-contracts`), `Animation.finished` rejecting on cancel (`css-transition-animation-contracts`), a `pan` probe matching `span`/`expand` (`payment-page-client-security`), a duplicated host-allowlist CSP trap row (`frontend-security-baseline`), an unreachable references file (`file-ingest-contracts`), an "always regresses LCP" overclaim (`responsive-image-contracts`), the INP long-task phase claim and `scheduler.yield` feature detection (`core-web-vitals-performance-contracts`), missing CSRF/origin evidence in the release gate (`bff-proxy-security-contracts`), the missing-cleanup-versus-late-setState distinction (`async-effect-race-contracts`), one-time-code framed as Safari-only (`frontend-auth-flow-contracts`), and a compressed clause implying presentation is never reusable (`component-extraction-judgment`).
- Repaired two rotted citations found by the first full link sweep: the moved react-spectrum `runAfterTransition.ts` (now commit-pinned) and the retired Vue Router typedoc page.
- Replaced pinned version matrices with time-safe phrasing where they rot (React `<ViewTransition>` channel, Temporal support), labelled Sentry-specific options as such, and generalized incident-shaped wording in `bff-proxy-security-contracts`.
- Trimmed the three longest frontmatter descriptions under the spec cap and compressed generic sections in six skills while leaving their gates intact.

## [0.1.0] - 2026-06-25

### Added

- Initial public release of `frontend-niche-skills`.
- 14 focused frontend skills:
  - `webview-bridge-pages`
  - `a11y-contract-testing`
  - `cjk-text-and-input`
  - `deeplink-hydration`
  - `i18n-copy-and-layout`
  - `frontend-security-baseline`
  - `frontend-auth-flow-contracts`
  - `payment-page-client-security`
  - `datetime-correctness`
  - `ssr-hydration-mismatch`
  - `constraint-validation-contracts`
  - `js-form-validation-contracts`
  - `design-to-code-fidelity`
  - `component-extraction-judgment`
