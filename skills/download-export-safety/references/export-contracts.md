# Export contracts reference

Use this reference only after `download-export-safety` triggers and the task involves CSV/Excel, Blob downloads, Object URLs, or Clipboard API.

## Official references

- OWASP CSV Injection: CSV/Formula Injection occurs when untrusted input is embedded in CSV files and spreadsheet software interprets cells starting with formula characters such as `=`, `+`, `-`, or `@`. OWASP also notes separator/quote tricks and Excel behavior can affect mitigations. <https://owasp.org/www-community/attacks/CSV_Injection>
- MDN `URL.createObjectURL()`: creates a Blob/Object URL string for a Blob/File/MediaSource. MDN says release an Object URL by calling `URL.revokeObjectURL()`. <https://developer.mozilla.org/en-US/docs/Web/API/URL/createObjectURL_static>
- MDN `URL.revokeObjectURL()`: releases an existing Object URL when it is no longer needed. <https://developer.mozilla.org/en-US/docs/Web/API/URL/revokeObjectURL_static>
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
