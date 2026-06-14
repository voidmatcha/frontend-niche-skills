# XSS & sanitization

XSS is solved by **where you put data**, not by how hard you scrub it. The recurring
expensive mistake is reaching for an encoder or a sanitizer to make a dangerous
operation safe, when choosing a safe operation removes the danger entirely.

## Safe sinks beat encoding

- **Assign untrusted data to a text sink** — `element.textContent`, `.value`,
  `insertAdjacentText`, `createTextNode` — not `innerHTML`/`outerHTML`/`document.write`.
  A text sink is structurally inert: the browser never parses the string as markup, so
  there is nothing to encode and nothing to get wrong.
- The frequent error is "escape your output", so a value gets HTML-encoded and then piped
  into `innerHTML` anyway — fragile, and one missed context reopens the hole. **Refactor
  to the right sink instead of encoding into the wrong one.** OWASP: *"The best way to fix
  DOM based cross-site scripting is to use the right output method (sink)… don't use
  `innerHtml`, instead use `innerText` or `textContent`. This will solve the problem."*

## Encode for the exact context

When you genuinely must build markup, **output-encode for the precise context** the value
lands in — they parse differently and need different encoders:

| Context | Encoding |
|---------|----------|
| HTML body | HTML-entity (`&` → `&amp;`) |
| HTML attribute | attribute encoding (and **quote** the attribute) |
| Inline JavaScript string | `\uXXXX` JS encoding (and quote the string) |
| URL / query value | `%HH` percent-encoding |
| CSS value | `\XX` hex encoding |

A single global HTML-escaper at the template layer does nothing for a value inside a
`<script>` block, an `onmouseover` handler, a CSS value, or a `javascript:` URL — the app
is still wide open. OWASP: *"There are many different output encoding methods because
browsers parse HTML, JS, URLs, and CSS differently. Using the wrong encoding method may
introduce weaknesses or harm the functionality of your application."*

## Code-execution sinks

- **Never** pass user-controlled input to `eval()`, `new Function()`, or the **string**
  form of `setTimeout`/`setInterval`. Encoding is not a defense here — JS-encoded payloads
  still execute. Pass a real function reference to the timers, and use `JSON.parse()` (never
  `eval`) to turn JSON into objects.
- OWASP: *"It is always a bad idea to use a user-controlled input in dangerous sources such
  as eval… simply don't do it instead of trying to sanitize the input."*

## Sanitizing rich HTML

When users must author rich HTML (WYSIWYG, comments, CMS), you can't avoid parsing markup —
so sanitize it:

- **Use a maintained, parser-driven allowlist sanitizer.** OWASP: *"OWASP recommends
  DOMPurify for HTML Sanitization."* (`DOMPurify.sanitize(dirty)`). A hand-rolled regex that
  strips `<script>` is defeated by tolerant HTML parsing — mutation XSS, malformed tags,
  SVG/MathML namespaces, event-handler attributes — so it is not a substitute.
- **Keep the sanitizer patched.** OWASP: *"You must regularly patch DOMPurify or other HTML
  Sanitization libraries that you use. Browsers change functionality and bypasses are being
  discovered regularly."*
- **Sanitize last, mutate nothing after.** Running a string tweak, a markdown/template pass,
  or another DOM library *after* `sanitize()` can re-introduce what sanitization removed.
  cure53/DOMPurify: *"if you first sanitize HTML and then modify it afterwards, you might
  easily void the effects of sanitization. If you feed the sanitized markup to another
  library after sanitization, please be certain that the library doesn't mess around with
  the HTML on its own."*

Paste-ready — DOMPurify defaults are already safe; the value of an explicit config is a
*narrow allowlist* (a comment field needs far less than a CMS), so reach for the secure
sink last:

```js
import DOMPurify from 'dompurify';

// Tight allowlist for a user comment: a few inline tags, links, line breaks — nothing else.
const clean = DOMPurify.sanitize(dirty, {
  ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br', 'ul', 'ol', 'li', 'code'],
  ALLOWED_ATTR: ['href'],            // omit anything you don't render; never add `on*` handlers
  ALLOW_DATA_ATTR: false,
});
element.innerHTML = clean;           // assign the RETURNED string; never sanitize in place then re-edit
```

DOMPurify blocks `javascript:` URLs and `on*` event-handler attributes by default; `data:`
URIs are allowed only on a built-in set of data-URI-safe tags (images/media via `DATA_URI_TAGS`)
and otherwise blocked — if you allow such tags, constrain `ALLOWED_URI_REGEXP`/`DATA_URI_TAGS`
deliberately. Either way, the smaller the allowlist the smaller the bypass surface. To emit a `TrustedHTML` value under
a Trusted Types policy (below), add `RETURN_TRUSTED_TYPE: true`.

## Framework escape hatches

Auto-escaping is the default; each framework has one hatch that turns it off. That hatch is
exactly where CMS/markdown XSS lands.

- **React — `dangerouslySetInnerHTML`.** JSX interpolation auto-escapes; this bypasses it.
  React docs: *"This is dangerous. As with the underlying DOM `innerHTML` property, you must
  exercise extreme caution! Unless the markup is coming from a completely trusted source, it
  is trivial to introduce an XSS vulnerability this way."* A payload as simple as
  `<img src=x onerror=…>` needs no `<script>` tag. Pass only trusted, sanitized data, and
  build the `{__html: …}` object in a dedicated function so every raw-HTML site is greppable.
- **Vue — `v-html` (and `innerHTML` in render functions).** `{{ }}` auto-escapes; `v-html`
  does not. Vue docs warn: *"User-provided HTML can never be considered 100% safe unless
  it's in a sandboxed iframe or in a part of the app where only the user who wrote that HTML
  can ever be exposed to it."* Use it only on HTML you know is safe — and "user-provided"
  includes API responses, bios, and query params, not just form fields. (Vue's docs also
  note frontend URL sanitization is itself a smell — *"if you're ever doing URL sanitization
  on the frontend, you already have a security issue"* — sanitize URLs on the backend.)
- **Angular — `DomSanitizer.bypassSecurityTrust*`.** Angular treats all bound/interpolated
  values as untrusted and auto-sanitizes; the `bypassSecurityTrustHtml/Url/Script/Style/
  ResourceUrl` methods disable that for a value. Use them only on content you fully control,
  and construct the value close to its source. Angular docs: *"Always make sure to construct
  SafeValue objects as close as possible to the input data so that it's easier to check if
  the value is safe."* When you've stepped outside templates into direct DOM APIs, Angular
  recommends `DomSanitizer.sanitize()` with the appropriate `SecurityContext` for the
  unavoidable case.

> Cross-cutting: for untrusted rich text in any framework, sanitize with DOMPurify before it
> reaches the hatch (per the OWASP recommendation above) — the per-framework docs back the
> *escape-hatch danger*, while DOMPurify is the sanitizer OWASP names.

## Trusted Types

Sanitize-and-encode depends on every developer remembering, at every sink, forever. **Trusted
Types** removes that dependency. It originated in Chromium (Chrome/Edge 83+) and has since
shipped in Safari 26+ and Firefox 148+ (MDN marks `require-trusted-types-for` Baseline 2026);
treat it as defense-in-depth that degrades gracefully — older browsers ignore the directive:

- Send `Content-Security-Policy: require-trusted-types-for 'script'`. Injection sinks
  (`innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `script.src`,
  `iframe.srcdoc`, …) then reject raw strings and accept only typed `TrustedHTML`/
  `TrustedScript` values produced by a vetted policy (e.g. one wrapping DOMPurify).
- Roll out with `Content-Security-Policy-Report-Only` first to surface violations before
  enforcing. Trusted Types don't sanitize for you — they *enforce* that every sink value came
  from a vetted policy, and that policy's `createHTML` is where sanitization actually happens
  (e.g. wrapping `DOMPurify.sanitize(s, { RETURN_TRUSTED_TYPE: true })`). web.dev: *"Trusted
  Types give you the tools to write, security review, and keep applications free of DOM XSS
  vulnerabilities by making dangerous web API functions secure by default."*

## Find these in your codebase

A grep is a fast first pass — treat every hit as a review point, not an automatic bug:

```sh
# Dangerous HTML sinks + code-execution — each needs a safe sink (textContent) or a sanitizer
rg -n 'innerHTML|outerHTML|insertAdjacentHTML|document\.write|\beval\(|new Function\(' src/
# Framework escape hatches — each should sit right next to a DOMPurify call
rg -n 'dangerouslySetInnerHTML|v-html|bypassSecurityTrust' src/
```

## Sources

- OWASP — [DOM-based XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html)
  (right-sink-over-encoding; `eval`/dangerous-sources)
- OWASP — [XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
  (context-specific output encoding; "OWASP recommends DOMPurify"; patch regularly)
- cure53 — [DOMPurify README](https://github.com/cure53/DOMPurify) (sanitize last; don't
  modify or re-parse sanitized markup afterward)
- React — [Common components: `dangerouslySetInnerHTML`](https://react.dev/reference/react-dom/components/common#dangerously-setting-the-inner-html)
- Vue — [Security best practices](https://vuejs.org/guide/best-practices/security.html)
  (HTML injection / `v-html`; user-provided HTML never 100% safe; backend URL sanitization)
- Angular — [Security](https://angular.dev/best-practices/security) (auto-sanitization;
  `bypassSecurityTrust*`; construct SafeValue close to input; `DomSanitizer.sanitize`)
- web.dev — [Prevent DOM-based XSS with Trusted Types](https://web.dev/articles/trusted-types)
