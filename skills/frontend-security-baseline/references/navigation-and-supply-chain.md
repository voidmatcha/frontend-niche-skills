# Navigation & supply chain

Two classes of "looks handled" bugs. Outbound navigation: browsers fixed the
anchor default, so teams either cargo-cult the old fix or quietly reopen the hole
the moment they switch to `window.open`. Supply chain: the dangerous code runs at
**install** time, on the dev's machine or the CI runner, before anyone reviews a
line — long before the bundle ships.

## Reverse tabnabbing and the opener reference

- On every outbound link that opens a new tab, set `rel="noopener noreferrer"`.
  `noopener` severs the new page's `window.opener` handle so it can't navigate
  your original tab to a look-alike phishing page; `noreferrer` additionally
  strips the `Referer` header. MDN (`noopener`): *"instructs the browser to
  navigate to the target resource without granting the new browsing context access
  to the document that opened it — by not setting the Window.opener property on
  the opened window (it returns null)."*
- Modern browsers already imply `noopener` for `target="_blank"` on these
  elements, so fresh anchor HTML is protected by default. MDN: *"Setting
  `target=\"_blank\"` on `<a>`, `<area>` and `<form>` elements implicitly provides
  the same `rel` behavior as setting `rel=\"noopener\"` which does not set
  `window.opener`."* Treat this as a baseline, not a reason to drop the explicit
  attribute: it doesn't add `noreferrer` (referrer still leaks), and it doesn't
  cover older engines, email/PDF/WebView surfaces, or framework router components
  that don't inherit the anchor default.
- The expensive regression: `window.open()` is **not** covered by that implicit
  default — it returns a usable `opener` unless you opt out. Code that migrates
  from `<a target="_blank">` to a JS click handler calling `window.open(url)`
  silently reintroduces the opener leak the team thought browsers had solved. Pass
  the features string: `window.open(url, '_blank', 'noopener,noreferrer')`. MDN
  (`Window.open`): *"noreferrer: If this feature is set, the browser will omit the
  Referer header, as well as set noopener to true."* (And never restore opener
  access — `rel="opener"` — for an untrusted destination.)

## Open redirects: allow-list, never denylist

- Don't redirect to a raw user-controlled URL. Prefer accepting a short
  name/ID/token mapped server-side to the real target. OWASP: *"Where possible,
  have the user provide short name, ID or token which is mapped server-side to a
  full target URL."* If you must accept a URL, validate the host against an
  allow-list of trusted hosts (OWASP sanctions a list of hosts or a regex; we
  additionally recommend a **real URL parser** over a hand-rolled regex, since
  regex host checks are error-prone), and otherwise show a "you are leaving this
  site" interstitial.
- The trap is reflecting `?next=`/`?returnUrl=` and "validating" it with
  `startsWith` or a denylist of bad hosts. Encoding tricks, the userinfo
  separator (`https://yoursite.com@evil.com`), and protocol-relative URLs
  (`//evil.com`) sail through string checks, turning your trusted domain into a
  phishing and OAuth-token-theft launchpad. OWASP: *"This should be based on an
  allow-list approach, rather than a denylist."*

## Reproducible installs: `npm ci`, not `npm install`

- Commit the lockfile and install with `npm ci` (or `yarn install
  --frozen-lockfile`) in CI and production builds. These install strictly from the
  lockfile and abort on any mismatch, instead of silently resolving new versions.
- The trap: `npm install` in CI lets a `package.json`/lockfile mismatch — or a
  semver range — pull in a newer, never-reviewed version, defeating the point of
  having a lockfile (the same loose resolution that let the ua-parser-js
  account-hijack reach projects whose caret ranges resolved a malicious version
  during its ~4-hour window — a strict `npm ci` pinned to a reviewed lockfile would
  not have). OWASP: *"When they detect an inconsistency between the project's
  package.json and the lockfile, they compensate for such change based on the
  package.json manifest by installing different versions than those that were
  recorded in the lockfile. This kind of situation can be hazardous for build and
  production environments."*

## Lifecycle scripts run arbitrary code at install

- Set `ignore-scripts=true` in your project `.npmrc` to block automatic execution
  of dependency `preinstall`/`install`/`postinstall` scripts. When a specific
  package legitimately needs them (e.g. native builds like `sharp`), grant it via
  an explicit allow-list (e.g. `@lavamoat/allow-scripts`) rather than re-enabling
  scripts globally.
- This is the lowest-friction supply-chain vector — eslint-scope, crossenv, and
  the Shai-Hulud worm all used it: a poisoned transitive package runs the
  moment it's installed, with full access to SSH keys, cloud creds, and npm
  tokens, before any code review. (`ignore-scripts` does not stop build- or
  run-time injection such as the 2018 event-stream/flatmap-stream attack, whose
  payload executed during a downstream project's release build rather than on
  install — `npm ci`, lockfiles, and provenance/allow-list review cover that vector.) OWASP: *"bad actors may create or alter packages
  to perform malicious acts by running any arbitrary command when their package is
  installed… When installing packages make sure to add the --ignore-scripts suffix
  to disable the execution of any scripts by third-party packages. Consider adding
  ignore-scripts=true to your .npmrc project file, or to your global npm
  configuration."*

## Typosquatting, slopsquatting & dependency confusion

- Before adding any new dependency — especially one an AI assistant suggested —
  confirm it exists and is legitimate (`npm view <pkg>`: download counts, publish
  date, a real repository). Names are first-come, first-served with no proof of
  ownership, so one mistyped or hallucinated name (`node-fetch-promise` vs
  `node-fetch`) installs attacker code.
- Dependency confusion is the sharper edge: publishing a public package matching
  your **internal** name with a higher version makes the installer prefer the
  malicious public one. OWASP: *"A dependency confusion attack occurs when an
  attacker publishes a malicious package on the public npm registry using the same
  name as your internal private package, but with a higher version number."* The
  defense is scoped names pinned to your private registry: *"Always use scoped
  package names for internal packages (e.g., @yourorg/package-name instead of
  package-name)"* — and teams leak internal names through public `package.json`
  files and job postings without realizing it.

## Nothing shipped to the browser is secret

- Never hardcode API keys, credentials, internal IPs, or hidden admin routes in
  client-side JS — anything shipped to the browser is readable. Route privileged
  calls through a server-side proxy and keep the secret on the server. OWASP WSTG:
  *"many programmers also hardcode sensitive information in JavaScript variables on
  the frontend. Sensitive information can include (but is not limited to): Private
  API Keys."* An under-restricted key (e.g. a Google Maps key usable on
  unrestricted APIs) means *you* pay for the attacker's usage.
- Don't publish production source maps. Minification is not obfuscation — and a
  leftover `.map` file, reachable by appending `.map` to a JS URL, restores the
  full original source. OWASP WSTG: *"source map files or files for debugging if
  released to the production environment will make their source more
  human-readable. It can make it easier for attackers to find vulnerabilities from
  the frontend or collect sensitive information from it."*

> Subresource Integrity for third-party `<script>`/`<link>` (and the
> `crossorigin`-or-the-load-fails trap) lives in
> [csp-and-headers](./csp-and-headers.md), alongside the rest of the header story.

## Find these in your codebase

The `window.open`, redirect-param, and CI-install probes live in the SKILL.md "Quick probes" triage block — kept there as the single source of truth. Every hit is a review point, not an automatic bug.

## Sources

- MDN — [`rel="noopener"`](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/rel/noopener)
  (severs `window.opener`; implicit-`noopener` default for `target="_blank"`)
- MDN — [`Window.open()`](https://developer.mozilla.org/en-US/docs/Web/API/Window/open)
  (`window.open` not covered by the anchor default; `noreferrer` omits `Referer`
  and sets `noopener`)
- OWASP — [Unvalidated Redirects and Forwards Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Unvalidated_Redirects_and_Forwards_Cheat_Sheet.html)
  (map a server-side ID; allow-list not denylist; interstitial)
- OWASP — [NPM Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/NPM_Security_Cheat_Sheet.html)
  (`npm ci` over `install`; `ignore-scripts`; dependency confusion & scoped names)
- OWASP WSTG — [Review Web Page Content for Information Leakage](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/01-Information_Gathering/05-Review_Web_Page_Content_for_Information_Leakage)
  (no hardcoded secrets in client JS; production source maps expose source)
