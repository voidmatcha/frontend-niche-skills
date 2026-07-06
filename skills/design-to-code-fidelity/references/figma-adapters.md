# Design source adapters

How to resolve and export an exact design reference, and how to map raw design
values back to code. Use after the workflow's "Resolve the design source" step.

## Figma

Use exact file/frame URLs or API identifiers:

```text
https://www.figma.com/design/<FILE_KEY>/<name>?node-id=<NODE>
https://www.figma.com/file/<FILE_KEY>/<name>?node-id=<NODE>
```

- URL node ids use dashes (`3-809`); Figma API ids use colons (`3:809`). The bundled export script normalizes this.
- `https://www.figma.com/files/<id>/recents-and-sharing` identifies a workspace/recents surface, not a design frame. Use the browser only to discover the real `/design/<FILE_KEY>` file and node ids.
- Public browser visibility is not enough. The Figma token account must have API access to the file. `/v1/images/<file-key>` returning `Not found`, `403`, `404`, or `429 Rate limit exceeded` means the case is blocked until export succeeds.
- Do not substitute `figma.com/api/oembed`, OpenGraph images, file cover thumbnails, screenshots of the editor canvas, or social previews for the Images API export. They are not exact frame evidence.
- Fetch comments when design notes matter; comments can contain acceptance criteria such as "gap 8px", "variant B", "status bar excluded", or "animation not required".

Example reference export:

```bash
FIGMA_TOKEN=... bash scripts/figma-export.sh "$FILE_KEY" "3-809,1-3472" tmp/ref 2
identify tmp/ref/*.png
```

Use `figma-spacing.mjs` after a diff points to spacing/position drift:

```bash
node scripts/figma-spacing.mjs "$FILE_KEY" "3-809,1-3472" 8
```

Adapter priority:

1. **Official Figma MCP or equivalent authenticated design adapter** when available: collect metadata,
   screenshot/export, design context, variables, assets, and comments; store raw inputs/outputs in
   `design.json`.
2. **Figma Desktop / Plugin API / local CLI adapter** when the file is open locally and REST is
   blocked or rate-limited. Record that this is not the REST Images API, the open file/page/node,
   and the local tool version. This can avoid REST rate limits but is reproducible only on machines
   with the same desktop/plugin access.
3. **REST Images API fallback** with `figma-export.sh`; treat 401/403/404/429 as blocked, not as a
   failed UI comparison.

Never confuse a Figma node id (`3:809`) with a component key. Component import, Code Connect, and
instance override checks need component keys/properties; screenshot export and node metadata need
node ids.

## Other design sources

For Sketch, Adobe XD, Penpot, Zeplin, Framer, design-token systems, prototype screenshots, PDFs/SVGs, motion specs, email previews, or exported asset packs, use the source's authoritative export/API when available. Otherwise record provenance and downgrade to T2/T3 unless the artifact is approved as the acceptance reference:

- who/what exported it and from which design file/version or token/spec version,
- frame/component name and variant/state,
- viewport, crop/framing, scroll position, scale/DPR, color profile/space, rendering method, font availability, and theme,
- whether device chrome/safe-area/browser chrome is included,
- whether the image is the approved acceptance reference.

Unproven images can support T2/T3, not strict T1.

## Design-system and code-mapping triage

Use source evidence to decide whether a visual mismatch is a product bug, a generator bug, or a
capture/setup issue:

- **Token mapping:** raw hex/rgb/px values should map to project tokens when token authority exists.
  Reverse-map raw colors/spacing/radii to variables before declaring a mismatch. If a token alias is
  missing or asymmetric, report the alias gap rather than hardcoding pixels.
- **Instances and Code Connect:** if the design node is an instance with a known component mapping,
  compare component properties, overrides, variant names, and nested instance size hints before
  replacing it with raw markup. Use raw fallback only when the design cannot be represented by the
  component API.
- **Auto layout vs absolute geometry:** preserve flow/gap/padding where the design uses auto layout
  or CSS flex/grid can represent it. Reserve absolute positioning for irregular/out-of-flow geometry
  and document why.
- **SVG/vector assets:** export or import the real vector asset. Do not redraw paths, swap to a
  similar icon, or lose stroke width/viewBox/currentColor semantics without evidence.
- **Text and truncation:** preserve source text and text-box behavior. Do not fake truncation by
  inserting literal ellipses unless the design content itself contains them.
- **Round-trip candidates:** when converting code back to design, verify with screenshot plus node
  tree plus pixel metric; an editable node tree alone is not visual fidelity.
