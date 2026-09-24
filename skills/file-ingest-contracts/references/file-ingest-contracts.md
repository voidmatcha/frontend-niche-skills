# File ingest contracts reference

Use this reference only after `file-ingest-contracts` triggers and the task involves drag-and-drop, file inputs, paste-to-upload, directory upload, or object-URL previews.

## Official references

- MDN Drag operations: any element becomes a drop target only by canceling the `dragover` event with `preventDefault()`; the `drop` event must also be canceled, or the drop is rejected and the browser handles the file itself. <https://developer.mozilla.org/en-US/docs/Web/API/HTML_Drag_and_Drop_API/Drag_operations>
- MDN `DataTransfer.dropEffect`: controls the cursor/operation feedback (`none`, `copy`, `link`, `move`); for `dragenter` and `dragover` it "will be initialized based on what action the user is requesting", so set it in every `dragover`. Use `none` to reject a spot. <https://developer.mozilla.org/en-US/docs/Web/API/DataTransfer/dropEffect>
- MDN `dragenter`/`dragleave` and File drag and drop: `dragenter` fires on entry to each element and `dragleave` on the previous one; because these fire for child elements, a naive highlight toggle flickers. MDN recommends toggling on `dragenter` (not `dragover`) to minimize redraws. <https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/dragleave_event>, <https://developer.mozilla.org/en-US/docs/Web/API/HTML_Drag_and_Drop_API/File_drag_and_drop>
- MDN `DataTransfer.items` / `DataTransferItem`: the drag data store is a list of items; each item is `string` (`getAsString`) or `file` (`getAsFile`). `DataTransfer.files` is a flat `FileList` and cannot represent directories. <https://developer.mozilla.org/en-US/docs/Web/API/DataTransferItem>
- MDN `DataTransferItem.webkitGetAsEntry()`: returns a `FileSystemFileEntry`/`FileSystemDirectoryEntry` so you can recurse into dropped folders; prefixed (MDN notes it "may be renamed to `getAsEntry()` in the future, so you should code defensively, looking for both") and only valid while the item is in read mode. Feature-detect and fall back. <https://developer.mozilla.org/en-US/docs/Web/API/DataTransferItem/webkitGetAsEntry>
- MDN `DataTransferItem.getAsFileSystemHandle()`: returns a file or directory handle for a dragged item; MDN marks it Experimental and Non-standard with limited availability, so feature-detect it and pair it with a fallback. <https://developer.mozilla.org/en-US/docs/Web/API/DataTransferItem/getAsFileSystemHandle>
- MDN `accept` attribute: filters the file picker as a hint; it does not validate the selected files and must be backed by server-side validation. <https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/accept>
- MDN `HTMLInputElement.webkitdirectory`: `<input webkitdirectory multiple>` "can only select directories instead of files", and each returned `File` has a `webkitRelativePath`. The name keeps its WebKit prefix, but MDN shows "Baseline 2025 Newly available" (checked 2026-09-25), so check older targets. <https://developer.mozilla.org/en-US/docs/Web/API/HTMLInputElement/webkitdirectory>
- OWASP File Upload Cheat Sheet: do not trust `Content-Type`/extension; validate true type (magic bytes / re-encode), enforce size limits (including post-decompression for zip/xml bombs), and treat the server as the trust boundary. <https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html>
- MDN paste event and `ClipboardEvent.clipboardData`: on `paste`, `clipboardData` is a `DataTransfer`; iterate `items`, take `kind === 'file'` (or `type` starting `image/`), and call `getAsFile()`. A paste may carry text and image both. <https://developer.mozilla.org/en-US/docs/Web/API/Element/paste_event>, <https://developer.mozilla.org/en-US/docs/Web/API/ClipboardEvent/clipboardData>
- MDN `URL.createObjectURL` / `URL.revokeObjectURL`: the create and revoke APIs. <https://developer.mozilla.org/en-US/docs/Web/API/URL/createObjectURL_static>, <https://developer.mozilla.org/en-US/docs/Web/API/URL/revokeObjectURL_static>
- MDN, Using files from web applications: "Each time you call `URL.createObjectURL()`, a unique object URL is created even if you've created an object URL for that file already. Each of these must be released. While they are released automatically when the document is unloaded, if your page uses them dynamically you should release them explicitly." It also explains not revoking right after the image loads, "because doing so would make the image unusable for user interactions (such as right-clicking to save the image or opening it in a new tab)". <https://developer.mozilla.org/en-US/docs/Web/API/File_API/Using_files_from_web_applications>

## Evidence framing

- Treat code-search hits as leads, not findings.
- For the drop contract, confirm both `dragover` and `drop` are canceled and that a drop outside the zone cannot navigate the page (window-level guard or target scope check).
- For flicker, confirm the drop zone actually has child elements and the highlight toggles on raw `dragenter`/`dragleave` without a counter.
- For directory/multiple, confirm the code reads `files` where it needs `items` + `webkitGetAsEntry`, and that `items` is read synchronously inside the handler.
- For type trust, show that `accept` or `file.type` is used as an enforcement decision (not just UX) with no server re-validation; magic-byte sniffing on the client is a pre-filter, not the boundary.
- For previews, inspect shared helpers/hooks — a call site can be safe when the helper revokes on cleanup.

## Test shapes

- Drop contract: dispatch `dragover` without `preventDefault` and assert the drop is not handled; assert a drop on a non-zone target does not navigate.
- Flicker: simulate `dragenter` parent → `dragenter` child → `dragleave` parent and assert the highlight stays on until the counter returns to 0.
- dropEffect: assert `dataTransfer.dropEffect` is set inside the `dragover` handler.
- items/directory: drop a `DataTransferItem` whose `webkitGetAsEntry()` is a directory and assert recursion yields the nested files.
- Type trust: feed a `.png`-named file whose magic bytes are not PNG and assert the pre-filter rejects it (and that the server is still the authority).
- Paste: dispatch a `paste` with `clipboardData.items` containing an image `file` and assert `getAsFile()` is read and count/size limits apply.
- Object URL: mock `createObjectURL`/`revokeObjectURL`; assert one URL per preview and revoke on replace/unmount, not on `img` load.
