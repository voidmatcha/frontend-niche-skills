# Public prior art for component extraction judgment

This reference is intentionally public and generic. It must not contain company-specific repository paths, screenshots, or product terms.

## Near-duplicate component scanners

- [`Muronuch/react-unify`](https://github.com/Muronuch/react-unify) scans React/TypeScript source for structurally similar components using AST-shaped fingerprints and writes a clickable report. Its README emphasizes read-only operation, human/agent control over every diff, optional LLM proposals, and TypeScript verification for proposed unified components.
- [`pfrankov/duplicalis`](https://github.com/pfrankov/duplicalis) classifies duplicate React components with categories such as `#prop-parameterizable`, `#copy-paste-variant`, `#logic-duplicate`, `#style-duplicate`, `#wrapper-duplicate`, and `#forked-clone`. Those labels map well to a judgment matrix, but they are still signals rather than permission to merge.

## Design fidelity and extraction adjacent tools

- [`jovd83/design-fidelity-auditor`](https://github.com/jovd83/design-fidelity-auditor) frames design alignment as a review artifact: inspect implementation files plus design authority, produce a scorecard, distinguish confirmed violations from ambiguous drift, and avoid silently redesigning UI.
- [`gbechtold/Hi-Fidelity-Design`](https://github.com/gbechtold/Hi-Fidelity-Design) uses a design/implementation IR, mapping, numeric deltas, and reports sorted by largest mismatch. The useful transfer here is evidence tiering and adapter boundaries, not copying its implementation.
- [Claude Figma plugin](https://claude.com/plugins/figma) documents design context extraction, design tokens, Figma component mapping, and implementation from Figma references. Component extraction decisions should preserve that design authority instead of flattening variants into one generic component.
- [`dennisonbertram/steal-react-component`](https://github.com/dennisonbertram/steal-react-component) is extraction-oriented prior art for recovering components/design systems from live sites. It is adjacent to implementation reconstruction, but this skill is for refactoring code you own, not cloning production sites.

## Accessibility and rendered-contract checks

- [`eslint-plugin-jsx-a11y`](https://github.com/jsx-eslint/eslint-plugin-jsx-a11y) describes itself as a static AST checker for accessibility rules and recommends combining static checks with rendered DOM/accessibility testing. This supports the rule that component extraction must preserve rendered role/name/state, not just JSX attributes.
- [Storybook accessibility testing](https://storybook.js.org/docs/writing-tests/accessibility-testing) uses axe-based checks against component stories. It is useful for variant-level regression, but automated a11y checks do not replace keyboard/focus and accessible-name contract assertions.

## React design principles

- [Thinking in React](https://react.dev/learn/thinking-in-react) encourages breaking UI into a component hierarchy around data and responsibilities, then identifying where state lives. That supports extracting by semantic responsibility, not visual similarity alone.
- [Passing Props to a Component](https://react.dev/learn/passing-props-to-a-component) frames props as the parent-to-child contract. Extraction should produce clear, named props rather than vague boolean/escape-hatch APIs.
- [Reusing Logic with Custom Hooks](https://react.dev/learn/reusing-logic-with-custom-hooks) distinguishes behavior reuse from UI reuse. Repeated state/side-effect logic often belongs in a custom hook even when visual components should remain separate.
