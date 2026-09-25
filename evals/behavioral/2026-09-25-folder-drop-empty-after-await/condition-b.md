# Condition B — with skill

## What is going on

There are two separate problems here. Only the first one causes the empty list.

### 1. The `await` makes the `DataTransfer` unreadable

`e.dataTransfer` is only readable while the `drop` event is being dispatched. Once your handler hits its first `await` (`await checkQuota()`), the function returns to the event loop and dispatch ends. The browser then puts the drag data store into "protected" or disabled mode. When the code resumes, `e.dataTransfer.items` has length 0, or its entries return `null` from `getAsFile()` and `webkitGetAsEntry()`. `e.dataTransfer.files` is empty too. So after the quota check, every drop reads as empty: folders and single files alike.

The switch from `files` to `items` was the right fix for folders. `files` is a flat `FileList` with no directory support, and only `items` → `webkitGetAsEntry()` can walk into a dropped directory. It worked in local testing because nothing awaited before the loop. The quota check broke it because it runs *before* the capture.

One more thing to watch for: the directory walk itself is async (`DirectoryReader.readEntries()` and `FileEntry.file()` use callbacks). That part is fine *as long as* you have already collected the `FileSystemEntry` objects synchronously. Entries stay usable after the event ends. The `DataTransfer` and its items do not.

### 2. `accept="image/*"` will not refuse dropped files

`accept` only filters the OS file picker, and MDN is explicit that it does not validate. Files dropped onto your own drop zone go through your `drop` handler and never touch the input's `accept`. So the plan would not do what product wants. Also, even in the picker, users can switch the dialog to "All files". `file.type` is not a real gate either. It is guessed from the file extension, can be spoofed by renaming, and is often an empty string.

## Smallest safe fix

### Fix 1: capture synchronously, then await

Read everything you need from `dataTransfer` before the first `await`, then do the quota check and the async directory walk:

```js
zone.addEventListener('drop', async (e) => {
  e.preventDefault();

  // Synchronous capture — must happen before any await.
  const entries = [];
  const looseFiles = [];
  for (const item of e.dataTransfer.items) {
    if (item.kind !== 'file') continue;
    const entry = item.webkitGetAsEntry?.() ?? item.getAsEntry?.();
    if (entry) entries.push(entry);
    else {
      const f = item.getAsFile();
      if (f) looseFiles.push(f);
    }
  }

  // Now it is safe to go async.
  if (!(await checkQuota())) return;
  const files = [...looseFiles, ...(await walkEntries(entries))];
  handleFiles(files);
});
```

`walkEntries` recurses through `DirectoryEntry.createReader().readEntries()`. Call `readEntries` repeatedly until it returns an empty batch, because Chromium returns at most about 100 entries per call. For file entries, turn each one into a `File` with `entry.file()`.

If you'd rather keep the order "check quota first", you can't do it for the same drop. The check has to come after capture. Capture is cheap and has no side effects, so doing it first costs nothing.

Keep the existing `dragover` `preventDefault()`, or `drop` will not fire at all. If you don't already have one, a window-level `dragover`/`drop` `preventDefault` stops a near-miss drop from making the browser open the file and navigate away from the page.

### Fix 2: enforce "images only" in code, and on the server

- Keep `accept="image/*"` on the input as a **UX hint** for the picker. It is harmless and helpful, but it is not the gate.
- In the shared `handleFiles` path, which both picker and drop feed into, filter the files. A fast pre-check on `file.type.startsWith('image/')` gives users quick feedback. For a sturdier client-side check, sniff magic bytes (`await file.slice(0, 12).arrayBuffer()`, then compare against PNG/JPEG/GIF/WebP signatures) and reject files that don't match, with a visible message.
- **Re-validate on the server.** That is the actual trust boundary. Client checks, including magic-byte sniffing, are only a pre-filter and can be bypassed (header-only sniffing is also defeated by polyglot files). If "images only" is a security or policy requirement, not just a UX one, the server check is the one that counts. If SVG counts as an "image" for you, rendering it is its own risk (active content), so decide explicitly whether to allow it.
- For a clearer drag UX, you can set `e.dataTransfer.dropEffect = 'none'` in `dragover` when `items` show non-image types. Treat this as a hint only: during `dragover` you can read item `kind`/`type` but not file contents, and folders show no useful type.

## Verification

- **Regression test for Fix 1:** a DOM/unit test that dispatches a `drop` whose `dataTransfer` becomes empty after a microtask, with a mocked `checkQuota` that resolves asynchronously. Assert that the captured files still reach `handleFiles`. The failing version (await before capture) should produce an empty list.
- **Manual checks:** in Chromium, Firefox, and Safari, drop (a) one file, (b) several files, (c) a folder with nested subfolders and more than 100 entries, each with the quota check in place, and confirm the full list appears.
- **Fix 2:** drop a `.txt` file, a `.txt` renamed to `.png`, and a real PNG. The first two are rejected on the client, and the renamed one is also rejected by the server when uploaded directly with the client check bypassed.
