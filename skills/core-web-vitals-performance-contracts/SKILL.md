---
name: core-web-vitals-performance-contracts
description: "Use when field or lab Core Web Vitals regress and the cause must be attributed: LCP is discovered late or blocked, CLS comes from unreserved media/fonts/injected UI/layout animation, INP is delayed by long tasks or heavy handlers, or slow TTFB gates the page. Covers whole-page LCP/CLS/INP/TTFB evidence and budgets. Use responsive-image-contracts for srcset/sizes/fetchpriority mechanics, ssr-hydration-mismatch for SSR streaming correctness, css-transition-animation-contracts for animation jank, and client-error-observability-contracts for RUM wiring."
---

# Core web vitals performance contracts

Core Web Vitals are three field metrics — LCP (loading), CLS (visual stability), INP (responsiveness, "good" at 2.5 s / 0.1 / 200 ms) — plus TTFB as an upstream diagnostic. This is a review lens for attributing a failing vital to a specific element, shift, or task and prescribing the narrowest fix; it is not a metrics tutorial (web.dev owns that).

## Checklist (lead with the trap)

1. **Name the real LCP element before you optimize anything.** LCP is whatever the largest in-viewport paint is on that load — often an `<img>`, but it can be a text block, a `<video>` poster, or a CSS `background-image`. Read it from a trace / `PerformanceObserver` / DevTools, not from "the hero looks big." A preload or `fetchpriority="high"` aimed at the wrong element wastes bandwidth and can demote the true LCP resource.
2. **The LCP resource must be discoverable early and never lazy.** It belongs in the initial HTML `src`/`srcset` so the preload scanner finds it; late-discovered ones (CSS `background-image`, script-loaded) need `<link rel="preload">` — and preloaded images still default to low priority, so pair with `fetchpriority="high"`. `loading="lazy"` on the LCP element is always a bug.
3. **Unblock the critical path and TTFB before micro-tuning.** Render-blocking CSS/synchronous `<script>` in `<head>` and a slow TTFB (aim under 800 ms) can make good LCP unreachable regardless of image work — check them and non-streaming SSR before blaming the asset.
4. **Attribute every layout shift to a source — don't just quote the CLS number.** Each shift traces to something concrete — an unreserved media/iframe/embed/ad box, a web-font swap with mismatched fallback metrics (FOUT reflow), a consent banner or toast injected above existing content, or an animation of layout properties. Fix the source, not the aggregate.
5. **Reserve space and animate on the compositor.** Give media and late/async content an explicit box (`width`/`height` or `aspect-ratio`), tame font swap with `font-display: optional` for body text or a metric-matched fallback via `size-adjust`, and animate `transform`/`opacity` — never layout properties.
6. **INP: break up long tasks and shrink handler work.** INP (over 200 ms is poor; it replaced FID) has three phases — input delay, processing, presentation. A long task (>50 ms) overlapping the interaction inflates whichever phase it lands on. Do the minimum in `click`/`keydown`/`pointerdown` handlers, defer non-urgent work, and yield with `scheduler.yield()`/`scheduler.postTask()` so the browser can paint feedback first — feature-detect each method (`globalThis.scheduler?.yield`, `?.postTask`): Safari does not ship the Scheduler API, so keep a `setTimeout(0)`/`requestIdleCallback` chunking fallback. Watch `setInterval` and third-party timers that steal the main thread.
7. **INP: budget hydration and render bursts.** A large hydration pass or one big render/state update is a long task that inflates input delay exactly when users first interact (the main thread is busiest at startup). Attribute it with Long Animation Frames (`blockingDuration`) rather than guessing which script is at fault.

## Quick probes

`rg` only surfaces candidates — attribution needs a trace: Lighthouse / PageSpeed Insights (lab + CrUX field), the DevTools Performance panel (LCP marker + Layout Shifts track), and the `web-vitals` library with Long Animation Frames in the field.

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

- This skill: whole-page LCP/CLS/INP/TTFB budgeting — which element is LCP, whether it is discoverable + prioritized + unblocked, per-shift CLS attribution, main-thread/long-task/INP work.
- **responsive-image-contracts** — `srcset`/`sizes`/`fetchpriority`/`<picture>` mechanics; it owns image-load priority for the LCP `<img>`, this skill owns whether that image is even the LCP element and the whole-page budget.
- **ssr-hydration-mismatch** — hydration correctness and SSR streaming mechanics; this skill owns hydration *cost* as an INP/long-task source, that skill owns the mismatch itself.
- **css-transition-animation-contracts** — animation lifecycle and jank mechanics; this skill flags layout-property animation only as a CLS/INP source.
- **client-error-observability-contracts** — RUM/field capture wiring (`web-vitals`, error payloads); this skill consumes field data, that skill owns the capture contract.

## PR-worthiness gate

Count a Core Web Vitals finding only when all hold:

1. There is evidence the metric is actually failing — field/CrUX data or a lab trace — not a hunch that code "looks slow."
2. The finding is attributed to a specific element, shift, or task, not to the aggregate score.
3. The fix is narrow: one preload/`fetchpriority`/de-lazy on the true LCP element, one reserved-box/`aspect-ratio`/`font-display`, or one handler split/yield.

Reject weak findings:

- A hero image with `fetchpriority="high"` and no lazy attribute is a positive control, not a defect.
- `loading="lazy"` on below-the-fold images is correct and expected.
- A CLS number with no attributable source is not yet a finding — get the trace first.
- INP micro-tuning with no field signal is speculative; measure before prescribing.

## Output shape

- **Vital**: LCP | CLS | INP | TTFB.
- **Attribution**: the actual LCP element / shifting element / blocking task, with file/line plus trace evidence.
- **Symptom**: late-discovered or lazy LCP, render-blocking or slow TTFB, unreserved box, FOUT reflow, injected banner, long task/heavy handler, hydration burst.
- **Fix**: smallest change — preload + `fetchpriority`, de-lazy, `aspect-ratio`, `font-display`, reserve a box, split/yield the task.
- **Verification**: re-measure (Lighthouse, DevTools trace, or field `web-vitals`) and confirm the target metric moved.

## Sources

- LCP metric and Optimize LCP (preload scanner, never lazy-load the LCP image) — <https://web.dev/articles/lcp> , <https://web.dev/articles/optimize-lcp>
- Fetch Priority API (preload keeps low priority without it) — <https://web.dev/articles/fetch-priority>
- CLS metric and Optimize CLS (reserve space, late-injected content) — <https://web.dev/articles/cls> , <https://web.dev/articles/optimize-cls>
- Best practices for fonts (`font-display: optional`, `size-adjust`) — <https://web.dev/articles/font-best-practices>
- INP metric (200 ms threshold, replaced FID, three phases) — <https://web.dev/articles/inp>
- Optimize INP, long tasks, and input delay (yield, third-party timers) — <https://web.dev/articles/optimize-inp> , <https://web.dev/articles/optimize-long-tasks> , <https://web.dev/articles/optimize-input-delay>
- TTFB and Optimize TTFB (under 800 ms, streaming SSR) — <https://web.dev/articles/ttfb> , <https://web.dev/articles/optimize-ttfb>
- Find slow interactions in the field (Long Animation Frames, `blockingDuration`) — <https://web.dev/articles/find-slow-interactions-in-the-field>
- MDN — Scheduler: `yield()` method (feature detection) — <https://developer.mozilla.org/en-US/docs/Web/API/Scheduler/yield>
