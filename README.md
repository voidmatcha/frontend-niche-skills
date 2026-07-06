<div align="center">
<img src="docs/assets/hero.png" alt="frontend-niche-skills — frontend edge-case agent skills for WebView, IME, semantic markup, hydration, forms, dates, auth, payment pages, a11y, and design drift." width="100%" />
</div>

# Frontend Niche Skills

[![Agent Skills](https://img.shields.io/badge/Agent_Skills-31-1FC07C?style=flat-square&labelColor=black)](#skills)
[![Claude Code](https://img.shields.io/badge/Claude_Code-compatible-D97757?style=flat-square&labelColor=black&logo=anthropic&logoColor=white)](https://claude.com/product/claude-code)
[![Codex](https://img.shields.io/badge/Codex-compatible-412991?style=flat-square&labelColor=black&logo=openai&logoColor=white)](https://github.com/openai/codex)
[![Frontend edge cases](https://img.shields.io/badge/WebView_%7C_IME_%7C_a11y_%7C_payment-included-37B0E6?style=flat-square&labelColor=black)](#skills)
[![License](https://img.shields.io/badge/License-Apache--2.0-37B0E6?style=flat-square&labelColor=black)](./LICENSE)

**Agent Skills for frontend edge cases that broad checklists often miss — WebView pages, semantic markup, overlay lifecycle, IME/CJK input, hydration, forms, auth, payment pages, exports, dates, visual fidelity, and report triage.**

`frontend-niche-skills` gives Claude Code, Codex, and other `AGENTS.md`-compatible coding agents focused playbooks for bugs where the right fix depends on separating evidence types: layout vs paint, DOM vs accessibility tree, browser vs native WebView host, server render vs client hydration, payment-page data boundary vs runtime script surface, and export file vs spreadsheet/Blob/clipboard behavior.

These skills are not replacements for project conventions, security review, QSA/legal decisions, or real browser/device testing. They help agents ask for the right evidence before applying plausible but generic fixes.

## Contents

- [Install](#install)
- [Quick example](#quick-example)
- [Workflow](#workflow)
- [Skills](#skills)
- [Symptom map](#symptom-map)
- [Evidence](#evidence)
- [Development checks](#development-checks)
- [FAQ](#faq)
- [License](#license)

## Install

Install the [`skills` CLI](https://www.skills.sh/). Skills follow the [`SKILL.md` format](https://agentskills.io/specification).

The `voidmatcha/frontend-niche-skills` commands below assume the public repository or plugin marketplace entry is available. For a local or pre-release checkout, use the local checkout commands in this section instead.

```bash
# Claude Code + Codex via skills CLI
npx skills add voidmatcha/frontend-niche-skills --skill '*' -g -a claude-code -a codex

# Other agents supported by the installed skills CLI
npx skills add voidmatcha/frontend-niche-skills --skill '*' -g --agent '*'
```

### Claude Code plugin

```bash
/plugin marketplace add voidmatcha/frontend-niche-skills
/plugin install frontend-niche-skills@voidmatcha
```

### Codex plugin local checkout

This repo includes `.codex-plugin/plugin.json` and Claude plugin manifests. From a local checkout:

```bash
codex plugin marketplace add "$(pwd)"
codex plugin add frontend-niche-skills@frontend-niche-skills
```

Start a new Codex or Claude Code session after installing or updating so bundled skills refresh.

## Quick example

```text
You: Review this React Native WebView onboarding page. The CTA area is still
clickable after app resume, but the button label and footer text disappear.

frontend-niche-skills / webview-bridge-pages:

[Diagnosis] Separate layout, hit-test, and paint evidence
- Footer box exists and receives taps.
- Missing pieces are child text/button paint, not bridge routing.
- Reproduce in the native app WebView, not only desktop Chrome.

Likely fix direction
- Remove stale JS height measurement if flex layout can own the footer.
- If hit-test survives but children vanish, inspect compositing/layering:
  isolation boundary, child z-index, transform layer promotion, gradient fallback.

Verification
- Resume/reopen WebView, rotate if relevant, and capture screenshot/video.
- Confirm the CTA is both visible and tappable; do not accept click-only evidence.
```

Pattern value: make the agent test the right hypothesis before applying another generic patch.

## Workflow

1. **Pick the symptom skill.** Use the narrowest skill whose failure mode matches the bug.
2. **Read repo context.** Pair the skill with project routing, design tokens, i18n, tests, and browser/device support.
3. **Separate evidence types.** Layout, paint, hit-test, DOM structure, accessibility tree, network, hydration, locale behavior, runtime scripts, and exported files can disagree.
4. **Fix the cause, not the symptom.** Prefer removing fragile timing or duplicated logic over adding retries.
5. **Verify in the right host.** WebView bugs need app-WebView evidence; payment-page findings need runtime script/PAN-boundary evidence; visual fidelity needs reference/render capture; form/a11y findings need regression tests where possible.

## Skills

31 skills, grouped by the kind of frontend failure they target. If the report is messy or crosses domains, start with `frontend-report-triage`.

Practical priority:

- **Default high-value checks:** SSR/deep-link routing, form validation, datetime, auth/security, payment/export boundaries, overlays, accessibility, and semantic HTML. These catch bugs that are common or expensive after release.
- **Host/product-specific checks:** WebView, CJK/IME, i18n/RTL, and payment-page evidence are most valuable when the product actually ships those surfaces.
- **Quality/maintenance checks:** design fidelity and component extraction are useful when review pain is visual drift, AI-generated UI, or premature abstraction rather than a runtime bug.

Source model: README lists routing and evidence documents; detailed citations live in each skill's `## Sources` block or its `references/*.md` files so the README does not duplicate every upstream URL.

### Start here

| Skill | Use when |
| --- | --- |
| [`frontend-report-triage`](./skills/frontend-report-triage/SKILL.md) | Triage a vague or multi-symptom frontend bug report across the pack; return likely failure classes, evidence gaps, and the 1-3 best follow-up skills. |

### Runtime host edges

| Skill | Use when |
| --- | --- |
| [`webview-bridge-pages`](./skills/webview-bridge-pages/SKILL.md) | Building or debugging pages loaded inside native WebViews: bridge contracts, safe-area/viewport layout, lifecycle, hit-test vs paint/compositing, app-host quirks. |
| [`deeplink-hydration`](./skills/deeplink-hydration/SKILL.md) | Debugging SPA/SSR deep links that lose query params or land on the wrong state before router hydration is ready. |
| [`ssr-hydration-mismatch`](./skills/ssr-hydration-mismatch/SKILL.md) | Diagnosing hydration mismatches from locale/time/randomness/browser-only APIs, storage, auth state, responsive branches, or data races. |
| [`realtime-transport-contracts`](./skills/realtime-transport-contracts/SKILL.md) | Debugging a WebSocket/SSE client across a connection drop: reconnect backoff/jitter, SSE Last-Event-ID/cursor resume, out-of-order/duplicate/gapped deltas, heartbeat/zombie detection, bufferedAmount backpressure, and refreshing auth on an open socket. |

### Markup, accessibility, and overlays

| Skill | Use when |
| --- | --- |
| [`semantic-markup-contracts`](./skills/semantic-markup-contracts/SKILL.md) | Reviewing native HTML structure: buttons vs links, headings, landmarks, labels, tables/lists, invalid interactive nesting, native-before-ARIA fixes. |
| [`overlay-focus-scroll-contracts`](./skills/overlay-focus-scroll-contracts/SKILL.md) | Reviewing modal, drawer, sheet, popover, menu, and command-palette runtime contracts: focus trap/restore, inert/aria-hidden timing, nested stacks, scroll-lock cleanup. |
| [`a11y-contract-testing`](./skills/a11y-contract-testing/SKILL.md) | Turning accessibility semantics into regression tests: roles, names, states, focus, dialogs, menus, comboboxes, tabs. |
| [`view-transitions-contracts`](./skills/view-transitions-contracts/SKILL.md) | Reviewing a View Transitions API animation that silently aborts, freezes on a stale snapshot, ignores reduced-motion, or ghosts — the review/PR-worthiness lens, not a re-implementation guide. |
| [`css-transition-animation-contracts`](./skills/css-transition-animation-contracts/SKILL.md) | Reviewing enter/exit transitions for dialogs/popovers/top-layer (`@starting-style`, `allow-discrete`, `overlay`) and cleanup gated on a transition finishing (`transitionend` vs `getAnimations().finished`). |
| [`responsive-image-contracts`](./skills/responsive-image-contracts/SKILL.md) | Reviewing responsive image markup: `srcset`/`sizes` vs the real layout, intrinsic-width labels, LCP eager/`fetchpriority`, `picture` art-direction, and `width`/`height` for CLS. |

### Input, content, and time

| Skill | Use when |
| --- | --- |
| [`cjk-text-and-input`](./skills/cjk-text-and-input/SKILL.md) | Handling Korean, Japanese, or Chinese text/input: wrapping, IME composition, Enter handling, grapheme-safe length, validation timing. |
| [`i18n-copy-and-layout`](./skills/i18n-copy-and-layout/SKILL.md) | Reviewing localization copy/layout: pluralization, expansion, bidi/RTL, locale formatting, translation-key contracts. |
| [`datetime-correctness`](./skills/datetime-correctness/SKILL.md) | Auditing date/time code: timezone, DST, parsing, formatting, `datetime-local`, relative time, server/client clock issues. |
| [`money-and-precision-contracts`](./skills/money-and-precision-contracts/SKILL.md) | Money/quantity arithmetic: float drift (`0.1 + 0.2`), integer minor units vs decimal libraries, `toFixed`/rounding-mode surprises, summing/tax order, `Intl` currency output vs parsing localized amounts. |

### Forms, auth, security, and payment

| Skill | Use when |
| --- | --- |
| [`constraint-validation-contracts`](./skills/constraint-validation-contracts/SKILL.md) | Native HTML Constraint Validation API contracts: `setCustomValidity`, `reportValidity`, `:user-invalid`, invalid-then-valid lifecycle. |
| [`js-form-validation-contracts`](./skills/js-form-validation-contracts/SKILL.md) | React Hook Form, Formik, Final Form, vee-validate, Valibot, or custom JS form flows: stale errors, disabled submits, async/server races, server field-error mapping. |
| [`frontend-auth-flow-contracts`](./skills/frontend-auth-flow-contracts/SKILL.md) | Hardening browser-facing auth: returnTo redirects, OAuth/passkey/autocomplete contracts, token storage boundaries, CSRF edges. |
| [`frontend-security-baseline`](./skills/frontend-security-baseline/SKILL.md) | Checking frontend XSS, DOM injection, sanitizer misuse, CSP, third-party scripts, storage, and URL parsing basics. |
| [`payment-page-client-security`](./skills/payment-page-client-security/SKILL.md) | Reviewing checkout/payment page client evidence: hosted-field vs direct PAN handling, runtime script inventory, third-party script risk, CSP/SRI/header evidence, PCI DSS evidence gaps. |
| [`optimistic-update-rollback-contracts`](./skills/optimistic-update-rollback-contracts/SKILL.md) | Optimistic UI mutations: applying a change before the server confirms, temp vs server IDs, rollback on failure, reconciling with refetch/invalidation, and races between the response and a background refetch. |
| [`file-ingest-contracts`](./skills/file-ingest-contracts/SKILL.md) | Bringing files into the page via drag-drop, file input, or paste: drop-event cancel/`dropEffect`, dragenter/leave flicker, `DataTransfer` items vs files, directory upload, `accept`/`file.type` trust, and object-URL preview lifecycle. |

### Output, design, abstraction, and maintenance

| Skill | Use when |
| --- | --- |
| [`download-export-safety`](./skills/download-export-safety/SKILL.md) | Reviewing CSV/Excel exports, Blob/Object URL downloads, clipboard writes, generated filenames, export-specific data boundaries. |
| [`design-to-code-fidelity`](./skills/design-to-code-fidelity/SKILL.md) | Comparing implementation against design references with export, capture, visual diff, and evidence grading. |
| [`component-extraction-judgment`](./skills/component-extraction-judgment/SKILL.md) | Deciding whether repeated UI should become a shared component, wrapper, hook, token, or stay separate. |
| [`client-error-observability-contracts`](./skills/client-error-observability-contracts/SKILL.md) | Wiring frontend error capture: `window.onerror`/`unhandledrejection`, error-boundary limits, the `Script error.` cross-origin blackout, shipping vs uploading source maps, grouping, and PII scrubbing. |

### Performance, data, and offline

| Skill | Use when |
| --- | --- |
| [`core-web-vitals-performance-contracts`](./skills/core-web-vitals-performance-contracts/SKILL.md) | Attributing a failing Core Web Vital (LCP, CLS, INP, TTFB) to a specific element, layout shift, or main-thread task before fixing — whole-page budgeting, not just the score. |
| [`frontend-data-fetching-cache-contracts`](./skills/frontend-data-fetching-cache-contracts/SKILL.md) | Client data cache (React Query, SWR, RTK Query, Apollo) showing stale data after a mutation, request waterfalls, over/under-fetching, or pagination/revalidation cache bugs. |
| [`async-effect-race-contracts`](./skills/async-effect-race-contracts/SKILL.md) | Raw async effects misbehaving: fetch-on-deps races (stale response wins), missing cleanup/`AbortController`, StrictMode double-invoke, or stale closures in intervals/subscriptions. |
| [`pwa-offline-cache-contracts`](./skills/pwa-offline-cache-contracts/SKILL.md) | Service-worker/offline caching going wrong: stale build after deploy, `ChunkLoadError`, precache gaps, cache versioning/eviction, SW update lifecycle, or caching authed responses. |
| [`large-list-data-grid-contracts`](./skills/large-list-data-grid-contracts/SKILL.md) | A virtualized list/grid that jumps or loses scroll position, or find-in-page / screen-reader totals / focus breaking because off-screen rows are unmounted; pinned-column/header drift. |

## Symptom map

Use this after scanning the grouped skill list. Start from the failure signal, pick the most specific runtime evidence first, then hand off to sibling skills as needed.

| Failure signal | Start with | First question to ask |
| --- | --- | --- |
| Page runs inside React Native WebView, WKWebView, Android WebView, Flutter WebView, or an in-app browser; safe area, keyboard, resume, bridge, or paint differs from desktop Chrome. | `webview-bridge-pages` | Is this layout, hit-test, paint/compositing, bridge timing, or host lifecycle? |
| HTML structure itself looks suspect: div buttons, wrong links, labels/headings/lists, invalid interactive nesting. | `semantic-markup-contracts` | Can native HTML express this before ARIA, CSS, or JavaScript? |
| Modal, drawer, sheet, popover, menu, or command palette looks fine but focus, background interaction, Escape/backdrop, or scroll lock fails. | `overlay-focus-scroll-contracts` | What happens on open, nested open, close, unmount, and route change? |
| Dialog, menu, combobox, tab, or custom widget needs accessibility regression coverage. | `a11y-contract-testing` | Can a test assert role, name, state, and focus contract? |
| Korean, Japanese, or Chinese text/input behaves wrong: IME Enter, composition, grapheme length, wrapping, truncation. | `cjk-text-and-input` | Is the code mixing composition text, committed text, and displayed text? |
| Translated copy breaks layout, pluralization, bidi/RTL, number/date formatting, or translation-key contracts. | `i18n-copy-and-layout` | Is the bug copy, layout, locale behavior, or input composition? |
| Deep link, auth redirect, SPA/SSR route, or query params initialize the wrong screen. | `deeplink-hydration` | What is the URL state before router readiness, hydration, and auth bounce? |
| WebSocket or SSE client breaks across a connection drop: reconnect storm, duplicated/missing events, out-of-order deltas, a frozen UI on an OPEN-but-dead socket, buffer growth, or a token that expired after the handshake. | `realtime-transport-contracts` | Is this reconnect/backoff, resume/cursor, delta folding, liveness/heartbeat, backpressure, or socket re-auth? |
| Browser-facing auth UI has returnTo, OAuth/passkey, autocomplete, OTP, token storage, or CSRF-edge issues. | `frontend-auth-flow-contracts` | What browser contract should the auth flow preserve? |
| Raw HTML, sanitizer, CSP, opener, storage, URL parsing, or third-party script risk appears outside a payment page. | `frontend-security-baseline` | Is there a concrete browser security source-to-sink path? |
| Checkout/payment page needs client-side evidence: hosted fields, direct PAN/CVV handling, runtime scripts, CSP/SRI/header controls. | `payment-page-client-security` | What evidence shows the payment data boundary and runtime script surface? |
| CSV/Excel export, file download, Blob URL, clipboard write, generated filename, or export schema is involved. | `download-export-safety` | What leaves the browser, and how are spreadsheet cells, Object URLs, clipboard failures, and filenames handled? |
| Date shifted, timezone/DST issue, date-only input, `datetime-local` round trip, relative time, or server/client clock disagreement. | `datetime-correctness` | Is the value an instant, local date-time, date-only value, or formatted display string? |
| Money/quantity total is off by a fraction or a penny, rounding looks wrong, or a localized amount parses incorrectly. | `money-and-precision-contracts` | Is the value computed in binary floats, and which rounding mode and minor-unit representation does the math use? |
| Native Constraint Validation API is involved: `setCustomValidity`, `reportValidity`, `:user-invalid`, invalid-to-valid lifecycle. | `constraint-validation-contracts` | Does native validity clear and report at the right time? |
| React Hook Form, Formik, Final Form, vee-validate, Valibot, or custom JS validation has stale errors, disabled submits, or async/server races. | `js-form-validation-contracts` | Which library state owns error, validity, submit, and server-field mapping? |
| Hydration warning or server/client mismatch involves locale, time, randomness, browser-only APIs, storage, auth state, or responsive branches. | `ssr-hydration-mismatch` | What must be deterministic on the first client render? |
| Implementation should match Figma, screenshot, design reference, or visual spec. | `design-to-code-fidelity` | Can you export the reference, capture the render, and diff before subjective review? |
| Repeated UI might become a component, wrapper, hook, token, or should stay separate. | `component-extraction-judgment` | Is the duplication stable enough to extract without hiding product differences? |
| Optimistic UI update applied before the server confirms behaves wrong: flicker, double-apply, a failed mutation that never rolls back, or stale data after the response races a refetch. | `optimistic-update-rollback-contracts` | What is the apply -> confirm/rollback -> reconcile contract, and how are temp/server IDs and concurrent mutations ordered? |
| Files brought into the page misbehave: a drop-zone highlight flickers, a dropped file navigates the page away, a dropped folder yields nothing, a wrong-type file passes, paste-image breaks, or preview URLs leak. | `file-ingest-contracts` | Which ingest link fails: drag-event cancel, `DataTransfer` items vs files, type trust, paste, or object-URL lifecycle? |
| Frontend errors are missing from the dashboard, unreadable (minified / `Script error.`), or the app white-screens despite error boundaries. | `client-error-observability-contracts` | Is capture wired for async/rejections, are cross-origin/source-map settings correct, and what is scrubbed before send? |
| A View Transitions animation misbehaves: it randomly does not fire (silent abort), freezes on a stale/old frame, ignores reduced-motion, or leaves ghost morphs. | `view-transitions-contracts` | Duplicate `view-transition-name`, an unpainted snapshot (Suspense/decode), a missing reduced-motion block, or wrong Transition wrapping? |
| A dialog/popover enter or exit animation cuts off, or cleanup/focus/unmount is stuck because a transition never "finished". | `css-transition-animation-contracts` | Is `display`/`overlay` missing from the transition (with `allow-discrete`), or is code gated on `transitionend` that never fires? |
| The wrong image file ships, an image over-downloads, the hero is lazy-loaded, or images cause layout shift. | `responsive-image-contracts` | Does `srcset` have a `sizes` matching the real layout, correct width descriptors, LCP `eager`/`fetchpriority`, and `width`/`height`? |
| A page's LCP/CLS/INP fails and you need to attribute it, not just report the score. | `core-web-vitals-performance-contracts` | Which element is LCP (discoverable/prioritized?), what sources each layout shift, and which long tasks inflate INP? |
| Client-cached data is stale after a mutation, or requests waterfall / over-fetch (React Query/SWR/RTK Query/Apollo). | `frontend-data-fetching-cache-contracts` | Which query key should invalidate, and are reads parallelized with the right stale/gc timing? |
| An async effect shows the wrong data, fires twice, leaks, or reads a stale value. | `async-effect-race-contracts` | Is there take-latest/`AbortController` + cleanup, and is the effect idempotent under StrictMode? |
| Users get a stale build after deploy, `ChunkLoadError`, or a service worker serves wrong/stale bytes offline. | `pwa-offline-cache-contracts` | Is there an SW update flow, complete precache, cache versioning, and a do-not-cache rule for authed HTML/API? |
| A virtualized list/grid jumps or loses scroll, or Ctrl+F / screen-reader totals / focus break under virtualization. | `large-list-data-grid-contracts` | Is `estimateSize`/overscan right, and are `aria-setsize`/`aria-posinset` (or `aria-rowcount`) set for unmounted rows? |
| Report is vague, crosses multiple domains, or you are not sure which specialized skill should own it. | `frontend-report-triage` | What are the top 1-3 likely failure classes, and what evidence would distinguish them? |

## Evidence

The repo avoids treating a grep hit as a bug. The docs separate confirmed examples, candidate leads, positive controls, and known false positives.

Where evidence lives:

- [`docs/oss-validation-cases.md`](./docs/oss-validation-cases.md) — public OSS cases used to sanity-check skill boundaries and PR shapes.
- [`docs/oss-maintainer-candidate-backlog.md`](./docs/oss-maintainer-candidate-backlog.md) — public OSS research candidates with file/line evidence. Re-check the current default branch and reproduce locally before filing.
- [`docs/why-webview-bridge-pages.md`](./docs/why-webview-bridge-pages.md) — WebView-specific prior art, bridge libraries, host behavior references, and ecosystem notes.
- [`docs/skill-evidence-coverage.md`](./docs/skill-evidence-coverage.md) — per-skill map showing whether support comes from validated cases, candidate leads, primary-source references, or routing examples.
- [`docs/frontend-report-triage.md`](./docs/frontend-report-triage.md) — integrated report triage contract and examples.
- `skills/*/SKILL.md` and `skills/*/references/*.md` — per-skill official docs, prior art, examples, false-positive notes, and implementation-specific evidence.

Candidate OSS findings are **not** confirmed upstream bugs until the current branch is re-checked, reproduced locally, and accepted by a maintainer or supported by a failing test.

## Development checks

Repo-local checks can run directly or through lefthook:

```bash
./scripts/pre-push-checks.sh

# Optional: install Git hooks after installing lefthook locally.
lefthook install
lefthook run pre-push
```

`lefthook.yml` only delegates to the repo script, so contributors can run the same checks without lefthook. The script audits skill metadata, README links/counts, plugin manifests, local markdown links, overclaim wording, and bundled script syntax. It also runs `git diff --check`.

## FAQ

### Is this a generic frontend checklist?

No. These skills focus on frontend edges generic UI review often misses: WebView host behavior, native HTML structure, IME/CJK input, accessibility contracts, hydration, forms, datetime, auth, payment-page client evidence, exports, overlays, and design fidelity.

### Does `payment-page-client-security` decide PCI scope?

No. It collects frontend evidence: payment-page script inventory, PAN/CVV boundaries, CSP/SRI/header controls, and PCI DSS 6.4.3/11.6.1 discussion points. A QSA, acquirer, payment owner, or security owner decides scope and compliance.

### Should these replace project-local rules?

No. Keep project-local conventions: routing, components, design tokens, auth model, test runner, browser/device matrix, and release gates. Use these skills as issue-specific playbooks.

### Why not one huge skill?

Smaller skills keep context focused. `frontend-report-triage` exists for messy reports, but it should route to the smallest useful set rather than loading all skills.

## License

Apache-2.0 © [voidmatcha](https://github.com/voidmatcha). See [LICENSE](./LICENSE).
