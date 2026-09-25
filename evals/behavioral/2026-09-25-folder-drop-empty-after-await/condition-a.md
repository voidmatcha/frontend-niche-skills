# Condition A — without skill

## What is going on

There are two separate problems here.

### 1. The `await` makes the drop data unreadable

A `DataTransfer` can only be read while the `drop` event is being dispatched. Per the HTML drag-and-drop model, the drag data store is in *read-only* mode during `drop` and switches to *protected* mode once the handler returns. In protected mode, `dataTransfer.items` reports length 0, `dataTransfer.files` is empty, and `item.webkitGetAsEntry()` / `item.getAsFile()` return `null`.

An `await` ends the synchronous part of the handler. Everything after `await checkQuota()` runs in a later microtask, after dispatch has finished, so the loop over `e.dataTransfer.items` finds nothing. That explains why every drop is empty now, folders and single files alike. Local testing looked fine earlier only because nothing was awaited before the items were read.

Related points:

- Iterating `items` is the right idea for folders, because `files` does not recurse into directories. But the folder part only works through `item.webkitGetAsEntry()` (or `getAsFileSystemHandle()` where it exists) plus walking the directory. `getAsFile()` on a directory item gives you nothing useful.
- You have to grab those entry objects synchronously. Once you hold a `FileSystemEntry`, you can walk it asynchronously as long as you like. It is only the `DataTransfer` itself that goes dead.
- `FileSystemDirectoryReader.readEntries()` returns results in batches (Chromium caps each batch at around 100 entries). Call it repeatedly until it returns an empty array, or large folders will silently lose files.
- Skip items whose `kind !== 'file'`. Drags from other pages or apps can carry string items as well.
- `e.preventDefault()` in `dragover` and `drop` must also run synchronously, before any `await`. Otherwise the browser may open the file instead.

### 2. `accept="image/*"` will not restrict drops

`accept` is a hint to the native file picker. It narrows what the OS dialog shows (and the user can often switch to "All files" anyway). It has no effect on files that reach your own `drop` handler on a custom drop zone, and it is not enforced when files are dropped onto or assigned to the input. So the plan would not refuse non-image drops. It isn't a security boundary either way.

## Smallest safe fix

Read the `DataTransfer` synchronously first, then `await`:

```js
async function onDrop(e) {
  e.preventDefault();

  // 1. Synchronous snapshot, before any await.
  const entries = [];
  const looseFiles = [];
  for (const item of e.dataTransfer.items) {
    if (item.kind !== 'file') continue;
    const entry = item.webkitGetAsEntry?.();
    if (entry) entries.push(entry);
    else {
      const f = item.getAsFile();
      if (f) looseFiles.push(f);
    }
  }

  // 2. Now it is safe to await.
  const ok = await checkQuota();
  if (!ok) return;

  // 3. Walk the captured entries asynchronously.
  const files = [...looseFiles];
  for (const entry of entries) files.push(...(await collect(entry)));

  // 4. Apply the image-only rule in code.
  const images = files.filter(isImage);
  const rejected = files.length - images.length;
  handleFiles(images, { rejected });
}

function collect(entry) {
  if (entry.isFile) {
    return new Promise((res, rej) => entry.file(f => res([f]), rej));
  }
  if (entry.isDirectory) {
    const reader = entry.createReader();
    return (async () => {
      const out = [];
      for (;;) {
        const batch = await new Promise((res, rej) => reader.readEntries(res, rej));
        if (batch.length === 0) break; // readEntries is batched; loop until empty
        for (const child of batch) out.push(...(await collect(child)));
      }
      return out;
    })();
  }
  return Promise.resolve([]);
}

const IMAGE_EXT = /\.(png|jpe?g|gif|webp|avif|bmp|svg|heic|heif)$/i;
function isImage(file) {
  // file.type can be empty (e.g. for files from folders, or unknown types), so fall back to the extension.
  return file.type ? file.type.startsWith('image/') : IMAGE_EXT.test(file.name);
}
```

For the image-only requirement:

- Keep `accept="image/*"` on the input for a better picker experience, but know that it only filters the picker.
- Put the same `isImage` filter on both the picker path and the drop path, and tell the user which files were skipped instead of dropping them without a word.
- Enforce the rule on the server by checking the actual content (magic bytes / decoding the image), not the client-reported MIME type or extension. Client-side filtering is a UX nicety and can be bypassed. Decide on purpose whether SVG counts as an allowed "image", since it can carry script if you serve it back inline.

## Checks before shipping

- Drop a single file, several files, a folder, a nested folder, and a folder with more than 100 files, with the quota check in place.
- Drop a mixed folder (images plus other files) and confirm only images are queued and the rejected count is shown.
- Test in Chromium, Firefox, and Safari. Entry APIs are widely supported but carry the `webkit` prefix, so keep the `getAsFile()` fallback.
- Add a regression test or a code comment explaining that nothing may be awaited before the `DataTransfer` snapshot, so the next "just add a check at the top" change doesn't bring the bug back.
