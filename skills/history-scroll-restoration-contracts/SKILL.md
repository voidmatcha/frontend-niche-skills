---
name: history-scroll-restoration-contracts
description: "Use when SPA Back/Forward or same-document navigation restores the wrong scroll position: the page jumps to the top, restores before async content creates enough height, jumps a second time after layout, loses a nested scroll container, or mishandles a hash target/history entry. Covers History API and router scroll restoration within the current document. Route bfcache document resume to browser-page-lifecycle-bfcache-contracts, cold URL reconstruction to deeplink-hydration, virtualized-row anchoring to large-list-data-grid-contracts, and modal scroll locking to overlay-focus-scroll-contracts."
---

# History and scroll restoration contracts

Scroll restoration is a coordination contract between the session-history
entry, the scroll owner, and layout readiness. A saved offset can be correct
while restoration still fails because it is applied to the wrong entry or
container, before the destination has enough scrollable extent, or again after
the browser already restored it.

## Checklist

1. Reproduce the exact navigation shape in a real browser: link navigation,
   `history.back()`/Back, Forward, `navigate(-1)`, or same-document hash
   traversal. Record the URL, history-entry identity or router key, navigation
   action, scroll owner, saved offset, applied offset, and final offset after
   async content settles.
2. Decide who owns restoration. Leave `history.scrollRestoration` as `auto`
   when browser restoration is the product contract. Use `manual` only when
   the application or router owns the whole save-and-restore path. Competing
   browser and application writes can create a second jump or make success
   timing-dependent.
3. Key positions by the intended history-entry semantics. A unique location
   key preserves separate positions for repeated visits to the same pathname;
   pathname-based keys intentionally reuse a position. Do not silently switch
   between these contracts or collapse query/hash-distinct entries without a
   product reason.
4. Identify the actual scroll owner. `window.scrollY` does not represent a
   nested `overflow: auto` route shell. Save and restore each intended
   container explicitly, and verify that a remounted container is the same
   logical owner before applying an old offset.
5. Restore only when the destination can represent the saved position. If
   async loaders, images, fonts, suspense boundaries, or conditional sections
   change the scroll extent, an immediate `scrollTo()` can be clamped and look
   successful in logs while landing too high. Tie restoration to an observable
   route/data/layout readiness boundary, then confirm the offset remains stable
   after the content above it finishes changing.
6. Do not replace readiness with an arbitrary delay or an unbounded retry loop.
   A fixed timeout is device- and network-dependent; repeated writes fight user
   input and browser scroll anchoring. Bound any retry by the destination entry
   and stop after success, user scroll, route change, or a documented timeout.
7. Treat fragments as navigation state, not just string parsing. Verify that
   Back/Forward between hash entries reaches the intended target after it
   exists. When the fragment is an accessibility navigation target, verify
   focus separately instead of treating correct scrolling as evidence of
   correct focus.
8. Keep scroll anchoring enabled by default. `overflow-anchor` can reduce
   content-shift jumps; disable it only on the smallest demonstrated region
   when anchoring itself conflicts with the explicit restoration contract.

## Quick probes

- Log `{ pathname, search, hash, entryKey, navigationType, owner, savedOffset,
  appliedOffset, finalOffset }` for one Back and one Forward traversal. Read
  `entryKey` only from an allowlisted router/history-state field; omit or redact
  every other `history.state` value because it may contain unrelated
  application data.
- At restore time, compare the saved offset with the owner's maximum possible
  offset (`scrollHeight - clientHeight`). A smaller maximum explains a clamped
  write but not why the layout was unready.
- Mark browser, router, and application scroll writes separately. Two writes
  for one entry are a stronger lead than the presence of any one listener.
- Repeat the sequence with delayed content above the saved position and with a
  nested scroll container. A document-only happy path is not sufficient
  evidence for a container restoration claim.

## Boundary with sibling skills

- `browser-page-lifecycle-bfcache-contracts` owns restoration of an existing
  top-level `Document`, `pageshow.persisted`, frozen resources, and stale state
  after bfcache resume. This skill owns same-document/router entry-to-position
  coordination.
- `deeplink-hydration` owns reconstructing a screen from a cold URL and router
  parameter readiness. This skill starts after the destination history entry
  is known and asks where that entry should scroll.
- `large-list-data-grid-contracts` owns virtualized row measurement, prepend
  compensation, overscan, and anchors for rows that may not be mounted. This
  skill may restore the outer route or container but does not invent a
  virtualized-list anchor.
- `overlay-focus-scroll-contracts` owns body scroll lock, scrollbar
  compensation, and focus/scroll restoration when a modal or drawer closes.
- `ssr-hydration-mismatch` owns server/client DOM divergence. Async height
  growth without a hydration mismatch remains in this skill.

## Minimal browser regression

Create route A with a meaningful saved position and content above it that
resolves asynchronously, then navigate to route B and traverse Back:

1. Assert the destination URL and history-entry key before checking position.
2. Wait for the route's explicit data/layout-ready signal, not a sleep chosen
   to make the test pass.
3. Assert the correct scroll owner reaches the saved offset within a small,
   documented tolerance.
4. Collect explicit evidence that every known layout producer above or
   affecting the target has settled, or observe that the scroll extent remains
   stable across the product's final async boundary. Only after the evidence
   shows that no later producer remains may two animation frames serve as a
   final stability check. Assert there is no second jump.
5. Traverse Forward and Back again to catch overwritten entry keys, duplicate
   listeners, and one-shot restoration.

Add a separate hash case when fragments are supported and a nested-container
case when the application scrolls an element instead of the document.

## PR-worthiness gate

Require a real browser traversal with the destination entry, scroll owner,
saved offset, restoration timing, and final post-layout offset captured. Tie
the failure to a visible wrong position, second jump, lost reading context, or
broken fragment target, then add the smallest regression for that navigation
shape.

The bundled Playwright fixture runs in the bundled Chromium, Firefox, and
WebKit engines and exercises duplicate same-URL history entries, asynchronous
layout readiness, exact saved offsets, and two-frame post-restoration stability
within one `Document`. It does not establish branded Safari behavior,
cross-document bfcache behavior, or virtualized-list anchoring.

Reject weak findings: a `popstate`, `scrollTo`, `history.scrollRestoration`, or
`overflow-anchor` occurrence with no failing traversal; an offset difference
within an intentional sticky-header tolerance; browser-managed restoration
that remains stable after layout; a nested container that the feature does not
promise to preserve; or a hypothetical async race with no clamped or late
position. Do not prescribe `manual`, global `overflow-anchor: none`, arbitrary
timeouts, or repeated scroll writes from source inspection alone.

## Output shape

- **Disposition**: confirmed | candidate/needs evidence | reject | route.
- **Sequence**: browser, A -> B -> Back/Forward/hash action, destination URL and
  entry key.
- **Evidence**: scroll owner, saved/applied/final offsets, maximum extent at
  restore time, async layout boundary, and competing writes.
- **Boundary**: why this is history restoration rather than bfcache, cold
  deep-link readiness, virtualized anchoring, or overlay scroll lock.
- **Smallest fix**: ownership, entry key, correct container, readiness signal,
  bounded cancellation, or narrowly scoped anchoring change.
- **Verification**: real-browser regression and any remaining timing,
  browser, or accessibility gap.

## Sources

- MDN, `History.scrollRestoration` and its `auto`/`manual` ownership modes:
  <https://developer.mozilla.org/en-US/docs/Web/API/History/scrollRestoration>
- MDN, `popstate`, including same-document history state and the ordering of
  persisted scroll state and fragment navigation:
  <https://developer.mozilla.org/en-US/docs/Web/API/Window/popstate_event>
- MDN, `overflow-anchor`, including default scroll anchoring and narrowly
  opting out when it causes a demonstrated problem:
  <https://developer.mozilla.org/en-US/docs/Web/CSS/overflow-anchor>
- Playwright, browser installation and its bundled Chromium, Firefox, and
  WebKit builds:
  <https://playwright.dev/docs/browsers>
- React Router, `ScrollRestoration`, `getKey`, and `storageKey`:
  <https://reactrouter.com/api/components/ScrollRestoration>
- Public React Router issue reproducing restoration before asynchronously
  rendered content provides sufficient page height:
  <https://github.com/remix-run/react-router/issues/11158>
- Public React Router issue reproducing Back/navigation restoration failure
  with a hash router:
  <https://github.com/remix-run/react-router/issues/11590>
- Public Next.js issue showing that fragment navigation must verify target
  focus separately from URL/scroll behavior:
  <https://github.com/vercel/next.js/issues/22838>
- Public Next.js issue showing a host-specific iOS swipe/snapshot symptom that
  should not be generalized without separating page lifecycle evidence:
  <https://github.com/vercel/next.js/issues/62133>
- Public Next.js issue reproducing different Back restoration behavior across
  router modes:
  <https://github.com/vercel/next.js/issues/68746>
