---
name: core-web-vitals-performance-contracts
description: "Use when a page's Core Web Vitals fail in the field or lab and you need to attribute the cause, not just report a score: LCP over 2.5 s because the largest element (hero image, H1 text block, video poster, CSS background) is discovered late, left loading=lazy, low-priority, or stuck behind render-blocking CSS/JS or a slow TTFB; CLS above 0.1 from images/iframes/embeds/ads with no reserved box, web-font swap (FOUT) reflow, a late-injected banner or cookie bar pushing content down, or animating top/left/width/height; INP over 200 ms (the metric that replaced FID) from long tasks blocking the main thread, heavy click/input handlers, a big hydration or render burst, or input delay while the main thread is busy; a slow non-streaming TTFB gating everything downstream. Whole-page LCP/CLS/INP/TTFB budgeting scope: for the srcset/sizes/fetchpriority mechanics of the LCP image itself see responsive-image-contracts, for hydration correctness and SSR streaming see ssr-hydration-mismatch, for compositor-only vs layout-animating jank see css-transition-animation-contracts, for RUM/field-data capture wiring see client-error-observability-contracts."
---

# Core web vitals performance contracts

Core Web Vitals are three field metrics — LCP (loading), CLS (visual stability), INP (responsiveness, "good" at 2.5 s / 0.1 / 200 ms) — plus TTFB as an upstream diagnostic. This is a review lens for attributing a failing vital to a specific element, shift, or task and prescribing the narrowest fix; it is not a metrics tutorial (web.dev owns that).

## Checklist (lead with the trap)

1. **Name the real LCP element before you optimize anything.** LCP is whatever the largest in-viewport paint is on that load — often an `<img>`, but it can be a text block, a `<video>` poster, or a CSS `background-image`. Read it from a trace / `PerformanceObserver` / DevTools, not from "the hero looks big." A preload or `fetchpriority="high"` aimed at the wrong element wastes bandwidth and can demote the true LCP resource.
2. **The LCP resource must be discoverable early and never lazy.** It should sit in the initial HTML `src`/`srcset` (not `data-src` or JS-injected) so the preload scanner finds it; late-discovered ones (CSS `background-image`, `@font-face`, script-loaded) need `<link rel="preload">`. Preloaded images still default to low priority, so pair preload with `fetchpriority="high"`. `loading="lazy"` on the LCP element is always a bug — it defers the load until layout confirms visibility.
3. **Unblock the critical path and TTFB before micro-tuning.** Parser-blocking CSS or synchronous `<script>` in `<head>` blocks all content from rendering; a slow TTFB (aim under 800 ms) can make good LCP unreachable regardless of image work. Check render-blocking `<link rel="stylesheet">`/`<script>` and non-streaming SSR before blaming the asset.
4. **Attribute every layout shift to a source — don't just quote the CLS number.** Each shift traces to something concrete: media/iframe/embed/ad with no `width`+`height` or `aspect-ratio` reserving its box; a web-font swap where fallback and web font have different metrics (FOUT reflow); a banner, cookie bar, or toast injected above existing content; or an animation of layout properties. Fix the source, not the aggregate.
5. **Reserve space and animate on the compositor.** Give media explicit `width`/`height` or `aspect-ratio`; reserve a box for late/async content (ads, embeds, notices) instead of letting it push content down. Reduce font-swap shift with `font-display: optional` for body text or a metric-matched fallback via `size-adjust`. Animate `transform`/`opacity`, not `top`/`left`/`width`/`height`.
6. **INP: break up long tasks and shrink handler work.** INP (over 200 ms is poor; it replaced FID) has three phases — input delay, processing, presentation. Any task over 50 ms on the main thread blocks all three. Do the minimum in `click`/`keydown`/`pointerdown` handlers, defer non-urgent work, and yield with `scheduler.yield()`/`scheduler.postTask()` so the browser can paint feedback first. Watch `setInterval` and third-party timers that steal the main thread.
7. **INP: budget hydration and render bursts.** A large hydration pass or one big render/state update is a long task that inflates input delay exactly when users first interact (the main thread is busiest at startup). Attribute it with Long Animation Frames (`blockingDuration`) rather than guessing which script is at fault.

## Quick probes

`rg` only surfaces candidates; the actual attribution needs a trace. Route mechanical measurement to Lighthouse / PageSpeed Insights (lab + CrUX field data), the DevTools Performance panel (LCP marker + Layout Shifts track), and the `web-vitals` library with Long Animation Frames for field attribution.

```sh
rg -n 'loading=.?lazy|data-src|data-srcset|lazyload' src/ app/ public/ 2>/dev/null   # LCP image deferred / JS-loaded?
rg -n 'fetchpriority|rel=.?preload' src/ app/ 2>/dev/null                             # is the LCP resource prioritized at all?
rg -n '<img|<iframe|<video' src/ app/ 2>/dev/null | rg -v 'width|height|aspect-ratio' # media with no reserved box -> CLS
rg -n 'font-display|size-adjust|@font-face' src/ app/ 2>/dev/null                     # FOUT reflow risk on swap
rg -n 'transition:|animation:|animate\(' src/ app/ 2>/dev/null | rg 'top|left|right|bottom|width|height|margin' # layout-animating -> CLS/jank
rg -n 'addEventListener\(.?.?(click|input|keydown|pointerdown)|onClick=|onInput=' src/ app/ 2>/dev/null # heavy interaction handlers -> INP
rg -n 'setInterval\(|scheduler\.yield|scheduler\.postTask|requestIdleCallback' src/ app/ 2>/dev/null    # long-task / yielding signals
```

## Boundary with sibling skills

- This skill: whole-page LCP/CLS/INP/TTFB budgeting — which element is LCP, whether it is discoverable + prioritized + unblocked, per-shift CLS attribution, and main-thread/long-task/INP work.
- **responsive-image-contracts** — the `srcset`/`sizes`/`fetchpriority`/`<picture>` mechanics and honest intrinsic-width labels of an image; it owns image-load priority for the LCP `<img>`, this skill owns whether that image is even the LCP element and the whole-page budget.
- **ssr-hydration-mismatch** — hydration correctness/determinism and SSR streaming mechanics; this skill owns hydration *cost* as an INP/long-task source, that skill owns the mismatch itself.
- **css-transition-animation-contracts** — enter/exit transition lifecycle and compositor-only vs layout-animating jank; cite it for animation mechanics, this skill flags layout-property animation only as a CLS/INP source.
- **client-error-observability-contracts** — wiring RUM/field capture (`web-vitals`, error payloads); this skill consumes field data, that skill owns the capture contract.

## PR-worthiness gate

Count a Core Web Vitals finding only when all hold:

1. There is evidence the metric is actually failing — field/CrUX data or a lab trace — not a hunch that code "looks slow."
2. The finding is attributed to a specific element, shift, or task, not to the aggregate score.
3. The fix is narrow: one preload/`fetchpriority`/de-lazy on the true LCP element, one reserved-box/`aspect-ratio`/`font-display`, or one handler split/yield.

Do not over-file:

- A hero image with `fetchpriority="high"` and no lazy attribute is a positive control, not a defect.
- `loading="lazy"` on below-the-fold images is correct and expected.
- A CLS number with no attributable source is not yet a finding — get the trace first.
- INP micro-tuning with no field signal is speculative; measure before prescribing.

## Output shape

- **Vital**: LCP | CLS | INP | TTFB.
- **Attribution**: the actual LCP element / the shifting element / the blocking task, with file/line plus trace evidence.
- **Symptom**: late-discovered or lazy LCP, render-blocking or slow TTFB, unreserved box, FOUT reflow, injected banner, long task/heavy handler, hydration burst.
- **Fix**: smallest change — preload + `fetchpriority`, de-lazy, `aspect-ratio`, `font-display`, reserve a box, split/yield the task.
- **Verification**: re-measure in Lighthouse or a DevTools trace, or in field `web-vitals`, and confirm the target metric moved.

## Sources

- LCP metric and 2.5 s "good" threshold — <https://web.dev/articles/lcp>
- Optimize LCP (preload scanner, never lazy-load the LCP image, load phases, render-blocking) — <https://web.dev/articles/optimize-lcp>
- Fetch Priority API (`fetchpriority="high"` on the LCP image; preload keeps low priority) — <https://web.dev/articles/fetch-priority>
- CLS metric and 0.1 threshold — <https://web.dev/articles/cls>
- Optimize CLS (reserve space, size media, late-injected content) — <https://web.dev/articles/optimize-cls>
- Best practices for fonts (`font-display: optional`, `size-adjust`, FOUT/FOIT reflow) — <https://web.dev/articles/font-best-practices>
- INP metric (over 200 ms is poor, replaced FID, input/processing/presentation phases) — <https://web.dev/articles/inp>
- Optimize INP (long tasks, event callbacks, large rendering updates) — <https://web.dev/articles/optimize-inp>
- Optimize long tasks (break up work, yield to the main thread) — <https://web.dev/articles/optimize-long-tasks>
- Optimize input delay (main-thread work, `setTimeout`/`setInterval`, third-party timers) — <https://web.dev/articles/optimize-input-delay>
- TTFB (aim under 800 ms; HTML streams as it arrives) and Optimize TTFB (streaming SSR, CDN, caching) — <https://web.dev/articles/ttfb> , <https://web.dev/articles/optimize-ttfb>
- Find slow interactions in the field (Long Animation Frames, `blockingDuration`, forced layout) — <https://web.dev/articles/find-slow-interactions-in-the-field>
- MDN — Scheduler: `yield()` method (break up long tasks, feature detection) — <https://developer.mozilla.org/en-US/docs/Web/API/Scheduler/yield>
- MDN — Largest Contentful Paint glossary — <https://developer.mozilla.org/en-US/docs/Glossary/Largest_contentful_paint>
- MDN — Cumulative Layout Shift glossary (web-font swap is a common cause) — <https://developer.mozilla.org/en-US/docs/Glossary/CLS>
