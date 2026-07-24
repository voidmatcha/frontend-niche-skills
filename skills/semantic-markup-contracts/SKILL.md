---
name: semantic-markup-contracts
description: "Use when reviewing or implementing frontend markup structure: clickable divs that should be buttons, links used as buttons, heading/landmark hierarchy, form label/control association, table/list semantics, invalid interactive nesting, overused ARIA replacing native HTML, or markup that breaks the accessibility tree, role-based tests, or hydration (and weakens SEO structure signals). Native HTML/semantic structure scope; for rendered role/name/state/focus regression tests use a11y-contract-testing, for visual design drift use design-to-code-fidelity."
---

# Semantic markup contracts

Use this skill when the question is **which HTML structure should exist** before
styling, scripting, or ARIA patches — structure that browsers, assistive
technology, crawlers, forms, and tests can all rely on. Prefer the native element
whose built-in contract already matches the user action; add ARIA only when
native HTML cannot express the pattern, then test the rendered contract.

## Boundary with sibling skills

This skill owns element choice and document structure (buttons vs links,
headings, landmarks, labels, tables, lists, nesting, native
disclosure/dialog/form semantics). **a11y-contract-testing** owns rendered
role/name/state/focus tests (`getByRole`, keyboard paths, ARIA state);
**constraint-validation-contracts** owns the native validity lifecycle;
**design-to-code-fidelity** owns visual spacing/ordering drift a semantic fix may
cause.

## Review checklist

1. **Action semantics** — fake-disabled links that still navigate and
   fake-disabled buttons that remain focusable; the `div`-`onClick` and
   `href="#"` smells are in the defect table.
2. **Heading hierarchy** — levels describe section order, never font size;
   repeated cards must not spawn noisy top-level headings unless they are real
   navigable sections.
3. **Landmarks** — one primary `<main>` per page; named regions only where they
   aid orientation, not landmark spam in every card.
4. **Forms** — beyond the programmatic label, associate error/help text via
   `aria-describedby` when users need it to fix input, and group related
   radios/checkboxes with fieldset/legend.
5. **Collections and data** — lists for repeated peer items, tables with
   meaningful row/column headers for two-dimensional data; div grids only when the
   component supplies the full grid contract and tests.
6. **Hydration and parser stability** — check invalid nesting that browsers
   silently repair before React/Vue/Svelte hydration, especially paragraphs
   containing block elements and interactive elements nested inside interactive
   elements.

## Defect patterns

| Smell | Risk | Better direction |
| --- | --- | --- |
| `div`/`span` with `onClick` and `tabIndex` | Missing keyboard/form/disabled semantics | Use `<button type="button">` or a real link |
| Link with `href="#"` for command | Broken navigation, history, keyboard expectations | Use button; use link only for real URL |
| Card wrapped in one link plus inner action buttons | Invalid/ambiguous interactive targets | Separate link area and action buttons |
| Visual heading implemented as bold text | Screen-reader/test heading structure lost (SEO signal is soft — text is still indexed) | Use correct heading level then style it |
| Labels only as placeholders | Label disappears after input; weak form contract | Use visible label or stable programmatic label |
| ARIA role added to fix native mismatch | Can create worse or duplicate semantics | Change native element first, then test |

## Quick probes

Use these as leads, not proof; inspect rendered output before filing:

```sh
# Clickable non-interactive elements that likely should be <button>/<a>
rg -n '<(div|span)[^>]*\bon[A-Z][a-z]+=|<(div|span)[^>]*\bonclick=' src/ app/ packages/ 2>/dev/null

# ARIA roles overriding native element semantics
rg -n 'role="(button|link|heading|list|listitem|checkbox|tab|dialog)"' src/ app/ packages/ 2>/dev/null

# Headings possibly chosen for font size, and <b>/<i> used for meaning
rg -n '<h[1-6][^>]*class=|</?[bi]>' src/ app/ packages/ 2>/dev/null

# Landmark coverage — expect one <main> plus purposeful named regions
rg -n '<main\b|role="main"|<nav\b|<header\b|<footer\b|<aside\b' src/ app/ packages/ 2>/dev/null
```

## PR-worthiness gate

Count a markup finding only when all are true:

1. **User-facing contract**: the element participates in navigation, command,
   form input, section structure, or data interpretation.
2. **Native mismatch**: current markup lacks or contradicts the native contract a
   browser would otherwise provide.
3. **Small fix path**: a native element/structure change can preserve behavior,
   or the remaining custom pattern has a clear `a11y-contract-testing` follow-up.

Do not over-file:

- A decorative wrapper without user interaction is not a semantic defect by
  itself.
- A native element with correct implicit role does not need redundant ARIA.
- A design preference for heading size is not a heading hierarchy bug unless it
  changes section meaning.
- A headless component may supply semantics outside the visible file; inspect
  rendered output before claiming the contract is broken.

## Output shape

Per finding: **markup contract** (expected native structure), **evidence**
(file/line or rendered DOM), **risk** (user/test/browser behavior that can fail),
**fix** (smallest structural change), **follow-up** (`a11y-contract-testing`,
visual check, or hydration check if needed).

## Sources

- HTML Living Standard (WHATWG): [sections](https://html.spec.whatwg.org/multipage/sections.html), grouping, and text-level semantics — the native element contracts. (The old HTML outline algorithm was never implemented and was removed from the spec in 2022; heading rank h1–h6 in logical order conveys structure.)
- W3C [ARIA in HTML](https://www.w3.org/TR/html-aria/): allowed roles/`aria-*` per element and when native semantics must not be overridden.
- W3C [WAI-ARIA Authoring Practices Guide](https://www.w3.org/WAI/ARIA/apg/) and its ["Read Me First"](https://www.w3.org/WAI/ARIA/apg/practices/read-me-first/) — the "no ARIA is better than bad ARIA" first rule.
- MDN: [HTML elements reference](https://developer.mozilla.org/en-US/docs/Web/HTML/Element) and [ARIA](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA).
