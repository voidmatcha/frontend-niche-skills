# Diff interpretation, dynamic fidelity, and escalation

How to read `visual-diff.sh` output, validate dynamic/transition behavior, and
drill from the cheapest summary to a reviewer pass. Use after a diff runs or
when a single screenshot is not enough to validate the design.

## Diff interpretation

For cross-renderer comparisons, raw AE is noisy because of font hinting, antialiasing, gradient rasterization, vector/raster asset differences, remote assets, and native/browser chrome. Use structural gating:

```bash
AE_FUZZ=10% STRUCT_GATE=1 bash scripts/visual-diff.sh tmp/ref/case.png tmp/impl/case.png tmp/diff/case.png
```

- `STATUS=PASS` at raw AE threshold is mostly useful for identical-source baselines, not proof of design completeness.
- For design-vs-render, treat `STRUCT=ALIGNED|DRIFT` as a screening signal; inspect ref/render/diff artifacts, thresholds, and known blind spots before making a claim.
- Size mismatch invalidates the diff unless resizing/cropping is the intentional test. Fix viewport/framing first.
- Tall pages can turn a small vertical offset into wall-to-wall AE. Align/crop by documented regions before trusting whole-page metrics.
- Big contiguous blocks, or blocks large relative to a small component/icon, are drift candidates: they may indicate missing section, wrong inset, misplaced fixed bar, unsupported variant, collapsed spacing, or a capture/setup problem.
- Thin text/icon/1px border residuals may be suppressed by fuzz/erosion and can pass unnoticed. Verify thin strokes/dividers quantitatively when they matter.
- Masks and exclusions are part of the test definition. Because the bundled script has no mask parameter, masked comparisons require explicit preprocessing plus recorded mask artifacts. An undocumented mask downgrades the result to T2.

## Dynamic fidelity and invalid-evidence checks

Static screenshot parity is necessary but not enough when the design depends on media,
motion, stateful chrome, or generated visuals. Add explicit matrix rows for every
dynamic family present in the reference:

- **Runtime media:** video, Lottie/bodymovin, canvas, WebGL, animated image, and
  remote image inventory must mount, render, and play/load in the target runtime.
  Package names, import strings, or `data-*` attributes are hints, not proof.
- **Transition fidelity:** hover, pressed, focus, dropdown, reveal, sticky/pinned,
  parallax, scroll-scrubbed, and page-load transitions need trigger plus sampled
  frame evidence (capture with `ALLOW_ANIMATION=1`). A single final-state screenshot cannot validate the transition.
- **State-machine fidelity:** scroll/header/theme/body/root classes and open/closed
  UI states must show `initial -> active/open -> settled/closed` behavior when the
  reference has toggles, velocity, timers, or scroll progress. Hardcoding an active
  class into the first render is a mismatch.

Reject evidence or downgrade it to T2/T3 when it can pass pixels while hiding the
real behavior:

- screenshot or exported reference pasted as an implementation background;
- stale local server/browser session, stale screenshots, or artifacts older than
  the current implementation build;
- reference CSS/JS copied wholesale when the task is to implement with the target
  design system;
- hidden duplicate DOM, forced final-state CSS (`opacity:1`, `transform:none`,
  `transition:none`), or disabled animations that remove required behavior;
- diff run against the wrong route/story, viewport, state, locale, theme, fixture,
  or device chrome policy.

## Diagnostic escalation ladder (L1-L5)

Read the cheapest summary first, then drill only where it fails:

1. **L1 summary:** artifact manifest, dimensions, AE/ratio/struct status, missing
   rows, stale-artifact timestamps.
2. **L2 structural checks:** DOM/accessibility tree, computed styles, layout boxes,
   image/font/media inventory, token mapping.
3. **L3 targeted diagnosis:** one failing section/state with ref/render/diff images,
   selector-level computed-style diff, layout-tree diff, hover/focus/transition
   samples, or scroll/keyframe samples.
4. **L4 sweep:** all viewports/states/locales/themes and all transition families
   only after the targeted failure mode is understood.
5. **L5 reviewer pass:** final semantic review of intentional differences, design
   authority, and remaining blind spots.

Before handing work to another agent, pass a compact evidence pack: comparison
matrix, artifact manifest, current verdict, failing rows, exact commands, and the
next minimal diagnostic. Do not make the receiver rediscover raw screenshots first.

## Iteration loop guard

When the task is to improve generated or hand-written UI, take a baseline before editing. Run the
same capture/diff after each patch. If the visual score or structural diff regresses and the change is
not an intentional design correction, revert or split that patch before continuing. Keep the loop
bounded by explicit stop criteria: target tier reached, score/metric plateau, blocked adapter/access,
or remaining diffs documented as intentional.
