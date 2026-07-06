#!/usr/bin/env node
// figma-spacing.mjs — extract Figma layout measurements from node JSON so a
// design-to-code review can compare margin/padding/gap *values*, not just pixels.
//
//   Usage:  node figma-spacing.mjs <file-key> <node-id[,node-id,...]> [depth=8]
//           node-id accepts URL form (3-809) or API form (3:809); both normalize.
//   Token:  FIGMA_TOKEN, else FIGMA_API_KEY (never inline a token on argv).
//   Stdout: an indented node tree; per node — bounding box, auto-layout mode,
//           padding (T,R,B,L), item gap, alignment, STROKES (border/divider: weight
//           or per-edge weights + align + color), TEXT TYPOGRAPHY (font size,
//           line-height, weight), icon/instance size, and the computed gap between
//           each pair of consecutive children (recovered from bounding boxes when
//           the frame is NOT auto-layout). Strokes matter: a 1px row/cell border is
//           a divider that a fuzzed/eroded pixel diff cannot see.
//
// Why this complements the pixel diff: figma-export.sh returns a rendered PNG
// (source of truth for color/paint, ideal for an AE diff) but carries NO layout
// numbers. The /v1/files/:key/nodes endpoint returns auto-layout `paddingLeft/Right/
// Top/Bottom`, `itemSpacing`, and `absoluteBoundingBox` — from those the exact
// spacing is recoverable. Use this when a pixel diff says "spacing drifted here"
// and you need the actual px target to fix the CSS gap/padding/margin precisely.
//
// Caveats honored: a frame with `layoutMode: NONE` has no itemSpacing — gaps are
// then derived from children bounding boxes (axis inferred from the larger spread).
// Figma auto-layout padding/itemSpacing are in design px at scale 1; multiply by your deviceScaleFactor
// only when comparing against a 2x screenshot's raw pixels (CSS px already match 1x).

const [, , FILE_KEY, NODES_RAW, DEPTH_RAW] = process.argv;
const TOKEN = process.env.FIGMA_TOKEN || process.env.FIGMA_API_KEY;

if (!FILE_KEY || !NODES_RAW) {
  console.error('Usage: node figma-spacing.mjs <file-key> <node-ids> [depth]');
  process.exit(2);
}
if (!TOKEN) {
  console.error('ERROR: set FIGMA_TOKEN or FIGMA_API_KEY (never inline a token)');
  process.exit(2);
}
if (typeof fetch !== 'function') {
  console.error('ERROR: global fetch unavailable — run with Node 18+');
  process.exit(2);
}

const DEPTH = DEPTH_RAW == null ? '8' : String(DEPTH_RAW);
if (!/^\d+$/.test(DEPTH)) {
  console.error(`ERROR: depth must be a non-negative integer (got "${DEPTH_RAW}")`);
  process.exit(2);
}
const REQUESTED_IDS = NODES_RAW.split(',')
  .map((s) => s.trim())
  .filter(Boolean)
  .map((s) => s.replace(/-/g, ':'));
const IDS = REQUESTED_IDS.join(',');
const url = `https://api.figma.com/v1/files/${FILE_KEY}/nodes`
  + `?ids=${encodeURIComponent(IDS)}&depth=${encodeURIComponent(DEPTH)}`;

let res;
try {
  res = await fetch(url, { headers: { 'X-Figma-Token': TOKEN } });
} catch (err) {
  console.error(`ERROR: Figma API request failed: ${err?.message || err}`);
  process.exit(2);
}
if (!res.ok) {
  console.error(`ERROR: Figma API ${res.status} ${res.statusText} (check token / file-key / node-id)`);
  process.exit(2);
}
let data;
try {
  data = await res.json();
} catch (err) {
  console.error(`ERROR: failed to parse Figma API JSON: ${err?.message || err}`);
  process.exit(2);
}
if (data.err) {
  console.error('ERROR: figma nodes api:', data.err);
  process.exit(2);
}

const r2 = (n) => (typeof n === 'number' ? Math.round(n * 100) / 100 : n);

const bboxStr = (n) => (n.absoluteBoundingBox
  ? `(${r2(n.absoluteBoundingBox.x)},${r2(n.absoluteBoundingBox.y)} ${r2(n.absoluteBoundingBox.width)}x${r2(n.absoluteBoundingBox.height)})`
  : '(no-bbox)');

function padStr(n) {
  const p = [n.paddingTop, n.paddingRight, n.paddingBottom, n.paddingLeft];
  if (p.every((v) => v == null)) return '';
  return ` pad(T,R,B,L)=${p.map((v) => (v == null ? 0 : r2(v))).join(',')}`;
}

function layoutStr(n) {
  if (!n.layoutMode || n.layoutMode === 'NONE') return '';
  const gap = n.itemSpacing != null ? ` gap=${r2(n.itemSpacing)}` : '';
  const main = n.primaryAxisAlignItems ? ` main=${n.primaryAxisAlignItems}` : '';
  const cross = n.counterAxisAlignItems ? ` cross=${n.counterAxisAlignItems}` : '';
  return ` layout=${n.layoutMode}${gap}${main}${cross}`;
}

function rgba(c, opacity) {
  if (!c) return '';
  const to255 = (v) => Math.round((v || 0) * 255);
  const a = opacity != null ? opacity : (c.a != null ? c.a : 1);
  return `rgba(${to255(c.r)},${to255(c.g)},${to255(c.b)},${r2(a)})`;
}

// Borders & DIVIDERS live in `strokes` (NOT fills) — and a 1px stroke repeated on
// row/cell frames is a divider line that a fuzzed/eroded pixel diff WILL MISS. So
// surface it quantitatively here. `individualStrokeWeights` pins which edge carries
// it (e.g. bottom-only = a row divider); `strokeAlign` affects whether it adds size.
function strokeStr(n) {
  const ss = (n.strokes || []).filter((s) => s.visible !== false);
  if (!ss.length) return '';
  const isw = n.individualStrokeWeights;
  const weight = isw
    ? `T,R,B,L=${[isw.top, isw.right, isw.bottom, isw.left].map((v) => r2(v ?? 0)).join(',')}`
    : `${r2(n.strokeWeight ?? 0)}px`;
  const align = n.strokeAlign ? `/${n.strokeAlign}` : '';
  const solid = ss.find((s) => s.type === 'SOLID' && s.color);
  const color = solid ? rgba(solid.color, solid.opacity) : ss.map((s) => s.type).join(',');
  return ` stroke=${weight}${align}(${color})`;
}

function lineHeightStr(style) {
  // Figma REST lineHeightUnit enum: PIXELS | FONT_SIZE_% | INTRINSIC_% (INTRINSIC_% = auto).
  const unit = style?.lineHeightUnit;
  if (unit === 'PIXELS' && style.lineHeightPx != null) return `${r2(style.lineHeightPx)}px`;
  if (unit === 'FONT_SIZE_%' && style.lineHeightPercentFontSize != null) {
    return `${r2(style.lineHeightPercentFontSize)}%`;
  }
  if (unit === 'INTRINSIC_%') return 'auto';
  if (style?.lineHeightPx != null) return `${r2(style.lineHeightPx)}px`;
  if (style?.lineHeightPercentFontSize != null) return `${r2(style.lineHeightPercentFontSize)}%`;
  return 'auto';
}

function fontStr(n) {
  if (n.type !== 'TEXT' || !n.style) return '';
  const size = n.style.fontSize != null ? r2(n.style.fontSize) : '?';
  const lineHeight = lineHeightStr(n.style);
  const weight = n.style.fontWeight != null ? r2(n.style.fontWeight) : '?';
  return ` font=${size}/${lineHeight}/${weight}`;
}

function sizeStr(n) {
  if (!n.absoluteBoundingBox) return '';
  const iconLikeType = ['INSTANCE', 'VECTOR', 'BOOLEAN_OPERATION'].includes(n.type);
  const iconLikeName = /(^|[\s/_-])(icon|ic|logo|glyph|symbol|badge|check|plus|minus|arrow|chevron)([\s/_-]|$)/i.test(n.name || '')
    && Math.max(n.absoluteBoundingBox.width, n.absoluteBoundingBox.height) <= 64;
  if (!iconLikeType && !iconLikeName) return '';
  return ` size=${r2(n.absoluteBoundingBox.width)}x${r2(n.absoluteBoundingBox.height)}`;
}

// Gaps between consecutive children. Auto-layout already reports itemSpacing, so
// only derive from bounding boxes when the frame is not auto-layout.
function childGaps(n) {
  if (n.layoutMode && n.layoutMode !== 'NONE') return [];
  const kids = (n.children || []).filter((c) => c.absoluteBoundingBox);
  if (kids.length < 2) return [];
  const xs = kids.map((c) => c.absoluteBoundingBox.x);
  const ys = kids.map((c) => c.absoluteBoundingBox.y);
  const vertical = (Math.max(...ys) - Math.min(...ys)) >= (Math.max(...xs) - Math.min(...xs));
  const sorted = [...kids].sort((a, b) => (vertical
    ? a.absoluteBoundingBox.y - b.absoluteBoundingBox.y
    : a.absoluteBoundingBox.x - b.absoluteBoundingBox.x));
  const gaps = [];
  for (let i = 1; i < sorted.length; i += 1) {
    const prev = sorted[i - 1].absoluteBoundingBox;
    const cur = sorted[i].absoluteBoundingBox;
    const g = vertical ? cur.y - (prev.y + prev.height) : cur.x - (prev.x + prev.width);
    gaps.push(`${sorted[i - 1].name} → ${sorted[i].name}: ${r2(g)}px (${vertical ? 'vertical' : 'horizontal'})`);
  }
  return gaps;
}

function walk(n, indent = '') {
  console.log(`${indent}${n.name} [${n.type}] ${bboxStr(n)}${layoutStr(n)}${padStr(n)}${strokeStr(n)}${fontStr(n)}${sizeStr(n)}`);
  for (const g of childGaps(n)) console.log(`${indent}  ↕ heuristic derived gap ${g}`);
  if (n.children) for (const c of n.children) walk(c, `${indent}  `);
}

const nodes = data.nodes || {};
if (!Object.keys(nodes).length) {
  console.error('ERROR: no nodes returned (check node-id / file access)');
  process.exit(2);
}
const missing = REQUESTED_IDS.filter((id) => !(id in nodes));
const nullish = REQUESTED_IDS.filter((id) => id in nodes && (!nodes[id] || !nodes[id].document));
if (missing.length || nullish.length) {
  console.error('ERROR: requested Figma nodes unavailable; treat as T4 blocked/not validated, not a failed spacing audit.');
  if (missing.length) console.error(`  missing nodes: ${missing.join(',')}`);
  if (nullish.length) console.error(`  null/unrenderable nodes: ${nullish.join(',')}`);
  process.exit(2);
}
const entries = REQUESTED_IDS.map((id) => [id, nodes[id]]);
if (!entries.length) {
  console.error('ERROR: no node ids requested (check node-id argument)');
  process.exit(2);
}
console.log('NOTE: auto-layout padding/itemSpacing and node bounds are direct Figma values; sibling gaps for layoutMode=NONE are heuristic and can be misleading for grids, overlays, hidden layers, or wrapped layouts.');

for (const [id, entry] of entries) {
  // missing/nullish entries already exited above as T4 blocked; entry.document is guaranteed here.
  console.log(`\n=== node ${id} ===`);
  walk(entry.document);
}
