# frontend-niche-skills

Verified agent skills for the **frontend topics general best-practice skills don't
cover** — the long tail where the first mistake is expensive and English-only,
browser-only testing never catches it.

Two rules for everything in this collection:

1. **Every factual claim is checked against official sources** (specs, vendor docs)
   before release; community-sourced claims are labeled as such.
2. Each skill is a compact one-pass checklist; depth lives in per-skill `references/`.

## Skills

| Skill | Use when |
|-------|----------|
| [`webview-bridge-pages`](./skills/webview-bridge-pages/SKILL.md) | Building a page loaded in a native WebView (React Native, WKWebView, Android WebView, Flutter): postMessage bridge contracts, native close/back, blank-screen READY signals, query-param A/B variants, webview layout pitfalls |
| [`a11y-contract-testing`](./skills/a11y-contract-testing/SKILL.md) | Locking accessibility semantics in as testable contracts — dialog roles/names, `getByRole` queries, sentinel specs that fail when a modal ships unnamed |
| [`cjk-text-and-input`](./skills/cjk-text-and-input/SKILL.md) | CJK line breaking (`keep-all`, `line-break`), IME composition events breaking controlled inputs, Enter-during-composition, grapheme-safe length counting |
| [`deeplink-hydration`](./skills/deeplink-hydration/SKILL.md) | Deep links losing query params on first SPA/SSR render — `router.isReady` gating, `window.location` fallback, auth-bounce `returnTo`, direct-navigation tests |

`webview-bridge-pages` ships with host references
([`references/`](./skills/webview-bridge-pages/references/)): contract-design ·
page-implementation · react-native · wkwebview · android-webview · flutter.

## Install

Skills follow the [agentskills.io](https://agentskills.io/specification) `SKILL.md`
format, compatible with Claude Code and Codex.

### Claude Code (plugin, recommended)

```shell
/plugin marketplace add dididy/frontend-niche-skills
/plugin install frontend-niche-skills@frontend-niche-skills
```

### Manual (Claude Code or Codex)

```bash
# Claude Code (user-level) — repeat per skill you want
ln -s <repo>/skills/<skill-name> ~/.claude/skills/<skill-name>

# Codex (user-level; some setups use a shared ~/.agents/skills instead)
ln -s <repo>/skills/<skill-name> ~/.codex/skills/<skill-name>
```

Project-level: symlink or copy into the repo's `.claude/skills/` / `.codex/skills/`.
Codex has no plugin system — the manual symlink is the supported path there.

## License

[Apache-2.0](./LICENSE.txt) · Copyright 2026 YONGJAE LEE ·
[Security policy](./SECURITY.md) · [Changelog](./CHANGELOG.md)

## Scope

These skills are deliberately generic — no company-specific paths, i18n systems, or
component names. Pair them with project-local skills for repo conventions.

## Related libraries & further reading (webview)

The webview skill is the **knowledge layer** — it tells you how to design the page and
the contract. For the transport implementation itself, or deeper dives, these are
solid (all links live-verified 2026-06):

### Bridge libraries (transport implementations)

| Library | What it gives the web side |
|---------|---------------------------|
| [gronxb/webview-bridge](https://github.com/gronxb/webview-bridge) | Type-safe React Native ↔ web bridge (tRPC-style); ships a dedicated `@webview-bridge/web` package. Active as of 2026-02 (v1.7.9). |
| [daangn/metabridge](https://github.com/daangn/metabridge) | JSON-Schema-driven codegen from Karrot: one schema → typed TS SDK for the page + Kotlin/Swift stubs. |
| [marcuswestin/WebViewJavascriptBridge](https://github.com/marcuswestin/WebViewJavascriptBridge) | The classic iOS bridge (14k★); injects a `registerHandler`/`callHandler` shim into the page. Dormant but historically formative. |
| [kibotu/jsbridge](https://github.com/kibotu/jsbridge) | One injected `bridge.js` for both Android `@JavascriptInterface` and iOS `WKScriptMessageHandler` — single `window.jsbridge` API. |
| [inokawa/react-native-react-bridge](https://github.com/inokawa/react-native-react-bridge) | Bundles a React app as inline HTML into an RN WebView with a message hook on each side. |

### Engineering write-ups

- [Shopify — Mobile Bridge: Making WebViews Feel Native](https://shopify.engineering/mobilebridge-native-webviews) (2025) — ~600 WebView screens: background preloading, snapshotting against blank screens.
- [Close — Communicating with React Native Web Views](https://making.close.com/posts/react-native-webviews/) (2024) — strongly-typed `{action, payload}` message bridge design (equivalent envelope to this skill's `{ type, data }` — standardize on one).
- [Zellic — You're Probably Using WebViews Wrong](https://www.zellic.io/blog/webview-security) (2025) — bridge security: iframe access, origin checks, spoofed messages.
- [MECH2CS — RN WebView 브릿지 통신 안정성 개선](https://blog.mech2cs.com/posts/react-native-webview-bridge-handshake) (2025, Korean) — independently converges on the WEB_READY handshake this skill recommends.
- [당근 — 웹 프로젝트 배포하기 #1: 파일 기반 웹뷰](https://medium.com/daangn/%EB%8B%B9%EA%B7%BC%EB%A7%88%EC%BC%93%EC%97%90-%EC%9B%B9-%ED%94%84%EB%A1%9C%EC%A0%9D%ED%8A%B8-%EB%B0%B0%ED%8F%AC%ED%95%98%EA%B8%B0-1-%ED%8C%8C%EC%9D%BC-%EA%B8%B0%EB%B0%98-%EC%9B%B9%EB%B7%B0-d312b17e697c) (2022, Korean) — local `file://` webview serving, its origin-model limits, and why they moved off it.
- [우아한형제들 — 플로팅웹뷰 도입기](https://techblog.woowahan.com/24165/) (2025, Korean) — native chrome overlapping web popups, safe-area, page-to-page messaging.
- [Wonderwall — 웹뷰 브릿지 개선기: 버전 분기 지옥에서 벗어나기](https://tech.wonderwall.kr/articles/webviewsinglebridge/) (2026, Korean) — migrating to a single typed `sendBridge` entrypoint, the same shape as this skill's transport adapter.
- [Toss 앱인토스 — WebView 시작하기](https://developers-apps-in-toss.toss.im/tutorials/webview.html) — a production mini-app platform's official web-side docs (incl. a SafeAreaInsets API mirroring this skill's inset guidance).

### Compatibility & standards

- [CanIWebView](https://caniwebview.com/) — W3C WebView Community Group's cross-platform compatibility reference (Android WebView vs WKWebView behaviors: CORS, cookies, storage, JS injection).
- [W3C WebView Community Group](https://www.w3.org/community/webview/) — the standards-side effort on WebView/web-content friction.
- [web.dev — Web on Android](https://web.dev/articles/web-on-android) — WebView vs Custom Tabs vs TWA from the web developer's perspective.
