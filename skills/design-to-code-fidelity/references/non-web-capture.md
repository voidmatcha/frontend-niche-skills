# Implementation capture adapters

How to capture the real implementation pixels per platform. The per-platform
capture-adapter list lives here once; the workflow only names which adapter to
select. The bundled `render-capture.mjs` is the **web adapter** — do not force
it onto non-web UI.

## T3-vs-T4 fallback rule

The canonical rule is stated once in `SKILL.md` ("T3-vs-T4 fallback rule"):
when the capture adapter is missing, use **T3** only when exact
design/source-code evidence supports a static audit, else **T4**; always name
the missing adapter instead of inventing a diff result. It applies to every
platform below.

## Web / Storybook / local routes

Capture at the exact design viewport/scale. The web adapter defaults to `CAPTURE_MODE=viewport` so the output height matches the requested viewport; set `CAPTURE_MODE=fullPage` only when the design reference is also a full-page/stitch-style frame and document that choice.

```bash
INIT_SCRIPT='const t=Date.parse("2026-01-01T00:00:00Z"); Date.now=()=>t;' \
  CAPTURE_MODE=viewport \
  node scripts/render-capture.mjs "https://preview.example.test/path?fixture=case" tmp/impl/case.png 360 780 2
```

Use readiness knobs when needed: `WAIT_FOR_SELECTOR`, `WAIT_FOR_TEXT`, `WAIT_UNTIL`, `WAIT_TIMEOUT_MS`, `STORAGE_STATE`, `LOCALE`, `TIMEZONE_ID`, `COLOR_SCHEME`, `REDUCED_MOTION`, and `EXTRA_WAIT_MS`.

`render-capture.mjs` neutralizes CSS animations/transitions by default for deterministic static parity. This does **not** stop JS-driven motion — Web Animations API (`Element.animate()`), `requestAnimationFrame` loops, canvas/WebGL, or libraries like GSAP that write inline styles keep running — so pin or disable those via `INIT_SCRIPT` when you need a truly static frame. Set `ALLOW_ANIMATION=1` to also keep CSS animations/transitions running (required for transition/dynamic-fidelity capture; see `references/diff-interpretation.md`).

For fixed/sticky bottom bars, full-page screenshots can drop or strand the bar. Neutralize only when that matches the design reference:

```bash
NEUTRALIZE_CSS='[class*="floating"]{position:static!important;transform:none!important;left:auto!important;bottom:auto!important}' \
  node scripts/render-capture.mjs "$URL" tmp/impl/case.png 360 1200 2
```

Always state whether fixed bars were captured as fixed, neutralized to static, or intentionally excluded.

Storybook is preferred for component/state fidelity because it can pin props, fixtures, viewport,
theme, and design annotations. If no story exists, generate or request the smallest story/harness
that exposes the target state before relying on app navigation. Put external wrapper layout in a
decorator/harness, not in component props, so visual drift is attributable.

## Native / mobile / desktop / canvas

Use a capture path that exercises the real implementation:

- **iOS:** simulator/device screenshot (`xcrun simctl io booted screenshot`), XCTest, Detox, Maestro, or app view-shot harness.
- **Android:** `adb exec-out screencap`, Espresso, Detox, Maestro, or app view-shot harness.
- **React Native:** prefer a deterministic fixture screen plus simulator/device screenshot; code-only audit is T3 until a screenshot exists.
- **Desktop/native shells:** use OS/window screenshot tooling and record window size/device scale.
- **Canvas/WebGL/video/animation:** freeze frame/time and capture a deterministic frame; record GPU/browser/device variance.
- **Email/PDF/document rendering:** capture the actual target renderer output, not just source HTML or design preview.
- **Static rendered artifact:** compare the produced raster output directly only if it is the actual shipped artifact.
