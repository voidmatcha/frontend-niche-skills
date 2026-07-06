# Generic mismatch checklist

Recurring, PR-worthy defects to look for across projects. Run this after a failing or suspect row has structural diff and source/setup evidence.

## Design QA hot spots

Design QA usually catches the places where implementation looks "almost right" but breaks visual intent. Check these before asking design to re-review:

- **Hero/section background:** missing fill, wrong gradient direction, clipped glow, opacity/blend mismatch, or background only covering content instead of the full section.
- **CTA and bottom chrome:** misplaced fixed/sticky button, wrong bottom safe-area spacing, button text vertically off-center, disabled/pressed state not matching, or click target present while visual child is missing.
- **Badges/ribbons/discount labels:** text wrapping unexpectedly, label clipped by mask, icon/ribbon offset wrong, or dynamic percentage/currency values not covered.
- **Spacing rhythm:** top/bottom padding, card-to-footer gap, row gap, list divider spacing, or vertical centering drift; small deltas compound over stacked content.
- **Typography:** font size, line-height, weight, letter spacing, text alignment, font fallback, and localization line breaks. Verify intentional `\n` and long-token behavior.
- **Radius and clipping:** parent radius differs from child/image clipping; nested cards or tables leak square corners.
- **Stroke, divider, shadow, blur:** 1px borders and thin icon strokes can disappear in fuzzy diffs; inspect them explicitly.
- **Icons/SVG/assets:** wrong asset variant, viewport box, stroke width, fill color, export scale, or rasterized asset treatment.
- **State coverage:** default, selected, disabled, pressed, loading, error, empty, hover/focus, modal/open, and scrolled/sticky states.
- **Responsive/localized variants:** narrow width, high font scale, RTL, CJK wrapping, long translated labels, and price/currency extremes.
- **Native/browser chrome policy:** status bar, safe-area, app header/footer, browser chrome, and screenshot crop included in one side but not the other.
- **Unsupported design variant:** design has a section/state/locale/breakpoint/theme that component props or data model cannot express.
- **Copy/content drift:** implementation string differs from approved content/localization source. If design is not canonical copy source, report it as a design-vs-code mismatch candidate or blocker rather than an implementation defect.

## Visual regression gate

Use visual regression when a change can visually affect layout, CSS fallback, responsive behavior, or design QA hot spots. This includes CSS polyfills, legacy browser markers, safe-area/viewport fixes, fixed CTA changes, typography, and asset replacements.

Minimum useful matrix:

- **Baseline branch:** current supported browser/runtime with marker/fallback disabled.
- **Fallback branch:** forced feature-detection marker or legacy branch enabled.
- **Design-sensitive states:** at least one narrow viewport and one representative content extreme, such as long label, large discount, RTL, or localized copy.
- **Control comparison:** modern branch before/after should be unchanged unless the design intentionally changed.

Rules:

- Capture before editing when behavior is uncertain, then re-run the same capture after the patch.
- Treat visual snapshots as product evidence only after reviewing artifacts, not just snapshot pass/fail.
- CSS polyfills plus Playwright can demonstrate that the forced fallback branch stays visually aligned; they do not show that an old engine can parse/render the page. Pair actual-engine evidence when documenting legacy compatibility.
- Keep masks/exclusions explicit. Undocumented masks downgrade the claim.
- Do not update snapshots until the diff is understood and either fixed or accepted as intentional by the design/source owner.

## Generic mismatch candidates

- Missing or invisible section/background fill.
- Wrong border color/width, gradient, shadow, opacity, blend mode, or image treatment.
- Corner radius mismatch, especially cards/tables where child clipping differs from parent radius.
- Font size, line-height, weight, letter spacing, or text alignment drift.
- Icon/SVG/vector box size, stroke width, viewport, or asset variant mismatch.
- Table/list row dividers and 1px borders; structural diff may erase them as noise.
- Fixed/sticky CTA, toolbar, toast, modal, or overlay captured in the wrong coordinate system.
- Native/status-bar/safe-area/browser chrome included in design but not implementation, or vice versa.
- Dynamic content not pinned: countdown, dates, prices, remote images, randomized recommendations, or A/B flags.
- Responsive overflow: long-label cases change line breaks and vertical rhythm. For translated-copy overflow and RTL mirroring, use the i18n sibling skill; this skill flags only rendered UI mismatch against design reference.
- Accessibility-driven visible state mismatch: focus rings, disabled/selected states, hover/pressed states, and menu/dialog open states.
