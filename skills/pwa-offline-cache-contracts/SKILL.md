---
name: pwa-offline-cache-contracts
description: "Use when a service worker or offline cache serves the wrong bytes: a waiting worker leaves users on an old build, stale HTML references purged chunks, Workbox patterns omit required assets, old caches accumulate, one failed cache.addAll entry aborts install, activation happens without a reload path, navigation lacks an offline fallback, or authenticated responses enter shared Cache Storage. Covers service-worker and asset-cache lifecycle. Use client-error-observability-contracts for monitoring failures, frontend-data-fetching-cache-contracts for runtime query caches, and frontend-security-baseline for authenticated-cache policy."
---

# PWA offline cache contracts

A service worker turns your app into cached bytes that outlive any single deploy, so every cache decision is a freshness contract: what is precached, when a new worker takes over, when old caches are deleted, and what must never be cached at all. The bugs are not in the offline happy path — they are stale builds that never update, navigations that fail on purged chunks, and per-user responses served to the wrong session.

## Checklist (lead with the trap)

1. **A long-cached index.html plus content-hashed chunks is the classic post-deploy break.** The HTML is cached with a long `max-age` while a deploy emits new hashed chunks (`app-B2.js`) and purges the old (`app-A1.js`). Returning users load the stale HTML, it still asks for the purged chunk, and the dynamic import rejects with `ChunkLoadError` (webpack) or `Failed to fetch dynamically imported module` (Vite native ESM). Serve HTML with `Cache-Control: no-cache` (revalidate every load) or route it Network First in the SW, keep hashed assets immutable/Cache First, and add a `vite:preloadError` / lazy-import handler that reloads once with a retry cap — never an unbounded reload loop.
2. **The waiting worker is why "I deployed but users still see the old app."** A new worker installs then sits in `waiting` until every client controlled by the old worker closes; a refresh does not release it because clients overlap. So a deploy silently does nothing for active tabs. Detect the update (`updatefound` -> `statechange` to `installed`, and also check `registration.waiting` on load in case the prompt was missed) and give the user a path to activate. `registration.update()` only refetches the script; a byte-different worker still waits.
3. **Delete old caches in activate, keyed by an explicit version — not in install.** Open a versioned cache name per release (`app-static-v3`); on `activate`, walk `caches.keys()` and delete any not in your current allowlist. Do cleanup in `activate`, not `install`, because the old worker is still serving pages while the new one installs. Installing a new worker does not evict old caches for you; without cleanup they accumulate against the storage quota.
4. **cache.addAll is all-or-nothing: one bad URL aborts the whole install.** `cache.addAll` is atomic (Workbox precaching fetches entries individually rather than via `addAll`, but its install is equally all-or-nothing) — if any single request fails (a 404, a redirect, an opaque cross-origin response), the promise rejects, and wrapped in `event.waitUntil` the install fails, so nothing is cached and the worker never activates. These rejections are hard to see from inside the worker. Precache only same-origin URLs you expect to return 200; cache optional or third-party assets separately with `cache.put` and per-item error handling.
5. **Custom globPatterns replace the default match set — enumerate every asset type.** In `workbox-build` / vite-plugin-pwa, setting `globPatterns` overrides the defaults instead of extending them. The defaults cover only a subset (JS/CSS/HTML); once you set your own, `woff2` fonts, `png`/`svg` icons, and JSON drop out of the precache and the app breaks only offline. List every extension the app needs and mind `maximumFileSizeToCacheInBytes` (large files are silently skipped). A built-manifest assertion (HTML + JS + CSS + icons + fonts all present) catches the regression.
6. **Decide skipWaiting / clients.claim vs prompt-to-reload deliberately.** `self.skipWaiting()` activates the new worker immediately, so it can control pages loaded by the old version — early fetches were served old, later ones new, mixing mismatched HTML and chunks. `clients.claim()` lets an active worker control already-open tabs. Both are fine for pure precache-and-serve; for an app where mixed versions break, prefer a prompt: skip waiting only when the user accepts, then reload on `controllerchange`. Do not paste `skipWaiting` + `clients.claim` as boilerplate without deciding.
7. **Give navigations a fallback and a real offline page.** For an SPA, register a `NavigationRoute` serving the precached shell (`createHandlerBoundToURL('/index.html')`) so client-side routes resolve offline, with `allowlist`/`denylist` so it does not swallow API or file URLs (it matches all navigations by default). Provide a dedicated offline fallback for navigations that miss the cache — otherwise a first offline visit shows the browser error page, not your app.
8. **Never precache or runtime-cache authenticated HTML/API responses.** Cache Storage is per-origin, not per-user, and the Cache API ignores HTTP cache headers — whatever you put stays until you delete it. Caching an authenticated page or per-user API JSON lets the next session (logout/login, shared device) read another user's data, or stale-after-logout data. Route authenticated/personalized endpoints Network Only (never written to cache); reserve Cache First for hash-versioned static assets and Network First for shell HTML, and gate cacheable responses to status 200 so opaque (status 0) responses are not stored blindly.

## Quick probes

Treat hits as leads; open the SW source and the build config before filing. Route mechanical checks to your build tool's Workbox output (glob count, precache size, size-limit warnings) and DevTools Application panel — Service Workers shows the waiting worker and the Update-on-reload switch, Cache Storage shows what was actually precached. (Lighthouse's PWA category was removed in v12; do not point CI at it.)

```sh
rg -n "skipWaiting|clients\.claim|registration\.waiting|updatefound|controllerchange" src/ app/ 2>/dev/null
rg -n "globPatterns|precacheAndRoute|__WB_MANIFEST|maximumFileSizeToCacheInBytes|injectManifest" . 2>/dev/null
rg -n "caches\.open|cache\.addAll|caches\.delete|caches\.keys|CACHE_VERSION|cacheName" src/ app/ 2>/dev/null
rg -n "NavigationRoute|createHandlerBoundToURL|navigateFallback|NetworkOnly|CacheFirst|NetworkFirst" . 2>/dev/null
rg -n "vite:preloadError|ChunkLoadError|Failed to fetch dynamically imported" src/ app/ 2>/dev/null
```

Also inspect the deployed HTML response headers (`Cache-Control`) and confirm hashed assets are immutable while `index.html` revalidates.

## Boundary with sibling skills

- This skill: the service-worker + Cache Storage asset lifecycle — precache completeness, cache versioning/eviction, install atomicity, the update/waiting flow, navigation fallback, and which responses must never be cached.
- **client-error-observability-contracts** — capturing the SW / ChunkLoadError signal in monitoring (`window.onerror` vs `unhandledrejection`, cross-origin `Script error.` on chunk fetches). This skill decides the caching fix; that one wires the reporting.
- **frontend-data-fetching-cache-contracts** — the runtime data-fetch cache (SWR / TanStack Query / Apollo staleness, invalidation, infinite-scroll eviction), a JS-memory cache above the network; this skill owns the Cache Storage / SW layer beneath it.
- **frontend-security-baseline** — the policy ruling on storing authenticated responses and token exposure; this skill flags the SW cache write, that one owns the security stance.

## PR-worthiness gate

File a finding only when a caching contract is actually broken and user-visible:

- **Stale/broken deploy**: long-lived `index.html` plus purged hashed chunks with no `no-cache` HTML, no update flow, and no preload-error handler.
- **Stuck update**: a new worker that only ever waits — no `updatefound`/`waiting` handling, and `skipWaiting` not chosen either.
- **Incomplete precache**: custom `globPatterns` that drop an asset type the app needs offline, or a precache that aborts because `addAll` hit a non-200.
- **Cache growth / stale serve**: old versioned caches never deleted in `activate`.
- **Leak**: an authenticated HTML/API response written to Cache Storage.

Reject weak findings:

- A worker that already versions caches, cleans them in `activate`, precaches a complete manifest, and has an update prompt — that is the correct pattern.
- `skipWaiting` on a pure precache-and-serve app with no mixed-version risk — intentional, not a bug.
- A missing offline page on an app with no offline requirement.
- Which exact `max-age` to pick — deployment tuning, not a contract break, unless it strands users on purged chunks.

Minimal useful PR: set HTML to `no-cache` while assets stay immutable; add an `updatefound`/`registration.waiting` reload prompt; add the missing `globPatterns` extension plus a built-manifest assertion; move an authenticated route to Network Only; or add the `activate`-time cache cleanup — each with a smoke test (offline navigation, or deploy-then-reload).

## Output shape

- **Contract**: precache completeness / versioning+eviction / install atomicity / update-waiting flow / navigation fallback / do-not-cache.
- **Evidence**: file/line in the SW or build config, the cached HTML plus purged-chunk URL, or the `globPatterns` diff.
- **Symptom**: stale build after deploy, ChunkLoadError / failed dynamic import, missing-offline asset, aborted install, or cross-session cached data.
- **Fix**: smallest change — HTML `no-cache`, cache cleanup in `activate`, glob extension, update prompt, or Network Only route.
- **Verification**: deploy-then-reload check, offline navigation smoke test, or a built-manifest assertion.

## Sources

- MDN — Using Service Workers (install/activate lifecycle, `waitUntil`, deleting old caches in `activate`): <https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API/Using_Service_Workers>
- MDN — Cache: addAll() (atomic; if any request fails, nothing is added): <https://developer.mozilla.org/en-US/docs/Web/API/Cache/addAll>
- MDN — ServiceWorkerRegistration: update() (refetch + byte comparison; a byte-different worker installs then waits): <https://developer.mozilla.org/en-US/docs/Web/API/ServiceWorkerRegistration/update>
- MDN — ServiceWorkerRegistration: updatefound event (fires when a new worker starts installing; watch `statechange` to `installed`): <https://developer.mozilla.org/en-US/docs/Web/API/ServiceWorkerRegistration/updatefound_event>
- MDN — Clients: claim() (an active worker controls already-open clients; fires `controllerchange`): <https://developer.mozilla.org/en-US/docs/Web/API/Clients/claim>
- web.dev — The service worker lifecycle (the waiting worker, `skipWaiting`/`clients.claim` caveats, `registration.update`): <https://web.dev/articles/service-worker-lifecycle>
- web.dev — The offline cookbook (versioned cache names, cache-first vs network-first, network-only for non-GET): <https://web.dev/offline-cookbook/>
- Chrome for Developers — workbox-precaching (`precacheAndRoute`, `__WB_MANIFEST`, revisioning, `NavigationRoute` app shell): <https://developer.chrome.com/docs/workbox/modules/workbox-precaching>
- Chrome for Developers — Strategies for service worker caching (Network First for HTML/API, Cache First for hashed assets, Network Only for authenticated routes): <https://developer.chrome.com/docs/workbox/caching-strategies-overview>
- Vite PWA — Service Worker Precache (`globPatterns`, `includeAssets`, `maximumFileSizeToCacheInBytes`): <https://vite-pwa-org.netlify.app/guide/service-worker-precache>
- Vite — Building for Production (`vite:preloadError` on a failed dynamic import after deploy; reload with a retry cap): <https://vite.dev/guide/build>
