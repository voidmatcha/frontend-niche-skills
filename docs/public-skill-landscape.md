# Public skill landscape

Last checked: 2026-07-31.

Use this document before adding broad frontend skills. It records public skill
packs that overlap with `frontend-niche-skills`, then explains whether they are
duplicates, complements, or sources for routing ideas.

## Methodology

- Checked opened public GitHub repositories at pinned commits and opened
  `skills.sh` pages where GitHub search was insufficient.
- Preferred `SKILL.md` files and repository trees over marketplace summaries.
- Treated broad implementation guides as complementary execution surfaces, not
  evidence that this pack should add the same broad skill.
- Did not claim an exhaustive census. GitHub code search and Exa search hit
  intermittent rate limits during the wider sweep, so this is a maintained
  snapshot of opened evidence, not the whole ecosystem.
- Marketplace-only links below record pages retrieved on 2026-07-31. They are
  mutable discovery evidence, not reproducible source snapshots; conclusions
  based only on those pages remain provisional until a pinned upstream source
  is available.

## Comparable public packs

| Pack | Opened source | What overlaps | Decision |
| --- | --- | --- | --- |
| OpenAI Build Web Apps | [`frontend-app-builder`](https://github.com/openai/plugins/blob/11c74d6ba24d3a6d48f54a194cd00ef3beea18f9/plugins/build-web-apps/skills/frontend-app-builder/SKILL.md), [`frontend-testing-debugging`](https://github.com/openai/plugins/tree/11c74d6ba24d3a6d48f54a194cd00ef3beea18f9/plugins/build-web-apps/skills/frontend-testing-debugging), [`react-best-practices`](https://github.com/openai/plugins/tree/11c74d6ba24d3a6d48f54a194cd00ef3beea18f9/plugins/build-web-apps/skills/react-best-practices) | App building, browser testing, React/Next.js practices, UI polish. | Complement. Do not copy broad app-builder behavior into this pack; route to it when the user wants a whole app or redesign. |
| Anthropic skills | [`webapp-testing`](https://github.com/anthropics/skills/blob/b29e7cf65e5cb78a5ac33d582270551bc74a14eb/skills/webapp-testing/SKILL.md), [`web-artifacts-builder`](https://github.com/anthropics/skills/tree/b29e7cf65e5cb78a5ac33d582270551bc74a14eb/skills/web-artifacts-builder) | Playwright-based local web testing and artifact creation. | Complement. Keep our skills focused on failure contracts; use this when the missing piece is browser automation. |
| Vercel skills tooling | [`vercel-labs/skills`](https://github.com/vercel-labs/skills/tree/7cb7db64dc1201052dea305e508a2fc490f7e5e2), [`find-skills`](https://github.com/vercel-labs/skills/blob/7cb7db64dc1201052dea305e508a2fc490f7e5e2/skills/find-skills/SKILL.md) | Discovery and installation, not frontend bug contracts. | Complement. Link as ecosystem/tooling context only. |
| Vercel Agent Browser | [`agent-browser`](https://github.com/vercel-labs/agent-browser/blob/215880302a6fac217fd2741210d45685b36d6b7c/skills/agent-browser/SKILL.md), [`skills.sh page`](https://www.skills.sh/vercel-labs/agent-browser/agent-browser) | Browser interaction, screenshots, form filling, exploratory QA. | Complement. Use for runtime evidence collection; do not replace symptom-specific review skills. |
| Addy Osmani web-quality-skills | [`core-web-vitals`](https://github.com/addyosmani/web-quality-skills/blob/95d6e255afe1596b557d7a8498517884438f5b3a/skills/core-web-vitals/SKILL.md), [`accessibility`](https://github.com/addyosmani/web-quality-skills/tree/95d6e255afe1596b557d7a8498517884438f5b3a/skills/accessibility), [`web-quality-audit`](https://github.com/addyosmani/web-quality-skills/tree/95d6e255afe1596b557d7a8498517884438f5b3a/skills/web-quality-audit) | Core Web Vitals, accessibility, performance, SEO, general audits. | Near match. Our CWV skill should stay attribution-first and reject score-only fixes; broad audit checklists belong outside this pack. |
| mgifford accessibility-skills | [`forms`](https://github.com/mgifford/accessibility-skills/blob/cb9af604e08e3656b96676a3c731bff7945bef46/skills/forms/SKILL.md), [`touch-pointer`](https://github.com/mgifford/accessibility-skills/blob/cb9af604e08e3656b96676a3c731bff7945bef46/skills/touch-pointer/SKILL.md), [`keyboard`](https://github.com/mgifford/accessibility-skills/tree/cb9af604e08e3656b96676a3c731bff7945bef46/skills/keyboard), [`print`](https://github.com/mgifford/accessibility-skills/tree/cb9af604e08e3656b96676a3c731bff7945bef46/skills/print) | Forms, pointer/touch, keyboard, print, navigation, tables, contrast, tooltips. | Near match. Keep our accessibility skills contract-and-regression focused; use this pack as a WCAG depth complement. |
| oakoss agent-skills | [`hydration-guardian`](https://github.com/oakoss/agent-skills/blob/0283bed313563d5677a0838f4bf921b03296cf6c/skills/hydration-guardian/SKILL.md), [`service-worker`](https://github.com/oakoss/agent-skills/blob/0283bed313563d5677a0838f4bf921b03296cf6c/skills/service-worker/SKILL.md), [`responsive-images`](https://github.com/oakoss/agent-skills/blob/0283bed313563d5677a0838f4bf921b03296cf6c/skills/responsive-images/SKILL.md), [`accessibility`](https://github.com/oakoss/agent-skills/blob/0283bed313563d5677a0838f4bf921b03296cf6c/skills/accessibility/SKILL.md), [`Astro view transitions`](https://github.com/oakoss/agent-skills/blob/0283bed313563d5677a0838f4bf921b03296cf6c/skills/astro/references/view-transitions.md) | Direct implementation overlap for hydration, service workers, responsive images, accessibility, and Astro transitions. | Mixed. Retain this pack's evidence and review boundaries; do not describe oakoss as merely adjacent. |
| agents-inc skills | [`file-upload-patterns`](https://github.com/agents-inc/skills/blob/d6f49ba161d2932d790e256e6a4a004e767bd44b/dist/plugins/web-files-file-upload-patterns/skills/web-files-file-upload-patterns/SKILL.md), [`view-transitions`](https://github.com/agents-inc/skills/blob/d6f49ba161d2932d790e256e6a4a004e767bd44b/dist/plugins/web-animation-view-transitions/skills/web-animation-view-transitions/SKILL.md), [`web-accessibility`](https://github.com/agents-inc/skills/blob/d6f49ba161d2932d790e256e6a4a004e767bd44b/dist/plugins/web-accessibility-web-accessibility/skills/web-accessibility-web-accessibility/SKILL.md), [`service-workers`](https://github.com/agents-inc/skills/blob/d6f49ba161d2932d790e256e6a4a004e767bd44b/dist/plugins/web-pwa-service-workers/skills/web-pwa-service-workers/SKILL.md) | Concrete frontend implementation skills alongside marketplace and orchestration material. | Near or direct implementation overlap, but not a pack-level replacement. |
| bfcache specialists | [`Google debug-bfcache`](https://github.com/google-marketing-solutions/web-performance-lab/blob/19e3a62c1a7d3123f4585c3821657b3ec88c6cf8/workshop/ai-infused-dev-day-demo/.agents/skills/debug-bfcache/SKILL.md), [`Coast bfcache-optimization`](https://github.com/coastdigitalgroup/coastai-skills/blob/d64945b8bb3198c7842e3ac45cf98050fec09423/website-development/bfcache-optimization/SKILL.md) | Back/Forward testing, `notRestoredReasons`, eligibility blockers, and `pageshow`/`pagehide` restoration. | Direct implementation and debugging overlap; retain the pack's user-visible resume and idempotence boundary. |
| lennondotw agent-skills | [`pointer-drag-release`](https://github.com/lennondotw/agent-skills/blob/09ed7cd81bf2855d1e7b64c74078d77ac83ec6e8/skills/web/pointer-drag-release/SKILL.md) | Missing-release recovery through `buttons === 0`, `lostpointercapture`, active-pointer guards, and cancellation semantics. | Direct narrow match; retain the broader pointer skill only for demonstrated event-delivery, `touch-action`, teardown, and cross-input contracts. |
| Sailscast Boring Stack | [`durable-ui / scroll-restoration`](https://github.com/sailscastshq/boring-stack/blob/ccc373682513dd40014c9602e372d7254af221fa/skills/durable-ui/rules/scroll-restoration.md) | Back/Forward, container, asynchronous-content, and anchor scroll restoration. | Direct implementation overlap; retain this pack's entry ownership, readiness, and no-arbitrary-delay review boundary. |
| Rich-text editor skills | [`Lit rich-text editor tutorial`](https://skills.sh/rodydavis/skills/building-a-rich-text-editor-with-lit), [`Syncfusion React Rich Text Editor`](https://skills.sh/syncfusion/react-ui-components-skills/syncfusion-react-rich-text-editor) | Component construction, toolbar formatting, and vendor-specific editor setup. | Complement. In the opened snapshot, these are implementation guides rather than browser selection, editing-transaction, undo, composition, and teardown contract reviews. |
| Offline/local-first skills | [`agents-inc web-pwa-offline-first`](https://skills.sh/agents-inc/skills/web-pwa-offline-first), [`pwa-review`](https://skills.sh/emrahub/pwa-review-skill/pwa-review) | Local-first sync queues and broad PWA/offline audits. | Complement. Keep server sync and service-worker breadth outside the narrower IndexedDB commit, cross-tab upgrade, storage-pressure evidence, and truthful-recovery contract. |
| fudesign2008 open-skills | [`hybrid-debug`](https://skills.sh/fudesign2008/open-skills/hybrid-debug) | Four-layer debugging across the web runtime, native-web bridge, native configuration, and platform runtime. | Partial WebView match. It is a cross-layer debugging methodology, not a browser-page bridge contract or host-message lifecycle replacement. |
| VueUse | [`vueuse-functions`](https://github.com/vueuse/vueuse/blob/c5a0850254d04cfc13697541d3222cfdafc2c512/skills/vueuse-functions/SKILL.md) | Browser `useUserMedia` primitive selection and usage in Vue applications. | Complement. It covers framework implementation primitives, not permission failure taxonomy, track ownership, interruption, replacement, and teardown evidence. |

## Direct and near skill matches

| Our area | Public overlap | What to do here |
| --- | --- | --- |
| Hydration and React render timing | oakoss `hydration-guardian` directly covers SSR/client mismatch diagnosis and deterministic hydration; OpenAI has broader React guidance. | Keep `ssr-hydration-mismatch` and `deeplink-hydration` narrow around server/client and cold-URL evidence; do not claim hydration has only broad public overlap. |
| Core Web Vitals | Addy Osmani has a direct `core-web-vitals` skill. | Keep our skill focused on element attribution, field/lab evidence, and rejecting score-only fixes. |
| Accessibility testing and semantics | Addy Osmani, mgifford, oakoss, and agents-inc all cover accessibility. | Keep `semantic-markup-contracts`, `overlay-focus-scroll-contracts`, and `a11y-contract-testing` separate by evidence surface: DOM, runtime focus/scroll, and regression tests. |
| PWA/service worker | oakoss `service-worker` and agents-inc `web-pwa-service-workers` are direct lifecycle, cache, and update specialists. | Keep `pwa-offline-cache-contracts` only for the stale-deploy, authenticated-cache, and evidence-gated contract distinction. |
| Form validation | mgifford has a strong accessibility form skill; OpenAI Build Web Apps includes shadcn form guidance. | Keep `constraint-validation-contracts` and `js-form-validation-contracts` split by browser validity vs JS form state/server-error races. |
| Responsive images | oakoss `responsive-images` directly covers `srcset`/`sizes`, LCP priority, dimensions/CLS, and `<picture>`. | Keep our skill only for actual-layout versus candidate-selection evidence and regression boundaries. |
| View transitions and CSS transitions | agents-inc has a direct View Transitions implementation skill; oakoss adds Astro-specific guidance. | Keep our two motion skills as failure-contract reviews, not animation implementation guides. |
| File upload and file ingest | agents-inc `file-upload-patterns` directly covers dropzones, validation, previews, progress, chunking/resume, and accessibility. | Keep `file-ingest-contracts` for browser ingest, event, directory, and object-URL contracts; treat transfer lifecycle as existing public prior art. |
| Pointer and gesture | lennondotw `pointer-drag-release` is a direct missing-release match; mgifford `touch-pointer` is the accessibility complement. | Keep `pointer-gesture-contracts` only for its broader single-pointer event-delivery, `touch-action`, teardown, and sibling-routing contract. |
| bfcache and scroll restoration | Google and Coast are direct bfcache specialists; Sailscast is a direct scroll-restoration implementation reference. | Keep the local skills for their concrete resume-idempotence, entry-ownership, and asynchronous-layout-stability boundaries. |
| Browser media capture | The targeted search found native Axiom [`camera-capture`](https://skills.sh/charleswiltgen/axiom/axiom-camera-capture) and [`camera-capture-diag`](https://skills.sh/charleswiltgen/axiom/axiom-camera-capture-diag) pages plus VueUse's pinned browser `useUserMedia` implementation guidance. | No standalone browser-lifecycle failure-contract skill was found in this targeted, non-exhaustive search. Keep `media-capture-device-contracts` bounded to permission taxonomy, track ownership, interruption, replacement, and teardown; do not claim ecosystem-wide uniqueness. |
| Contenteditable and Selection | The opened public results were a Lit construction tutorial and Syncfusion-specific editor skill, not a browser editing-host failure-contract workflow. | Keep `contenteditable-selection-contracts` bounded to live Selection/Range ownership, `beforeinput`/`input`, native-vs-model history, composition-safe DOM replacement, insertion range, focus, and teardown. Route editor-framework internals, sanitization, file ingest, accessibility, and language-specific IME elsewhere. |
| IndexedDB and storage durability | The opened public results were a local-first/PWA architecture skill and a broad PWA audit, while the `idb` library documents implementation callbacks and transaction completion. | Keep `browser-storage-durability-contracts` bounded to whether browser-local data committed and recovery claims remain truthful across transaction completion, cross-context schema change, storage pressure, and absence. Route service-worker caches, client query caches, security policy, and sync/backup architecture elsewhere. |
| User activation and gesture-gated APIs | OpenAI Build Web Apps [`frontend-testing-debugging`](https://github.com/openai/plugins/blob/11c74d6ba24d3a6d48f54a194cd00ef3beea18f9/plugins/build-web-apps/skills/frontend-testing-debugging/SKILL.md) validates rendered interactions with browser/runtime evidence, but does not classify transient versus sticky activation, activation consumption, or permission and insecure-context false positives. | Complement. Keep `user-activation-contracts` for trusted-gesture-to-gated-call ordering, real API denial or null results, and truthful fallback testing; use the public skill for the broader browser-validation loop. |
| ResizeObserver layout cycles and measurement | [`react-virtuoso`](https://github.com/petyosi/react-virtuoso/blob/b7feb0c2415044a99c75c7c8d03f5f7c14342038/skills/react-virtuoso/SKILL.md) uses ResizeObserver for virtual-list measurement and mentions the same undelivered-notifications warning; [`responsiveness-check`](https://github.com/jezweb/claude-skills/blob/e875a6bfff809e5d42c584104031e36e1f014f18/plugins/dev-tools/skills/responsiveness-check/SKILL.md) detects viewport reflow through screenshots. | Partial overlap and complements. Route virtual-list measurement and scroll symptoms to `large-list-data-grid-contracts`; retain `resize-observer-layout-contracts` for general callback read/write cycles, box selection, stale-target cleanup, and geometry-plus-error evidence. Viewport screenshots alone do not prove an observer lifecycle defect. |
| WebView | fudesign2008 `hybrid-debug` directly addresses cross-layer WebView diagnosis, but not the page-side bridge contract itself. | Keep `webview-bridge-pages` for message validation, host readiness, navigation ownership, and teardown; use the public skill as a native/web/platform diagnostic complement. |

## Differentiator for this pack

In the surveyed set, most sources are broad implementation guides, audit checklists, or
browser automation helpers; the direct matches above are implementation or
debugging guides rather than pack-level replacements. This pack should stay
narrower:

1. Start from the user-visible symptom.
2. Identify the exact evidence surface: DOM, accessibility tree, network,
   lifecycle event, browser metric, host bridge, file bytes, or runtime state.
3. Reject weak findings before recommending a fix.
4. Route to sibling skills when a keyword overlaps but the evidence model does
   not.
5. End with the smallest reproduction or regression shape that can support the
   contract.

That shape is why a public near match should not automatically block one of our
skills. A near match blocks us only when it already owns the same trigger,
evidence type, success criterion, and false-positive boundary.

## Adoption rules

- Do not import whole packs. They carry broad product, framework, or tool
  assumptions that would blur this pack's edge-case routing.
- Treat broad app-builder, React, accessibility, and web-quality skills as
  complementary execution surfaces.
- Add a new skill only when it passes `docs/skill-quality-standard.md`: recurring
  failure, cross-framework or real host surface, general-agent difficulty,
  distinct sibling boundary, testability, and weak-finding rejection.
- Prefer improving sibling routing over adding a skill when a public pack already
  covers the same failure model.
- If a public skill has a stronger workflow for evidence collection, cite it as
  a complementary tool and keep our `SKILL.md` focused on the frontend contract.

## Open follow-ups

- Re-run a wider marketplace search when GitHub code search and Exa are not rate
  limited.
- Recheck browser-permission skills before admitting a generic permissions
  candidate; the current API-specific activation, iframe-policy, and media
  boundaries remain safer.
- Research a plain mobile-browser/PWA viewport-and-keyboard candidate separately
  from `webview-bridge-pages`. Admit it only after a reproducible mobile-browser
  case and boundary evals against WebView, overlay/focus, and design-fidelity
  ownership; the current issue reports are leads, not enough runtime evidence
  for a new public skill.
- Keep cross-tab state coordination as research-only until independent recurring
  examples and a two-context regression distinguish it from bfcache restoration,
  IndexedDB durability, authentication revalidation, and server sync policy.
- Periodically repeat the IndexedDB and contenteditable searches. The opened
  snapshot found broad implementation/PWA complements, not a direct replacement
  for the newly admitted failure-contract skills.
- If a new public pack becomes a direct match, add it here before changing the
  README or manifests.
