---
name: responsive-image-contracts
description: "Use when responsive image markup ships the wrong file: width-descriptor srcset lacks accurate sizes, descriptors do not match intrinsic file widths, an LCP image is lazy or low priority, img lacks reserved dimensions and causes CLS, candidate coverage is poor, density and width descriptors are mixed, picture art direction omits media/type, or sizes=auto is used without lazy loading. Covers image selection, role-based sizing, load priority, and candidate verification. Use design-to-code-fidelity for visual drift, i18n-copy-and-layout for localized copy, and core-web-vitals-performance-contracts for whole-page budgets."
---

# Responsive image contracts

A responsive image is a contract between the file you ship and the box it renders into. Linters can check that the syntax is valid; they cannot tell you the `sizes` value matches the real layout, that the intrinsic-width labels are honest, or that the LCP image loads first. This lens reviews that judgment: role-based sizing (hero vs grid cell vs thumbnail), load priority, and which candidate the browser actually downloads.

## Checklist (lead with the trap)

1. **`w`-descriptor `srcset` with no `sizes` -> the browser assumes `100vw`** and downloads the widest candidate that fits the full viewport. A 400px thumbnail with `srcset="...1600w"` and no `sizes` fetches the 1600w file on a wide screen: wasted bytes and, if it is the LCP element, a slower paint. Add `sizes` describing the real rendered width.
2. **`sizes` must match the actual CSS layout, not a guess.** `sizes="100vw"` on an image that renders in a 3-column grid (really ~33vw) over-downloads ~3x; a too-small `sizes` under-downloads and renders soft. `sizes` is a media-condition list read left-to-right, first true wins, with a bare fallback length last. Measure the rendered width across breakpoints; do not eyeball it.
3. **Intrinsic-width descriptors must equal the file's real decoded width.** `photo-1200.jpg 640w` when the file is 1200px poisons the selection math — the browser thinks 640w is enough and serves blur, or the opposite. Verify each `w`/`x` label against the actual pixel width of the file it points at.
4. **The hero/LCP image must not be `loading="lazy"`.** Lazy delays discovery and typically regresses LCP. Use `loading="eager"` (or omit `loading`) plus `fetchpriority="high"` so it wins network priority from discovery. Cap `fetchpriority="high"` at 1-2 elements per page — if everything is high, nothing is — and keep genuinely below-the-fold images `loading="lazy"`.
5. **Every `<img>` needs `width` + `height` attributes (or a reserved `aspect-ratio`)** or it shifts layout when the file arrives (CLS). An image sized only in CSS (`width: 100%; height: auto`) with no `width`/`height` attributes collapses to height 0 until it downloads, then shoves the content below it down the page. Keep the attributes so the browser derives an `aspect-ratio` and reserves the box up front, and pair them with CSS `max-width: 100%; height: auto` to stay responsive. Do not override with a fixed CSS `height` (it distorts the ratio) or drop the attributes (the collapse returns).
6. **Too few candidates.** One or two widths in `srcset` cannot serve DPR 2-3 phones and wide desktops well; provide a spread that brackets the real `sizes` range. Do not over-file: a fixed-size icon or logo needs no `srcset` at all.
7. **Descriptor type must match intent.** `x` (density) descriptors are for a fixed display size across DPRs; `w` (width) descriptors + `sizes` are for variable layout width. Mixing them, or adding `sizes` to an `x`-descriptor `srcset` (where it is ignored), is a misuse — `sizes` is only meaningful with `w`.
8. **`<picture>` is for art-direction and format fallback, not resolution switching.** Use `<source media="...">` when the crop/aspect genuinely changes per breakpoint, and `<source type="image/avif">` before webp/jpg for format fallback. Each `<source>` needs its `media` or `type`, and a real `<img src alt>` must close the `<picture>`. If only the resolution changes, drop `<picture>` and put `srcset`/`sizes` on the `<img>`.
9. **`sizes="auto"` is only valid with `loading="lazy"`.** On an eager image the value is invalid and browsers fall back to `100vw` (over-download). Keep explicit `sizes` lengths for eager/hero images; only use `auto` on lazy ones, and keep `width`/`height` for the aspect ratio.

## Quick probes

Leads, not proof — HTML/JSX tags can span multiple lines, so confirm on the rendered tag before filing. Mechanical validity belongs to the linters below; use these to find candidates to *judge*.

```sh
# w-descriptor srcset with no sizes on the same line -> 100vw over-download
rg -n '<img[^>]*srcset=' src/ app/ components/ 2>/dev/null | rg -v 'sizes='
# <img> tags to eyeball for missing width/height (CLS)
rg -n '<img\b' src/ app/ components/ 2>/dev/null | rg -v 'width='
# density (x) vs width descriptors, <picture> sources, and sizes=auto
rg -n 'srcset=[^>]*[0-9]x|<source\b|sizes="auto"' src/ app/ components/ 2>/dev/null
# LCP/hero must not be lazy; below-fold should be
rg -n 'loading="(lazy|eager)"|fetchpriority' src/ app/ components/ 2>/dev/null
```

Run the mechanical linters first — they own syntax so this lens can own judgment. [RespImageLint](https://ausi.github.io/respimagelint/) is a bookmarklet that resizes the page across viewports, measures each image's real rendered width, and prints the correct `sizes`/`srcset`. The [W3C Nu Html Checker](https://validator.w3.org/nu/) flags the mechanical conformance violations in CI (it has an API) — `sizes` without `srcset`, a `w`-descriptor `srcset` with no `sizes`, or `sizes="auto"` on a non-lazy image — and [Markuplint](https://markuplint.dev/docs/rules)'s `invalid-attr` rule checks each `srcset`/`sizes`/`loading` value against the HTML standard. [eslint-plugin-layout-shift](https://github.com/mizdra/eslint-plugin-layout-shift) fails the build on media elements missing `width`/`height`.

## Boundary with sibling skills

- **Prior art / route the mechanical checks out.** The mechanical `srcset`/`sizes`/`width`-`height` constraints are already enforced by linters — RespImageLint (bookmarklet), the W3C Nu Html Checker and Markuplint's `invalid-attr` rule (`srcset`/`sizes`/`loading` conformance), and eslint-plugin-layout-shift (require width/height). Send "is the syntax valid / is width/height present" there. This skill owns the review *judgment* those tools cannot make: role-based sizing (hero vs thumbnail vs grid cell), the LCP eager/`fetchpriority` decision, whether `sizes` matches the actual CSS layout, and diagnosing *which candidate the browser really downloaded* (DevTools -> the element's `currentSrc`, or the actual URL in the Network panel; on Chromium with a server `Accept-CH` opt-in, the `Sec-CH-Width` request hint).
- **design-to-code-fidelity** — for rendered-vs-design visual/pixel drift (wrong crop, visible blur, off dimensions treated as a visual mismatch), not the `srcset` selection contract.
- **i18n-copy-and-layout** — only for localized caption, filename, or `alt` copy display, not image selection.
- **LCP scope.** This lens owns image-load priority for the LCP element (eager + `fetchpriority`, discoverable in the HTML). Whole-page Core Web Vitals budgeting — JS/CSS, fonts, TTFB, non-image LCP — is out of scope.

## PR-worthiness gate

Count a finding only when all are true:

1. **Real user-visible cost**: extra bytes downloaded, a soft/blurry render, a layout shift, or a delayed LCP — not merely non-idiomatic markup.
2. **The declared contract provably disagrees with the layout or role**: `sizes` vs measured rendered width, descriptor vs actual file width, `loading="lazy"` on the LCP element, missing space reservation.
3. **A narrow fix exists**: one `sizes` value, one `loading`/`fetchpriority` change, one `width`/`height` pair, or a `<picture>`/`<img>` swap.
4. **The mechanical linters do not already catch and gate it.**

Reject weak findings:

- Valid syntax the linter already owns, with no measured over/under-download.
- A fixed-size icon, logo, or sprite that legitimately needs no `srcset`.
- `fetchpriority="high"` absent on a genuinely below-the-fold image (correct).
- `sizes="100vw"` on an image that really does span the viewport (a true hero/banner).
- A framework image component (`next/image`, `@astrojs/image`, a CDN loader) that computes `sizes`/`srcset` — inspect the generated output before claiming a defect.

## Output shape

Return compact findings:

- **Contract**: sizes-vs-layout / descriptor-vs-file / LCP priority / CLS reservation / picture-vs-srcset / sizes=auto.
- **Evidence**: file:line, the real rendered width or image role, and the candidate actually downloaded (`currentSrc`, or the requested URL in the Network panel) when available.
- **Cost**: wasted bytes, blur, CLS, or LCP delay.
- **Fix**: the smallest attribute change.
- **Verification**: re-run RespImageLint or re-check `currentSrc` at the target viewport, or a Lighthouse/DevTools LCP-discovery check.

## Sources

- MDN, [Using responsive images in HTML](https://developer.mozilla.org/en-US/docs/Web/HTML/Guides/Responsive_images) — resolution switching (`srcset`/`sizes`, `w` vs `x` descriptors) vs art direction, and the selection math.
- MDN, [`HTMLImageElement.sizes`](https://developer.mozilla.org/en-US/docs/Web/API/HTMLImageElement/sizes) and [`.srcset`](https://developer.mozilla.org/en-US/docs/Web/API/HTMLImageElement/srcset) — `sizes` defaults to `100vw`, is only meaningful with `w` descriptors, and the `auto` keyword requires `loading="lazy"`.
- Web Platform features, [`<img sizes="auto">`](https://web-platform-dx.github.io/web-features-explorer/features/sizes-auto/) — `sizes="auto"` applies only to `loading="lazy"` images; otherwise browsers fall back to `100vw`.
- MDN, [`<picture>`](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/picture) — `media`/`type` on `<source>`, the mandatory `<img>` fallback, and when to prefer `srcset` over `<picture>`.
- web.dev, [Browser-level image lazy loading](https://web.dev/articles/browser-level-image-lazy-loading) and [Fetch Priority API](https://web.dev/articles/fetch-priority) — never lazy-load the LCP image; use `fetchpriority="high"` on 1-2 resources.
- Chrome for Developers, [LCP request discovery](https://developer.chrome.com/docs/performance/insights/lcp-discovery) and MDN, [Fix image LCP](https://developer.mozilla.org/en-US/blog/fix-image-lcp/) — make the LCP image discoverable, `fetchpriority="high"`, and not `loading="lazy"`.
- web.dev, [Optimize Cumulative Layout Shift](https://web.dev/articles/optimize-cls) — set `width`/`height` attributes or `aspect-ratio` to reserve space; keep `height: auto; max-width: 100%` in CSS so images sized only in CSS do not collapse to height 0.
- Tools: [RespImageLint](https://ausi.github.io/respimagelint/), [W3C Nu Html Checker](https://validator.w3.org/nu/) and [Markuplint rules](https://markuplint.dev/docs/rules) (`invalid-attr`), [eslint-plugin-layout-shift](https://github.com/mizdra/eslint-plugin-layout-shift) (`require-size-attributes`).
