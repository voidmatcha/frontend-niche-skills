---
name: large-list-data-grid-contracts
description: "Use when a virtualized list or data grid breaks at windowing seams: variable-height measurement makes scroll jump, overscan blanks rows or harms INP/memory, tests disable virtualization and miss production failures, find-in-page or accessibility counts assume every row is mounted, focus disappears when a row unmounts, or sticky/pinned regions drift from the body. Covers virtualization/windowing contracts. Route row-count semantics to a11y-contract-testing, focus restoration to overlay-focus-scroll-contracts, row images to responsive-image-contracts, and paginated/infinite data reads to frontend-data-fetching-cache-contracts."
---

# Large list data grid contracts

A virtualized list or grid keeps only a window of rows mounted, so three things form a contract: the **total scroll size** derived from a per-row size estimate, the **overscan** buffer that mounts rows just outside the viewport, and the **set of features that assume every row is in the DOM** (find-in-page, screen-reader counts, focus, sticky alignment). The bugs are never in the small happy-path fixture; they surface at the seams — a wrong estimate yanks the scroll, too-little overscan blanks white, and DOM-window assumptions fail silently on real data.

## Checklist (lead with the trap)

1. **A test that disables virtualization hides every bug below it.** `disableVirtualization` (MUI X), `onShouldVirtualize={() => false}` (Fluent), `renderAllRows` (Handsontable), or a 5-row jsdom fixture mounts the whole list, so blank rows, offset drift, and focus loss never reproduce. Keep at least one path with virtualization ON — a browser/e2e test at a realistic item count and a fixed container height — or CI stays green on a broken grid.
2. **estimateSize must be close, and measurement must not yank the scroll.** The virtualizer sizes the total scroll range from `estimateSize` before rows measure; when `measureElement` reports the real height, following offsets shift. A flat `() => 35` for rows that wrap to variable heights makes scrolling jump and flicker as each row corrects. Give a realistic estimate and attach `measureElement` so measured rows report true size.
3. **Prepending items (chat/feed) is where position-loss bites hardest.** Inserting rows above the viewport pushes every following offset down; with no compensation the user's read position jumps. Anchor to a stable item (many libs expose `firstItemIndex`/prepend support or a `scrollToIndex` restore). Note CSS `overflow-anchor` only anchors real DOM nodes — it cannot anchor a row the virtualizer has not mounted.
4. **Overscan is a two-sided budget.** Too small blanks white gaps on fast scroll (rows unmount before the next ones mount and measure); too large mounts extra rows every frame and costs INP and memory. Tune per surface, and lean slightly higher for dynamically-measured lists where measurement lag is what causes the blanks.
5. **Features that assume rows are all in the DOM break silently.** Ctrl+F / find-in-page matches nothing off-screen; "select all", export-visible, and `querySelector`-based logic see only the window. If in-page search is a requirement, `content-visibility: auto` with `contain-intrinsic-size` keeps rows in the DOM (searchable, in the a11y tree) while skipping paint — a different tradeoff from true windowing, not a drop-in fix.
6. **Screen readers need the full set size, not the mounted count.** Without `aria-setsize`/`aria-posinset` on list items (`role="option"`/`listitem`, or `article` in a `role="feed"`), AT announces "3 of 20" instead of "3 of 5000". For grids, put `aria-rowcount`/`aria-colcount` on the `role="grid"` container and `aria-rowindex`/`aria-colindex` reflecting the true position on partially-loaded rows and cells; use `-1` when the total is unknown.
7. **Focus is lost when the focused row unmounts.** Scrolling the focused row out of the window removes its node, so focus falls back to `<body>` — keyboard nav and the AT reading position reset. Manage focus deliberately (roving `tabindex`, restore on remount); the grid pattern expects author-managed focus with a single tab stop into the widget.
8. **Sticky header and pinned column must share the body's scroll math.** A header or pinned column rendered outside the virtualized body drifts from the rows when heights are dynamic or the scrollbar changes width. Verify alignment with variable-height rows and at the top and bottom scroll extremes, not just at rest.

## Quick probes

Treat hits as leads; confirm the estimate-to-measure-to-render path and the aria/focus wiring at the call site. No linter catches windowing bugs — the source of truth is a browser/e2e scroll test with virtualization enabled; route the aria row/set-size assertions to a11y-contract-testing's harness (axe/AT), since value-dependent attributes are invisible to `eslint-plugin-jsx-a11y`.

```sh
rg -n 'useVirtualizer|Virtuoso|react-window|FixedSizeList|VariableSizeList|AutoSizer|DataGrid' src/ app/ 2>/dev/null
rg -n 'estimateSize|measureElement|overscan|rowBufferPx|columnBufferPx|rowBuffer' src/ app/ 2>/dev/null
rg -n 'disableVirtualization|onShouldVirtualize|renderAllRows|renderAllColumns' src/ app/ test/ 2>/dev/null  # virtualization off — esp. in tests
rg -n 'aria-setsize|aria-posinset|aria-rowcount|aria-rowindex|aria-colcount|aria-colindex' src/ app/ 2>/dev/null
rg -n 'prepend|unshift|firstItemIndex|scrollToIndex|scrollToItem' src/ app/ 2>/dev/null  # prepend/scroll-restore paths
```

## Boundary with sibling skills

- This skill: the virtualization/windowing contract — `estimateSize`/`measureElement` offset correctness, overscan budget, virtualization-disabled tests, DOM-window assumptions, and sticky/pinned alignment.
- **a11y-contract-testing** — turning `aria-setsize`/`aria-posinset` (and `aria-rowcount`/`aria-rowindex`) into a test contract and running the AT/axe assertions; this skill flags that they are missing or wrong, that skill owns the harness.
- **overlay-focus-scroll-contracts** — focus restore, scroll-lock, and the focus lifecycle when a node unmounts (shared with row-unmount focus loss; the general mechanics live there).
- **responsive-image-contracts** — `srcset`/`sizes`/`loading`/`decoding` for images inside virtualized rows, where remount churn re-triggers image loads.
- **frontend-data-fetching-cache-contracts** — the paginated/infinite query feeding the list (page eviction, dedupe, revalidation). This skill owns what the list does with rows, not how they are fetched or cached.

## PR-worthiness gate

File a finding only when a user-visible windowing contract is broken:

- **Scroll defect**: jump/flicker/blank traceable to a wrong `estimateSize`, missing `measureElement`, uncompensated prepend, or too-small overscan under real scroll.
- **Hidden by test**: virtualization disabled in the test path while production runs it, masking one of the above.
- **DOM-window assumption**: a real feature broken — find-in-page, screen-reader count (missing/wrong `setsize`/`posinset` or `rowcount`/`rowindex`), or focus lost on row unmount.
- **Alignment**: sticky header/pinned column drifting from the body with dynamic heights.

Reject weak findings:

- A fixed-height list with a correct `estimateSize` and default overscan that scrolls cleanly — not a defect.
- Demanding `aria-setsize` on a small, fully-rendered list where every item is already in the DOM (the browser computes position/size).
- Overscan tuning with no visible blank and no measured INP regression — that is config, not a bug.
- "Replace the virtualizer with `content-visibility`" as a blanket rewrite; raise it only when in-page search/findability is a stated requirement.

Minimal useful PR: a browser/e2e test with virtualization enabled at a realistic count that scrolls to the middle and end, asserts no blank rows, and asserts a stable anchor after a prepend; plus, for a11y, that `setsize`/`posinset` (or `rowcount`/`rowindex`) reflect the full dataset, not the window.

## Output shape

- **Contract**: estimate/measure offset | overscan budget | virtualization-disabled test | DOM-window assumption (find-in-page / aria count / focus) | sticky-pinned alignment.
- **Evidence**: file/line and the virtualizer config or the row/cell render path.
- **Symptom**: scroll jump/flicker, blank gap, wrong "N of M" announcement, lost focus, drifting sticky column.
- **Fix**: smallest change — realistic `estimateSize`, wire `measureElement`, adjust overscan, add `setsize`/`posinset` (or `rowcount`/`rowindex`), roving-tabindex focus restore, or share the scroll math.
- **Verification**: browser/e2e scroll test with virtualization ON; AT/axe assertion for the aria counts.

## Sources

- TanStack Virtual — Virtualizer API (`estimateSize`, `measureElement`, `overscan`, `lanes`; overscan guidance to keep fast scroll smooth): <https://tanstack.com/virtual/latest/docs/api/virtualizer>
- TanStack Virtual — VirtualItem (a virtual item's `size` is the estimate until `measureElement` replaces it with the measured value): <https://tanstack.com/virtual/latest/docs/api/virtual-item>
- TanStack Table — Virtualization Guide (map virtual items, not `getRowModel().rows.map(...)`; a stable estimate so the scroll range is known immediately): <https://tanstack.com/table/v8/docs/guide/virtualization>
- MUI X — Data Grid Virtualization (`rowBufferPx`, `columnBufferPx`, `disableVirtualization`, and why disabling grows the DOM): <https://mui.com/x/react-data-grid/virtualization/>
- MDN — aria-setsize (set the total set size; `-1` when unknown; unneeded when all items are in the DOM): <https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Attributes/aria-setsize>
- MDN — aria-posinset (an item's position in the full set when only a subset is in the DOM; pair with `aria-setsize`): <https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Attributes/aria-posinset>
- MDN — aria-rowcount / aria-rowindex (put the total on the container and the true index on partially-loaded rows/cells; `-1` when unknown): <https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Attributes/aria-rowcount>
- MDN — CSS overflow-anchor (scroll anchoring minimizes content-shift jumps; it can only anchor DOM nodes that exist): <https://developer.mozilla.org/en-US/docs/Web/CSS/overflow-anchor>
- web.dev — content-visibility (off-screen content with `auto` stays in the DOM and a11y tree and remains findable via find-in-page; pair with `contain-intrinsic-size`): <https://web.dev/articles/content-visibility>
- W3C ARIA APG — Feed Pattern (feed articles carry `aria-posinset`/`aria-setsize`; scroll-based loading contract): <https://www.w3.org/WAI/ARIA/apg/patterns/feed/>
