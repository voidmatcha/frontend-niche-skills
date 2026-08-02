# Open-source casebook

Purpose: check whether selected bundled frontend niche skills find real, PR-worthy defects rather than search-noise. Newly added skills may start without a validation case until a reproduced OSS example exists. A case counts only when it has source-line evidence, a concrete user-visible failure mode, a small plausible patch, and a maintainer-facing rationale.

Status as of 2026-08-01: nothing in this document has been filed upstream and no
maintainer has accepted anything. With one exception, every row is a
source-verified reading of public code at a pinned commit and nothing more. The
exception is the n8n Storybook Callout row, which carries a recorded
export/render/diff run. Individual sections do not repeat this disclaimer; it
applies to the whole document.

Snapshots: 2026-06-17 and 2026-06-26 for the per-skill cases and the candidate
sweep, 2026-07-04 for the skill axes not yet shipped as first-class skills.
Temporary local checkouts and public GitHub tree/raw-file research were used.

Verification posture: evidence references should stay source-addressable by repository, commit, path, and line range. Treat third-party script URLs in code snippets as source evidence about the inspected project, not as availability or endorsement claims for that provider URL.

Freshness note: every candidate is tied to the inspected commit, not a claim about the repository forever. Re-check the default branch before filing. A 2026-06-26 audit found all 10 `payment-page-client-security` candidates still at the default-branch HEAD; several high-churn first-13-skill research repos had already moved, so those rows remain useful leads but need current-source confirmation.

## Evidence status

Every row below sits at **E2 source-verified** on the evidence ladder in
[skill-evidence-coverage.md](./skill-evidence-coverage.md) unless it says
otherwise: the cited lines exist at the pinned commit and say what the row
claims. That is the whole claim. E2 is not a defect claim, and no E2 row here has
been reproduced, filed, or accepted upstream. Re-check the current default branch
and reproduce locally before filing an issue or PR.

Exactly one row sits at **E1 measured**: the n8n Storybook Callout case in the
strict Figma export recheck at the end of this document. A Figma export, a
Storybook render, and a pixel diff were actually run and the result recorded. It
is still not filed and still not a confirmed production defect.

Rows come in two depths. **Worked cases** carry a failure mode and a minimal PR
shape and are presented as tables. **Leads** are one-line source-verified
observations that have not been worked into full cases yet. Both sit at E2; they
differ in how much analysis has been done, not in how well the source was
checked.

Positive-control rows document patterns the skills should **not** flag as bugs.
They keep that label; the ladder rung describes verification, not verdict.

## Repositories sampled

| Repository | Commit inspected | Notes |
| --- | --- | --- |
| `ChatGPTNextWeb/NextChat` | `89b8f26` | Next.js/React app with i18n, SSR/client state, chat UI. |
| `actualbudget/actual` | `597bd86` | React desktop/client components and server integrations. |
| `appwrite/console` | `c1d66e2` | SvelteKit console with auth, forms, billing, filters. |
| `appwrite/console` | `cfd97e3` | Current tree/raw-file research for modal scroll-lock coordination. |
| `chatwoot/chatwoot` | `cf134de` | Vue dashboard widgets and custom attributes. |
| `maybe-finance/maybe` | `77b5469` | Rails app and design-system components. |
| `n8n-io/n8n` | `65660a4` | Vue app and design system. |
| `n8n-io/n8n` | `2cef574` | Current tree/raw-file research for clipboard, modal, drawer, and overlay cases. |
| `outline/outline` | `54be0a9` | React editor/plugins. |
| `calcom/cal.com` | `62317bd` | React app/utilities with booking CSV export and embed modal. |
| `directus/directus` | `de73e75` | Vue app and API import/export plus focus-trap overlays. |
| `formbricks/formbricks` | `fc93a74` | Survey/web app with CSV sample download and custom focus trap. |
| `grafana/grafana` | `70b22cbc51ac` | React app/design-system with inspector exports and modal API. |
| `lobehub/lobe-chat` | `97b48df` | React app utilities for file export, download, clipboard. |
| `mattermost/mattermost` | `f31c286` | React webapp with generated report downloads. |
| `outline/outline` | `34907e1` | React editor/settings app with CSV helper, download helper, inline menu overlay. |
| `supabase/auth-ui` | `d5e0827` | React/Solid/Svelte auth UI package. |
| `twentyhq/twenty` | `eedd838` | React app auth, onboarding, forms. |
| `gronxb/webview-bridge` | `2aec6ee` | React Native WebView bridge library. |
| `alinz/react-native-webview-bridge` | `8f303f5` | React Native WebView bridge library. |
| `inokawa/react-native-react-bridge` | `7f9e070` | React Native/Web bridge library. |
| `react-native-webview/react-native-webview` | `c152077` | React Native WebView core library/docs. |
| `Codecademy/gamut` | `837a2e6` | Design system + Figma Code Connect. |
| `narmi/design_system` | `d1d1323` | Design system + Figma Code Connect. |
| `primer/react` | `e58907c` | Design system + Figma Code Connect. |
| `spurtcommerce/spurtcommerce` | `34d3066` | Node/Angular e-commerce platform; Stripe redirect templates. |
| `saleor/storefront` | `14ffe08` | Next.js storefront with checkout root layout and Stripe payment components. |
| `SalesforceCommerceCloud/storefront-next-template` | `7f8d282` | Salesforce Commerce Cloud checkout template with analytics hooks. |
| `vendurehq/storefront-angular-starter` | `45b2f4e` | Angular commerce starter with example checkout payment form. |
| `bagisto/bagisto` | `ec179b5` | Laravel e-commerce platform with Razorpay drop-in UI package. |
| `spree/storefront` | `7ad5a07` | Official Next.js Spree storefront with global analytics and checkout tracking. |
| `spree/spree` | `7752652` | Spree docs for GTM analytics and payment integrations. |
| `pretix/pretix` | `a8997f8` | Django ticketing checkout with Stripe plugin frontend JS. |
| `reactioncommerce/example-storefront` | `4d6de85` | Next.js Reaction Commerce example storefront with analytics and Stripe. |
| `medusajs/nextjs-starter-medusa` | `9818886` | Next.js Medusa starter with Stripe payment wrapper. |
| `actualbudget/actual` | `fbdad57` | Validation-case snapshot. |
| `appwrite/console` | `1b41137` | Validation-case snapshot. |
| `chatwoot/chatwoot` | `41a3ab6` | Validation-case snapshot. |
| `date-fns/tz` | `9f391a0` | Validation-case snapshot. |
| `excalidraw/excalidraw` | `28a9b17` | Validation-case snapshot. |
| `excalidraw/excalidraw` | `c070c8f` | Validation-case snapshot. |
| `nextauthjs/next-auth-example` | `39ff2b7` | Validation-case snapshot. |
| `radix-ui/primitives` | `71a7122` | Validation-case snapshot. |
| `react-hook-form/react-hook-form` | `782313f` | Validation-case snapshot. |
| `remix-run/react-router` | `09e6020` | Validation-case snapshot. |
| `twentyhq/twenty` | `1b4bddb` | Validation-case snapshot. |

## Per-skill casebook

### `semantic-markup-contracts`

Status: covered by markup/a11y overlap cases below. The Maybe Finance tabs and Actual Budget menu/select rows exercise native HTML and ARIA role/state contracts, but they remain under `a11y-contract-testing` because the maintainer-facing patch shape is role-based regression coverage.

### `a11y-contract-testing`

| Case | Evidence | Failure mode | Minimal PR shape | Status |
|---|---|---|---|---|
| Maybe Finance design-system tabs expose only buttons/classes, not a tab contract|`maybe-finance/maybe@app/components/DS/tabs/nav.rb:12-15` renders `button` with only `data` targets; `tabs.rb:15-16` hides panels with class/data only; `tabs_controller.js:10,25,27` toggles classes. `rg role/aria` on the tabs files found no tab roles/states, only unrelated `variant` text.|Screen readers and role-based tests cannot discover `tab`, `tabpanel`, `aria-selected`, or tab-panel pairing even though the UI is visually tabbed.|Add `role="tablist"`, `role="tab"`, `role="tabpanel"`, stable ids, `aria-controls`, `aria-labelledby`, and update `aria-selected` in the controller. Add a ViewComponent/system test with `getByRole('tab', { name })`.| E2 source-verified, 2026-06-26 |
| Actual Budget component-library `Menu`/`Select` are keyboard-managed but not exposed as menu/listbox/combobox|`actualbudget/actual@packages/component-library/src/Menu.tsx:150-157` uses a focusable `View`; `Menu.tsx:185-217` maps items to `Button`; `Select.tsx:108-135` opens `Popover` + `Menu`. `rg role/aria` in those two files found only a textbox guard at `Menu.tsx:140`.|Custom menu/select works visually, but AT sees generic buttons/containers rather than `menu`/`menuitem` or `combobox`/`listbox`/`option` state.|Either migrate to React Aria `Menu/ListBox/Select` primitives or add the matching APG roles/states and tests that open the select/menu and query items by role.| E2 source-verified, 2026-06-26 |

Additional leads (source-verified, not worked into full cases):

1. **Appwrite branch selector mixes button trigger and listbox without full combobox state.** Evidence: `appwrite/console@src/lib/components/git/branchSelector.svelte:152-183` renders a trigger button, search input, and `ul role="listbox"`; options are at `:194-197`. Why: keyboard and screen-reader users need `aria-expanded`, active descendant/selection, and labelled popup relationships. Minimal PR: add combobox/listbox contract tests or use an accessible select primitive. Status: E2 source-verified, 2026-06-26.
2. **Actual Budget autocomplete rows use `role="button"` for a WebKit touch workaround.** Evidence: `actualbudget/actual@packages/desktop-client/src/components/autocomplete/Autocomplete.tsx:173-181` documents the touch hack and assigns `role="button"`. Why: list suggestions exposed as buttons can break combobox/listbox expectations. Minimal PR: reproduce touch issue and replace with semantic option roles plus targeted CSS/event workaround. Status: E2 source-verified, 2026-06-26.
3. **Actual Budget category autocomplete repeats the WebKit `role="button"` result hack.** Evidence: `actualbudget/actual@packages/desktop-client/src/components/autocomplete/CategoryAutocomplete.tsx:323-331`. Why: duplicate pattern means a semantic fix needs shared contract coverage. Minimal PR: cover both generic and category autocomplete with keyboard/screen-reader tests. Status: E2 source-verified, 2026-06-26.
4. **Actual Budget tag multi-autocomplete exposes selectable tags as buttons.** Evidence: `actualbudget/actual@packages/desktop-client/src/components/autocomplete/TagMultiAutocomplete.tsx:82` uses `role="button"`. Why: multi-select controls usually need listbox/option or checkbox semantics, not arbitrary button roles. Minimal PR: inspect rendered UX and add ARIA role contract test. Status: E2 source-verified, 2026-06-26.
5. **Appwrite bottom modal alert uses a clickable role button with ignored key-event lint.** Evidence: `appwrite/console@src/lib/components/bottomModalAlert.svelte:439-442` suppresses click-events-have-key-events and adds `tabindex="0" role="button"`. Why: Enter/Space activation and focus order are easy to regress in custom controls. Minimal PR: replace with `<button>` or add complete keyboard handlers/tests. Status: E2 source-verified, 2026-06-26.
6. **Appwrite collapsible item suppresses redundant-role lint on a button-like wrapper.** Evidence: `appwrite/console@src/lib/components/collapsibleItem.svelte:24-31` imports `clickOnEnter`, suppresses `a11y-no-redundant-roles`, and adds `role="button" tabindex="0"`. Why: a component-level a11y contract test can decide whether native button semantics are feasible. Minimal PR: convert to `<button>` or document/cover the custom interaction contract. Status: E2 source-verified, 2026-06-26.

### `cjk-text-and-input`

| Case | Evidence | Failure mode | Minimal PR shape | Status |
|---|---|---|---|---|
| NextChat search submits while IME composition is still active|`ChatGPTNextWeb/NextChat@app/components/search-chat.tsx:122-126` runs search on `e.key === "Enter"`. Same repo already has a correct guard in chat submit: `chat.tsx:266-290` tracks composition, ignores `keyCode == 229`, and checks `nativeEvent.isComposing`.|Korean/Japanese/Chinese users pressing Enter to confirm a candidate can trigger a premature search.|Reuse the existing chat submit IME guard in search input before accepting Enter. Add a regression test for `isComposing`/`keyCode 229`.| E2 source-verified, 2026-06-26 |
| Actual Budget reusable `Input` fires `onEnter` from `onKeyUp` without composition guard|`actualbudget/actual@packages/component-library/src/Input.tsx:71-76` calls `onEnter` whenever `e.key === 'Enter'`.|Every consumer of `onEnter` can submit/select while IME composition is confirming text.|In `Input`, skip `onEnter` when `e.nativeEvent.isComposing` or legacy `keyCode === 229`; document that `onEnter` is post-composition only.| E2 source-verified, 2026-06-26 |

Additional leads (source-verified, not worked into full cases):

1. **Actual Budget autocomplete save predicate treats Enter code as sufficient.** Evidence: `actualbudget/actual@packages/desktop-client/src/components/autocomplete/Autocomplete.tsx:199-201` returns `e.code === 'Enter'`; `:544-572` also handles Enter in the dropdown. Why: IME confirmation can be misread as save/select. Minimal PR: route all Enter-save paths through a shared `isComposing` guard. Status: E2 source-verified, 2026-06-26.
2. **Actual Budget tag autocomplete has a local keydown path separate from shared input.** Evidence: `actualbudget/actual@packages/desktop-client/src/components/autocomplete/TagAutocomplete.tsx:119-168` defines `handleKeyDown` and passes it to the input. Why: a fix in the base `Input` may not cover this direct handler. Minimal PR: add a utility and IME tests for tag entry. Status: E2 source-verified, 2026-06-26.
3. **Outline find-and-replace search Enter path lacks visible composition guard.** Evidence: `outline/outline@app/editor/components/FindAndReplace.tsx:235-262` handles find keys; `:248` switches on Enter. Why: CJK composition in find text can trigger navigation instead of committing text. Minimal PR: ignore Enter while `ev.nativeEvent.isComposing` and add editor test. Status: E2 source-verified, 2026-06-26.
4. **Outline replacement input submits replace on Enter without composition guard.** Evidence: `outline/outline@app/editor/components/FindAndReplace.tsx:309-314` calls `handleReplace(ev)` on `ev.key === "Enter"`; the input is wired at `:483-490`. Why: composing replacement text can execute replace too early. Minimal PR: guard composition in `handleReplaceKeyDown`. Status: E2 source-verified, 2026-06-26.
5. **Outline link editor handles Enter separately from another guarded media-link editor.** Evidence: `outline/outline@app/editor/components/LinkEditor.tsx:127-141` handles Enter; `MediaLinkEditor.tsx:80-88` explicitly checks `event.nativeEvent.isComposing`. Why: adjacent editor controls have inconsistent IME policy. Minimal PR: port the existing guard into `LinkEditor` and regression-test IME input. Status: E2 source-verified, 2026-06-26.
6. **Chatwoot inline input discards the KeyboardEvent for Enter.** Evidence: `chatwoot/chatwoot@app/javascript/dashboard/components-next/inline-input/InlineInput.vue:58` defines `onEnterPress` with no event; `:120` binds `@keydown.enter.prevent="onEnterPress"`. Why: the handler cannot check `event.isComposing`, so inline rename/save can fire mid-composition. Minimal PR: pass event, guard `isComposing`, test with Korean/Japanese IME. Status: E2 source-verified, 2026-06-26.
7. **NextChat prompt hints listen for global Enter while prompt suggestions are open.** Evidence: `ChatGPTNextWeb/NextChat@app/components/chat.tsx:325-352` registers `window` keydown and selects a prompt on Enter. Why: global handlers can race with focused composing text unless they check the event target/composition state. Minimal PR: ignore composing events and text-input targets. Status: E2 source-verified, 2026-06-26.
8. **Actual Budget sidebar rename handlers use Enter inline.** Evidence: `actualbudget/actual@packages/desktop-client/src/components/budget/SidebarCategory.tsx:169-170` and `SidebarGroup.tsx:243-244` branch on Enter. Why: if those controls are editable text fields, IME confirmation can save too early. Minimal PR: reproduce the edit state and add shared IME-safe Enter utility if applicable. Status: E2 source-verified, 2026-06-26.

### `constraint-validation-contracts`

| Case | Evidence | Failure mode | Minimal PR shape | Status |
|---|---|---|---|---|
| Appwrite migration export sets custom validity but never clears it on edit|`appwrite/console@src/routes/(console)/project-[region]-[project]/settings/migrations/exportModal.svelte:83-85` calls `endpointInput.setCustomValidity('Please enter a valid endpoint')` + `reportValidity()`; `:145-151` binds `endpointUrl`; `:181` disables by `isValidEndpoint(endpointUrl)`. No corresponding `setCustomValidity('')` was found for `endpoint`.|Once invalid, the native field can remain invalid even after the value becomes valid, blocking submission or keeping stale native error state.|Clear custom validity before validation and whenever `endpointUrl` changes; add a component test: invalid endpoint shows message, valid edit clears `validationMessage` and allows submit.| E2 source-verified, 2026-06-26 |
| Appwrite optional phone field keeps stale error after clearing an invalid value|`appwrite/console@src/lib/elements/forms/inputPhone.svelte:24-43` maps native validity to `error`; `:45-46` clears only when `value` is truthy; `auth/user-[user]/updatePhone.svelte:45-50` uses `InputPhone` without `required`.|For an optional phone, entering an invalid value then deleting it leaves the UI in error state even though empty is valid.|Clear when the element is valid, or when `!required && !value`; add a test for invalid phone -> empty string -> no helper/error state.| E2 source-verified, 2026-06-26 |

Additional leads (source-verified, not worked into full cases):

1. **Appwrite `InputDate` clears errors only after a non-empty value.** Evidence: `appwrite/console@src/lib/elements/forms/inputDate.svelte:24-38`. Why: optional date fields corrected to empty can retain stale invalid state. Minimal PR: distinguish required-empty from optional-empty and clear accordingly. Status: E2 source-verified, 2026-06-26.
2. **Appwrite `InputDomain` repeats truthy-only stale error clearing.** Evidence: `appwrite/console@src/lib/elements/forms/inputDomain.svelte:24-40`. Why: domain optional empty or corrected-to-empty states can stay invalid. Minimal PR: extract shared validity/error-state helper. Status: E2 source-verified, 2026-06-26.
3. **Appwrite `InputChoice` clears only on truthy value.** Evidence: `appwrite/console@src/lib/elements/forms/inputChoice.svelte:19-30`. Why: switch/checkbox wrappers can keep stale error when value becomes a valid false. Minimal PR: treat boolean false as valid when not required. Status: E2 source-verified, 2026-06-26.
4. **Appwrite `InputOTP` repeats custom invalid state with manual clear.** Evidence: `appwrite/console@src/lib/elements/forms/inputOTP.svelte:29-46,69-70`. Why: OTP pattern/required errors should clear as soon as the current value is valid. Minimal PR: centralize invalid-state handling and add pattern correction test. Status: E2 source-verified, 2026-06-26.

### `datetime-correctness`

| Case | Evidence | Failure mode | Minimal PR shape | Status |
|---|---|---|---|---|
| Appwrite timezone conversion reparses a locale string|`appwrite/console@src/routes/(console)/bottomAlerts.ts:39-48` builds `targetString`, then does `new Date(new Date(targetString).toLocaleString('en-US', { timeZone }))` before comparing with `now`.|Locale-string reparse is environment-dependent and loses the actual intended zone instant; promotions can start on the wrong local day/time.|Use an explicit timezone conversion helper/library (`date-fns-tz`, Temporal polyfill, or a known Appwrite helper) and test with non-local zones around midnight/DST.| E2 source-verified, 2026-06-26 |
| Chatwoot date-only custom attribute converts date input to UTC instants|`chatwoot/chatwoot@app/javascript/dashboard/components-next/CustomAttributes/DateAttribute.vue:37-54` displays with `toLocaleDateString()`, fills `<input type=date>` via `toISOString().slice(0, 10)`, and stores `new Date(value).toISOString()`.|A date-only UI value can shift by timezone because `YYYY-MM-DD` is treated as an instant/UTC conversion instead of a plain date.|Store/round-trip the plain `YYYY-MM-DD` value, or use date-only helpers; test in `America/Los_Angeles` and `Asia/Seoul`.| E2 source-verified, 2026-06-26 |

Additional leads (source-verified, not worked into full cases):

1. **Appwrite filters convert local `datetime-local` values to UTC ISO without an explicit timezone contract.** Evidence: `appwrite/console@src/lib/components/filters/content.svelte:112-113,170,252` creates a local datetime default and later `new Date(value).toISOString()`. Why: filter boundaries can shift around DST/timezones. Minimal PR: define UTC vs local filter semantics and test non-UTC timezone. Status: E2 source-verified, 2026-06-26.
2. **Appwrite filters modal has a parallel datetime conversion path.** Evidence: `appwrite/console@src/lib/components/filters/filtersModal.svelte:60-70` prepares local query values separately from filter content. Why: duplicated conversion paths can disagree. Minimal PR: share one datetime serializer/parser and timezone tests. Status: E2 source-verified, 2026-06-26.
3. **Actual Budget EnableBanking API formats dates via UTC ISO slices.** Evidence: `actualbudget/actual@packages/sync-server/src/app-enablebanking/app-enablebanking.ts:497-501` uses `new Date().toISOString().split('T')[0]` and `new Date(startDate).toISOString().split('T')[0]`. Why: bank date ranges are date-only and can shift for local dates. Minimal PR: use date-only formatting in the account/user timezone or API timezone. Status: E2 source-verified, 2026-06-26.
4. **NextChat chat list renders locale timestamps directly in render.** Evidence: `ChatGPTNextWeb/NextChat@app/components/chat-list.tsx:146` passes `new Date(item.lastUpdate).toLocaleString()`. Why: SSR/client locale or timezone differences can alter rendered text. Minimal PR: defer to client-only formatting or serialize locale-independent display. Status: E2 source-verified, 2026-06-26.
5. **Appwrite DPA download uses full ISO timestamp for a date-named document.** Evidence: `appwrite/console@src/routes/(console)/organization-[organization]/settings/downloadDPA.svelte:10` sets `const today = new Date().toISOString()`. Why: document/date labels can include UTC date not local user's date. Minimal PR: use date-only local/business timezone format. Status: E2 source-verified, 2026-06-26.
6. **Appwrite payment expiration month options depend on render-time local date.** Evidence: `appwrite/console@src/routes/(console)/account/payments/editPaymentModal.svelte:26,60-62,90` computes current year/month from `new Date()`. Why: SSR/client timezone or midnight edge can hide/show wrong expiration month. Minimal PR: compute on client or from server-provided current date with tests. Status: E2 source-verified, 2026-06-26.
7. **Appwrite collection layout builds default document timestamps at load time.** Evidence: `appwrite/console@src/routes/(console)/project-[region]-[project]/databases/database-[database]/collection-[collection]/+layout.svelte:11-17` uses `new Date().toISOString()` for initial document data. Why: defaults generated during SSR/load can become stale or mismatch client expectations. Minimal PR: generate at explicit create action time. Status: E2 source-verified, 2026-06-26.
8. **Appwrite collection export filename timestamp is generated at module/component evaluation.** Evidence: `appwrite/console@src/routes/(console)/project-[region]-[project]/databases/database-[database]/collection-[collection]/export/+page.svelte:24-31` uses `toLocalDateTimeISO(Date.now())`. Why: long-lived pages can export with stale timestamp. Minimal PR: compute timestamp when export starts. Status: E2 source-verified, 2026-06-26.

### `deeplink-hydration`

| Case | Evidence | Failure mode | Minimal PR shape | Status |
|---|---|---|---|---|
| Appwrite email/password login loses protected-route query state|`appwrite/console@src/routes/+layout.ts:87` sets `redirect` to `url.pathname` only, then redirects with other params at `:112`; login email/password only uses `$redirectTo`/account invalidation at `login/+page.svelte:60-66`. The GitHub OAuth path separately reconstructs `redirect + page.url.search` at `login/+page.svelte:81-91`.|Visiting a protected deep link with query params can return to the path but drop the original screen/filter/query after email/password login.|Preserve `url.pathname + url.search` as a safe same-origin redirect, or make email/password mirror the OAuth redirect+residual-search handling.| E2 source-verified, 2026-06-26 |
| Maybe Finance protected links always land at root after login|`maybe-finance/maybe@app/controllers/concerns/authentication.rb:18-25` redirects unauthenticated users to `new_session_url`; `sessions_controller.rb:16-17` creates the session then `redirect_to root_path`.|A user following `/accounts/123?tab=activity` or a shared import/deep link loses the intended destination after auth.|Store the requested full path in session for GET requests and redirect back after login with same-origin/path validation; add controller/request tests.| E2 source-verified, 2026-06-26 |

Additional leads (source-verified, not worked into full cases):

1. **Maybe Finance MFA path also loses return destination.** Evidence: `maybe-finance/maybe@app/controllers/sessions_controller.rb:11-17` redirects OTP-required users to `verify_mfa_path` and otherwise root; no return path is carried into the MFA branch. Why: protected deep links requiring MFA can succeed auth but still lose navigation context. Minimal PR: carry and validate same-origin return path through MFA. Status: E2 source-verified, 2026-06-26.
2. **Appwrite template deploy builds `login?redirect=` without encoding the full return URL.** Evidence: `appwrite/console@src/routes/(public)/template-[template]/+page.ts:13-15` sets `redirectTo` to `url.pathname + url.search` but redirects with `base + '/login?redirect=' + url.pathname + url.search`. Why: nested `?`/`&` params can become login-page params instead of return params. Minimal PR: use `encodeURIComponent(fullUrl)` like functions/sites deploy pages. Status: E2 source-verified, 2026-06-26.
3. **Appwrite hackathon public route redirects unauthenticated users to login without return state.** Evidence: `appwrite/console@src/routes/(public)/hackathon/+page.ts:4-8` redirects `!account` to `/login`. Why: public campaign/deep-link entry can be lost after authentication. Minimal PR: include encoded return path or use shared redirect helper. Status: E2 source-verified, 2026-06-26.
4. **Appwrite password recovery always navigates to login after success.** Evidence: `appwrite/console@src/routes/(public)/recover/+page.svelte:56-64` updates recovery then `goto(`${base}/login`)`. Why: password-reset flows often originate from protected links; return state may be lost after reset. Minimal PR: carry a validated `redirect` param through recovery if supplied. Status: E2 source-verified, 2026-06-26.
5. **NextChat command hook mutates `URLSearchParams` in place while processing command params.** Evidence: `ChatGPTNextWeb/NextChat@app/command.ts:15-30` iterates `searchParams`, deletes command keys, then calls `setSearchParams(searchParams)`. Why: mutation during iteration can drop or reorder unrelated deep-link query params. Minimal PR: clone params before deletion and test multi-param command links. Status: E2 source-verified, 2026-06-26.
6. **Twenty email verification cross-workspace redirect may drop `nextPath`.** Evidence: `twentyhq/twenty@packages/twenty-front/src/modules/auth/components/VerifyEmailEffect.tsx:87-95` redirects to workspace domain with `loginToken`, then only sets `verifyEmailRedirectPath` locally when already on the workspace. Why: verification links that include a target path can lose it across domain handoff. Minimal PR: include validated `nextPath` in `redirectToWorkspaceDomain` params. Status: E2 source-verified, 2026-06-26.
7. **Twenty verify-login-token fallback navigates to sign-in without preserving current return context.** Evidence: `twentyhq/twenty@packages/twenty-front/src/modules/auth/components/VerifyLoginTokenEffect.tsx:29-33` calls `navigate(AppPath.SignInUp)` when no token and no access pair. Why: expired/malformed magic links can lose where the user intended to return. Minimal PR: carry `returnToPath` or show recoverable error state with preserved query. Status: E2 source-verified, 2026-06-26.
8. **Twenty query-param state initializer is the single gate for `returnToPath`.** Evidence: `twentyhq/twenty@packages/twenty-front/src/modules/app/hooks/useInitializeQueryParamState.ts:48-60` reads `returnToPath` from `window.location.search` and validates it. Why: domain redirects or intermediate auth screens that omit the param lose return intent. Minimal PR: add a cross-auth-flow test covering `returnToPath` through verification/MFA. Status: E2 source-verified, 2026-06-26.

### `frontend-auth-flow-contracts`

| Case | Evidence | Failure mode | Minimal PR shape | Status |
|---|---|---|---|---|
| Supabase Auth UI update-password forms lack `autocomplete="new-password"`|React `supabase/auth-ui@packages/react/src/components/Auth/interfaces/UpdatePassword.tsx:48-56`; Solid `packages/solid/src/components/Auth/interfaces/UpdatePassword.tsx:52-62`. Both render password inputs without autocomplete.|Password managers cannot reliably generate/fill a new password in the reset/update-password flow.|Add `autoComplete="new-password"` / `autocomplete="new-password"` in React/Solid/Svelte update-password inputs; add a shallow/render assertion.| E2 source-verified, 2026-06-26 |
| Supabase Auth UI OTP token inputs lack `autocomplete="one-time-code"`|React `packages/react/src/components/Auth/interfaces/VerifyOtp.tsx:108-116`; Solid `packages/solid/src/components/Auth/interfaces/VerifyOtp.tsx:93-100`.|Mobile browsers cannot offer SMS/email OTP autofill for the token field.|Add `autoComplete="one-time-code"` / `autocomplete="one-time-code"` to token inputs; keep email/phone fields on their respective autocomplete values.| E2 source-verified, 2026-06-26 |

Additional leads (source-verified, not worked into full cases):

1. **Supabase Svelte update-password mirrors the missing new-password token.** Evidence: `supabase/auth-ui@packages/svelte/src/lib/Auth/interfaces/UpdatePassword.svelte:50-52` renders `id="password" type="password" name="password"`. Why: three framework packages should share auth-field contracts. Minimal PR: add `autocomplete="new-password"` and fixture parity. Status: E2 source-verified, 2026-06-26.
2. **Supabase Svelte OTP uses nonstandard `autocomplete="token"`.** Evidence: `supabase/auth-ui@packages/svelte/src/lib/Auth/interfaces/VerifyOtp.svelte:89-93` sets `autocomplete="token"`. Why: browsers expect `one-time-code`; `token` is not the WebAuthn/OTP autofill token. Minimal PR: change to `one-time-code`. Status: E2 source-verified, 2026-06-26.
3. **Appwrite password input primitive only accepts boolean autocomplete.** Evidence: `appwrite/console@src/lib/elements/forms/inputPassword.svelte:39-50` maps `autocomplete ? 'on' : 'off'`. Why: callers cannot express `current-password`, `new-password`, or account-specific auth tokens. Minimal PR: accept string autocomplete tokens with boolean backward compatibility. Status: E2 source-verified, 2026-06-26.
4. **Appwrite recovery form cannot mark reset fields as new password through the primitive.** Evidence: `appwrite/console@src/routes/(public)/recover/+page.svelte:82-104` uses password inputs for recovery; the primitive at `inputPassword.svelte:50` only emits on/off. Why: password managers can save/fill reset fields incorrectly. Minimal PR: pass `autocomplete="new-password"` after primitive supports string tokens. Status: E2 source-verified, 2026-06-26.
5. **Appwrite account password update form cannot distinguish current vs new password fields.** Evidence: `appwrite/console@src/routes/(console)/account/updatePassword.svelte:35-59` renders password update fields through the same primitive. Why: current password and new password need different autocomplete semantics. Minimal PR: use `current-password` for old password and `new-password` for new/confirm. Status: E2 source-verified, 2026-06-26.
6. **Appwrite OTP input primitive cannot express `one-time-code`.** Evidence: `appwrite/console@src/lib/elements/forms/inputOTP.svelte:55-66` maps `autocomplete ? 'on' : 'off'`. Why: MFA/OTP inputs miss mobile one-time-code autofill. Minimal PR: support string autocomplete and set OTP callsites to `one-time-code`. Status: E2 source-verified, 2026-06-26.

### `frontend-security-baseline`

| Case | Evidence | Failure mode | Minimal PR shape | Status |
|---|---|---|---|---|
| Appwrite AI markdown rewrites rendered anchors after markdown generation|`appwrite/console@src/lib/commandCenter/panels/ai.svelte:112-117` renders markdown then regex-rewrites `<a href>` to add `target="_blank"`; the HTML is injected with `{@html ...}` at `:198`.|This is a hardening/policy-consistency case, not a confirmed reverse-tabnabbing vulnerability claim: modern anchors generally imply `noopener`, but the post-render HTML rewrite is fragile and cannot add project-wide `noreferrer` consistently.|Generate `target`, `rel="noopener noreferrer"`, and allowed link attributes through the markdown renderer link rule instead of post-render regex; add a rendered-html assertion.| E2 source-verified, 2026-06-26 |
| NextChat plugin editor injects editable plugin YAML as HTML|`ChatGPTNextWeb/NextChat@app/components/plugin.tsx:347-349` uses `contentEditable` with `dangerouslySetInnerHTML={{ __html: editingPlugin.content }}`; `:61-72` reads edited text back into plugin content.|Plugin/YAML text is not HTML and can contain markup; rendering it as HTML creates an avoidable XSS/DOM clobbering surface.|Render plugin content as text (`{editingPlugin.content}` or `textContent` via ref) and preserve edit behavior; add a test with `<img onerror>`/`<script>` literal content.| E2 source-verified, 2026-06-26 |

Additional leads (source-verified, not worked into full cases):

1. **n8n dependency pill opens dynamic package links without opener isolation.** Evidence: `n8n-io/n8n@packages/frontend/editor-ui/src/app/components/DependencyPill.vue:163-171` calls `window.open(href, '_blank')`. Why: dependency URLs are external and user-visible. Minimal PR: add `noopener,noreferrer` features or safe link component. Status: E2 source-verified, 2026-06-26.
2. **n8n main header opens external links without explicit noopener.** Evidence: `n8n-io/n8n@packages/frontend/editor-ui/src/app/components/MainHeader/MainHeader.vue:198,229,247` calls `window.open(href, '_blank')`. Why: top-level navigation helpers should enforce a single external-link policy. Minimal PR: route through a shared `openExternal`. Status: E2 source-verified, 2026-06-26.
3. **n8n workflow card opens route hrefs in a new tab without opener isolation.** Evidence: `n8n-io/n8n@packages/frontend/editor-ui/src/app/components/WorkflowCard.vue:333` calls `window.open(route.href, '_blank')`. Why: even internal new-tab helpers should intentionally choose opener behavior. Minimal PR: add features or document same-origin exception with tests. Status: E2 source-verified, 2026-06-26.
4. **Appwrite bottom modal alert injects HTML message content.** Evidence: `appwrite/console@src/lib/components/bottomModalAlert.svelte:465` renders `{@html mobileConfig.message}`; the component also opens action URLs at `:135` and `:159`. Why: alert content and external actions should share sanitizer/link policy. Minimal PR: sanitize message HTML and route external opens through helper. Status: E2 source-verified, 2026-06-26.
5. **Appwrite CSV export opens generated download URLs without opener policy.** Evidence: `appwrite/console@src/lib/components/csvExportBox.svelte:31` calls `window.open(downloadUrl, '_blank')`. Why: generated URLs are usually safe, but the helper should encode intended opener behavior. Minimal PR: use a safe download helper or `noopener` feature. Status: E2 source-verified, 2026-06-26.
6. **NextChat artifacts share link uses `_blank` without `rel`.** Evidence: `ChatGPTNextWeb/NextChat@app/components/artifacts.tsx:194` renders `<a target="_blank" href={shareUrl}>`, while another repo link at `:232` includes `rel="noopener noreferrer"`. Why: inconsistent policy indicates a straightforward safety fix. Minimal PR: add `rel="noopener noreferrer"` to share link. Status: E2 source-verified, 2026-06-26.

### `i18n-copy-and-layout`

| Case | Evidence | Failure mode | Minimal PR shape | Status |
|---|---|---|---|---|
| Supabase Auth UI password-limit error is hardcoded English and misspelled|React `EmailAuth.tsx:87-88`, `UpdatePassword.tsx:28-29`; Solid `EmailAuth.tsx:72-73`, `UpdatePassword.tsx:23-24`; Svelte `EmailAuth.svelte:50-51`, `UpdatePassword.svelte:28-29` all set `Password exceeds maxmium length of 72 characters`.|Localized apps cannot translate the error; all frameworks show a typo in user-facing auth copy.|Move the message into shared i18n variables (with a corrected default: “maximum”), parameterize `{max}`, and reuse it across React/Solid/Svelte.| E2 source-verified, 2026-06-26 |
| Chatwoot writer character counter is hardcoded English/plural text|`chatwoot/chatwoot@app/javascript/dashboard/components/widgets/WootWriter/constants.js:6-8` defines English `characters remaining/over`; `ReplyTopPanel.vue:144-147` builds strings with template concatenation.|Non-English locales get English text; singular/plural languages get incorrect forms such as `1 characters remaining`.|Replace constants with `$t`/i18n plural keys, pass `count`, and add locale entries/tests for `one` and `other`.| E2 source-verified, 2026-06-26 |

Additional leads (source-verified, not worked into full cases):

1. **Appwrite domain input has hardcoded validation strings.** Evidence: `appwrite/console@src/lib/elements/forms/inputDomain.svelte:24-36` sets `Must be a valid domain`, `This field is required`, and native messages. Why: validation copy is user-facing and repeated across locales. Minimal PR: localize custom messages and preserve native fallback only where intended. Status: E2 source-verified, 2026-06-26.
2. **Appwrite email input has hardcoded validation strings.** Evidence: `appwrite/console@src/lib/elements/forms/inputEmail.svelte:21-32` sets `Emails should be formatted as: name@example.com` and required text. Why: form errors are core UI copy. Minimal PR: localize with shared validation messages. Status: E2 source-verified, 2026-06-26.
3. **Appwrite number input has hardcoded range messages.** Evidence: `appwrite/console@src/lib/elements/forms/inputNumber.svelte:33-51` builds English less-than/greater-than errors. Why: grammar and interpolation order differ by locale. Minimal PR: move min/max messages to translation helpers. Status: E2 source-verified, 2026-06-26.
4. **Appwrite file input has hardcoded extension/size errors.** Evidence: `appwrite/console@src/lib/elements/forms/inputFile.svelte:54-59,74-81,104-109` sets English upload errors. Why: upload failures often block task completion and should be localizable. Minimal PR: shared localized file-validation helper. Status: E2 source-verified, 2026-06-26.
5. **Appwrite branch selector hardcodes search placeholder text.** Evidence: `appwrite/console@src/lib/components/git/branchSelector.svelte:164-170` renders `placeholder="Find a branch..."`. Why: search controls should not remain English in localized console screens. Minimal PR: accept translated placeholder prop or use i18n. Status: E2 source-verified, 2026-06-26.
6. **Appwrite recovery success copy has an English grammar typo.** Evidence: `appwrite/console@src/routes/(public)/recover/+page.svelte:64-68` emits `Password been updated successfully`. Why: auth recovery copy is high-trust UI. Minimal PR: correct grammar and route through localization if available. Status: E2 source-verified, 2026-06-26.

### `ssr-hydration-mismatch`

| Case | Evidence | Failure mode | Minimal PR shape | Status |
|---|---|---|---|---|
| NextChat default chat state is generated with `nanoid()`/`Date.now()` during module initialization|`ChatGPTNextWeb/NextChat@app/store/chat.ts:68-71` creates message ids/dates with `nanoid()` and `new Date().toLocaleString()`; `:99` creates `BOT_HELLO`; `:104-115` creates default sessions with `nanoid()` and `Date.now()`; `:227` and `:271` initialize stores with `createEmptySession()`.|Server-rendered default store and client first render can disagree on ids/dates before persisted-store hydration, causing hydration warnings or immediate DOM replacement.|Use deterministic SSR-safe initial state (empty until hydration or fixed ids/dates), then create real sessions client-side after hydration. Add a hydration smoke test that asserts no recoverable hydration errors.| E2 source-verified, 2026-06-26 |
| NextChat chat-list renders locale-dependent time during first render|`ChatGPTNextWeb/NextChat@app/components/chat-list.tsx:146` renders `new Date(item.lastUpdate).toLocaleString()` and `:148` keys by generated id.|Server locale/timezone and browser locale/timezone can produce different timestamp text for the same session; this amplifies the default-state mismatch above.|Render a stable ISO/placeholder during SSR and localize after mount, or pin explicit locale/timeZone; assert hydration has no text mismatch.| E2 source-verified, 2026-06-26 |

Additional leads (source-verified, not worked into full cases):

1. **NextChat exporter preview renders Date.now fallback and locale string.** Evidence: `ChatGPTNextWeb/NextChat@app/components/exporter.tsx:552-554` formats `props.messages.at(-1)?.date ?? Date.now()` with `toLocaleString()`. Why: empty/export preview can mismatch across SSR/client. Minimal PR: compute fallback after mount or pass deterministic export time. Status: E2 source-verified, 2026-06-26.
2. **NextChat message selector formats message dates with locale strings.** Evidence: `ChatGPTNextWeb/NextChat@app/components/message-selector.tsx:222` renders `new Date(m.date).toLocaleString()`. Why: repeated localized render-time formatting needs one hydration-safe display helper. Minimal PR: shared timestamp component with SSR-safe placeholder. Status: E2 source-verified, 2026-06-26.
3. **NextChat mask defaults include generated IDs/timestamps.** Evidence: `ChatGPTNextWeb/NextChat@app/store/mask.ts:37,45` uses generated IDs/date defaults. Why: persisted stores that initialize during render can mismatch. Minimal PR: ensure defaults are client-only or serialized. Status: E2 source-verified, 2026-06-26.
4. **NextChat config defaults include `Date.now()`.** Evidence: `ChatGPTNextWeb/NextChat@app/store/config.ts:42` uses `Date.now()` in default state. Why: non-deterministic default state can leak into SSR markup/tests. Minimal PR: move to client initialization. Status: E2 source-verified, 2026-06-26.
5. **Appwrite footer computes current year during component evaluation.** Evidence: `appwrite/console@src/lib/layout/footer.svelte:17,40` sets `const currentYear = new Date().getFullYear()` and renders it. Why: New Year boundary can produce SSR/client mismatch. Minimal PR: server-provided year or client-only update. Status: E2 source-verified, 2026-06-26.
6. **Appwrite collection export timestamp is created before the user starts export.** Evidence: `appwrite/console@src/routes/(console)/project-[region]-[project]/databases/database-[database]/collection-[collection]/export/+page.svelte:24-31`. Why: render-time timestamps can be stale and potentially mismatch. Minimal PR: compute on export action. Status: E2 source-verified, 2026-06-26.

### `webview-bridge-pages`

| Case | Evidence | Failure mode | Minimal PR shape | Status |
|---|---|---|---|---|
| `gronxb/webview-bridge` native `onMessage` parses every message as bridge JSON without a guard|`gronxb/webview-bridge@packages/react-native/src/createWebView.tsx:217-224` calls consumer `props.onMessage?.(event)`, then immediately `JSON.parse(event.nativeEvent.data)` and switches on `type` at `:225+`.|Any non-bridge `postMessage` from page content can throw in the bridge handler, breaking the WebView message loop despite consumer `onMessage` having handled it.|Wrap parse/schema validation in `try/catch`; ignore/pass through unknown messages; unit-test invalid JSON and unknown `type`.| E2 source-verified, 2026-06-26 |
| `linkBridge` fires `onReady` before delayed native hydration has completed|`gronxb/webview-bridge@packages/web/src/linkBridge.ts:116-132` reads `window.__bridgeMethods__ ?? []` and subscribes to a `hydrate` event when empty; `:165` calls `onReady?.(proxy)` unconditionally before waiting for that hydrate callback.|A web page can enable bridge-dependent UI while no native methods/state are available yet, causing fallback/no-op calls and racey startup behavior.|If methods are absent, call `onReady` only after the hydrate event updates the instance; otherwise call immediately. Add a startup test where native injects methods after page load.| E2 source-verified, 2026-06-26 |

Additional leads (source-verified, not worked into full cases):

1. **`alinz/react-native-webview-bridge` Android native-to-web message injection is not JavaScript-string escaped.** Evidence: `alinz/react-native-webview-bridge@android/src/main/java/com/github/alinz/reactnativewebviewbridge/WebViewBridgeManager.java:56-58` builds `WebViewBridge.onMessage('` + message + `')`. Why: apostrophes, backslashes, or script fragments in messages can break delivery or execute unintended code. Minimal PR: JSON-stringify/quote payloads before interpolation and add quote/backslash regression tests. Status: E2 source-verified, 2026-06-26.
2. **`alinz/react-native-webview-bridge` iOS native-to-web injection uses the same raw quoted payload shape.** Evidence: `alinz/react-native-webview-bridge@ios/RCTWebViewBridge.m:97-107` formats `WebViewBridge.__push__('%@')` into a JavaScript command. Why: the iOS path can diverge or fail on the same payloads as Android. Minimal PR: share/port a safe JavaScript string encoder and test both platforms. Status: E2 source-verified, 2026-06-26.
3. **`alinz/react-native-webview-bridge` web receive queue is LIFO, not FIFO.** Evidence: `alinz/react-native-webview-bridge@scripts/webviewbridge.js:30-37` does `receiveQueue.push(message)` then `receiveQueue.pop()`. Why: bursts of native messages can be delivered in reverse order. Minimal PR: replace `pop()` with `shift()` or drain FIFO and add a two-message ordering test. Status: E2 source-verified, 2026-06-26.
4. **`alinz/react-native-webview-bridge` embedded iOS bridge duplicates the LIFO receive queue.** Evidence: `alinz/react-native-webview-bridge@ios/RCTWebViewBridge.m:361-368` embeds the same `receiveQueue.push()`/`receiveQueue.pop()` script. Why: fixing only `scripts/webviewbridge.js` would leave the shipped iOS injected copy stale. Minimal PR: update generated/embedded script and add parity check. Status: E2 source-verified, 2026-06-26.
5. **`inokawa/react-native-react-bridge` silently swallows malformed WebView messages.** Evidence: `inokawa/react-native-react-bridge@src/native/index.ts:32-39` catches `JSON.parse(event.nativeEvent.data)` errors and leaves `// NOP`. Why: integration failures become invisible to app code and tests. Minimal PR: optional `onMessageError`, dev warning, or ignored-message filter with tests. Status: E2 source-verified, 2026-06-26.
6. **`gronxb/webview-bridge` debug console integration parses forwarded log payloads without guard.** Evidence: `gronxb/webview-bridge@packages/react-native/src/integrations/console.ts:40-47` calls `JSON.parse(message)` inside `handleLog`. Why: a bridge debug log with unexpected payload can crash debug handling and mask the original WebView issue. Minimal PR: guard parse and display raw payload fallback. Status: E2 source-verified, 2026-06-26.
7. **`alinz/react-native-webview-bridge` hides loading/error WebViews with height/flex only.** Evidence: `alinz/react-native-webview-bridge@webview-bridge/index.android.js:102-107,229-232` and `webview-bridge/index.ios.js:154-155,310-313` push `styles.hidden` with `height: 0, flex: 0`. Why: WebView surfaces can retain focus/paint/touch artifacts even when layout-collapsed. Minimal PR: verify with RN smoke test; if reproduced, add `opacity`, `pointerEvents`, or conditional unmount. Status: E2 source-verified, 2026-06-26.
8. **`react-native-webview` examples still normalize wildcard `originWhitelist`.** Evidence: `react-native-webview/react-native-webview@docs/Getting-Started.md:129` and `docs/Guide.md:32` show `originWhitelist={['*']}`. Why: bridge pages often copy examples into app WebViews; safer docs can reduce accidental external navigation trust. Minimal PR: docs-only note showing tight origin lists for app-owned bridge pages. Status: E2 source-verified, 2026-06-26.

### `download-export-safety`

Strict note: these are open-source export/copy cases, not a list of confirmed defects. Positive controls keep the skill from flagging safe helpers as bugs. Re-check the current default branch and add a local reproduction before filing.

1. **Outline members CSV helper**
   - Evidence: `outline/outline@shared/utils/csv.ts:21-29,82-94`; `app/scenes/Settings/components/ExportCSV.tsx:60-63`.
   - Validation value: Positive control; formula-prefix and control/bidi cleanup live in a shared helper.
   - Minimal PR/test shape: Keep helper tests for formula prefixes, controls, and export caller use.
   - Status: E2 source-verified, 2026-06-26, re-checked 2026-08-01 (positive control).

2. **Directus collection CSV export**
   - Evidence: `directus/directus@app/src/utils/save-as-csv.ts:45-59,78`.
   - Validation value: Candidate; collection/display values can become spreadsheet cells, so formula-cell policy needs confirmation.
   - Minimal PR/test shape: Add formula-prefix regression or document the existing `json2csv` transform policy.
   - Status: E2 source-verified, 2026-06-26, re-checked 2026-08-01.

3. **Cal.com booking CSV export**
   - Evidence: `calcom/cal.com@apps/web/modules/bookings/components/BookingsCsvDownload.tsx:102-105`; `packages/lib/csvUtils.ts:49-60`.
   - Validation value: Candidate; helper quotes quotes/commas/newlines but not formula prefixes.
   - Minimal PR/test shape: Extend `sanitizeValue` with a documented cell policy and tests for `=`, `+`, `-`, `@`, and newline-created cells.
   - Status: E2 source-verified, 2026-06-26, re-checked 2026-08-01.

4. **Grafana inspector CSV export**
   - Evidence: `grafana/grafana@public/app/features/inspector/utils/download.ts:78-92`.
   - Validation value: Positive/lead; Excel-aware branch shows spreadsheet compatibility is intentional, while formula policy should be checked for datasource text.
   - Minimal PR/test shape: Keep Excel delimiter/encoding tests; add formula-prefix test only if current `toCSV` lacks a policy.
   - Status: E2 source-verified, 2026-06-26, re-checked 2026-08-01.

5. **Outline Blob download helper**
   - Evidence: `outline/outline@app/utils/download.ts:78-80,104-106`.
   - Validation value: Positive control; object URL creation and scheduled revoke are helper-owned.
   - Minimal PR/test shape: Assert revoke after the click path at helper level.
   - Status: E2 source-verified, 2026-06-26 (positive control).

6. **Mattermost generated zip download**
   - Evidence: `mattermost/mattermost@webapp/channels/src/components/post_view/data_spillage_report/data_spillage_download_report/data_spillage_download_report.tsx:64-71`.
   - Validation value: Positive control; the large Blob URL is revoked after anchor click.
   - Minimal PR/test shape: Mock `createObjectURL`/`revokeObjectURL` if maintainers want coverage.
   - Status: E2 source-verified, 2026-06-26 (positive control).

7. **Formbricks sample CSV download**
   - Evidence: `formbricks/formbricks@apps/web/modules/ee/unify-feedback/sources/components/csv-feedback-source-ui.tsx:186-195`.
   - Validation value: Positive control; one-shot sample CSV creates and revokes a Blob URL.
   - Minimal PR/test shape: Keep the revoke assertion if the handler is tested.
   - Status: E2 source-verified, 2026-06-26 (positive control).

8. **Lobe Chat export helper**
   - Evidence: `lobehub/lobe-chat@packages/utils/src/client/exportFile.ts:3-18`.
   - Validation value: Positive control; shared helper revokes the Blob URL and removes the anchor.
   - Minimal PR/test shape: Do not flag call sites using this helper; test the helper once.
   - Status: E2 source-verified, 2026-06-26 (positive control).

9. **n8n clipboard helper**
   - Evidence: `n8n-io/n8n@packages/frontend/editor-ui/src/app/composables/useClipboard.ts:24-32`.
   - Validation value: Positive control; pop-out clipboard failure is caught and falls back.
   - Minimal PR/test shape: Keep a rejected clipboard path test so UI does not claim copied on failure.
   - Status: E2 source-verified, 2026-06-26 (positive control).

10. **NextChat image copy**
    - Evidence: `ChatGPTNextWeb/NextChat@app/components/exporter.tsx:427-440`.
    - Validation value: Candidate; `navigator.clipboard.write(...).then(...)` inside `try` needs explicit async rejection handling.
    - Minimal PR/test shape: Use `await` or `.catch` and test that a rejected clipboard promise shows failure state.
    - Status: E2 source-verified, 2026-06-26.

#### Re-verification, 2026-08-01

Method: raw-file fetch of each cited path at the default branch, then locating
the cited pattern and recording its current line. No local checkout, no
reproduction, and nothing filed. This only answers "does the evidence still
resolve", which is the first of the three things the evidence-status note above
requires before filing.

All five rows still resolve. Line drift since the 2026-06-26 snapshot is minor
and the cited ranges still contain the claimed code.

| Row | Cited 2026-06-26 | Located 2026-08-01 | Status |
| --- | --- | --- | --- |
| `outline/outline@shared/utils/csv.ts` | 21-29, 82-94 | formula-prefix replace at 22; `sanitizeValue` at 13, 75, 83, 93 | Positive control holds. The shared helper still prefixes `+ - = @` and a wider symbol class, strips control characters, zero-width and bidirectional marks, and both the header and body paths still route through `escapeCSVField(sanitizeValue(...))`. |
| `directus/directus@app/src/utils/save-as-csv.ts` | 45-59, 78 | display handler at 53; `text/csv` save at 78; `json2csv` at 2, 68 | Candidate still live. Display-transformed collection values still reach CSV cells, and the file contains no formula-prefix or sanitize step anywhere. |
| `calcom/cal.com@packages/lib/csvUtils.ts` | 49-60 | helper at 49; quote doubling at 55; comma/newline quoting at 57 | Candidate still live. The helper still quotes quotes, commas and newlines, and still applies no formula prefix. |
| `calcom/cal.com@apps/web/modules/bookings/components/BookingsCsvDownload.tsx` | 102-105 | row map at 103; filename and download at 104-105 | Caller unchanged within the cited range. |
| `grafana/grafana@public/app/features/inspector/utils/download.ts` | 78-92 | UTF-16LE BOM branch at 78; `toCSV` at 77 and 83; utf-8 blob at 85 | Positive/lead holds. The Excel-aware encoding branch is still deliberate, so spreadsheet consumption is intended and the formula-cell question is a policy question rather than an oversight. |

What this does not establish: that any of the three candidates is a defect the
maintainer would accept. Formula-cell policy on CSV export is contested, and a
project can reasonably decide the spreadsheet is responsible for how it
interprets a cell. The maintainer-facing question is whether the project intends
its exports to be opened in a spreadsheet, which the Grafana row shows can be an
explicit yes. Filing still requires the local reproduction and the failing test
this document asks for.

### `overlay-focus-scroll-contracts`

Strict note: these are open-source overlay lifecycle cases, not a list of confirmed defects. Positive controls prevent overclaiming around libraries that already manage focus, inertness, or scroll lock.

1. **Appwrite modal scroll-lock coordination**
   - Evidence: `appwrite/console@src/lib/components/modal.svelte:31-38`.
   - Validation value: Candidate/positive mix; the modal coordinates Melt listbox `removeScroll` side effects.
   - Minimal PR/test shape: Test modal plus combobox repeated open/close for body marker and padding restore.
   - Status: E2 source-verified, 2026-06-26.

2. **n8n modal active-element blur**
   - Evidence: `n8n-io/n8n@packages/frontend/editor-ui/src/app/components/Modal.vue:81-87`.
   - Validation value: Candidate; blur can avoid hidden-focus warnings but may lose the return target.
   - Minimal PR/test shape: Test open from trigger, close, and focus restore.
   - Status: E2 source-verified, 2026-06-26.

3. **n8n drawer active-element blur**
   - Evidence: `n8n-io/n8n@packages/frontend/editor-ui/src/app/components/ModalDrawer.vue:40-67`.
   - Validation value: Candidate; drawer focus restore and listener cleanup need separate coverage.
   - Minimal PR/test shape: Test drawer Escape/close focus restore and event cleanup.
   - Status: E2 source-verified, 2026-06-26.

4. **Directus dialog focus-trap manager**
   - Evidence: `directus/directus@app/src/components/v-dialog.vue:8-13,90-92`.
   - Validation value: Positive control; nested overlay trap coordination can be centralized.
   - Minimal PR/test shape: Keep manager tests so child close does not release the parent trap.
   - Status: E2 source-verified, 2026-06-26 (positive control).

5. **Directus menu focus-trap config**
   - Evidence: `directus/directus@app/src/components/v-menu.vue:149-155,167`.
   - Validation value: Positive control; non-dialog overlay still configures return focus and outside click.
   - Minimal PR/test shape: Test Tab/Escape/click-outside and return focus when enabled.
   - Status: E2 source-verified, 2026-06-26 (positive control).

6. **Excalidraw dialog active-element tracking**
   - Evidence: `excalidraw/excalidraw@packages/excalidraw/components/Dialog.tsx:52,73-75`.
   - Validation value: Positive control; restore decisions consider previous/current active element.
   - Minimal PR/test shape: Keep a test for nested menu/dialog close and focus restoration.
   - Status: E2 source-verified, 2026-06-26 (positive control).

7. **Cal.com embed ModalBox body overflow**
   - Evidence: `calcom/cal.com@packages/embeds/embed-core/src/ModalBox/ModalBox.ts:25-27,255-256`.
   - Validation value: Candidate; one static saved overflow slot may fail nested modals or pre-existing styles.
   - Minimal PR/test shape: Add a nested open/close test preserving previous overflow while another modal remains open.
   - Status: E2 source-verified, 2026-06-26.

8. **Formbricks custom focus trap**
   - Evidence: `formbricks/formbricks@packages/surveys/src/lib/use-focus-trap.ts:36-37,50-54`.
   - Validation value: Positive control; previous focus and `preventScroll` reduce scroll-jump regressions.
   - Minimal PR/test shape: Keep tests for delayed focus changes and restore guard.
   - Status: E2 source-verified, 2026-06-26 (positive control).

9. **Outline inline editor menu**
   - Evidence: `outline/outline@app/editor/components/InlineMenu.tsx:44-47,90-107`.
   - Validation value: Positive control; a non-modal Radix menu can intentionally pair with `RemoveScroll`.
   - Minimal PR/test shape: Test that the selection menu does not trap the whole page and still locks scroll as intended.
   - Status: E2 source-verified, 2026-06-26 (positive control).

10. **Grafana design-system Modal API**
    - Evidence: `grafana/grafana@packages/grafana-ui/src/components/Modal/Modal.tsx:19,37-53`.
    - Validation value: Positive control; `trapFocus` and custom-title `ariaLabel` are explicit consumer contracts.
    - Minimal PR/test shape: Cover `trapFocus={false}`, custom title `ariaLabel`, Escape, and backdrop defaults.
    - Status: E2 source-verified, 2026-06-26 (positive control).

### Skill axes covered by leads only

These skills have source-verified leads but no worked case yet.

#### `js-form-validation-contracts`

1. **Twenty CreateProfile Enter handler bypasses React Hook Form/Zod validation.** Evidence: `twentyhq/twenty@packages/twenty-front/src/pages/onboarding/CreateProfile.tsx:87-96` configures `useForm` with `zodResolver`, but `:167` calls `onSubmit(getValues())` directly instead of `handleSubmit(onSubmit)`. Why: keyboard submission can skip schema validation and field-error lifecycle. Minimal PR: route Enter through `handleSubmit(onSubmit)` and add keyboard test. Status: E2 source-verified, 2026-06-26.
2. **Outline webhook subscription can submit with no selected events.** Evidence: `outline/outline@plugins/webhooks/client/components/WebhookSubscriptionForm.tsx:140-153` initializes form state; event checkboxes are registered around `:274-277`; submit disables only on submit state around `:320-324`. Why: a webhook with zero events is likely useless or server-rejected. Minimal PR: add events length validation and group error. Status: E2 source-verified, 2026-06-26.
3. **Twenty PasswordReset surfaces server/update failures only as snackbars.** Evidence: `twentyhq/twenty@packages/twenty-front/src/pages/auth/PasswordReset.tsx:102-109` configures form resolver; `:161-164`, `:186-207` enqueue error snackbars. Why: validation-contract skill should check whether field-level errors are lost for password/token failures. Minimal PR: map password validation failures to field errors where possible. Status: E2 source-verified, 2026-06-26.
4. **Twenty onboarding InviteTeam has separate email validation and disabled state worth contract-testing.** Evidence: `twentyhq/twenty@packages/twenty-front/src/pages/onboarding/InviteTeam.tsx:12-20` uses `zodResolver`; workspace invite component also has email empty validation at `modules/workspace/components/WorkspaceInviteTeam.tsx:57-60,226`. Why: invite flows often regress by disabling submit without explaining invalid rows. Minimal PR: add tests for empty, invalid, duplicate, and mixed email lists. Status: E2 source-verified, 2026-06-26.
5. **Outline Matomo settings submit button does not appear disabled by form validity.** Evidence: `outline/outline@plugins/matomo/client/Settings.tsx:40-43` extracts `formState`; `:129-131` disables on `formState.isSubmitting`. Why: invalid base URL/site ID errors should block submit visibly before server roundtrip. Minimal PR: add `mode: 'onChange'`, required/url validation, and disabled/error tests. Status: E2 source-verified, 2026-06-26.
6. **Outline Google Analytics settings mirrors the same validity-gating question.** Evidence: `outline/outline@plugins/googleanalytics/client/Settings.tsx:38-41` extracts form state; `:108-110` disables only while submitting. Why: measurement ID format/required validation can be caught client-side. Minimal PR: add client validation and tests. Status: E2 source-verified, 2026-06-26.
7. **Outline API key creation relies on a custom `submitDisabled` path.** Evidence: `outline/outline@app/scenes/ApiKeyNew/index.tsx:71-98` handles submit; `:148` disables button with `submitDisabled`. Why: custom disabled logic can diverge from browser required/constraint validation. Minimal PR: add form-level tests for empty name/permission states. Status: E2 source-verified, 2026-06-26.
8. **Twenty WorkspaceInviteTeam duplicates validation outside form submit semantics.** Evidence: `twentyhq/twenty@packages/twenty-front/src/modules/workspace/components/WorkspaceInviteTeam.tsx:57-60,226` defines email empty validation and disables from `isEmailsEmpty || !!errors.emails`. Why: custom disabled state can prevent native submit/error reporting. Minimal PR: ensure disabled state and visible error text are covered together. Status: E2 source-verified, 2026-06-26.
9. **Appwrite migration export manually validates endpoint outside form control flow.** Evidence: `appwrite/console@src/routes/(console)/project-[region]-[project]/settings/migrations/exportModal.svelte:82-85` imperatively calls `setCustomValidity`/`reportValidity`. Why: imperative validation must clear and integrate with submit state. Minimal PR: move endpoint validation into input constraint/state and test invalid-then-valid submit. Status: E2 source-verified, 2026-06-26.
10. **Appwrite file input has separate drop and input validation paths.** Evidence: `appwrite/console@src/lib/elements/forms/inputFile.svelte:48-59,74-85,104-109` validates dropped files and selected files separately. Why: JS form validation contracts often fail when picker and drag/drop disagree. Minimal PR: shared file validator with tests for both paths. Status: E2 source-verified, 2026-06-26.

#### `component-extraction-judgment`

1. **Twenty workspace creation V1/V2 forms duplicate substantial business logic.** Evidence: `twentyhq/twenty@packages/twenty-front/src/modules/auth/sign-in-up/components/internal/SignInUpWorkspaceCreationForm.tsx:59-129` and `SignInUpWorkspaceCreationFormV2.tsx:101-177` both manage workspace name, subdomain availability, logo upload/remove, submit, and Enter behavior. Why: fixes to validation or upload behavior can drift between V1/V2. Minimal PR: extract a controller hook while keeping separate presentation. Status: E2 source-verified, 2026-06-26.
2. **Appwrite shared text-like inputs duplicate invalid-state mapping and stale clear logic.** Evidence: `appwrite/console@src/lib/elements/forms/inputText.svelte:24-44`, `inputEmail.svelte:21-37`, `inputDate.svelte:24-38`, `inputDomain.svelte:24-40`, `inputNumber.svelte:33-56`. Why: validation bugs appear across wrappers. Minimal PR: extract a validation-state helper/action. Status: E2 source-verified, 2026-06-26.
3. **Appwrite deploy entry pages duplicate login redirect return handling.** Evidence: `appwrite/console@src/routes/(public)/functions/deploy/+page.ts:15-19`, `sites/deploy/+page.ts:15-19`, and `template-[template]/+page.ts:13-15` each build redirect state. Why: template page already differs by missing encoding. Minimal PR: shared `redirectToLoginWithReturn(url)` helper. Status: E2 source-verified, 2026-06-26.
4. **Appwrite datetime filter conversion is split across filter content/modal code.** Evidence: `appwrite/console@src/lib/components/filters/content.svelte:112-113,170,252` and `filtersModal.svelte:60-70`. Why: date serialization drift creates hard-to-debug filter bugs. Minimal PR: extract datetime query serializer/parser with timezone tests. Status: E2 source-verified, 2026-06-26.
5. **Supabase Auth UI repeats password-limit typo and auth field contracts across React/Solid/Svelte.** Evidence: `supabase/auth-ui@packages/react/src/components/Auth/interfaces/EmailAuth.tsx:88`, Solid `EmailAuth.tsx:73`, Svelte `EmailAuth.svelte:51`, and update-password/OTP inputs in all three packages. Why: framework parity bugs are ideal candidates for shared fixtures or generated tests. Minimal PR: shared auth-field contract tests across packages. Status: E2 source-verified, 2026-06-26.
6. **Actual Budget Enter-key save behavior is duplicated across input/autocomplete components.** Evidence: `actualbudget/actual@packages/component-library/src/Input.tsx:71-76`, `packages/desktop-client/src/components/autocomplete/Autocomplete.tsx:199-201,550-579`, and `TagAutocomplete.tsx:119-168`. Why: IME-safe Enter fixes can miss one path. Minimal PR: extract `isCommitEnter(event)` helper and cover callsites. Status: E2 source-verified, 2026-06-26.
7. **Appwrite external-link opening is repeated across layout, modals, and export helpers.** Evidence: `appwrite/console@src/routes/(console)/+layout.svelte:107-132`, `src/lib/components/bottomModalAlert.svelte:135,159`, `src/lib/components/csvExportBox.svelte:31`. Why: security policy (`noopener`, URL validation) should not be repeated manually. Minimal PR: shared `openExternal`/`openDownload` helper. Status: E2 source-verified, 2026-06-26.
8. **Appwrite form autocomplete primitives repeat boolean-only autocomplete API.** Evidence: `appwrite/console@src/lib/elements/forms/inputPassword.svelte:50`, `inputOTP.svelte:66`, `inputEmail.svelte:56`, `inputDate.svelte:57`, `inputText.svelte:61`. Why: auth-specific autocomplete tokens cannot be expressed consistently. Minimal PR: extract typed autocomplete prop support across primitives. Status: E2 source-verified, 2026-06-26.
9. **NextChat repeats locale timestamp rendering across chat surfaces.** Evidence: `ChatGPTNextWeb/NextChat@app/components/chat-list.tsx:146`, `message-selector.tsx:222`, and `exporter.tsx:552-554`. Why: SSR/locale formatting fixes should be centralized. Minimal PR: shared `TimestampText` component with hydration-safe behavior. Status: E2 source-verified, 2026-06-26.
10. **Primer Code Connect form-control mappings would benefit from shared parity helpers.** Evidence: `primer/react@packages/react/src/TextInput/TextInput.figma.tsx:35-85`, `packages/react/src/Select/Select.figma.tsx:5-25`, `packages/react/src/Radio/Radio.figma.tsx:5-25`, and `packages/react/src/Checkbox/Checkbox.figma.tsx:5-29` map overlapping label/caption/validation concepts. Why: repeated mapping logic makes visual/design drift likely. Minimal PR: shared Code Connect form-control mapping utilities or parity tests. Status: E2 source-verified, 2026-06-26.

#### `payment-page-client-security`

1. **Spurtcommerce Stripe redirect templates load an unused jQuery CDN before Stripe.js.** Evidence: `spurtcommerce/spurtcommerce@api/views/pages/stripe/process.ejs:1-10` and `api/dist/add-ons/Payment/Stripe/template/process.ejs:1-10` load `cdnjs.cloudflare.com/ajax/libs/jquery/3.4.1/jquery.min.js`, then `https://js.stripe.com/v3/`, then only call `stripe.redirectToCheckout(...)`; no jQuery use is visible in the template. Why: this is a tiny payment-init page where an extra third-party script increases payment-path script inventory and authorization burden. Minimal PR: remove the unused jQuery script from source and packaged template or regenerate dist from the source fix. Status: E2 source-verified, 2026-06-26.
2. **Saleor Storefront renders Vercel Speed Insights inside the checkout root layout that also hosts Stripe payment UI.** Evidence: `saleor/storefront@src/app/(checkout)/layout.tsx:3,21-24` imports and renders `<SpeedInsights />`; `src/checkout/components/payment/integrated-payment-ui.tsx:48-62` routes Stripe providers to `StripePayment`; `src/checkout/components/payment/stripe/stripe-payment.tsx:5-6` uses Stripe loader/elements. Why: telemetry on a payment surface is not automatically wrong, but a maintainer can recognize the missing payment-page script inventory/justification question. Minimal PR: document or configure how to disable/justify Speed Insights on checkout/payment routes. Status: E2 source-verified, 2026-06-26.
3. **Salesforce Commerce Cloud storefront template tracks checkout events with auth/session payloads.** Evidence: `SalesforceCommerceCloud/storefront-next-template@src/components/checkout/checkout-form-page.tsx:328-349` calls `analytics.trackCheckoutStart` and `trackCheckoutStep`; `src/hooks/use-analytics.ts:83-91` adds payload fields `userType`, `encUserId`, and `usid`; `src/analytics/page-view-tracker.tsx:80-115` has a page-view blocklist mechanism that needs checkout/payment defaults verified. Why: starter templates influence merchants; checkout telemetry should be explicit, minimized, and blocklist-aware. Minimal PR: add default checkout/payment analytics blocklist guidance or payment-page analytics inventory docs. Status: E2 source-verified, 2026-06-26.
4. **Vendure Angular starter exposes a merchant-controlled card-number form in a starter checkout example.** Evidence: `vendurehq/storefront-angular-starter@src/app/checkout/components/checkout-payment/checkout-payment.component.html:6-19` warns not to use real cards but still binds `name="cardNumber"` with `[(ngModel)]="cardNumber"`; `checkout-payment.component.ts:19-21` stores `cardNumber`, `expMonth`, and `expYear`. Why: it is explicitly an example, so the finding is not a vulnerability claim, but starter code is commonly copied into production. Minimal PR: strengthen docs, remove real-looking PAN bindings, or replace the example with hosted-field/tokenization placeholder guidance. Status: E2 source-verified, 2026-06-26.
5. **Bagisto Razorpay drop-in UI has an external payment script plus inline payment orchestration with no visible CSP/header evidence in the template.** Evidence: `bagisto/bagisto@packages/Webkul/Razorpay/src/Resources/views/drop-in-ui.blade.php:6` loads `https://checkout.razorpay.com/v1/checkout.js`; `:59-105` constructs `new Razorpay(...)`, handles payment IDs/signature, and redirects. Why: Razorpay scripts are expected, but payment-page script/header inventory and inline-script nonce/hash posture are reviewer-recognizable evidence gaps. Minimal PR: add package docs or header/CSP guidance for this payment page; avoid claiming SRI is required for Razorpay’s dynamic script. Status: E2 source-verified, 2026-06-26.
6. **Spree Storefront loads GTM, Vercel Analytics, and Speed Insights globally while checkout emits payment-info analytics events.** Evidence: `spree/storefront@src/app/layout.tsx:1-3,52,57-58` imports/renders Google Tag Manager, Vercel Analytics, and Speed Insights globally; `src/app/[country]/[locale]/(checkout)/checkout/[id]/CheckoutPageContent.tsx:246` calls `trackBeginCheckout` and `:475` calls `trackAddPaymentInfo`; `src/lib/analytics/gtm.ts:251-260` pushes `add_payment_info`. Why: the README’s hosted-payment claim can still coexist with payment-page script evidence duties. Minimal PR: exclude/justify analytics on checkout/payment routes and document the payment-page runtime script inventory. Status: E2 source-verified, 2026-06-26.
7. **Spree docs promote GTM events including payment info next to payment integration docs without a payment-page script warning.** Evidence: `spree/spree@docs/integrations/analytics/google-tag-manager.mdx:7` explains GTM can deploy analytics/marketing scripts including Hotjar; `:65-71` lists checkout progress and payment info events; `docs/integrations/payments/stripe.mdx` documents Stripe integration. Why: this is a docs-hardening case, not a bug; maintainers can accept a narrow warning that GTM/marketing tags on checkout/payment pages need explicit authorization/inventory. Minimal PR: add a PCI payment-page script controls note to GTM/payment docs. Status: E2 source-verified, 2026-06-26.
8. **Pretix dynamically loads Stripe.js via jQuery `$.ajax` on the payment form.** Evidence: `pretix/pretix@src/pretix/plugins/stripe/static/pretixplugins/stripe/pretix-stripe.js:50-65` calls `$.ajax({ url: 'https://js.stripe.com/v3/', dataType: 'script' })` and initializes Stripe/Elements in the success handler. Why: dynamic loading may be intentional, but it makes runtime script inventory and CSP evidence less obvious than a provider script tag. Minimal PR: document the payment-page runtime script inventory and CSP expectations, or move to a clearer provider-compatible loader if maintainers prefer. Status: E2 source-verified, 2026-06-26.
9. **Reaction Commerce example storefront injects Segment analytics snippets and Stripe.js from the global document.** Evidence: `reactioncommerce/example-storefront@pages/_document.js:35-47` builds scripts from analytics providers with `innerHTML: provider.renderScript()` and conditionally adds `https://js.stripe.com/v3/`; `custom/analytics/segment.js:24-35` renders the Segment snippet; `components/StripeCard/StripeCard.js:94-99` confirms card payment with Stripe Elements. Why: example storefronts should make checkout analytics and payment scripts explicit. Minimal PR: document how to disable analytics on checkout/payment paths or add payment-page script inventory/CSP guidance. Status: E2 source-verified, 2026-06-26.
10. **Medusa Next.js starter uses Stripe Elements without a visible checkout CSP/payment-page script inventory example.** Evidence: `medusajs/nextjs-starter-medusa@src/modules/checkout/components/payment-wrapper/index.tsx:3,19-23` loads Stripe; `src/modules/checkout/components/payment-button/index.tsx:69-90` confirms card payment through Stripe elements; `next.config.js:1-58` has no visible `headers()`/CSP example, and `rg 'headers\(|Content-Security-Policy|script-src|frame-src|connect-src|form-action|integrity='` returns no hits in the checkout starter. Why: absence of CSP is common in starters, so this is a docs/example hardening candidate rather than a bug. Minimal PR: add optional checkout CSP/payment-page runtime script inventory guidance for Stripe deployments. Status: E2 source-verified, 2026-06-26.

### Skill axes not yet shipped as first-class skills

#### `core-web-vitals-performance-contracts`

1. **Next.js Image already encodes a single hero preload/fetch-priority contract.** Evidence: `vercel/next.js@65dbff0:packages/next/src/shared/lib/get-img-props.ts:557-559,773-783` maps `preload || priority` into metadata and exposes `fetchPriority`. Why: LCP regressions often come from copied hero-image examples that mix `priority`, `preload`, or `fetchPriority` inconsistently. Minimal PR: add a docs/example regression checking one above-the-fold image emits exactly one preload/fetch-priority path and warns on duplicated intent. Status: E2 source-verified, 2026-07-04 (positive control).
2. **Gatsby Image documents its CLS-prevention wrapper contract.** Evidence: `gatsbyjs/gatsby@1f38c85:docs/docs/conceptual/image-plugin-architecture.md:15-21,61` explains `GatsbyImage` and the `Sizer` wrapper that preserves layout before image load. Why: this is a strong source-backed pattern for a skill that checks image placeholders, aspect-ratio reservation, and layout shift. Minimal PR: add a docs smoke example that flags when a custom image wrapper drops the `Sizer`/aspect-ratio reservation. Status: E2 source-verified, 2026-07-04 (positive control).
3. **Nuxt eagerly discovers and prefetches visible route links.** Evidence: `nuxt/nuxt@252d77e:docs/1.getting-started/07.routing.md:50-52,59-61` says `<NuxtLink>` prefetches page components and payload when links enter the viewport. Why: dense link grids can improve navigation but also compete with critical current-page resources, affecting LCP/INP budgets. Minimal PR: add a performance note or example showing when to disable/tune prefetch for large above-fold nav/card grids. Status: E2 source-verified, 2026-07-04.
4. **Astro examples distinguish high-priority hero/background assets from sized content images.** Evidence: `withastro/astro@6929e40:examples/basics/src/components/Welcome.astro:7-11` sets `fetchpriority="high"` on a background image and explicit dimensions on the logo; `examples/blog/src/layouts/BlogPost.astro:63` renders a sized blog hero image. Why: a CWV skill can catch accidental `fetchpriority="high"` sprawl or missing dimensions in copied Astro examples. Minimal PR: add an Astro docs/example note and fixture for “only the real LCP image gets high priority; all image cards reserve dimensions.” Status: E2 source-verified, 2026-07-04.
5. **MUI Masonry documents SSR defaults that can decide CLS.** Evidence: `mui/material-ui@2bcf35f:docs/data/material/components/masonry/masonry.md:68-72` explains `defaultHeight`, `defaultColumns`, `defaultSpacing`, and warns that SSR item placement differs. Why: bad default height/column guesses produce visible masonry reflow after hydration. Minimal PR: add an SSR visual regression around under-estimated `defaultHeight` and document “reserve enough rows” as a contract. Status: E2 source-verified, 2026-07-04.
6. **Headless UI Transition history shows transition cleanup/order defects are user-visible.** Evidence: `tailwindlabs/headlessui@eea57cf:packages/@headlessui-react/CHANGELOG.md:601,612,619,631` lists fixes for scroll lock with hidden transitions, cleanup order, blank screens, and transitionend/transitioncancel. Why: animation primitives can damage INP/visual stability even when API usage looks correct. Minimal PR: add a reduced-motion/transitioncancel example test that verifies no blank screen and no stuck transition state. Status: E2 source-verified, 2026-07-04 (positive control).
7. **Chakra UI docs site has responsive card grids that can become image/layout-shift fixtures.** Evidence: `chakra-ui/chakra-ui@882af4b:apps/www/app/blog/page.tsx:34-38` and `apps/www/app/launch-week/page.tsx:132-170` use `SimpleGrid` plus Next images/cards. Why: copied docs-card layouts need explicit image sizing, priority discipline, and responsive grid shift checks. Minimal PR: add a docs-site visual/perf smoke around the launch/blog grid at mobile and desktop widths. Status: E2 source-verified, 2026-07-04.
8. **TanStack Router kitchen-sink wires route tree creation and provider setup in one large example.** Evidence: `TanStack/router@a3e24c3:examples/react/kitchen-sink-file-based/src/main.tsx:10,17,124` imports `routeTree`, creates the router, and renders `<RouterProvider>`. Why: large route trees plus default preloading can hide route-discovery or data-waterfall INP regressions. Minimal PR: add an example budget test that checks first-interaction latency when route preloading is enabled on many visible links. Status: E2 source-verified, 2026-07-04.
9. **Shopify Hydrogen examples eagerly load the first collection images and prefetch product links.** Evidence: `Shopify/hydrogen@bccd91a:docs/shopify-dev/analytics-setup/ts/app/routes/collections.$handle.tsx:89-94,120-124` passes `loading={index < 8 ? 'eager' : undefined}` and `prefetch="intent"`. Why: ecommerce collection pages are a realistic LCP/INP tradeoff: too many eager images or too much intent prefetch hurts current-page responsiveness. Minimal PR: add a docs note/test that caps eager image count and asserts product-link prefetch starts on intent, not initial render. Status: E2 source-verified, 2026-07-04.
10. **React Router exposes `discover` and `prefetch` knobs with performance tradeoffs.** Evidence: `remix-run/react-router@0cd1157:docs/api/components/Link.md:44-64` documents eager route discovery and data/module prefetching controls. Why: route-discovery defaults can become a CWV contract in link-heavy pages, especially dashboards and catalog grids. Minimal PR: add a doc example showing dense-list links with `discover="none"` or tuned prefetch plus a navigation smoke test. Status: E2 source-verified, 2026-07-04.

#### `frontend-data-fetching-cache-contracts`

1. **SWR infinite-scroll example mutates page size and resets to the first page.** Evidence: `vercel/swr@c822a5d:examples/infinite-scroll/pages/index.js:24,40,54` uses `useSWRInfinite`, `setSize(size + 1)`, and `setSize(1)`. Why: pagination cache contracts break when reset, mutate, and revalidation semantics are not tested together. Minimal PR: add an example test checking filter/reset does not show stale extra pages and revalidates the first page. Status: E2 source-verified, 2026-07-04.
2. **TanStack Query infinite-scroll example defines `useInfiniteQuery` with an initial page parameter.** Evidence: `TanStack/query@be8f11b:examples/react/load-more-infinite-scroll/src/pages/index.tsx:35-47`; related docs explain `maxPages` eviction at `docs/framework/react/guides/infinite-queries.md` when present. Why: cache eviction/back-navigation behavior is user-visible in long feeds. Minimal PR: add a test for “load pages, navigate away/back, no duplicated or evicted page surprise.” Status: E2 source-verified, 2026-07-04.
3. **Redux Toolkit Query documents infinite query page retention limits.** Evidence: `reduxjs/redux-toolkit@62d21b0:docs/rtk-query/usage/infinite-queries.mdx:70-78,123` defines `infiniteQueryOptions` and `maxPages: 3`. Why: list caches with eviction need explicit UX contracts for back/forward navigation and tag invalidation. Minimal PR: add a doc test showing invalidation after `maxPages` eviction and expected visible pages. Status: E2 source-verified, 2026-07-04.
4. **Apollo Client docs show `fetchPolicy` and `nextFetchPolicy` changing after the first execution.** Evidence: `apollographql/apollo-client@8408a6d:docs/source/data/queries.mdx:580-595,632` covers `network-only`, `cache-first`, and policy demotion. Why: a common stale-data bug is assuming the first network policy applies to later variable changes. Minimal PR: add a recipe/test for variable switch + offline/online transition checking the intended cache policy. Status: E2 source-verified, 2026-07-04.
5. **urql docs expose `requestPolicy` and `cache-and-network` double-delivery behavior.** Evidence: `urql-graphql/urql@d510a9a:docs/basics/react-preact.md:220-234,239-253` describes `cache-first` and `cache-and-network`. Why: components need a contract for stale cached result followed by network result without flicker or false loading state. Minimal PR: add a docs test showing stale render, network update, and loading indicator expectations. Status: E2 source-verified, 2026-07-04.
6. **Relay query-loader docs make query lifetime/disposal explicit.** Evidence: `facebook/relay@c8df8fd:website/docs/guided-tour/rendering/queries.mdx:122-129,177-179,208` introduces `useQueryLoader`, notes render-phase restrictions, and discusses disposal/lifetime management. Why: retained queries can leak data or show stale screens if ownership is unclear. Minimal PR: add a fixture that switches tabs/routes and asserts disposed query refs stop retaining stale data. Status: E2 source-verified, 2026-07-04.
7. **React Router documents race-aware revalidation after actions/fetchers.** Evidence: `remix-run/react-router@0cd1157:docs/explanation/race-conditions.md:27-33,88` says interrupted requests are cancelled and stale revalidations are not committed. Why: route data caches need explicit “fresh response wins” contracts when users submit multiple actions. Minimal PR: add an example test with two out-of-order fetcher responses and one page-data revalidation. Status: E2 source-verified, 2026-07-04 (positive control).
8. **Next.js app-router docs define cache mode defaults and route-level enforcement.** Evidence: `vercel/next.js@65dbff0:docs/01-app/02-guides/caching-without-cache-components.mdx:11-15,129-132,180` describes `cache: 'force-cache'`, `only-cache`, `only-no-store`, and `no-store` defaults. Why: server-data staleness bugs often start from route-level cache defaults being invisible in code review. Minimal PR: add a docs scenario that checks a route segment with strict cache policy errors or revalidates as described. Status: E2 source-verified, 2026-07-04.
9. **tRPC docs wire TanStack Query dehydration/hydration as the SSR data contract.** Evidence: `trpc/trpc@340811b:www/docs/client/tanstack-react-query/server-components.mdx:170-187,412` covers dehydrate options and `HydrationBoundary`. Why: stale hydration and duplicate refetches are hard to see without a concrete cache-boundary test. Minimal PR: add an SSR example test that checks server-prefetched data hydrates once and refetch policy is intentional. Status: E2 source-verified, 2026-07-04.
10. **Nuxt data-fetching docs require manual loading-state handling for lazy fetches.** Evidence: `nuxt/nuxt@252d77e:docs/1.getting-started/10.data-fetching.md:249-259,263-280` explains `lazy: true`, `status === 'pending'`, and `useLazyFetch`. Why: lazy data fetching is a cache/state contract, not just syntax; missing pending/empty states create blank or stale screens. Minimal PR: add a docs example test for lazy route navigation that verifies pending, success, and refetch states. Status: E2 source-verified, 2026-07-04.

#### `async-effect-race-contracts`

1. **React docs teach the classic `ignore` flag for effect fetch races.** Evidence: `reactjs/react.dev@2639f36:src/content/reference/react/useEffect.md:912-920,940-948,1001-1004` sets `let ignore = false`, checks it before `setBio`, and flips it in cleanup. Why: this is the canonical race-shape that a skill should detect and either accept or upgrade to abortable I/O. Minimal PR: add an adjacent `AbortController` variant and a test checking that stale promise resolution does not update state. Status: E2 source-verified, 2026-07-04 (positive control).
2. **Supabase React auth example mixes async session fetch and auth subscription cleanup.** Evidence: `supabase/supabase-js@7f9d2b3:packages/core/auth-js/example/react/src/App.tsx:29-35,38-59,62-71` calls `getSession()` in an effect and returns an unsubscribe for `onAuthStateChange`. Why: the initial async `getSession` path can still resolve after unmount while the subscription path is cleaned up. Minimal PR: add an ignore/abort guard for initial session load and a StrictMode test. Status: E2 source-verified, 2026-07-04.
3. **Firebase quickstart shows both one-shot and persistent auth observers.** Evidence: `firebase/quickstart-js@ecc525b:auth/google-credentials.html:63-64,129-136` self-unsubscribes one observer but registers another app-level `onAuthStateChanged` observer. Why: copied React/Vue wrappers often forget the persistent unsubscribe and duplicate listeners after remount. Minimal PR: add framework wrapper docs/tests requiring returned unsubscribe in component lifecycle. Status: E2 source-verified, 2026-07-04.
4. **Socket.IO examples attach long-lived event listeners in client stores.** Evidence: `socketio/socket.io@d2d753f:examples/basic-crud-application/angular-client/src/app/store.ts:30-54` registers connect and CRUD listeners on a store socket. Why: UI integrations that mount/unmount stores or React effects need `off`/cleanup contracts to avoid duplicate messages. Minimal PR: add a React/Angular lifecycle example test that destroys the store/component and asserts no duplicate listener after remount. Status: E2 source-verified, 2026-07-04.
5. **ws docs and examples make broken-connection termination explicit.** Evidence: `websockets/ws@a2f4e7c:README.md:452-517` covers heartbeat termination and clearing intervals on `close`; `examples/express-session-parse/public/app.js:41-42` nulls browser handlers. Why: WebSocket UI hooks need close/interval/listener cleanup, not just message handling. Minimal PR: add a browser-client example with mount/unmount cleanup and a fake-timer heartbeat test. Status: E2 source-verified, 2026-07-04.
6. **TanStack Query cancellation docs depend on consuming the provided `AbortSignal`.** Evidence: `TanStack/query@be8f11b:docs/framework/react/guides/query-cancellation.md:6-14,23-33,85` explains unused queries are not cancelled by default unless the signal is consumed. Why: fetchers that ignore `signal` can resolve stale data after unmount or key change. Minimal PR: add a lint/doc recipe that flags a query function not passing `signal` to fetch/axios. Status: E2 source-verified, 2026-07-04.
7. **React Router documents stale revalidation cancellation semantics.** Evidence: `remix-run/react-router@0cd1157:docs/explanation/race-conditions.md:12-33,88` describes interrupted navigation/fetcher cancellation and fresh-response commits. Why: it is a positive-control model for “latest request wins” UI behavior. Minimal PR: add a small out-of-order network test in docs/examples that users can copy. Status: E2 source-verified, 2026-07-04 (positive control).
8. **React Hook Form tracks async `defaultValues` with `isLoading`.** Evidence: `react-hook-form/react-hook-form@6112441:src/useForm.ts:61-66,81-82` sets `isLoading` when `defaultValues` is a function and resets when static defaults change. Why: identity switches during async default loading can race with user edits. Minimal PR: add a regression for user typing before async defaults resolve, then prop identity changes. Status: E2 source-verified, 2026-07-04.
9. **react-use `useAsyncFn` implements call-id and mounted guards.** Evidence: `streamich/react-use@fbe99c6:src/useAsyncFn.ts:41-59` increments `lastCallId` and checks `isMounted()` before setting success/error state. Why: this is a compact positive-control implementation for take-latest async UI effects. Minimal PR: add docs explicitly naming the stale-call contract and a two-promise race test. Status: E2 source-verified, 2026-07-04 (positive control).
10. **Zustand persist exposes manual hydration timing and rehydrate hooks.** Evidence: `pmndrs/zustand@a1f685c:src/middleware/persist.ts:114-120,139,370` defines `skipHydration`, `rehydrate`, and auto-hydration behavior; docs reference `onRehydrateStorage` and `skipHydration` at `docs/reference/integrations/persisting-store-data.md:149-166,288,748`. Why: pre-hydration writes can be overwritten by delayed storage hydration. Minimal PR: add a test for “user changes state before async storage resolves; rehydrate must not clobber newer state.” Status: E2 source-verified, 2026-07-04.

#### `pwa-offline-cache-contracts`

1. **vite-plugin-pwa docs warn that custom `globPatterns` replaces the default match set.** Evidence: `vite-pwa/vite-plugin-pwa@05670fc:docs/guide/service-worker-precache.md:29-46` and `docs/guide/static-assets.md:13-18,40` explain `globPatterns` and the need to include all asset patterns. Why: missing icons/fonts/HTML from the precache is an offline-only user-visible failure. Minimal PR: add a config smoke that builds and asserts manifest entries for HTML, JS, CSS, icons, and fonts. Status: E2 source-verified, 2026-07-04.
2. **Workbox precache entries allow nullable revisions.** Evidence: `GoogleChrome/workbox@62b9d8b:packages/workbox-precaching/src/_types.ts:22-23` defines `url` and optional `revision?: string | null`. Why: `revision: null` shifts freshness to URL hashing and can create stale runtime assets if copied blindly. Minimal PR: add docs/tests contrasting revisioned app assets with URL-versioned CDN assets. Status: E2 source-verified, 2026-07-04.
3. **Angular service-worker config distinguishes prefetch and lazy install/update modes.** Evidence: `angular/angular@b126dc9:adev/src/content/ecosystem/service-workers/config.md:56-68,93-120,206` documents `assetGroups`, `installMode`, and `dataGroups`. Why: a route can appear installable but be unavailable offline if lazy resources were never requested. Minimal PR: add an offline smoke recipe for first-load, lazy route, then airplane-mode navigation. Status: E2 source-verified, 2026-07-04.
4. **SvelteKit service-worker docs show eager app/static caching and note dev-mode manifest gaps.** Evidence: `sveltejs/kit@d89edcc:documentation/docs/30-advanced/40-service-workers.md:11-13,30,116` imports `build`, `files`, `version` and notes `build`/`prerendered` are empty in development. Why: offline tests that run only in dev can falsely pass or miss production precache behavior. Minimal PR: add a production-build offline smoke that asserts `build`, `files`, and prerendered pages are cached. Status: E2 source-verified, 2026-07-04.
5. **MDN PWA example uses `cache.addAll` in install and network fallback in fetch.** Evidence: `mdn/pwa-examples@901aca8:js13kpwa/sw.js:32-54` installs with `cache.addAll(contentToCache)` and falls back around `fetch(e.request)`. Why: `addAll` is all-or-nothing; one bad asset can break install and leave no offline shell. Minimal PR: add a failing-asset install test and docs warning about cache-manifest validation. Status: E2 source-verified, 2026-07-04.
6. **Mozilla serviceworker-cookbook demonstrates cache-first fallback patterns.** Evidence: `mozilla/serviceworker-cookbook@fb3b7c5:cache-from-zip/worker.js:33-34,116` checks `cache.match(event.request)` before `fetch` and opens a named cache. Why: cache-first examples need explicit stale-data and version-bump contracts. Minimal PR: add a versioned-cache example test checking old cached API/content purge on activate. Status: E2 source-verified, 2026-07-04.
7. **next-pwa default runtime caching uses Workbox strategy names that can affect auth/API staleness.** Evidence: `shadowwalker/next-pwa@2f21bc2:cache.js:7,18,29,40,108` lists `CacheFirst` and `StaleWhileRevalidate`; `index.js:76,279-334` wires default runtime caching. Why: API/runtime caching copied without auth and cache-key rules can leak or stale user data. Minimal PR: add docs/tests for authenticated API routes defaulting to `NetworkOnly` or explicit no-store. Status: E2 source-verified, 2026-07-04.
8. **@vite-pwa/astro examples add broad Workbox glob patterns.** Evidence: `vite-pwa/astro@76edbb1:examples/pwa-simple/astro.config.mjs:24,48-50` configures `registerType: 'autoUpdate'` and `globPatterns: ['**/*.{css,js,html,svg,png,ico,txt}']`. Why: Astro static assets can appear cached while fonts/data/routes are omitted. Minimal PR: add a built-manifest assertion for every public asset type used by the template. Status: E2 source-verified, 2026-07-04.
9. **@vite-pwa/nuxt transforms Nuxt build assets through Workbox config utilities.** Evidence: `vite-pwa/nuxt@468ebee:src/utils/config.ts:23-34,137` and `src/utils/module.ts:247,316-320` wire Workbox config and generated workbox files. Why: Nuxt baseURL/buildDir changes can break service-worker asset URLs silently. Minimal PR: add a fixture with non-root `app.baseURL` and assert offline asset URLs resolve. Status: E2 source-verified, 2026-07-04.
10. **Nuxt community PWA module documents offline page and opaque-response caveats.** Evidence: `nuxt-community/pwa-module@a533b0f:docs/content/en/workbox.md:9,120,212,374` and `src/workbox/defaults.ts:16,36` cover full offline support, `offlinePage`, opaque responses, and default runtime caching. Why: third-party and offline-fallback caching needs explicit strategy contracts. Minimal PR: add a docs/example test for third-party opaque request strategy and offline-page routing precedence. Status: E2 source-verified, 2026-07-04.

#### `large-list-data-grid-contracts`

1. **MUI X Data Grid documents row/column buffer and full virtualization disablement.** Evidence: `mui/mui-x@7eb9bfa46c7c365983545bec06fc8263d21e97b6:docs/data/data-grid/virtualization/virtualization.md:14,30,75-79` covers `rowBufferPx`, `columnBufferPx`, and `disableVirtualization`. Why: test suites often disable virtualization, masking production blank-row or over-render regressions. Minimal PR: add a production-mode scroll smoke that keeps virtualization enabled and checks no blank rows during fast scroll. Status: E2 source-verified, 2026-07-04.
2. **TanStack Virtual makes `estimateSize` and virtual item measurement explicit.** Evidence: `TanStack/virtual@850947a42dc322ac1dd0328a15ed344763932b60:docs/api/virtualizer.md:31-34,521` and `TanStack/virtual@850947a42dc322ac1dd0328a15ed344763932b60:docs/api/virtual-item.md:57-65` document estimated size, measurement, and lane assignment. Why: bad estimates create scroll jump, blank gaps, or masonry lane instability. Minimal PR: add a dynamic-height example test using measured rows and asserting scroll anchor preservation. Status: E2 source-verified, 2026-07-04.
3. **TanStack Table’s virtualization guide warns against rendering every row model row.** Evidence: `TanStack/table@393bb68:docs/framework/react/guide/virtualization.md:48,84,93,327` describes `useVirtualizer`, `estimateSize`, and the pitfall of rendering `table.getRowModel().rows.map(...)` instead of virtual items. Why: a table can look correct in small fixtures while exploding on large data. Minimal PR: add a guide test that flags when a virtualized example renders all 10k rows. Status: E2 source-verified, 2026-07-04.
4. **AG Grid documents row buffer math and custom-row-height impact.** Evidence: `ag-grid/ag-grid@5b13a14:documentation/ag-grid-docs/src/content/docs/dom-virtualisation/index.mdoc:23-29,48-56` explains `rowBuffer`, pixel range, custom heights, and ignored buffer when virtualization is suppressed. Why: row spans/custom heights can blank during scroll unless buffer sizing is tested. Minimal PR: add a scroll e2e with custom row height and low `rowBuffer` to assert no visual blanks. Status: E2 source-verified, 2026-07-04.
5. **React Data Grid computes viewport rows from `rowHeight`, scroll position, and virtualization flag.** Evidence: `adazzle/react-data-grid@3698d5e:src/hooks/useViewportRows.ts:7-23,31-35,105-110` handles numeric/function row heights and switches row overscan when virtualization is enabled. Why: variable row-height grids can drift between scroll math and rendered rows. Minimal PR: add a variable-height list test that scrolls to the middle and verifies row indexes and top offsets. Status: E2 source-verified, 2026-07-04.
6. **react-window examples and internals center row/column size contracts.** Evidence: `bvaughn/react-window@94b465b:README.md:71,223` documents `rowHeight`; `lib/components/grid/Grid.tsx:75,95` passes `itemSize` for columns and rows. Why: wrong `itemSize`/rowHeight creates invisible gaps or clipped content that unit tests miss. Minimal PR: add a visual fixture with deliberately wrong size and guidance for fixed vs dynamic rows. Status: E2 source-verified, 2026-07-04 (positive control).
7. **React Virtuoso documents overscan and total item count behavior.** Evidence: `petyosi/react-virtuoso@2c68507:apps/virtuoso.dev/docs/guides/virtuoso/overscan.md:9,22-28,118` shows `Virtuoso`, `totalCount`, and overscan tuning. Why: overscan is a UX/perf contract: too low blanks during fast scroll, too high hurts INP/memory. Minimal PR: add a fast-scroll example test that asserts overscan keeps the next viewport painted without over-rendering too many rows. Status: E2 source-verified, 2026-07-04.
8. **Handsontable explicitly documents disabling DOM virtualization for assistive tech.** Evidence: `handsontable/handsontable@066567e:docs/content/guides/accessibility/accessibility/accessibility.md:171-183,311` and `docs/content/guides/accessibility/accessibility-conformance-report/accessibility-conformance-report.md:66` discuss DOM virtualization, `renderAllRows`, and screen-reader completeness. Why: large-grid contracts are not only speed; a11y/search/copy behavior can require full DOM rendering. Minimal PR: add an a11y contract test comparing default virtualization with `renderAllRows/renderAllColumns`. Status: E2 source-verified, 2026-07-04.
9. **Glide Data Grid warns data changes force redraw by changing `getCellContent` identity.** Evidence: `glideapps/glide-data-grid@0875d78:packages/core/API.md:32-36,1182-1184` documents redraw via `getCellContent` identity and sticky trailing rows. Why: large canvas grids can show stale cells or redraw too much when cache identity is unstable. Minimal PR: add a benchmark/smoke asserting targeted cell updates do not recreate all visible cells unnecessarily. Status: E2 source-verified, 2026-07-04.
10. **Fluent UI DetailsList/List exposes `onShouldVirtualize` as an explicit virtualization escape hatch.** Evidence: `microsoft/fluentui@65db820d:packages/react/src/components/List/List.tsx:98,559-561,1138` and `packages/react/src/components/DetailsList/DetailsList.types.ts:306` wire `onShouldVirtualize`. Why: tests often set `onShouldVirtualize={() => false}` and then miss production scroll/focus bugs. Minimal PR: add a DetailsList example test that runs once with virtualization disabled for jsdom and once with virtualization enabled in browser e2e. Status: E2 source-verified, 2026-07-04.

## Second-pass cases after stricter gates

Purpose: these are additional cases for the medium-signal skills after adding false-positive gates. They are intentionally framed as small PRs a maintainer could review, not as raw grep hits.

Recheck rule (2026-06-17): `Candidate` or `hardening` rows are kept as useful leads, but they are not counted as the two solid PR-worthy cases for a skill until a focused test, local reproduction, or maintainer acceptance confirms the defect boundary.

### `a11y-contract-testing`

| Case | Evidence | Failure mode | Minimal PR shape | Status |
|---|---|---|---|---|
| Maybe Finance DS menu opens arbitrary interactive content without a menu/popover state contract|`maybe-finance/maybe@app/components/DS/menu.html.erb:3,7,14` wires only `data-DS--menu-target` trigger/content and `hidden`; `menu_controller.js:11` says the menu may contain links/buttons/forms; `:36,66,69,78` handles click/show/focus. No `role=/aria-*` attributes were present in the menu files.|The trigger is operable visually, but AT/tests cannot observe `aria-haspopup`, `aria-expanded`, trigger-content ownership, or menu item semantics. If it is a generic popover, that contract is also undocumented and untested.|Add `aria-haspopup`, `aria-expanded`, `aria-controls`, stable ids, and a role/name test for the trigger/content; if action-menu content is used, add `role="menu"`/`menuitem` or split into a popover component.| E2 source-verified, 2026-06-26 |
| Appwrite fake payment modal renders as styled divs with a visible title but no dialog role/name|`appwrite/console@src/lib/components/fakeModal.svelte:7,69,72,91,102` has `title`, backdrop, `.modal`, title slot, and close button; usages include `replaceCard.svelte:120` and `retryPaymentModal.svelte:170-176`. No `role="dialog"`, `aria-modal`, or `aria-labelledby` was found in the modal component.|Payment modals can be opened and closed visually, but `getByRole('dialog', { name })` and screen-reader dialog navigation cannot identify the modal by its title.|Give the modal container `role="dialog"`, `aria-modal` when outside interaction is blocked, and `aria-labelledby` to the title id; add a payment-modal accessibility contract test.| E2 source-verified, 2026-06-26 |

### `constraint-validation-contracts`

| Case | Evidence | Failure mode | Minimal PR shape | Status |
|---|---|---|---|---|
| Appwrite shared text-like inputs set native-invalid error state but do not clear it on edit|`inputText.svelte:34,40,62-66`, `inputEmail.svelte:32,50-57`, `inputURL.svelte:34,56-60`, `inputNumber.svelte:51,72-76`, and `inputPassword.svelte:31,48,52-53` set `error` from `validationMessage`, display `helper/state`, and bind value; the `on:input` directives forward/change value but do not clear/revalidate `error`.|After a failed submit, a corrected value can keep a stale warning/error visual state until another invalid/submit cycle, violating the clearing contract.|Centralize `clearErrorOnInput` or revalidate on input while preserving forwarded events; add a sequence test invalid submit -> type valid -> helper disappears -> submit succeeds.| E2 source-verified, 2026-06-26 |

### `frontend-security-baseline`

| Case | Evidence | Failure mode | Minimal PR shape | Status |
|---|---|---|---|---|
| NextChat share flow uses `window.open(res, "_blank")` without opener isolation|`ChatGPTNextWeb/NextChat@app/components/exporter.tsx:316-323` obtains a share URL from `api.share(msgs)` and displays/copies it; `:346-347` opens `res` with `window.open(res, "_blank")` and no feature string.|The opened share page receives a live `window.opener` reference in browsers unless `noopener` is requested, so a compromised/share destination can navigate the app tab.|Use `window.open(res, "_blank", "noopener,noreferrer")` or a helper that always sets opener isolation; add a unit/static assertion for popup features.| E2 source-verified, 2026-06-26 |
| Appwrite console command palette opens external docs/support tabs without `noopener,noreferrer`|`appwrite/console@src/routes/(console)/+layout.svelte:106-108`, `:114-116`, and `:130-132` call `window.open('https://appwrite.io/...', '_blank')` for docs/Discord commands.|Even constant trusted external links create an avoidable opener channel from the new tab back to the console tab; this is exactly the `window.open` gap not covered by modern anchor defaults.|Add a small `openExternal(url)` helper using `window.open(url, '_blank', 'noopener,noreferrer')` and test/grep command-palette actions through it.| E2 source-verified, 2026-06-26 (hardening, not a confirmed vulnerability) |

### `i18n-copy-and-layout`

| Case | Evidence | Failure mode | Minimal PR shape | Status |
|---|---|---|---|---|
| NextChat MCP market bypasses the app locale system for empty/loading/actions|`ChatGPTNextWeb/NextChat@app/components/mcp-market.tsx:464` hardcodes `No servers available`; `:697`, `:704`, `:725` hardcode `Cancel`/`Save`/`Close`; `:733` and `:746` hardcode loading/empty states. The component has no `Locale` import while the app uses `app/locales`.|Localized users see English action, loading, and empty-state copy in a localized product surface.|Add `Locale.McpMarket.*` keys and replace hardcoded strings; add one locale fixture/story or snapshot covering empty/loading/action states.| E2 source-verified, 2026-06-26 |
| NextChat error boundary imports `Locale` but recovery copy remains English|`ChatGPTNextWeb/NextChat@app/components/error.tsx:8` imports `Locale`; `:43`, `:52`, and `:59` hardcode `Oops, something went wrong!`, `Report This Error`, and `Clear All Data`; only the reset confirmation at `:61` uses `Locale`.|The most visible crash/recovery screen ignores the existing translation mechanism except for one confirm message.|Move title/actions into `Locale.ErrorBoundary` or equivalent and add locale entries/tests for the crash screen.| E2 source-verified, 2026-06-26 |

### `ssr-hydration-mismatch`

| Case | Evidence | Failure mode | Minimal PR shape | Status |
|---|---|---|---|---|
| NextChat Artifacts iframe id is generated with `nanoid()` during first render|`ChatGPTNextWeb/NextChat@app/components/artifacts.tsx:11,39,81-99` initializes `frameId` with `nanoid()`, embeds it in `srcDoc`, and keys the iframe by it; `home.tsx:43` imports Artifacts via `dynamic(...)` without `ssr: false`.|Server and client can render different iframe key/srcDoc ids before hydration, producing recoverable hydration errors or iframe replacement.|Initialize with a stable placeholder and set the random id in an effect, or isolate the iframe as no-SSR; add a hydration smoke test with `onRecoverableError`.| E2 source-verified, 2026-06-26 |
| Appwrite payment edit modal derives form constraints from `new Date()` during SSR-rendered component evaluation|`appwrite/console@src/routes/(console)/account/payments/editPaymentModal.svelte:26` computes `currentYear`, `:60-62` recomputes `currentMonth` for month options, and `:85,90` bind expiry month/year inputs. SvelteKit route components SSR by default.|Around a month/year boundary, server HTML can contain a different `min` year or month option list than the client first render.|Serialize a request-time `now`/billing date into props/load data or compute after mount with a placeholder; add a fake-clock SSR/client render test for month/year rollover.| E2 source-verified, 2026-06-26 (needs fake-clock SSR proof) |

## Negative controls / false positives

- `appwrite/console` `inputCheckbox.svelte` looked suspicious at first, but `:38-40` already clears `error` when checked; do **not** count it as a defect.
- `appwrite/console` `inputFile.svelte` drop handling looked suspicious, but recheck showed invalid extension/oversize paths return at `:54-60` before `setFiles(...)`; do **not** count it as a constraint-validation defect.
- `chatwoot/chatwoot` shared `ChatForm.vue` uses `:invalid`, but it is gated under a submitted-state selector; not the “red on page load” defect.
- `react-hook-form/react-hook-form` has extensive `setCustomValidity`/`reportValidity` tests and clears native validity in `validateField.ts`; it was a useful negative control for the constraint-validation skill.
- `nextauthjs/next-auth-example` uses `Math.random()` for a server-component avatar seed, but that is more a deterministic-output concern than a confirmed hydration mismatch, so it was not counted.
- `radix-ui/primitives` was mostly a positive a11y baseline; the sampled primitives already encode roles/states well, so it was not used as a defect source.
- `target="_blank"` on an anchor is not automatically a high-severity opener leak in modern browsers; count it as lower-confidence hardening unless `window.open()`, older WebView/browser support, or an explicit `noreferrer` policy makes the risk concrete.

## Practicality recheck (2026-06-17)

| Skill | Practical use | Niche strength | Action |
|---|---|---|---|
| `webview-bridge-pages` | High | High | Keep as a flagship niche skill; bridge lifecycle failures are rare in generic frontend guides. |
| `cjk-text-and-input` | High | High | Keep; add/maintain PR gates so it does not drift into generic i18n. |
| `deeplink-hydration` | High | High | Keep; router/query readiness plus auth-bounce preservation is a distinct frontend failure mode. |
| `constraint-validation-contracts` | High | High | Keep; focus on timing/clearing/submission contracts, not raw `:invalid` grep. |
| `datetime-correctness` | High | Medium-high | Keep; preserve frontend-specific date-only, timezone rendering, and input-roundtrip examples. |
| `frontend-auth-flow-contracts` | High | Medium | Keep but frame as browser-facing auth UI contracts; token/CSP/CSRF belongs in security baseline. |
| `a11y-contract-testing` | High | Medium | Keep but frame as semantic contract regression tests, not a generic accessibility audit. |
| `i18n-copy-and-layout` | High | Medium | Keep but frame as copy/layout failure contracts, not broad localization guidance. |
| `ssr-hydration-mismatch` | High | Medium | Keep with evidence gate; require SSR path plus first-render mismatch proof before calling a defect. |
| `frontend-security-baseline` | Medium-high | Low-medium | Keep only as trap-first hardening support or consider splitting; do not market it as the most niche/unique skill. |

Operational rule: flagship examples should come from High/Medium-high niche rows. Medium niche rows are still useful in real work, but their value depends on strict gates and concrete PR evidence.

## Efficiency verdict

| Skill | Signal quality | Notes |
|---|---|---|
| `a11y-contract-testing` | Medium-high | Raw `aria` grep is noisy, but component-library files with custom tabs/menus/selects produce strong PR candidates. |
| `cjk-text-and-input` | High | `Enter` handlers without `isComposing`/`keyCode 229` are easy to find and patch. |
| `constraint-validation-contracts` | Medium | `:invalid` searches are noisy; `setCustomValidity` and stale component error-state probes produce better signal. |
| `datetime-correctness` | High | Date-only and timezone-reparse traps are distinctive and line-local. |
| `deeplink-hydration` | High | Auth redirect and query-preservation flows are traceable with small patches. |
| `frontend-auth-flow-contracts` | High | Auth input autocomplete/OTP contracts are concrete and maintainer-friendly. |
| `frontend-security-baseline` | Medium-high | Must stay trap-first; broad raw-sink grep is noisy, but opener/raw-HTML cases were strong. |
| `i18n-copy-and-layout` | Medium-high | Best signal came from hardcoded user copy and concatenated count strings, not generic locale-file grep. |
| `ssr-hydration-mismatch` | Medium | Strong when default render uses nondeterministic values; weaker if the app is effectively client-only, so cases need careful framing. |
| `webview-bridge-pages` | High | Bridge startup/message-contract bugs were rare but highly specific and PR-shaped. |

## Addendum: `design-to-code-fidelity` validation cases (2026-06-17)

Additional public OSS checkouts inspected for design-to-code fidelity:

| Repository | Commit |
| --- | --- |
| `Codecademy/gamut` | `880fb1e` |
| `narmi/design_system` | `b542cbf` |

### `design-to-code-fidelity`

Scope note: these two cases validate the **Figma Code Connect / design-to-code mapping** half of the skill, not the full screenshot pixel-diff loop. The repositories contain Figma URLs in their Code Connect files, but local Figma Images API export returned `Not found` because the token account lacked file access. Count these as maintainer-plausible PR cases for code/design mapping drift; require a maintainer token or duplicated Figma file before claiming full Figma-PNG-vs-browser pixel-diff reproduction.

| Case | Evidence | Failure mode | Minimal PR shape | Status |
| --- | --- | --- | --- | --- |
| Codecademy Gamut Checkbox Code Connect maps checked/indeterminate states to string booleans|`Codecademy/gamut@packages/code-connect/Atoms/FormInputs/Checkbox.figma.tsx:19-27` maps Figma `checked` to `'true'`/`'false'` strings and `Indeterminate` to `'true'`/`'false'` strings. The component contract is boolean: `packages/gamut/src/Form/inputs/types.tsx:12-23` declares `indeterminate: boolean` / `checked?: boolean`, and `Checkbox.tsx:173-179,192,209-226` uses those props in boolean logic and DOM checkbox state.|A Figma unchecked state can generate `<Checkbox checked="false" indeterminate="false" />`; those are truthy strings in component logic, so the Code Connect preview/snippet can render an active/checked or indeterminate-looking checkbox instead of matching the Figma unchecked state.|Change the Code Connect mapping to real booleans (`true: true`, `false: false`, `Indeterminate: false`; `indeterminate` `Indeterminate: true` else `false`) and add a Code Connect/static test or story asserting generated examples use boolean props.| E2 source-verified, 2026-06-26 |
| Narmi Design System Chip Code Connect declares icon/close-button design props but drops them in the example|`narmi/design_system@src/Chip/index.figma.tsx:32-47` declares Figma props for `Show StartIcon`, `Show EndIcon`, `Show Count`, `CloseButton`, and an `onDismiss` handler. The generated example at `src/Chip/index.figma.tsx:52-53` only renders `<Chip kind={kind} label={label} count={count} />`. The component supports these visual props in `src/Chip/index.tsx:17-34` (`onDismiss`, `startIcon`, `endIcon`, `count`) and renders the close button when `onDismiss` is present at `src/Chip/index.tsx:94-114`.|Figma variants with a start icon, end icon, or close button produce a code example without those visible affordances. This is exactly the design-to-code fidelity class: the Figma design has visual elements, but the generated rendered component omits them.|Pass `startIcon`, `endIcon`, and `onDismiss` through the Code Connect example (or remove those Figma prop mappings if intentionally unsupported). Add a representative Code Connect/Storybook example for icon + dismissible chip.| E2 source-verified, 2026-06-26 |

Practical note: attempts to export public Figma links from `figma/sds`, `primer/react`, `narmi/design_system`, `inngest/inngest`, and `Codecademy/gamut` with the local token returned `Not found`; this validated the access trap now documented in `skills/design-to-code-fidelity/SKILL.md`. Public browser visibility is not enough for Figma Images API validation unless the token account has file access or a duplicated copy.

Additional leads (source-verified, not worked into full cases):

1. **Primer Autocomplete Code Connect exposes nested input state that can drift from rendered example.** Evidence: `primer/react@packages/react/src/Autocomplete/Autocomplete.figma.tsx:30-82` maps nested input props including caption/validation. Why: design-to-code fidelity depends on nested FormControl/TextInput props reaching the example. Minimal PR: snapshot generated example for disabled/required/validation cases. Status: E2 source-verified, 2026-06-26.
2. **Primer Select Code Connect declares a caption prop but renders only label/select/validation.** Evidence: `primer/react@packages/react/src/Select/Select.figma.tsx:5-25` declares `caption` and `validation`, then renders `<Select size={size} block={block} />` with validation. Why: generated code can omit visible helper/caption text from design. Minimal PR: render `FormControl.Caption` when caption is true/text. Status: E2 source-verified, 2026-06-26.
3. **Primer TextInput Code Connect has a broad prop surface that needs generated-output parity tests.** Evidence: `primer/react@packages/react/src/TextInput/TextInput.figma.tsx:35-85,114` maps required, inset, validation, size, caption. Why: one missed prop silently changes visual fidelity. Minimal PR: add Code Connect smoke outputs for inset/validation/caption combinations. Status: E2 source-verified, 2026-06-26.
4. **Primer TabNav Code Connect maps trailing action/counter states separately from tab links.** Evidence: `primer/react@packages/react/src/TabNav/TabNav.figma.tsx:4-43` maps `trailingAction`, children, selected, and counter. Why: generated tab examples can omit action/counter affordances that are visible in design. Minimal PR: add fixture for selected tab with counter and trailing action. Status: E2 source-verified, 2026-06-26.
5. **Primer Banner Code Connect maps dismissible to an `onDismiss` prop.** Evidence: `primer/react@packages/react/src/Banner/Banner.figma.tsx:5-19,45` maps `Dismissible?` then passes `onDismiss={dismissible}`. Why: if component expects a callback, a boolean mapping is not faithful executable code. Minimal PR: map true to a noop callback or omit unsupported dismiss behavior. Status: E2 source-verified, 2026-06-26.
6. **n8n Callout stories lack a Figma/Code Connect parity bridge for icon/action combinations.** Evidence: `n8n-io/n8n@packages/frontend/@n8n/design-system/src/components/N8nCallout/Callout.stories.ts:8-22,99-106` documents story controls/actions; component slots are at `Callout.vue:17-67`. Why: design variants with actions/icons can drift without generated-code parity. Minimal PR: add visual/code fixture for theme + icon + actions. Status: E2 source-verified, 2026-06-26.
7. **Narmi Checkbox Code Connect should be checked against real component required/error states.** Evidence: `narmi/design_system@src/Checkbox/index.figma.tsx:12-35` maps Figma props to the checkbox component. Why: checkbox design states commonly include disabled/error/label helper text that may not map fully. Minimal PR: compare generated examples against Storybook variants. Status: E2 source-verified, 2026-06-26.
8. **Primer Radio/Checkbox Code Connect state mappings should be audited together.** Evidence: `primer/react@packages/react/src/Radio/Radio.figma.tsx:5-25` and `packages/react/src/Checkbox/Checkbox.figma.tsx:5-29` are adjacent form-control mappings. Why: form controls need consistent required/caption/validation fidelity. Minimal PR: add a shared form-control Code Connect parity checklist. Status: E2 source-verified, 2026-06-26.

### `design-to-code-fidelity` strict Figma export recheck (2026-06-17)

Counting rule for this skill is now stricter than the earlier Code Connect checks: a case only counts as a full design-to-code validation when the Figma node is exported as an actual image, the implementation is rendered, and `visual-diff.sh` is run. Code Connect prop mapping cases remain useful, but they are not full Figma-vs-browser pixel-diff evidence.

| Case | Evidence | Failure mode | Minimal PR shape | Status |
| --- | --- | --- | --- | --- |
| n8n Storybook Callout design reference does not match the rendered Callout stories|OSS checkout at `n8n-io/n8n@854835dc`. Story source `packages/frontend/@n8n/design-system/src/components/N8nCallout/Callout.stories.ts:28-31` points the Callout story design panel at `https://www.figma.com/file/tPpJvbrnHbP8C496cYuwyW/Node-pinning?node-id=15%3A5777`. Figma Images API export succeeded with `figma-export.sh tPpJvbrnHbP8C496cYuwyW 15-5777 ...` and produced `15_5777.png` (`630x169`). Local Storybook rendered `core-callout--secondary-callout` via `render-capture.mjs` (`630x171`). `AE_FUZZ=10% STRUCT_GATE=1 visual-diff.sh` reported `STRUCT=DRIFT MAX_BLOCK=51838@630x169+0+0`.|The linked Figma node is a Node Pinning frame with two warning/info callouts and close affordances; the rendered Storybook examples are success/custom/secondary copy variants (`defaultCallout`, `customCallout`, `secondaryCallout`) and do not match that reference. The design panel therefore gives maintainers a stale/non-equivalent design target.|Either point the story at the real Callout component/spec in Figma, or add a dedicated Node Pinning/dismissible-callout story whose args/slots match the linked Figma frame. Then keep the Figma export + Storybook screenshot diff as a regression gate.| E1 measured, 2026-06-17 (Figma export, Storybook render, and pixel diff were run and recorded; the mismatch is against a Storybook design reference, not a proven production UI bug) |

Strict recheck notes:

- Rejected as **not full cases yet**: the earlier `Codecademy/gamut` Checkbox and `narmi/design_system` Chip findings. They are still strong Code Connect mapping issues, but they did not pass the Figma PNG export + browser render + pixel-diff bar.
- Figma Images API access was tested across 100 public OSS Figma links from Carbon, EUI, Fluent UI, Polaris, Ring UI, Twilio Paste, and related design-system repos; all returned `Not found` with the current token. This confirms that a public browser/community Figma URL is not enough for REST image export.
- Additional OSS links whose Images API access returned an image URL before the token hit the low-tier rate limit, but whose PNG export/diff was **not completed and therefore not counted**: Cal.com `Cal-DS---Components` node `25883-174646`, Cal.com booking logs node `5641-6732`, n8n old design-system nodes `2-23` and `79-6898`, and n8n `Node-pinning` node `15-5777`.
- Current blocker for finding the second strict case: Figma returned `429 Rate limit exceeded` with `x-figma-rate-limit-type: low` and a very large `Retry-After`. Do not claim a second full case until another token/maintainer token or reset window allows a fresh export and diff.
- `figma.com/api/oembed` thumbnails are **not acceptable substitutes** for strict validation: for n8n design-system nodes they returned generic cover thumbnails, not the target node/frame PNG.

## Filing strategy

Every row here is E2, with the single E1 exception noted at the top. None is ready to file as-is.

1. Pick a row whose failure mode is concrete and whose patch is small. Good first
   targets: Supabase autocomplete/OTP, Appwrite native validation stale errors,
   NextChat IME search, NextChat clipboard rejection handling, Cal.com CSV
   formula-prefix policy, Cal.com ModalBox nested scroll-lock tests, gronxb/alinz
   bridge guard/order issues, Appwrite/NextChat `_blank` opener fixes, and the
   Spurtcommerce unused payment-page script removal.
2. Re-check the cited lines against the current default branch. Line drift is
   normal; a vanished pattern means the row is dead.
3. Reproduce in the target repo with a failing unit/E2E/storybook/browser test or
   a minimal platform snippet. Without this the row stays at E2.
4. Keep issue titles narrow and maintainer-owned: one behavior, one failing
   reproduction, one proposed patch. Do not pitch the skill pack in the issue body.
5. Only promote to README evidence after a maintainer acknowledges, accepts, or
   merges the fix.
