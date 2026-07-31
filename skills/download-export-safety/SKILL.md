---
name: download-export-safety
description: "Use when reviewing or implementing client-side export/copy flows: CSV/Excel downloads, JSON/text/blob file downloads, URL.createObjectURL lifecycle, navigator.clipboard writes, generated filenames, and user-controlled spreadsheet cells. Export/download scope; keep this primary for observed payload leakage, stale fallback content, or success-before-settlement even when gesture timing is also suspect. Use user-activation-contracts when the gated call itself fails because activation is inactive or consumed, frontend-security-baseline for broad XSS/token/CSP issues, payment-page-client-security for payment card data, and datetime-correctness for timezone semantics in exported values."
---

# Download export safety

Use this skill for browser-owned export surfaces where data leaves the app through a file download or clipboard write. The goal is not a broad security audit; it is to make export behavior reviewable, recoverable, and safe around spreadsheet interpretation, Blob URL lifetime, clipboard permission failures, and generated filenames.

## Boundary with sibling skills

- Use **download-export-safety** for CSV/Excel formula risk, generated Blob/Object URLs, anchor downloads, clipboard copy/share, export filenames, and export-specific regression tests.
- Use **frontend-security-baseline** for raw HTML sinks, CSP, token storage, opener leaks, redirects, and generic browser security traps.
- Use **payment-page-client-security** when exported/copied data includes PAN/CVV or payment-page evidence.
- Use **datetime-correctness** when export values or filenames depend on timezone, DST, or date-only parsing.
- Use **i18n-copy-and-layout** for localized copy around export UI labels/messages.
- Use **user-activation-contracts** when the defect is that a gesture-gated
  clipboard or file-picker call runs after activation expires or another API
  consumes it. This skill still owns the outbound payload, rejected-call UI,
  fallback result, and file/Blob lifecycle.

## Review workflow

1. **Classify the export path** — CSV/Excel, JSON/YAML, image/canvas, zip/blob, clipboard text, clipboard rich content, Web Share, or server-generated attachment.
2. **Identify data ownership** — user-provided fields, imported third-party data, admin-entered metadata, logs, generated IDs, private tokens, and PII. Treat spreadsheet cells from users or integrations as untrusted.
3. **Check CSV/Excel interpretation** — inspect whether any cell can begin with `=`, `+`, `-`, `@`, tab, carriage return, line feed, or separator/quote tricks that start a new cell. Do not call a finding exploitable without showing the exported cell path.
4. **Check Blob/Object URL lifecycle** — each `URL.createObjectURL(blob)` should have a matching `URL.revokeObjectURL(url)` after the download is triggered. Do not revoke before the browser can start the download.
5. **Check clipboard rejection and fallback** — catch failures, provide visible
   feedback or a legacy fallback where project policy requires it, and avoid
   silent success UI. If the call itself is delayed beyond transient activation
   or follows another consuming API, route that timing defect to
   `user-activation-contracts`.
6. **Check filenames and metadata** — avoid path separators, surprising timezone/date shifts, private identifiers in filenames, and user-controlled filenames without normalization.
7. **Add narrow verification** — unit test CSV escaping, Object URL revoke, clipboard rejection/fallback, or export filename shape. Browser smoke tests are useful when the defect depends on download timing.

## Defect patterns

| Pattern | Why it matters | Better direction |
| --- | --- | --- |
| CSV built from user strings without spreadsheet-cell policy | Spreadsheet apps can interpret leading formula characters as formulas. | Escape/prefix cells according to the project spreadsheet target; document trade-offs. |
| Sanitizer only checks first character before CSV quoting/splitting | Separators or newlines can create a new cell that starts with a formula character. | Sanitize after cell boundaries are known, before serializing each final field. |
| `URL.createObjectURL` without revoke | Repeated large exports can retain Blob memory for the page lifetime. | Revoke after click/navigation handoff; add a test that revoke is called. |
| Revoke immediately before click completes | Some browsers may not start the download reliably. | Trigger click first, then revoke in a safe post-click path. |
| Clipboard write errors ignored while UI says copied | Permission, policy, activation, or platform differences can turn into false success. | Catch rejection, show failure/fallback, and test the rejected promise path; route activation timing separately. |
| Export filename uses unsanitized user title | For a client `a[download]`, browsers sanitize path separators/control chars in the download filename, so the real residual risks are private labels/PII in the name and server-set `Content-Disposition` filenames that skip sanitization. | Strip PII, use neutral date/id suffixes, and sanitize any server-side `Content-Disposition` filename (path separators, control chars, RFC 5987 encoding). |
| Export includes private values because UI filtered them visually | Downloads can expose hidden columns, tokens, notes, or raw server values. | Define an explicit export schema separate from visible table state. |

## Quick probes

Use probes as leads, then inspect the source-to-export path:

```sh
rg -n 'text/csv|application/vnd|toCSV|CSV|json2csv|Papa|downloadAsCsv|saveAs\(' src/ app/ packages/ 2>/dev/null
rg -n 'URL\.createObjectURL|createObjectURL\(|revokeObjectURL|new Blob\(|a\.download|download\s*=' src/ app/ packages/ 2>/dev/null
rg -n 'navigator\.clipboard|ClipboardItem|writeText\(|write\(' src/ app/ packages/ 2>/dev/null
rg -n 'export|download|clipboard|copy' src/ app/ packages/ 2>/dev/null | rg -i 'token|secret|password|email|phone|address|card|cvv|pan'
```

## PR-worthiness gate

Count an export finding only when all are true:

1. A user-visible download/copy path exists.
2. Data can be user-controlled, large, permission-gated, or sensitive enough for a specific risk.
3. Current code lacks an explicit project policy or regression check for that risk.
4. The proposed fix is narrow: one exporter/helper, one cell policy, one revoke/fallback test, or one filename normalization helper.

Reject weak findings:

- JSON export is not CSV formula injection by itself.
- `createObjectURL` with a nearby revoke is usually a positive-control example, not a defect.
- Clipboard API use is not wrong by itself. This skill needs an unsafe payload,
  unhandled rejection, incorrect fallback, or false-success UI; delayed or
  consumed activation belongs to `user-activation-contracts`.
- FileSaver or provider utilities may already own Object URL cleanup; inspect helper code before claiming a leak.

## References

Read [export-contracts](./references/export-contracts.md) for official references and evidence framing.

## Output shape

Return compact findings:

- **Export contract**: CSV cell policy / Blob URL lifecycle / clipboard fallback / filename/schema.
- **Evidence**: file/line and exported data path.
- **Risk**: spreadsheet interpretation, retained Blob memory, false copied state, sensitive filename/data exposure.
- **Fix**: smallest helper or call-site change.
- **Verification**: unit/browser test or manual export check that would catch regression.
