---
name: resize-observer-layout-contracts
description: "Use when ResizeObserver-driven UI flickers, grows forever, throws 'ResizeObserver loop completed with undelivered notifications', measures the wrong box, keeps observing replaced/unmounted elements, or a callback writes size-affecting styles that trigger itself. Ordinary component/container measurement scope; use iframe-embed-contracts for parent-guest sizing protocols, large-list-data-grid-contracts for virtualization measurement, core-web-vitals-performance-contracts for page-wide layout-shift attribution, and responsive-image-contracts for image intrinsic sizing."
---

# ResizeObserver layout contracts

`ResizeObserver` notifications run as part of rendering before paint. A callback
that changes the size it observes can create a cyclic layout dependency: the
browser may defer notifications and report an error, but that safeguard does
not fix the loop or the visible multi-frame layout.

## Checklist

1. Identify the observed element, requested box, values read from each entry,
   and every style/state write caused by the callback.
2. Draw the dependency: observed size -> callback -> DOM/style/state write ->
   layout -> observed size. A cycle exists only when the write can change the
   measured size or an ancestor/descendant dependency that feeds it.
3. Prefer CSS/container-query layout when JavaScript does not need the
   measurement. When JS owns the response, ignore unchanged expected sizes and
   keep the write monotonic or otherwise convergent.
4. If the intended update must happen after paint, schedule the write with
   `requestAnimationFrame`; do not use that as a blanket error suppressor.
   Verify stable geometry and the absence of repeated loop errors.
5. Use the box that matches the contract (`content-box`, `border-box`, or
   device-pixel content where appropriate) and handle the entry shape supported
   by the target browsers without mixing CSS pixels and device pixels.
6. Call `unobserve()` when one target leaves ownership or `disconnect()` when
   the observer is disposed. Make setup/cleanup idempotent under framework
   remounts and target replacement.
7. Test initial mount, content growth and shrink, container resize, hidden/show
   transitions when relevant, target replacement, and teardown. Capture final
   geometry and `window` error events.

## Quick probes

- Log the observed size and the exact size-affecting write for several frames;
  a repeating sequence reveals whether it converges.
- Temporarily remove callback writes. If the loop error disappears, restore
  writes one at a time to find the dependency.
- Count active observers/targets before and after remount or route change.
- Assert no `ResizeObserver loop completed with undelivered notifications`
  error during the focused reproduction; do not silence all `window.onerror`.

## Boundary with sibling skills

- `iframe-embed-contracts` owns guest-to-parent height messages and resize-loop
  protocols across documents.
- `large-list-data-grid-contracts` owns virtual-row measurement and scroll
  anchoring/windowing behavior.
- `core-web-vitals-performance-contracts` owns page-wide CLS attribution.
- `responsive-image-contracts` owns intrinsic image dimensions and candidate
  selection.

## PR-worthiness gate

Demonstrate a callback-induced size cycle, wrong-box calculation, stale target,
or cleanup leak. Record the resize/content/remount sequence, repeated error or
wrong geometry, and the stable expected result. Add the smallest test that
captures geometry plus observer errors or target counts.

Reject weak findings: the mere presence of `ResizeObserver`, a single benign
notification, a one-off error with no reproducible cycle or effect, a library
that already guards expected size and cleanup, or an iframe/virtualization bug
whose actual contract belongs to a sibling skill.

## Output shape

Start with a disposition: confirmed, candidate/needs evidence, reject, or route.
Report the observed element and box, read/write dependency, reproduction and
error/geometry evidence, lifecycle ownership, smallest convergent or cleanup
change when one is warranted, sibling-skill boundary, and the resize/remount
regression that confirms the result. For rejected findings, say that no code
change is warranted instead of inventing remediation.

## Sources

- MDN, `ResizeObserver`, including observation errors and mitigation patterns: <https://developer.mozilla.org/en-US/docs/Web/API/ResizeObserver>
- CSSWG Resize Observer specification: <https://drafts.csswg.org/resize-observer/>
- Public prior-art issue with a focused browser/framework/theme reproduction of an undelivered-notifications error: <https://github.com/fullcalendar/fullcalendar/issues/8090>
