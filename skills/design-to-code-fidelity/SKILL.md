---
name: design-to-code-fidelity
description: "Use when implementing or reviewing UI against a design reference when visual mismatches slip past review: design QA checklist, visual regression gates, wrong fill/stroke, missing section background, off spacing/radius, misplaced CTA, badge/ribbon clipping, copy drift, or unsupported variant. Turns a design source plus an implementation into reference export, deterministic capture, comparison, and an evidence-graded report. Scope: rendered UI does not match the design reference; for translated-copy overflow and RTL mirroring see i18n-copy-and-layout, for merge/extract calls see component-extraction-judgment."
---

# Design-to-code fidelity

Use this skill to assess how closely an implemented UI matches a design reference and to report the highest evidence tier reached. It must stay
**general-purpose**: do not bake in one product, one repository, one Figma file, one renderer,
or one design-tool vendor. Every finding must state which evidence tier it reached.

## Core contract

A valid fidelity run has four adapters:

```text
design reference adapter -> implementation capture adapter -> comparison adapter -> evidence report
```

- **Design reference adapter**: exports the intended pixels or supplies an approved static reference image.
- **Implementation capture adapter**: captures the real UI pixels from web, Storybook, mobile/native, desktop, canvas, or another renderer.
- **Comparison adapter**: compares same-intent reference/render images and reports structural drift.
- **Evidence report**: separates verified diffs from static audit findings and blocked checks.

Never claim more than the weakest adapter proves.

## Evidence tiers

Use these exact tiers in reports:

| Tier | Name | Counts as strict? | Required evidence |
| --- | --- | --- | --- |
| T1 | Strict raster-diff validated | yes | approved reference provenance/version + real implementation screenshot + matching crop/framing/chrome policy + same viewport/DPR/state + declared masks/exclusions/tolerances + reviewed comparison artifacts |
| T2 | Visual capture without strict gate | no | design image + implementation screenshot exist, but dimensions/state/masks/thresholds/exclusions are not yet trustworthy |
| T3 | Static design-vs-code audit | no | exact design export or node metadata + source code evidence; no real implementation screenshot |
| T4 | Blocked / not validated | no | missing token/access, missing renderer, rate limit, unavailable simulator/device, missing fixture, or no reproducible route |

Only T1 should be called strict raster-diff validated, and only for the declared reference, capture, viewport, crop, state, masks, and tolerances. It is not a guarantee of full design correctness. T2/T3 can produce maintainer-plausible PR/issue candidates, but must not be called verified.

**T3-vs-T4 fallback rule:** when the implementation capture adapter is missing, use T3 only when exact design/source-code evidence supports a static audit; otherwise use T4 for the missing capture/renderer/access. Name the missing adapter instead of inventing a diff result.

## Bundled scripts

| Script | Role | Dependencies |
| --- | --- | --- |
| `scripts/figma-export.sh <file-key> <node-ids> <out-dir> [scale]` | Export exact Figma nodes/frames as PNG reference images through the Figma Images API. Accepts `3-809` or `3:809`. | `curl`, `python3`, `FIGMA_TOKEN` or `FIGMA_API_KEY` |
| `scripts/figma-spacing.mjs <file-key> <node-ids> [depth]` | Extract quantitative layout data from Figma node JSON: frame sizes, auto-layout padding, item gaps, child bounds, text styles, strokes, and icon/vector boxes. Use after a visual diff flags drift. | Node 18+, Figma token |
| `scripts/render-capture.mjs <url> <out.png> [w] [h] [scale]` | Capture a web/Storybook/local-route screenshot at the target viewport and device scale. Supports `INIT_SCRIPT`, `NEUTRALIZE_CSS`, `ALLOW_ANIMATION=1` (keeps CSS animations/transitions running; JS-driven motion via WAAPI/rAF/canvas/GSAP is unaffected — neutralize it in `INIT_SCRIPT`), and `ALLOW_INSECURE_HTTPS=1` for local/self-signed capture only. | `@playwright/test` or `playwright` resolvable from cwd |
| `scripts/visual-diff.sh <ref.png> <render.png> [diff.png]` | Compare reference vs implementation screenshots. Stdout fields: `AE`, `AE_RATIO`, `STATUS=PASS\|FAIL`, `STRUCT=ALIGNED\|DRIFT\|UNKNOWN`, `MAX_BLOCK=<px>@<WxH+X+Y>`, `STRUCT_RATIO`, `REGION=<top\|middle\|bottom>`, `MAX_AE`. | ImageMagick |

The bundled capture script is a **web adapter**. For native/mobile/desktop/canvas, add or
invoke the appropriate capture adapter instead of forcing web tooling — see
[non-web-capture](./references/non-web-capture.md) for the per-platform list.

## Artifact contract

Use a run-scoped artifact directory instead of loose screenshots:

```text
artifacts/<slug>/
  design.json          # source URL/key/node ids, adapter/tool used, variants, variables, comments
  ref/                 # exported design rasters or approved reference images
  impl/                # implementation captures and capture notes
  diff/                # diff images, masks/crops, command logs
  report.md|json       # tier, findings, unknowns, upgrade path
```

Do not overwrite previous runs. Include viewport, DPR/scale, theme, locale, fixture, browser/device,
safe-area/chrome policy, and all masks/exclusions in the manifest. Project-native paths (`fixtures/figma`,
`fixtures/screenshots`, Storybook output) are fine if they carry the same information and the report links them.

## Universal workflow

1. **Resolve the design source.** Identify the exact frame/component/screen and exportable reference image. A workspace, recents, project, ticket, or social-preview URL is not enough. See [figma-adapters](./references/figma-adapters.md) for Figma and other design-source rules.
2. **Build the comparison matrix.** One row per screen/state/variant/locale/breakpoint/theme. Include viewport size, DPR/scale, crop/framing, scroll origin, fixture data, dynamic time, hover/focus/pressed/disabled/loading/error/empty state, theme/high-contrast mode, reduced-motion setting, orientation, browser/OS/font engine, expected chrome/safe-area handling, masks/exclusions, content source, and acceptance threshold.
3. **Select the implementation capture adapter.** Web app / Storybook / local preview uses `render-capture.mjs`; native/mobile/desktop/canvas/email/PDF use a renderer-specific path. The per-platform adapter list and the T3-vs-T4 fallback live in [non-web-capture](./references/non-web-capture.md).
4. **Freeze state.** Pin time, timers, animations, API fixtures, locale, theme, feature flags, auth/session, viewport, device scale, fonts where possible, network/image assets, and data payloads.
5. **Export and capture.** Reference and implementation images must match intended dimensions, crop/framing, scroll origin, device/browser/native chrome policy, safe-area policy, viewport, DPR/scale, and state. Check dimensions before trusting a diff.
6. **Normalize only with intent.** Crop, hide, or neutralize dynamic regions only when the comparison matrix documents why that region is out of scope. The bundled `visual-diff.sh` does not apply masks itself; if masks are needed, preprocess masked ref/render images first and record the mask artifact. Never silently mask mismatches. Undocumented masks downgrade the row to T2.
7. **Diff structurally as a screening signal.** For cross-renderer comparisons, run with tolerance and structural gating, for example:

```bash
AE_FUZZ=10% STRUCT_GATE=1 bash scripts/visual-diff.sh ref.png impl.png diff.png
```

   Interpret the output and validate dynamic/transition families per [diff-interpretation](./references/diff-interpretation.md).
8. **Diagnose with source/setup evidence.** Use node metadata, spacing extraction, DOM/computed styles, native layout inspector, accessibility/layout trees, and source code to investigate the largest drift candidates. Call them defects only after state/source evidence rules out capture/setup causes such as loaders, timing, fonts, media, theme, chrome, or fixture mismatch. Walk the design QA hot spots and visual regression gate in [mismatch-checklist](./references/mismatch-checklist.md), then use code-mapping triage in [figma-adapters](./references/figma-adapters.md).
9. **Report by tier.** Include commands, artifact paths, file/line evidence, expected vs actual, and unknowns.

## Boundary with sibling skills

- For translated-copy overflow and RTL mirroring see **i18n-copy-and-layout**; this skill flags only that the rendered UI does not match the design reference.
- For deciding whether near-duplicate components should be merged or extracted see **component-extraction-judgment**.

## Output shape

Use this shape for final findings:

```markdown
## Fidelity validation result

Tier: T1 strict raster-diff validated | T2 visual capture | T3 static audit | T4 blocked
Design source: <file/frame/url/node/image provenance>
Implementation source: <route/story/component/app/screen>
Viewport/state: <w x h x scale, locale, fixture, time, flags, masks>
Artifacts: <ref.png, impl.png, diff.png, logs, masks/crops, runtime/transition/state proofs if any>

Finding 1: <short mismatch>
- Evidence: <command output, file:line, node/frame id, diff metrics>
- Expected: <design behavior>
- Actual: <implementation behavior>
- Maintainer action: <minimal fix or follow-up>
- Confidence: high|medium|low

Unknowns / blockers:
- <what still needs capture/access/token/device/fixture>
```

## Stop conditions

Stop when every matrix row is one of:

- T1 `STRUCT=ALIGNED` plus reviewed artifacts, documented thresholds/masks/exclusions, and checked blind spots such as thin borders/text/icon residuals; or remaining diffs are documented intentional differences,
- T1 `STRUCT=DRIFT` with concrete source-backed fix recommendations,
- T2 explicitly labeled non-strict with the missing trust condition, or T3/T4 explicitly labeled with the missing adapter/access/state needed to upgrade it.

Do not publish a strict validation claim while any required row is only T2/T3/T4, or while known blind spots are unreviewed.

## References

- [figma-adapters](./references/figma-adapters.md) — design-source export rules, adapter priority, code-mapping triage.
- [non-web-capture](./references/non-web-capture.md) — per-platform capture adapters and the T3-vs-T4 fallback.
- [diff-interpretation](./references/diff-interpretation.md) — reading diff output, dynamic-fidelity checks, the L1-L5 ladder, the iteration loop guard.
- [mismatch-checklist](./references/mismatch-checklist.md) — recurring PR-worthy defect checklist.
