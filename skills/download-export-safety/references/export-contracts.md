# Export contracts reference

Use this reference only after `download-export-safety` triggers and the task involves CSV/Excel, Blob downloads, Object URLs, or Clipboard API.

## Official references

- OWASP CSV Injection: CSV/Formula Injection occurs when untrusted input is embedded in CSV files and spreadsheet software interprets cells starting with formula characters such as `=`, `+`, `-`, or `@`. OWASP also notes separator/quote tricks, full-width (double-byte) variants such as `＝ ＋ － ＠` that "may be interpreted as formulas in some locales", and that "Microsoft Excel may remove quotes or escape characters from CSV cells when a file is saved and re-opened". <https://owasp.org/www-community/attacks/CSV_Injection>
- MDN `URL.createObjectURL()`: creates a Blob/Object URL string for a Blob/File/MediaSource. MDN says release an Object URL by calling `URL.revokeObjectURL()`. <https://developer.mozilla.org/en-US/docs/Web/API/URL/createObjectURL_static>
- MDN `URL.revokeObjectURL()`: releases an existing Object URL when it is no longer needed. <https://developer.mozilla.org/en-US/docs/Web/API/URL/revokeObjectURL_static>
- MDN `blob:` URLs: each object URL "must be released by calling `URL.revokeObjectURL()`", but "avoid freeing the object URL too early". <https://developer.mozilla.org/en-US/docs/Web/URI/Reference/Schemes/blob>
- W3C File API, blob URLs: "a revoked blob URL can't be resolved/fetched anymore", so a download started after revocation has nothing to fetch. <https://w3c.github.io/FileAPI/#url-model>
- FileSaver.js @cea522bc41bfadc364837293d0c4dc585a65ac46: dispatches the anchor click in `setTimeout(..., 0)` and revokes with `setTimeout(function () { URL.revokeObjectURL(a.href) }, 4E4) // 40s`, prior art for deferring revoke past the click handoff. <https://github.com/eligrey/FileSaver.js/blob/cea522bc41bfadc364837293d0c4dc585a65ac46/src/FileSaver.js>
- RFC 6266 defines `Content-Disposition` `filename*`, which "uses the encoding defined in [RFC5987]"; RFC 8187 "obsoletes RFC 5987" and is the current definition of that encoding. <https://www.rfc-editor.org/rfc/rfc6266.html>, <https://www.rfc-editor.org/rfc/rfc8187.html>
- MDN `<a>` `download` attribute: "`/` and `\` characters are converted to underscores (`_`)… browsers will adjust the suggested name if necessary." <https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/a>
- HTML Standard, downloading resources: the suggested filename (from `download` or `Content-Disposition`) reaches a "sanitize" step where the user agent should "Adjust filename to be suitable for the local file system… removing characters that are not legal in filenames". <https://html.spec.whatwg.org/multipage/links.html#downloading-resources>
- MDN Clipboard API: clipboard read/write is available in secure contexts and has security/user-interaction requirements. <https://developer.mozilla.org/en-US/docs/Web/API/Clipboard_API>

## Evidence framing

- Treat code search hits as **leads**, not findings.
- For CSV formula risk, show at least one exported field that can contain untrusted text and reaches a spreadsheet cell without an explicit cell policy.
- For Object URL lifecycle, inspect shared helpers. A call site can be safe when the helper revokes internally.
- For Clipboard API, check rejected-promise handling and UI state. Do not claim all unsupported browsers fail unless verified.
- For filenames, distinguish user inconvenience from privacy/security risk. A private ID in a filename is a different claim than an invalid character.

## Test shapes

- CSV: input `=1+1`, `+cmd`, `-10`, `@SUM(1,1)`, `"x\n=1+1"`, and separator-containing values produce the intended safe cell text.
- Object URL: mock `URL.createObjectURL` and `URL.revokeObjectURL`; assert revoke is called after the click path.
- Clipboard: mock `navigator.clipboard.writeText` rejection; assert error/fallback state, not success toast.
- Filename: input title with `/`, `\\`, control chars, emoji, long text, or private prefix normalizes to the expected filename.
