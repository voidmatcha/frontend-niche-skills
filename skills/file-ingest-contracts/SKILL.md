---
name: file-ingest-contracts
description: "Use when bringing files INTO the page and the browser ingest path misbehaves: a drop-zone highlight flickering as the pointer crosses child elements (dragenter/leave counter), a dropped file that opens in the browser or navigates the page away instead of uploading (missing dragover preventDefault), a drop that never fires, a dropped folder yielding no files, files passing the picker with the wrong true type (accept attribute or file.type trusted over magic bytes), broken paste-image-from-clipboard, or preview thumbnails leaking memory from unrevoked object URLs. Covers DataTransfer.items vs files, dropEffect, directory/multiple upload, and object-URL lifecycle. Browser ingest/IN scope; server upload proxy budgets and multipart relay see bff-proxy-security-contracts, active SVG/HTML rendering risk see frontend-security-baseline, export/OUT see download-export-safety."
---

# File ingest contracts

Getting a file into the page is a chain of browser contracts: cancel the right drag events, read from the right DataTransfer surface, distrust the file's self-reported type, and revoke every preview URL you mint. Each link passes a happy-path demo and fails only with nested drop zones, dropped folders, spoofed types, clipboard pastes, or long sessions.

## Checklist (lead with the trap; test shapes and evidence framing in references/)

→ [file-ingest-contracts](./references/file-ingest-contracts.md)

1. **Cancel dragover or the drop never fires — and guard the window.** The default `dropEffect` on `dragover` is `none`, which blocks the drop, so you must `preventDefault()` on `dragover` (and `dragenter`) to make the element a drop target, then `preventDefault()` again in `drop`. Miss it and a file dropped on (or near) the zone makes the browser navigate to / open the file and throw away the page. Add a window-level `dragover`+`drop` `preventDefault` (or scope-check the target) so a near-miss can't blow away unsaved state.
2. **Toggle the highlight on a dragenter/dragleave counter, not raw events.** `dragenter` fires on every child element and `dragleave` fires when the pointer crosses from the parent into a child, so a naive add/remove-class flickers over nested content. Keep an integer: `++` on `dragenter`, `--` on `dragleave`, add the highlight when it reaches 1, clear when it returns to 0. Toggle on `dragenter`, not `dragover` (`dragover` refires every few hundred ms and forces needless repaints).
3. **Re-set dropEffect on every dragover.** `dropEffect` describes the desired effect for that one dispatch and reverts next tick; set `dataTransfer.dropEffect = 'copy'` inside the `dragover` handler each time or the cursor won't reflect the operation. Use `dropEffect = 'none'` to visibly reject a spot.
4. **Read folders through items + webkitGetAsEntry, not files.** `DataTransfer.files` is a flat `FileList` with no directory support; only `DataTransfer.items` → `DataTransferItem.webkitGetAsEntry()` (or `getAsFileSystemHandle()`) can recurse into a dropped directory, and both are non-standard — feature-detect (`'getAsFileSystemHandle' in DataTransferItem.prototype`) and fall back. `items` is only live inside the `drop`/`dragstart` handler, so capture entries synchronously before any `await`. For click-to-select folders use `<input webkitdirectory multiple>`; it can't also pick loose files and shows a browser trust prompt.
5. **Treat accept and file.type as UX hints, never a type gate.** `accept` only filters the OS picker (MDN is explicit: it does not validate) and drag-drop/paste bypass it entirely. `file.type` is guessed from the extension, is spoofable, and is often an empty string. For a real check, sniff magic bytes client-side (`Blob.slice(0, N)` → `arrayBuffer`/`FileReader` → compare the signature) as a fast pre-filter, and re-validate on the server — that is the trust boundary. Header-only sniffing is still defeated by polyglots. Route active SVG/HTML rendering risk to `frontend-security-baseline`; route frontend-owned server upload limits, multipart reconstruction, and relay policy to `bff-proxy-security-contracts`.
6. **Extract pasted images from clipboardData.items and bound count/size.** On the `paste` event, iterate `event.clipboardData.items`, take entries where `kind === 'file'` (or `type` starts with `image/`), and call `getAsFile()`. A single paste can carry both text and an image, so decide precedence rather than assuming one. Enforce `files.length` and `file.size` limits before you read — `accept`/`multiple` do not bound how many or how large.
7. **One object URL per preview, and revoke it.** `URL.createObjectURL` mints a new blob URL every call and pins the blob in memory until `URL.revokeObjectURL`; re-creating one per render leaks. Revoke when the preview is replaced and on unmount (React: `useEffect` cleanup) — but not inside the `img` `onload` handler, which breaks right-click / open-in-new-tab. The browser only frees these on document unload, so long single-page sessions accumulate them.

## Quick probes

Use as leads; confirm the source-to-sink path before filing.

```sh
rg -n "dragover|dragenter|dragleave|onDrop|dataTransfer" src/ app/ 2>/dev/null
rg -n "\.files\b|\.items\b|webkitGetAsEntry|getAsFileSystemHandle|webkitdirectory" src/ app/ 2>/dev/null
rg -n "accept=|\.type\b|magic|signature|FileReader|arrayBuffer\(" src/ app/ 2>/dev/null
rg -n "createObjectURL|revokeObjectURL|clipboardData|onPaste|'paste'" src/ app/ 2>/dev/null
```

## Boundary with sibling skills

- Use **file-ingest-contracts** for the IN path: the drag-drop event contract, `DataTransfer` items/files, directory/multiple, paste-image, and object-URL lifecycle for previews.
- Use **download-export-safety** for the OUT path — generating downloads, Blob/anchor saves, clipboard writes, and export filenames. (`createObjectURL` appears in both: ingest previews here, export downloads there.)
- Use **frontend-security-baseline** when untrusted SVG/HTML is rendered as active browser content.
- Use **bff-proxy-security-contracts** when a frontend-owned server route parses or relays uploads and must bound files, fields, aggregate bytes, headers, redirects, or multipart reconstruction. Magic-byte sniffing on the client is only a pre-filter.
- Use **i18n-copy-and-layout** for displaying the ingested filename: truncation, bidi/RTL in names, and expansion.

## PR-worthiness gate

File an ingest finding only when all hold:

1. A real ingest surface exists (drop zone, file input, or paste target) that users reach.
2. A specific contract is violated with a user-visible effect: highlight flicker over children, a drop that opens the file / navigates away, a folder drop that silently drops files, a type gate that trusts `accept`/`file.type`, broken paste, or a preview that leaks or goes stale.
3. Current code has no guard or test for it.
4. The fix is narrow: one drop handler, one counter, one `dropEffect` line, one items/`webkitGetAsEntry` switch, one magic-byte pre-check, or one revoke/cleanup.

Reject weak findings:

- A drop zone with no child elements does not need the counter.
- `createObjectURL` with a matching revoke on cleanup is a positive control, not a leak.
- Missing magic-byte sniffing is not client-side "insecurity" by itself — the server is the trust boundary; file it as UX/robustness or route real content risk to frontend-security-baseline.
- `accept` without server validation is a note, not a client bug, unless the client code claims the type is now trusted.

Minimal useful PR: one failing check — e.g. a drop over a nested child keeps the highlight stable (counter), or a preview URL is revoked on replace/unmount.

## Output shape

Return compact findings:

- **Ingest contract**: drag-event cancel/counter / dropEffect / items-vs-files / type-trust / paste / object-URL lifecycle.
- **Evidence**: file/line and the ingest-to-sink path.
- **Risk**: lost page state, flicker, dropped files, wrong-type acceptance, broken paste, retained blob memory / stale preview.
- **Fix**: smallest handler, counter, feature-detect, pre-check, or revoke.
- **Verification**: unit/DOM test or manual drop/paste/preview check that would catch the regression.

## Sources

- MDN, Drag operations — canceling `dragover` makes a drop target; `drop` must also be canceled: <https://developer.mozilla.org/en-US/docs/Web/API/HTML_Drag_and_Drop_API/Drag_operations>
- MDN, DataTransfer.dropEffect — set it per `dragover`; `none` rejects a spot: <https://developer.mozilla.org/en-US/docs/Web/API/DataTransfer/dropEffect>
- MDN, dragleave event and File drag and drop — child-element event noise and file-drop reading: <https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/dragleave_event>, <https://developer.mozilla.org/en-US/docs/Web/API/HTML_Drag_and_Drop_API/File_drag_and_drop>
- MDN, DataTransferItem.webkitGetAsEntry — directories via `items`; non-standard: <https://developer.mozilla.org/en-US/docs/Web/API/DataTransferItem/webkitGetAsEntry>
- web.dev, Drag and drop directories — feature-detect `getAsFileSystemHandle`/`webkitGetAsEntry`: <https://web.dev/patterns/files/drag-and-drop-directories>
- MDN, accept attribute — a hint for the picker, not validation; back with server-side checks: <https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/accept>
- OWASP File Upload Cheat Sheet — do not trust `Content-Type`; validate type/size server-side: <https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html>
- MDN, Element paste event and ClipboardEvent.clipboardData — `clipboardData.items` → `getAsFile()`: <https://developer.mozilla.org/en-US/docs/Web/API/Element/paste_event>, <https://developer.mozilla.org/en-US/docs/Web/API/ClipboardEvent/clipboardData>
- MDN, URL.createObjectURL and URL.revokeObjectURL — revoke to release; don't revoke too early: <https://developer.mozilla.org/en-US/docs/Web/API/URL/createObjectURL_static>, <https://developer.mozilla.org/en-US/docs/Web/API/URL/revokeObjectURL_static>
