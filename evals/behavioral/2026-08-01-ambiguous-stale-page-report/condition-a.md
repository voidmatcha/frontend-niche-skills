# Condition A — no skill in context

Short version: this reads like two separate problems that a deploy happens to trigger at the same moment. "Old version of the page" is a caching / asset-versioning problem. "Draft disappeared" is a client-state persistence problem. They are worth separating before you chase either one, because a fix for one will not fix the other.

Also worth saying up front: "refreshing fixes it" and "we cannot reproduce it on staging" are both strong signals, not dead ends. The first tells you the bad state is client-side and transient. The second usually tells you staging differs in cache headers, CDN presence, deploy strategy, or number of concurrently-served build versions — not that the bug is imaginary.

## The likely mechanisms

**1. Stale HTML with fresh asset URLs (or the reverse).**
The usual shape is: `index.html` is served from a CDN or browser cache with a long or ambiguous max-age, so it still points at `main.abc123.js`. After deploy, that hashed file is gone from the origin. The user gets either a 404 chunk, or a mixed state where some chunks are old and some are new. Classic symptom: the page renders but is "the old one," and a hard refresh clears it because the refresh revalidates the HTML.

**2. Lazy-loaded chunk fetched after the deploy.**
A user has the app open across the deploy. They click something that triggers a dynamic `import()`. That chunk no longer exists on the origin. Depending on your error handling you get a blank route, an error boundary, or a silent no-op — and if your framework's router catches it and does a full page load to recover, any in-memory draft is gone. This one fits your report unusually well because it explains stale-looking behavior *and* draft loss from a single event.

**3. Service worker serving the previous precache.**
If you have a service worker (Workbox, a PWA setup, a framework default you may not have opted into deliberately), the classic failure is the new SW installing but sitting in `waiting` because the old one still controls the tab. Users keep getting the old precached shell until every tab closes. "Refreshing usually fixes it" but not always — matches the "usually" in your report precisely, since a normal reload does not always release control.

**4. Multiple origin instances serving different builds.**
During a rolling deploy, requests can land on old and new instances. If the deploy window is short this affects a small slice of users, which explains "not everyone."

**5. Draft loss specifically.**
Three common causes, in rough order of likelihood: (a) draft lives only in React/Vue state and any full page load discards it; (b) draft is persisted but keyed by something that changes across versions — a storage key with a version prefix, a schema migration that discards unrecognized shapes, a `JSON.parse` that throws and gets swallowed into a reset; (c) an auth or session refresh at deploy time clears storage or logs the user out and the app resets on rehydrate.

## What I would ask you for

Please gather these — most are quick and most matter more than any code reading I could do:

1. **Do you have a service worker in production?** Check `navigator.serviceWorker.getRegistrations()` on the live site, and confirm whether staging registers one too. If prod has one and staging does not, that alone likely explains the reproduction gap.
2. **The actual response headers for the HTML document** in production, from a real user path (through the CDN, not curl against the origin): `cache-control`, `etag`, `age`, `x-cache` or the equivalent CDN hit/miss header. Same for one hashed JS asset. I want to see whether the HTML is cacheable and for how long.
3. **How the deploy works.** Atomic swap or rolling? Are old hashed assets retained after a deploy, and for how long? A lot of pipelines delete the previous build's files immediately — that is the single most common cause of this exact report.
4. **Are the drafts persisted at all,** and if so where — `localStorage`, `sessionStorage`, IndexedDB, or server-side autosave? What is the storage key, and does anything in it change between builds?
5. **Errors from the affected sessions.** Specifically: chunk load failures (`ChunkLoadError`, `Loading chunk N failed`, `Failed to fetch dynamically imported module`), and any 404s on `.js` files. Filter your error tracker by the deploy timestamp — if these spike within minutes of each deploy, that is your answer.
6. **Timing correlation.** For the users who reported it, how long had their tab been open, and when did they last load the page relative to the deploy? If they all had long-lived sessions spanning the deploy, that rules in mechanisms 2 and 3 and rules out most CDN theories.
7. **Which users.** Any pattern by browser, by whether they are returning visitors, by geography (CDN PoP), or by whether they are on a mobile app webview.

## How to reproduce it deliberately

Do not try to reproduce it by using the app normally — the window is too narrow. Force it:

- **Chunk-loss repro:** load the app in a browser, deploy (or manually delete/rename the previous build's chunk files from wherever they are served), then without refreshing, navigate to a lazily-loaded route. Type a draft first so you can see whether it survives.
- **Stale-HTML repro:** load the page, deploy, then reload *without* clearing cache and with devtools "Disable cache" turned OFF. Devtools with cache disabled hides this entire class of bug, which is very likely part of why staging looks clean.
- **Service worker repro:** load, deploy, reload once. Then check Application → Service Workers for a worker stuck in "waiting." If it is waiting, you have found it.
- **Make staging match prod first.** If staging has no CDN, or different cache headers, or deploys by full replacement while prod does rolling, staging cannot reproduce this. Aligning those is worth doing before spending more time on repro attempts.

## Fixes, once you know which one it is

- HTML must be `no-cache` (or very short max-age with revalidation); hashed assets get `max-age=31536000, immutable`. Those two rules together prevent most of this class.
- Retain the previous one or two builds' hashed assets for at least as long as a plausible session — commonly 24 hours. Cheap, and it turns a hard failure into a non-event.
- Handle chunk load errors explicitly: catch `ChunkLoadError` at the router or error boundary, and reload once (guard with a sessionStorage flag so you cannot loop). Save the draft before reloading.
- Persist the draft on a debounce to `localStorage` or IndexedDB, keyed by document/user, not by build. Restore on mount. This makes draft loss survivable regardless of which caching bug you eventually fix — I would do this first, since it converts the worst part of the user impact into a non-issue while you diagnose.
- If a service worker is involved, decide deliberately between `skipWaiting` + `clients.claim` and an explicit "new version available, reload" prompt. Both are fine; drifting into the default without choosing is what causes this.
- Consider a build-version check: expose the current build id at a known endpoint, poll it lightly or check on focus, and prompt the user to reload when it changes — after autosaving their draft.

## Verification

- Add a build/commit id to the app (a meta tag or a global) and log it with every error report. Then "old version" stops being a guess: you can see exactly which build each affected session was running.
- Track chunk load failures as a named metric and watch it across the next few deploys. Success looks like: the deploy-time spike goes to zero.
- After adding draft persistence, verify explicitly by killing the tab mid-edit and reopening — do not rely on the deploy path to test it.
- Re-check the header configuration from a real browser through the CDN after any cache change, not from curl against the origin, since the origin often has correct headers that the CDN then overrides.

If you can get me items 1, 2, 3, and 5 above, that is probably enough to name the mechanism without further guessing.
