# Iframe/embed prior-art and evidence snapshot

This is a bounded, reproducible search record, not a claim that no other iframe
skill exists. It records why this repository keeps a focused browser
parent/guest contract alongside its native-WebView and security skills.

Snapshot date: **2026-07-10**

## Search procedure

Agent Reach GitHub and web routes were used with these public queries:

```sh
gh search code postMessage --filename SKILL.md --limit 30
gh search code frame-ancestors --filename SKILL.md --limit 30
gh search code requestStorageAccess --filename SKILL.md --limit 30
gh search code iframe-resizer --filename SKILL.md --limit 30
gh search issues 'postMessage iframe' --sort comments --limit 30
gh search repos 'frontend agent skills accessibility performance SEO' --sort stars --limit 10
```

Official pages were read through their public MDN URLs.

## Strong overlap found

- [`ctxr-dev/skill-frontend-excellence` Embed Patterns](https://github.com/ctxr-dev/skill-frontend-excellence/blob/bcdd3a5fee4723e8ec1d206a5e3bf1553afa5b53/references/embed-patterns.md)
  is the closest match. It covers host/guest roles, sandboxing, Permissions
  Policy, postMessage handshakes, viewport reporting, storage, CSP, loading,
  and accessibility. The repository is MIT-licensed. This means the subject is
  **not unique in the public skill ecosystem**.
- [GoogleChrome/modern-web-guidance-src security](https://github.com/GoogleChrome/modern-web-guidance-src/blob/72f7de422b0c35397ffcb5b940780f668e1322e2/skills-src/security/SKILL.md)
  covers `frame-ancestors`, `postMessage`, and iframe capability delegation.
- [GoogleChrome/modern-web-guidance-src privacy](https://github.com/GoogleChrome/modern-web-guidance-src/blob/72f7de422b0c35397ffcb5b940780f668e1322e2/skills-src/privacy/SKILL.md)
  covers partitioned cookies and the Storage Access API.
- Security-focused skills such as
  [`insecure-postmessage`](https://github.com/zakirkun/ice-tea/blob/fa038558e578f8d71ef54d135403d057762f061d/skills/web/insecure-postmessage/SKILL.md)
  cover wildcard senders and origin validation, but not the full lifecycle,
  sizing, storage, and teardown contract.

## Broader skills deliberately not duplicated

- [`addyosmani/web-quality-skills`](https://github.com/addyosmani/web-quality-skills)
  already provides broad accessibility, best-practices, Core Web Vitals,
  performance, SEO, and web-quality-audit skills.
- [`Community-Access/accessibility-agents`](https://github.com/Community-Access/accessibility-agents)
  and [`better-frontend-skills`](https://github.com/dominika-zajac/better-frontend-skills)
  provide broad accessibility review/fix surfaces.

The local pack should therefore keep iframe work narrow rather than adding
generic SEO, Lighthouse, accessibility-audit, or whole-site security skills.

## Recurring implementation evidence

- [Shopify shopify-app-js #3214](https://github.com/Shopify/shopify-app-js/issues/3214):
  a blank embedded app accompanied by a `postMessage` target-origin mismatch.
- [Enketo #1515](https://github.com/enketo/enketo/issues/1515): demand for
  robust cross-origin height communication through `postMessage`.
- [WHATWG HTML #555](https://github.com/whatwg/html/issues/555): the long-running
  absence of automatic iframe content sizing and the need for parent/guest JS.
- [iframe-resizer #1309](https://github.com/davidjbradshaw/iframe-resizer/issues/1309):
  incorrect initial height and duplicated init work in a mature resizing
  implementation.

These issues are examples, not prevalence estimates.

## Local retention decision

Keep `iframe-embed-contracts` because this repository previously covered native
app WebViews, site-wide browser security, payment fields, and page-level
performance without one route that joins the two browser applications across an
iframe boundary. The local skill differs from broad prior art by enforcing this
pack's evidence tiers: exact parent/guest ownership, delivered policy evidence,
source/origin/schema checks, a bounded resize protocol, teardown, sibling-skill
routes, and a concrete browser regression path.

Reconsider or merge the skill only if another bundled skill acquires the same
parent/guest lifecycle and verification ownership. Do not justify retention by
claiming the topic is absent from the public ecosystem.
