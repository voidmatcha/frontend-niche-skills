# Condition B — frontend-report-triage in context

Short version: I can't call a root cause from this report, but the shape of it — post-deploy, partial cohort, self-healing on refresh, invisible on staging — narrows hard to "clients whose session straddled the deploy." Below is what I'd treat as known, the three hypotheses worth spending time on, and the smallest set of artifacts that would decide between them.

## 1. Report facts

Known:

- Trigger correlates with a deploy.
- Symptom A: page renders an old version of the app.
- Symptom B: an in-progress draft disappears.
- A reload "usually" fixes symptom A. "Usually" is doing a lot of work here — see hypothesis 1.
- Affects a subset of users.
- Not reproducible on staging.

Missing (and load-bearing):

- Whether the app registers a service worker, and if so its update strategy (`skipWaiting`/`clientsClaim`, `updateViaCache`, precache manifest).
- `Cache-Control` on the HTML document response versus on hashed assets.
- Whether the previous build's hashed chunks stay reachable after a deploy, or get purged/overwritten.
- Where the draft actually lives: React/component state only, `localStorage`, IndexedDB, or server-side autosave.
- Whether the affected users had a tab open *before* the deploy, or arrived fresh after it.
- Whether symptom A and symptom B hit the same users, or are two separate reports that got merged.
- Whether "refresh" means one reload, two reloads, or a hard reload.
- Any client error telemetry around the deploy window (`ChunkLoadError`, `Failed to fetch dynamically imported module`, `Importing a module script failed`).

## 2. Ranked hypotheses

**H1 — Service worker or document cache is serving the previous build. Likely.**

The single strongest signal is "refreshing *usually* fixes it." A service worker whose new version installs but sits in `waiting` behaves exactly like that: the first reload installs the update, the second one activates it. A plain `Cache-Control`-cached HTML document produces a similar but more deterministic pattern. Both explain the partial cohort — only clients that already had a controlled page or a cached document are affected — and both explain staging, where nobody keeps a tab open across a deploy and cache headers are frequently different.

**H2 — The stale HTML references chunks the deploy removed, and the recovery path destroys the draft. Likely, and probably the link between the two symptoms.**

An old document asking for `main.a1b2c3.js` after that file is gone gets a 404 or an HTML error page. A dynamic `import()` then rejects, an error boundary or an auto-reload handler fires, and any draft held only in component state dies with the remount. This is the cheapest explanation for why *one* deploy caused *both* symptoms in *one* cohort. It hinges entirely on whether old build artifacts are retained — which is a config question, not a debugging question.

**H3 — The draft's own persistence broke, independent of rendering. Possible.**

Worth separating because if it's this, fixing the cache fixes nothing. Candidate mechanisms, in the order I'd check them:

- Draft was never persisted at all — pure in-memory state. Then H2 fully explains it and there is no storage bug.
- IndexedDB version bump in the new build: the open pre-deploy tab holds the old DB version, the upgrade in a new tab fires `blocked`, and writes from then on fail or land nowhere. Fits "some users" and "invisible on staging" precisely.
- Autosave request now hits a changed API contract and fails silently, with no user-visible error.
- Storage key or schema renamed in the new build, so the old draft is still on disk but unreachable.

**Unlikely, but cheap to rule out:** bfcache restore. It produces stale-looking pages, but the deploy correlation and the draft loss don't fit it well. Check it only because the check is one line of DevTools work.

I am specifically *not* routing this toward anything security- or data-boundary-shaped. Nothing in the report supports that.

## 3. Evidence gaps — smallest artifacts that would change the route

Ranked by how much each one narrows things:

1. **Does the deploy keep the previous build's hashed assets reachable?** One question to whoever owns the pipeline. A "no" makes H2 near-certain and reframes H1 as an aggravator rather than the cause.
2. **Is there a service worker, and what is its update strategy?** One look at `navigator.serviceWorker.getRegistrations()` output, or a grep of the build config. Decides H1 outright.
3. **Where does the draft live?** Determines whether H3 exists at all.
4. **Error telemetry filtered to the deploy window,** specifically for chunk-load failures and IndexedDB `blocked`/`abort` events. If those spiked at deploy time, H2 and the IDB branch of H3 stop being hypotheses.
5. **Do the stale-page reports and the lost-draft reports name the same users?** Support can answer this without any engineering time, and it tells you whether you are chasing one bug or two.

Please don't send screenshots — they won't distinguish any of these.

## 4. Follow-up skills, in order

1. `pwa-offline-cache-contracts` — stale build/chunk serving and update lifecycle. Start here; it owns H1 and half of H2.
2. `browser-storage-durability-contracts` — blocked IndexedDB upgrades, silently inactive writes, disappearing saved data. Owns H3.
3. `client-error-observability-contracts` — only if telemetry turns out to be missing or unusable for the deploy window. "We cannot reproduce it" is often really "the errors never reached us," and that's worth fixing regardless of this bug.

## 5. First verification

Reproduce the actual condition, which staging has never been asked to do: **keep a tab open across a deploy.**

1. Open the app in a normal (non-incognito) window on staging. Start typing a draft. Leave the tab open and untouched.
2. Deploy a new build to staging with the *same* asset-retention behavior production uses. If staging keeps old artifacts and production purges them, change staging to match — that difference alone may be the entire "can't reproduce."
3. Return to the tab. Before touching anything, in DevTools:
   - **Application → Service Workers**: is there a worker stuck in `waiting`? Note the exact state.
   - **Network**, with "Disable cache" *off*: reload once and check the document's `Size` column — `(ServiceWorker)`, `(disk cache)`, `304`, or `200`. Then reload a second time and compare. If one reload gives you the old build and two give you the new one, H1 is confirmed and you can stop.
   - **Console**: any `ChunkLoadError` or failed dynamic import. That confirms H2.
4. Check whether the draft survived, and where it was supposed to be — `localStorage`, or **Application → IndexedDB** for the store and its version number. If IndexedDB shows an unexpected version or an empty store, follow the H3 branch.

If step 2 doesn't reproduce it, the next most likely missing ingredient is the CDN or hosting layer's document caching, which staging usually doesn't have in front of it. Compare production and staging response headers on the HTML document directly before spending more time on the app code.

## Immediate mitigation, independent of which hypothesis wins

Persisting the draft outside component state on a debounce is worth doing regardless — it converts every future variant of this failure from data loss into a cosmetic annoyance. I'd treat that as separate work from the diagnosis, not as the fix, since shipping it would also hide the evidence you need for H3.
