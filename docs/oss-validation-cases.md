# Open-source validation cases

Purpose: validate selected bundled frontend niche skills find real, PR-worthy defects rather than search-noise. Newly added skills may start without a validation case until a reproduced OSS example exists. A case counts only when it has source-line evidence, a concrete user-visible failure mode, a small plausible patch, and a maintainer-facing rationale.

Evaluation snapshot: 2026-06-26. Temporary local checkouts and public GitHub tree/raw-file research were used during evaluation.

## Evidence status

These rows are validation cases, not automatically confirmed upstream bugs. A row should stay here only when it has source-line evidence, a concrete user-visible failure mode, a plausible maintainer patch shape, and an explicit confidence level. Re-check the current default branch and reproduce locally before filing an issue or PR.

Positive-control rows document patterns the skills should not flag as bugs.

## Repositories sampled

| Repo | Commit |
|---|---:|
| `ChatGPTNextWeb/NextChat` | `89b8f26` |
| `actualbudget/actual` | `fbdad57` |
| `appwrite/console` | `1b41137` |
| `appwrite/console` | `cfd97e3` |
| `chatwoot/chatwoot` | `41a3ab6` |
| `date-fns/tz` | `9f391a0` |
| `excalidraw/excalidraw` | `28a9b17` |
| `excalidraw/excalidraw` | `c070c8f` |
| `gronxb/webview-bridge` | `2aec6ee` |
| `maybe-finance/maybe` | `77b5469` |
| `nextauthjs/next-auth-example` | `39ff2b7` |
| `radix-ui/primitives` | `71a7122` |
| `react-hook-form/react-hook-form` | `782313f` |
| `remix-run/react-router` | `09e6020` |
| `supabase/auth-ui` | `d5e0827` |
| `calcom/cal.com` | `62317bd` |
| `directus/directus` | `de73e75` |
| `formbricks/formbricks` | `fc93a74` |
| `grafana/grafana` | `70b22cbc51ac` |
| `lobehub/lobe-chat` | `97b48df` |
| `mattermost/mattermost` | `f31c286` |
| `n8n-io/n8n` | `2cef574` |
| `outline/outline` | `34907e1` |
| `twentyhq/twenty` | `1b4bddb` |

## Per-skill casebook

### `semantic-markup-contracts`

Status: covered by markup/a11y overlap cases below. The Maybe Finance tabs and Actual Budget menu/select rows exercise native HTML and ARIA role/state contracts, but they remain under `a11y-contract-testing` because the maintainer-facing patch shape is role-based regression coverage.

### `a11y-contract-testing`

| Case | Evidence | Failure mode | Minimal PR shape | Confidence |
|---|---|---|---|---|
| Maybe Finance design-system tabs expose only buttons/classes, not a tab contract | `maybe-finance/maybe@app/components/DS/tabs/nav.rb:12-15` renders `button` with only `data` targets; `tabs.rb:15-16` hides panels with class/data only; `tabs_controller.js:10,25,27` toggles classes. `rg role/aria` on the tabs files found no tab roles/states, only unrelated `variant` text. | Screen readers and role-based tests cannot discover `tab`, `tabpanel`, `aria-selected`, or tab-panel pairing even though the UI is visually tabbed. | Add `role="tablist"`, `role="tab"`, `role="tabpanel"`, stable ids, `aria-controls`, `aria-labelledby`, and update `aria-selected` in the controller. Add a ViewComponent/system test with `getByRole('tab', { name })`. | High |
| Actual Budget component-library `Menu`/`Select` are keyboard-managed but not exposed as menu/listbox/combobox | `actualbudget/actual@packages/component-library/src/Menu.tsx:150-157` uses a focusable `View`; `Menu.tsx:185-217` maps items to `Button`; `Select.tsx:108-135` opens `Popover` + `Menu`. `rg role/aria` in those two files found only a textbox guard at `Menu.tsx:140`. | Custom menu/select works visually, but AT sees generic buttons/containers rather than `menu`/`menuitem` or `combobox`/`listbox`/`option` state. | Either migrate to React Aria `Menu/ListBox/Select` primitives or add the matching APG roles/states and tests that open the select/menu and query items by role. | Medium-high |

### `cjk-text-and-input`

| Case | Evidence | Failure mode | Minimal PR shape | Confidence |
|---|---|---|---|---|
| NextChat search submits while IME composition is still active | `ChatGPTNextWeb/NextChat@app/components/search-chat.tsx:122-126` runs search on `e.key === "Enter"`. Same repo already has a correct guard in chat submit: `chat.tsx:266-290` tracks composition, ignores `keyCode == 229`, and checks `nativeEvent.isComposing`. | Korean/Japanese/Chinese users pressing Enter to confirm a candidate can trigger a premature search. | Reuse the existing chat submit IME guard in search input before accepting Enter. Add a regression test for `isComposing`/`keyCode 229`. | High |
| Actual Budget reusable `Input` fires `onEnter` from `onKeyUp` without composition guard | `actualbudget/actual@packages/component-library/src/Input.tsx:71-76` calls `onEnter` whenever `e.key === 'Enter'`. | Every consumer of `onEnter` can submit/select while IME composition is confirming text. | In `Input`, skip `onEnter` when `e.nativeEvent.isComposing` or legacy `keyCode === 229`; document that `onEnter` is post-composition only. | High |

### `constraint-validation-contracts`

| Case | Evidence | Failure mode | Minimal PR shape | Confidence |
|---|---|---|---|---|
| Appwrite migration export sets custom validity but never clears it on edit | `appwrite/console@src/routes/(console)/project-[region]-[project]/settings/migrations/exportModal.svelte:83-85` calls `endpointInput.setCustomValidity('Please enter a valid endpoint')` + `reportValidity()`; `:145-151` binds `endpointUrl`; `:181` disables by `isValidEndpoint(endpointUrl)`. No corresponding `setCustomValidity('')` was found for `endpoint`. | Once invalid, the native field can remain invalid even after the value becomes valid, blocking submission or keeping stale native error state. | Clear custom validity before validation and whenever `endpointUrl` changes; add a component test: invalid endpoint shows message, valid edit clears `validationMessage` and allows submit. | High |
| Appwrite optional phone field keeps stale error after clearing an invalid value | `appwrite/console@src/lib/elements/forms/inputPhone.svelte:24-43` maps native validity to `error`; `:45-46` clears only when `value` is truthy; `auth/user-[user]/updatePhone.svelte:45-50` uses `InputPhone` without `required`. | For an optional phone, entering an invalid value then deleting it leaves the UI in error state even though empty is valid. | Clear when the element is valid, or when `!required && !value`; add a test for invalid phone -> empty string -> no helper/error state. | High |

### `datetime-correctness`

| Case | Evidence | Failure mode | Minimal PR shape | Confidence |
|---|---|---|---|---|
| Appwrite timezone conversion reparses a locale string | `appwrite/console@src/routes/(console)/bottomAlerts.ts:39-48` builds `targetString`, then does `new Date(new Date(targetString).toLocaleString('en-US', { timeZone }))` before comparing with `now`. | Locale-string reparse is environment-dependent and loses the actual intended zone instant; promotions can start on the wrong local day/time. | Use an explicit timezone conversion helper/library (`date-fns-tz`, Temporal polyfill, or a known Appwrite helper) and test with non-local zones around midnight/DST. | High |
| Chatwoot date-only custom attribute converts date input to UTC instants | `chatwoot/chatwoot@app/javascript/dashboard/components-next/CustomAttributes/DateAttribute.vue:37-54` displays with `toLocaleDateString()`, fills `<input type=date>` via `toISOString().slice(0, 10)`, and stores `new Date(value).toISOString()`. | A date-only UI value can shift by timezone because `YYYY-MM-DD` is treated as an instant/UTC conversion instead of a plain date. | Store/round-trip the plain `YYYY-MM-DD` value, or use date-only helpers; test in `America/Los_Angeles` and `Asia/Seoul`. | High |

### `deeplink-hydration`

| Case | Evidence | Failure mode | Minimal PR shape | Confidence |
|---|---|---|---|---|
| Appwrite email/password login loses protected-route query state | `appwrite/console@src/routes/+layout.ts:87` sets `redirect` to `url.pathname` only, then redirects with other params at `:112`; login email/password only uses `$redirectTo`/account invalidation at `login/+page.svelte:60-66`. The GitHub OAuth path separately reconstructs `redirect + page.url.search` at `login/+page.svelte:81-91`. | Visiting a protected deep link with query params can return to the path but drop the original screen/filter/query after email/password login. | Preserve `url.pathname + url.search` as a safe same-origin redirect, or make email/password mirror the OAuth redirect+residual-search handling. | High |
| Maybe Finance protected links always land at root after login | `maybe-finance/maybe@app/controllers/concerns/authentication.rb:18-25` redirects unauthenticated users to `new_session_url`; `sessions_controller.rb:16-17` creates the session then `redirect_to root_path`. | A user following `/accounts/123?tab=activity` or a shared import/deep link loses the intended destination after auth. | Store the requested full path in session for GET requests and redirect back after login with same-origin/path validation; add controller/request tests. | Medium-high |

### `frontend-auth-flow-contracts`

| Case | Evidence | Failure mode | Minimal PR shape | Confidence |
|---|---|---|---|---|
| Supabase Auth UI update-password forms lack `autocomplete="new-password"` | React `supabase/auth-ui@packages/react/src/components/Auth/interfaces/UpdatePassword.tsx:48-56`; Solid `packages/solid/src/components/Auth/interfaces/UpdatePassword.tsx:52-62`. Both render password inputs without autocomplete. | Password managers cannot reliably generate/fill a new password in the reset/update-password flow. | Add `autoComplete="new-password"` / `autocomplete="new-password"` in React/Solid/Svelte update-password inputs; add a shallow/render assertion. | High |
| Supabase Auth UI OTP token inputs lack `autocomplete="one-time-code"` | React `packages/react/src/components/Auth/interfaces/VerifyOtp.tsx:108-116`; Solid `packages/solid/src/components/Auth/interfaces/VerifyOtp.tsx:93-100`. | Mobile browsers cannot offer SMS/email OTP autofill for the token field. | Add `autoComplete="one-time-code"` / `autocomplete="one-time-code"` to token inputs; keep email/phone fields on their respective autocomplete values. | High |

### `frontend-security-baseline`

| Case | Evidence | Failure mode | Minimal PR shape | Confidence |
|---|---|---|---|---|
| Appwrite AI markdown rewrites rendered anchors after markdown generation | `appwrite/console@src/lib/commandCenter/panels/ai.svelte:112-117` renders markdown then regex-rewrites `<a href>` to add `target="_blank"`; the HTML is injected with `{@html ...}` at `:198`. | This is a hardening/policy-consistency case, not a confirmed reverse-tabnabbing vulnerability claim: modern anchors generally imply `noopener`, but the post-render HTML rewrite is fragile and cannot add project-wide `noreferrer` consistently. | Generate `target`, `rel="noopener noreferrer"`, and allowed link attributes through the markdown renderer link rule instead of post-render regex; add a rendered-html assertion. | Medium |
| NextChat plugin editor injects editable plugin YAML as HTML | `ChatGPTNextWeb/NextChat@app/components/plugin.tsx:347-349` uses `contentEditable` with `dangerouslySetInnerHTML={{ __html: editingPlugin.content }}`; `:61-72` reads edited text back into plugin content. | Plugin/YAML text is not HTML and can contain markup; rendering it as HTML creates an avoidable XSS/DOM clobbering surface. | Render plugin content as text (`{editingPlugin.content}` or `textContent` via ref) and preserve edit behavior; add a test with `<img onerror>`/`<script>` literal content. | High |

### `i18n-copy-and-layout`

| Case | Evidence | Failure mode | Minimal PR shape | Confidence |
|---|---|---|---|---|
| Supabase Auth UI password-limit error is hardcoded English and misspelled | React `EmailAuth.tsx:87-88`, `UpdatePassword.tsx:28-29`; Solid `EmailAuth.tsx:72-73`, `UpdatePassword.tsx:23-24`; Svelte `EmailAuth.svelte:50-51`, `UpdatePassword.svelte:28-29` all set `Password exceeds maxmium length of 72 characters`. | Localized apps cannot translate the error; all frameworks show a typo in user-facing auth copy. | Move the message into shared i18n variables (with a corrected default: “maximum”), parameterize `{max}`, and reuse it across React/Solid/Svelte. | High |
| Chatwoot writer character counter is hardcoded English/plural text | `chatwoot/chatwoot@app/javascript/dashboard/components/widgets/WootWriter/constants.js:6-8` defines English `characters remaining/over`; `ReplyTopPanel.vue:144-147` builds strings with template concatenation. | Non-English locales get English text; singular/plural languages get incorrect forms such as `1 characters remaining`. | Replace constants with `$t`/i18n plural keys, pass `count`, and add locale entries/tests for `one` and `other`. | High |

### `ssr-hydration-mismatch`

| Case | Evidence | Failure mode | Minimal PR shape | Confidence |
|---|---|---|---|---|
| NextChat default chat state is generated with `nanoid()`/`Date.now()` during module initialization | `ChatGPTNextWeb/NextChat@app/store/chat.ts:68-71` creates message ids/dates with `nanoid()` and `new Date().toLocaleString()`; `:99` creates `BOT_HELLO`; `:104-115` creates default sessions with `nanoid()` and `Date.now()`; `:227` and `:271` initialize stores with `createEmptySession()`. | Server-rendered default store and client first render can disagree on ids/dates before persisted-store hydration, causing hydration warnings or immediate DOM replacement. | Use deterministic SSR-safe initial state (empty until hydration or fixed ids/dates), then create real sessions client-side after hydration. Add a hydration smoke test that asserts no recoverable hydration errors. | High |
| NextChat chat-list renders locale-dependent time during first render | `ChatGPTNextWeb/NextChat@app/components/chat-list.tsx:146` renders `new Date(item.lastUpdate).toLocaleString()` and `:148` keys by generated id. | Server locale/timezone and browser locale/timezone can produce different timestamp text for the same session; this amplifies the default-state mismatch above. | Render a stable ISO/placeholder during SSR and localize after mount, or pin explicit locale/timeZone; assert hydration has no text mismatch. | Medium-high |

### `webview-bridge-pages`

| Case | Evidence | Failure mode | Minimal PR shape | Confidence |
|---|---|---|---|---|
| `gronxb/webview-bridge` native `onMessage` parses every message as bridge JSON without a guard | `gronxb/webview-bridge@packages/react-native/src/createWebView.tsx:217-224` calls consumer `props.onMessage?.(event)`, then immediately `JSON.parse(event.nativeEvent.data)` and switches on `type` at `:225+`. | Any non-bridge `postMessage` from page content can throw in the bridge handler, breaking the WebView message loop despite consumer `onMessage` having handled it. | Wrap parse/schema validation in `try/catch`; ignore/pass through unknown messages; unit-test invalid JSON and unknown `type`. | High |
| `linkBridge` fires `onReady` before delayed native hydration has completed | `gronxb/webview-bridge@packages/web/src/linkBridge.ts:116-132` reads `window.__bridgeMethods__ ?? []` and subscribes to a `hydrate` event when empty; `:165` calls `onReady?.(proxy)` unconditionally before waiting for that hydrate callback. | A web page can enable bridge-dependent UI while no native methods/state are available yet, causing fallback/no-op calls and racey startup behavior. | If methods are absent, call `onReady` only after the hydrate event updates the instance; otherwise call immediately. Add a startup test where native injects methods after page load. | High |


### `download-export-safety`

Strict note: these are open-source export/copy cases, not a list of confirmed defects. Positive controls keep the skill from flagging safe helpers as bugs. Re-check the current default branch and add a local reproduction before filing.

1. **Outline members CSV helper**
   - Evidence: `outline/outline@shared/utils/csv.ts:21-29,82-94`; `app/scenes/Settings/components/ExportCSV.tsx:60-63`.
   - Validation value: Positive control; formula-prefix and control/bidi cleanup live in a shared helper.
   - Minimal PR/test shape: Keep helper tests for formula prefixes, controls, and export caller use.
   - Confidence: High

2. **Directus collection CSV export**
   - Evidence: `directus/directus@app/src/utils/save-as-csv.ts:45-59,78`.
   - Validation value: Candidate; collection/display values can become spreadsheet cells, so formula-cell policy needs confirmation.
   - Minimal PR/test shape: Add formula-prefix regression or document the existing `json2csv` transform policy.
   - Confidence: Medium-high

3. **Cal.com booking CSV export**
   - Evidence: `calcom/cal.com@apps/web/modules/bookings/components/BookingsCsvDownload.tsx:102-105`; `packages/lib/csvUtils.ts:49-60`.
   - Validation value: Candidate; helper quotes quotes/commas/newlines but not formula prefixes.
   - Minimal PR/test shape: Extend `sanitizeValue` with a documented cell policy and tests for `=`, `+`, `-`, `@`, and newline-created cells.
   - Confidence: High

4. **Grafana inspector CSV export**
   - Evidence: `grafana/grafana@public/app/features/inspector/utils/download.ts:78-92`.
   - Validation value: Positive/lead; Excel-aware branch shows spreadsheet compatibility is intentional, while formula policy should be checked for datasource text.
   - Minimal PR/test shape: Keep Excel delimiter/encoding tests; add formula-prefix test only if current `toCSV` lacks a policy.
   - Confidence: Medium

5. **Outline Blob download helper**
   - Evidence: `outline/outline@app/utils/download.ts:78-80,104-106`.
   - Validation value: Positive control; object URL creation and scheduled revoke are helper-owned.
   - Minimal PR/test shape: Assert revoke after the click path at helper level.
   - Confidence: High

6. **Mattermost generated zip download**
   - Evidence: `mattermost/mattermost@webapp/channels/src/components/post_view/data_spillage_report/data_spillage_download_report/data_spillage_download_report.tsx:64-71`.
   - Validation value: Positive control; the large Blob URL is revoked after anchor click.
   - Minimal PR/test shape: Mock `createObjectURL`/`revokeObjectURL` if maintainers want coverage.
   - Confidence: High

7. **Formbricks sample CSV download**
   - Evidence: `formbricks/formbricks@apps/web/modules/ee/unify-feedback/sources/components/csv-feedback-source-ui.tsx:186-195`.
   - Validation value: Positive control; one-shot sample CSV creates and revokes a Blob URL.
   - Minimal PR/test shape: Keep the revoke assertion if the handler is tested.
   - Confidence: High

8. **Lobe Chat export helper**
   - Evidence: `lobehub/lobe-chat@packages/utils/src/client/exportFile.ts:3-18`.
   - Validation value: Positive control; shared helper revokes the Blob URL and removes the anchor.
   - Minimal PR/test shape: Do not flag call sites using this helper; test the helper once.
   - Confidence: High

9. **n8n clipboard helper**
   - Evidence: `n8n-io/n8n@packages/frontend/editor-ui/src/app/composables/useClipboard.ts:24-32`.
   - Validation value: Positive control; pop-out clipboard failure is caught and falls back.
   - Minimal PR/test shape: Keep a rejected clipboard path test so UI does not claim copied on failure.
   - Confidence: High

10. **NextChat image copy**
    - Evidence: `ChatGPTNextWeb/NextChat@app/components/exporter.tsx:427-440`.
    - Validation value: Candidate; `navigator.clipboard.write(...).then(...)` inside `try` needs explicit async rejection handling.
    - Minimal PR/test shape: Use `await` or `.catch` and test that a rejected clipboard promise shows failure state.
    - Confidence: Medium-high

### `overlay-focus-scroll-contracts`

Strict note: these are open-source overlay lifecycle cases, not a list of confirmed defects. Positive controls prevent overclaiming around libraries that already manage focus, inertness, or scroll lock.

1. **Appwrite modal scroll-lock coordination**
   - Evidence: `appwrite/console@src/lib/components/modal.svelte:31-38`.
   - Validation value: Candidate/positive mix; the modal coordinates Melt listbox `removeScroll` side effects.
   - Minimal PR/test shape: Test modal plus combobox repeated open/close for body marker and padding restore.
   - Confidence: Medium

2. **n8n modal active-element blur**
   - Evidence: `n8n-io/n8n@packages/frontend/editor-ui/src/app/components/Modal.vue:81-87`.
   - Validation value: Candidate; blur can avoid hidden-focus warnings but may lose the return target.
   - Minimal PR/test shape: Test open from trigger, close, and focus restore.
   - Confidence: Medium

3. **n8n drawer active-element blur**
   - Evidence: `n8n-io/n8n@packages/frontend/editor-ui/src/app/components/ModalDrawer.vue:40-67`.
   - Validation value: Candidate; drawer focus restore and listener cleanup need separate coverage.
   - Minimal PR/test shape: Test drawer Escape/close focus restore and event cleanup.
   - Confidence: Medium

4. **Directus dialog focus-trap manager**
   - Evidence: `directus/directus@app/src/components/v-dialog.vue:8-13,90-92`.
   - Validation value: Positive control; nested overlay trap coordination can be centralized.
   - Minimal PR/test shape: Keep manager tests so child close does not release the parent trap.
   - Confidence: High

5. **Directus menu focus-trap config**
   - Evidence: `directus/directus@app/src/components/v-menu.vue:149-155,167`.
   - Validation value: Positive control; non-dialog overlay still configures return focus and outside click.
   - Minimal PR/test shape: Test Tab/Escape/click-outside and return focus when enabled.
   - Confidence: High

6. **Excalidraw dialog active-element tracking**
   - Evidence: `excalidraw/excalidraw@packages/excalidraw/components/Dialog.tsx:52,73-75`.
   - Validation value: Positive control; restore decisions consider previous/current active element.
   - Minimal PR/test shape: Keep a test for nested menu/dialog close and focus restoration.
   - Confidence: Medium-high

7. **Cal.com embed ModalBox body overflow**
   - Evidence: `calcom/cal.com@packages/embeds/embed-core/src/ModalBox/ModalBox.ts:25-27,255-256`.
   - Validation value: Candidate; one static saved overflow slot may fail nested modals or pre-existing styles.
   - Minimal PR/test shape: Add a nested open/close test preserving previous overflow while another modal remains open.
   - Confidence: Medium-high

8. **Formbricks custom focus trap**
   - Evidence: `formbricks/formbricks@packages/surveys/src/lib/use-focus-trap.ts:36-37,50-54`.
   - Validation value: Positive control; previous focus and `preventScroll` reduce scroll-jump regressions.
   - Minimal PR/test shape: Keep tests for delayed focus changes and restore guard.
   - Confidence: High

9. **Outline inline editor menu**
   - Evidence: `outline/outline@app/editor/components/InlineMenu.tsx:44-47,90-107`.
   - Validation value: Positive control; a non-modal Radix menu can intentionally pair with `RemoveScroll`.
   - Minimal PR/test shape: Test that the selection menu does not trap the whole page and still locks scroll as intended.
   - Confidence: Medium-high

10. **Grafana design-system Modal API**
    - Evidence: `grafana/grafana@packages/grafana-ui/src/components/Modal/Modal.tsx:19,37-53`.
    - Validation value: Positive control; `trapFocus` and custom-title `ariaLabel` are explicit consumer contracts.
    - Minimal PR/test shape: Cover `trapFocus={false}`, custom title `ariaLabel`, Escape, and backdrop defaults.
    - Confidence: High

## Second-pass cases after stricter gates

Purpose: these are additional cases for the medium-signal skills after adding false-positive gates. They are intentionally framed as small PRs a maintainer could review, not as raw grep hits.

Recheck rule (2026-06-17): `Candidate` or `hardening` rows are kept as useful leads, but they are not counted as the two solid PR-worthy cases for a skill until a focused test, local reproduction, or maintainer acceptance confirms the defect boundary.

### `a11y-contract-testing`

| Case | Evidence | Failure mode | Minimal PR shape | Confidence |
|---|---|---|---|---|
| Maybe Finance DS menu opens arbitrary interactive content without a menu/popover state contract | `maybe-finance/maybe@app/components/DS/menu.html.erb:3,7,14` wires only `data-DS--menu-target` trigger/content and `hidden`; `menu_controller.js:11` says the menu may contain links/buttons/forms; `:36,66,69,78` handles click/show/focus. No `role=/aria-*` attributes were present in the menu files. | The trigger is operable visually, but AT/tests cannot observe `aria-haspopup`, `aria-expanded`, trigger-content ownership, or menu item semantics. If it is a generic popover, that contract is also undocumented and untested. | Add `aria-haspopup`, `aria-expanded`, `aria-controls`, stable ids, and a role/name test for the trigger/content; if action-menu content is used, add `role="menu"`/`menuitem` or split into a popover component. | High |
| Appwrite fake payment modal renders as styled divs with a visible title but no dialog role/name | `appwrite/console@src/lib/components/fakeModal.svelte:7,69,72,91,102` has `title`, backdrop, `.modal`, title slot, and close button; usages include `replaceCard.svelte:120` and `retryPaymentModal.svelte:170-176`. No `role="dialog"`, `aria-modal`, or `aria-labelledby` was found in the modal component. | Payment modals can be opened and closed visually, but `getByRole('dialog', { name })` and screen-reader dialog navigation cannot identify the modal by its title. | Give the modal container `role="dialog"`, `aria-modal` when outside interaction is blocked, and `aria-labelledby` to the title id; add a payment-modal accessibility contract test. | High |

### `constraint-validation-contracts`

| Case | Evidence | Failure mode | Minimal PR shape | Confidence |
|---|---|---|---|---|
| Appwrite shared text-like inputs set native-invalid error state but do not clear it on edit | `inputText.svelte:34,40,62-66`, `inputEmail.svelte:32,50-57`, `inputURL.svelte:34,56-60`, `inputNumber.svelte:51,72-76`, and `inputPassword.svelte:31,48,52-53` set `error` from `validationMessage`, display `helper/state`, and bind value; the `on:input` directives forward/change value but do not clear/revalidate `error`. | After a failed submit, a corrected value can keep a stale warning/error visual state until another invalid/submit cycle, violating the clearing contract. | Centralize `clearErrorOnInput` or revalidate on input while preserving forwarded events; add a sequence test invalid submit -> type valid -> helper disappears -> submit succeeds. | Medium-high |

### `frontend-security-baseline`

| Case | Evidence | Failure mode | Minimal PR shape | Confidence |
|---|---|---|---|---|
| NextChat share flow uses `window.open(res, "_blank")` without opener isolation | `ChatGPTNextWeb/NextChat@app/components/exporter.tsx:316-323` obtains a share URL from `api.share(msgs)` and displays/copies it; `:346-347` opens `res` with `window.open(res, "_blank")` and no feature string. | The opened share page receives a live `window.opener` reference in browsers unless `noopener` is requested, so a compromised/share destination can navigate the app tab. | Use `window.open(res, "_blank", "noopener,noreferrer")` or a helper that always sets opener isolation; add a unit/static assertion for popup features. | High |
| Appwrite console command palette opens external docs/support tabs without `noopener,noreferrer` | `appwrite/console@src/routes/(console)/+layout.svelte:106-108`, `:114-116`, and `:130-132` call `window.open('https://appwrite.io/...', '_blank')` for docs/Discord commands. | Even constant trusted external links create an avoidable opener channel from the new tab back to the console tab; this is exactly the `window.open` gap not covered by modern anchor defaults. | Add a small `openExternal(url)` helper using `window.open(url, '_blank', 'noopener,noreferrer')` and test/grep command-palette actions through it. | Medium (hardening; keep as lead, not counted as solid) |

### `i18n-copy-and-layout`

| Case | Evidence | Failure mode | Minimal PR shape | Confidence |
|---|---|---|---|---|
| NextChat MCP market bypasses the app locale system for empty/loading/actions | `ChatGPTNextWeb/NextChat@app/components/mcp-market.tsx:464` hardcodes `No servers available`; `:697`, `:704`, `:725` hardcode `Cancel`/`Save`/`Close`; `:733` and `:746` hardcode loading/empty states. The component has no `Locale` import while the app uses `app/locales`. | Localized users see English action, loading, and empty-state copy in a localized product surface. | Add `Locale.McpMarket.*` keys and replace hardcoded strings; add one locale fixture/story or snapshot covering empty/loading/action states. | High |
| NextChat error boundary imports `Locale` but recovery copy remains English | `ChatGPTNextWeb/NextChat@app/components/error.tsx:8` imports `Locale`; `:43`, `:52`, and `:59` hardcode `Oops, something went wrong!`, `Report This Error`, and `Clear All Data`; only the reset confirmation at `:61` uses `Locale`. | The most visible crash/recovery screen ignores the existing translation mechanism except for one confirm message. | Move title/actions into `Locale.ErrorBoundary` or equivalent and add locale entries/tests for the crash screen. | High |

### `ssr-hydration-mismatch`

| Case | Evidence | Failure mode | Minimal PR shape | Confidence |
|---|---|---|---|---|
| NextChat Artifacts iframe id is generated with `nanoid()` during first render | `ChatGPTNextWeb/NextChat@app/components/artifacts.tsx:11,39,81-99` initializes `frameId` with `nanoid()`, embeds it in `srcDoc`, and keys the iframe by it; `home.tsx:43` imports Artifacts via `dynamic(...)` without `ssr: false`. | Server and client can render different iframe key/srcDoc ids before hydration, producing recoverable hydration errors or iframe replacement. | Initialize with a stable placeholder and set the random id in an effect, or isolate the iframe as no-SSR; add a hydration smoke test with `onRecoverableError`. | High |
| Appwrite payment edit modal derives form constraints from `new Date()` during SSR-rendered component evaluation | `appwrite/console@src/routes/(console)/account/payments/editPaymentModal.svelte:26` computes `currentYear`, `:60-62` recomputes `currentMonth` for month options, and `:85,90` bind expiry month/year inputs. SvelteKit route components SSR by default. | Around a month/year boundary, server HTML can contain a different `min` year or month option list than the client first render. | Serialize a request-time `now`/billing date into props/load data or compute after mount with a placeholder; add a fake-clock SSR/client render test for month/year rollover. | Candidate (needs fake-clock SSR proof; keep as lead, not counted as solid) |

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

| Case | Evidence | Failure mode | Minimal PR shape | Confidence |
| --- | --- | --- | --- | --- |
| Codecademy Gamut Checkbox Code Connect maps checked/indeterminate states to string booleans | `Codecademy/gamut@packages/code-connect/Atoms/FormInputs/Checkbox.figma.tsx:19-27` maps Figma `checked` to `'true'`/`'false'` strings and `Indeterminate` to `'true'`/`'false'` strings. The component contract is boolean: `packages/gamut/src/Form/inputs/types.tsx:12-23` declares `indeterminate: boolean` / `checked?: boolean`, and `Checkbox.tsx:173-179,192,209-226` uses those props in boolean logic and DOM checkbox state. | A Figma unchecked state can generate `<Checkbox checked="false" indeterminate="false" />`; those are truthy strings in component logic, so the Code Connect preview/snippet can render an active/checked or indeterminate-looking checkbox instead of matching the Figma unchecked state. | Change the Code Connect mapping to real booleans (`true: true`, `false: false`, `Indeterminate: false`; `indeterminate` `Indeterminate: true` else `false`) and add a Code Connect/static test or story asserting generated examples use boolean props. | High |
| Narmi Design System Chip Code Connect declares icon/close-button design props but drops them in the example | `narmi/design_system@src/Chip/index.figma.tsx:32-47` declares Figma props for `Show StartIcon`, `Show EndIcon`, `Show Count`, `CloseButton`, and an `onDismiss` handler. The generated example at `src/Chip/index.figma.tsx:52-53` only renders `<Chip kind={kind} label={label} count={count} />`. The component supports these visual props in `src/Chip/index.tsx:17-34` (`onDismiss`, `startIcon`, `endIcon`, `count`) and renders the close button when `onDismiss` is present at `src/Chip/index.tsx:94-114`. | Figma variants with a start icon, end icon, or close button produce a code example without those visible affordances. This is exactly the design-to-code fidelity class: the Figma design has visual elements, but the generated rendered component omits them. | Pass `startIcon`, `endIcon`, and `onDismiss` through the Code Connect example (or remove those Figma prop mappings if intentionally unsupported). Add a representative Code Connect/Storybook example for icon + dismissible chip. | High |

Practical note: attempts to export public Figma links from `figma/sds`, `primer/react`, `narmi/design_system`, `inngest/inngest`, and `Codecademy/gamut` with the local token returned `Not found`; this validated the access trap now documented in `skills/design-to-code-fidelity/SKILL.md`. Public browser visibility is not enough for Figma Images API validation unless the token account has file access or a duplicated copy.

### `design-to-code-fidelity` strict Figma export recheck (2026-06-17)

Counting rule for this skill is now stricter than the earlier Code Connect checks: a case only counts as a full design-to-code validation when the Figma node is exported as an actual image, the implementation is rendered, and `visual-diff.sh` is run. Code Connect prop mapping cases remain useful, but they are not full Figma-vs-browser pixel-diff evidence.

| Case | Evidence | Failure mode | Minimal PR shape | Confidence |
| --- | --- | --- | --- | --- |
| n8n Storybook Callout design reference does not match the rendered Callout stories | OSS checkout at `n8n-io/n8n@854835dc`. Story source `packages/frontend/@n8n/design-system/src/components/N8nCallout/Callout.stories.ts:28-31` points the Callout story design panel at `https://www.figma.com/file/tPpJvbrnHbP8C496cYuwyW/Node-pinning?node-id=15%3A5777`. Figma Images API export succeeded with `figma-export.sh tPpJvbrnHbP8C496cYuwyW 15-5777 ...` and produced `15_5777.png` (`630x169`). Local Storybook rendered `core-callout--secondary-callout` via `render-capture.mjs` (`630x171`). `AE_FUZZ=10% STRUCT_GATE=1 visual-diff.sh` reported `STRUCT=DRIFT MAX_BLOCK=51838@630x169+0+0`. | The linked Figma node is a Node Pinning frame with two warning/info callouts and close affordances; the rendered Storybook examples are success/custom/secondary copy variants (`defaultCallout`, `customCallout`, `secondaryCallout`) and do not match that reference. The design panel therefore gives maintainers a stale/non-equivalent design target. | Either point the story at the real Callout component/spec in Figma, or add a dedicated Node Pinning/dismissible-callout story whose args/slots match the linked Figma frame. Then keep the Figma export + Storybook screenshot diff as a regression gate. | Medium-high: full export/render/diff was run, but it is a Storybook-design-reference mismatch more than a proven production UI bug. |

Strict recheck notes:

- Rejected as **not full cases yet**: the earlier `Codecademy/gamut` Checkbox and `narmi/design_system` Chip findings. They are still strong Code Connect mapping issues, but they did not pass the Figma PNG export + browser render + pixel-diff bar.
- Figma Images API access was tested across 100 public OSS Figma links from Carbon, EUI, Fluent UI, Polaris, Ring UI, Twilio Paste, and related design-system repos; all returned `Not found` with the current token. This confirms that a public browser/community Figma URL is not enough for REST image export.
- Additional OSS links whose Images API access returned an image URL before the token hit the low-tier rate limit, but whose PNG export/diff was **not completed and therefore not counted**: Cal.com `Cal-DS---Components` node `25883-174646`, Cal.com booking logs node `5641-6732`, n8n old design-system nodes `2-23` and `79-6898`, and n8n `Node-pinning` node `15-5777`.
- Current blocker for finding the second strict case: Figma returned `429 Rate limit exceeded` with `x-figma-rate-limit-type: low` and a very large `Retry-After`. Do not claim a second full case until another token/maintainer token or reset window allows a fresh export and diff.
- `figma.com/api/oembed` thumbnails are **not acceptable substitutes** for strict validation: for n8n design-system nodes they returned generic cover thumbnails, not the target node/frame PNG.
