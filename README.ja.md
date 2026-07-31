<div align="center">
<img src="docs/assets/hero.png" alt="frontend-niche-skills — frontend edge-case agent skills for WebView, IME, semantic markup, hydration, forms, dates, auth, payment pages, a11y, and design drift." width="100%" />
</div>

# Frontend Niche Skills

<p align="center">
<a href="#skills"><img alt="Agent Skills" src="https://img.shields.io/badge/Agent_Skills-41-1FC07C?style=flat-square&amp;labelColor=black" /></a>
<a href="https://claude.com/product/claude-code"><img alt="Claude Code" src="https://img.shields.io/badge/Claude_Code-compatible-D97757?style=flat-square&amp;labelColor=black&amp;logo=anthropic&amp;logoColor=white" /></a>
<a href="https://github.com/openai/codex"><img alt="Codex" src="https://img.shields.io/badge/Codex-compatible-412991?style=flat-square&amp;labelColor=black&amp;logo=openai&amp;logoColor=white" /></a>
<a href="#skills"><img alt="Frontend edge cases" src="https://img.shields.io/badge/WebView_%7C_IME_%7C_a11y_%7C_payment-included-37B0E6?style=flat-square&amp;labelColor=black" /></a>
<a href="./LICENSE"><img alt="License" src="https://img.shields.io/badge/License-Apache--2.0-37B0E6?style=flat-square&amp;labelColor=black" /></a>
</p>

<p align="center">
<a href="README.md">🇺🇸 English</a> | <a href="README.ko.md">🇰🇷 한국어</a> | <strong>🇯🇵 日本語</strong> | <a href="README.zh-cn.md">🇨🇳 简体中文</a>
</p>

**幅広いチェックリストが見落としがちなフロントエンドのエッジケースのための Agent Skills — WebView ページ、セマンティックマークアップ、オーバーレイのライフサイクル、IME/CJK 入力、ハイドレーション、フォーム、認証、決済ページ、エクスポート、日時、ビジュアル忠実度、レポートトリアージ。**

`frontend-niche-skills` は、Claude Code、Codex、その他 `AGENTS.md` 互換のコーディングエージェントに、正しい修正がエビデンスの種類の切り分けにかかっているバグ — レイアウト vs ペイント、DOM vs アクセシビリティツリー、ブラウザ vs ネイティブ WebView ホスト、サーバーレンダリング vs クライアントハイドレーション、決済ページのデータ境界 vs ランタイムスクリプトサーフェス、エクスポートファイル vs スプレッドシート/Blob/クリップボードの挙動 — に対する、焦点を絞ったプレイブックを提供します。

これらのスキルは、プロジェクトの規約、セキュリティレビュー、QSA/法務の判断、実ブラウザ/実機テストの代わりにはなりません。もっともらしいだけの汎用的な修正を当てる前に、エージェントが正しいエビデンスを求められるようにするためのものです。

## 目次

- [インストール](#インストール)
- [クイック例](#クイック例)
- [ワークフロー](#ワークフロー)
- [スキル](#スキル)
- [症状マップ](#症状マップ)
- [エビデンス](#エビデンス)
- [開発チェック](#開発チェック)
- [FAQ](#faq)
- [ライセンス](#ライセンス)

## インストール

[`skills` CLI](https://www.skills.sh/) をインストールしてください。スキルは [`SKILL.md` フォーマット](https://agentskills.io/specification)に従っています。

これらのスキルは、仕様の `description` 1024 文字上限に従う Claude Code や Codex などを対象とし、適切なスキルが起動するようその文字数をトリガー表現に使っています。Claude.ai のアップロード経路では `description` が 200 文字に制限されるため、そのままアップロードすると失敗します([Claude ドキュメント](https://claude.com/docs/skills/how-to))。

以下の `voidmatcha/frontend-niche-skills` コマンドは、公開リポジトリまたはプラグインマーケットプレイスのエントリーが利用可能であることを前提としています。ローカルまたはプレリリースのチェックアウトでは、代わりにこのセクションのローカルチェックアウト用コマンドを使ってください。

```bash
# Claude Code + Codex via skills CLI
npx skills add voidmatcha/frontend-niche-skills --skill '*' -g -a claude-code -a codex

# Other agents supported by the installed skills CLI
npx skills add voidmatcha/frontend-niche-skills --skill '*' -g --agent '*'
```

### Claude Code プラグイン

```bash
/plugin marketplace add voidmatcha/frontend-niche-skills
/plugin install frontend-niche-skills@voidmatcha
```

### Codex プラグインのローカルチェックアウト

このリポジトリには `.codex-plugin/plugin.json` と Claude プラグインのマニフェストが含まれています。ローカルチェックアウトから:

```bash
codex plugin marketplace add "$(pwd)"
codex plugin add frontend-niche-skills@frontend-niche-skills
```

インストールや更新のあとは、バンドルされたスキルを再読み込みさせるため、Codex または Claude Code の新しいセッションを開始してください。

## クイック例

```text
You: Review this React Native WebView onboarding page. The CTA area is still
clickable after app resume, but the button label and footer text disappear.

frontend-niche-skills / webview-bridge-pages:

[Diagnosis] Separate layout, hit-test, and paint evidence
- Footer box exists and receives taps.
- Missing pieces are child text/button paint, not bridge routing.
- Reproduce in the native app WebView, not only desktop Chrome.

Likely fix direction
- Remove stale JS height measurement if flex layout can own the footer.
- If hit-test survives but children vanish, inspect compositing/layering:
  isolation boundary, child z-index, transform layer promotion, gradient fallback.

Verification
- Resume/reopen WebView, rotate if relevant, and capture screenshot/video.
- Confirm the CTA is both visible and tappable; do not accept click-only evidence.
```

このパターンの価値: 汎用的なパッチをもう 1 つ当てる前に、エージェントに正しい仮説を検証させることです。

## ワークフロー

1. **症状に合うスキルを選ぶ。** バグと失敗モードが一致する、最も範囲の狭いスキルを使います。
2. **リポジトリのコンテキストを読む。** スキルを、プロジェクトのルーティング、デザイントークン、i18n、テスト、ブラウザ/デバイスサポートと組み合わせます。
3. **エビデンスの種類を切り分ける。** レイアウト、ペイント、ヒットテスト、DOM 構造、アクセシビリティツリー、ネットワーク、ハイドレーション、ロケール挙動、ランタイムスクリプト、エクスポートされたファイルは、互いに食い違うことがあります。
4. **症状ではなく原因を直す。** リトライを足すより、壊れやすいタイミング依存や重複ロジックを取り除くことを優先します。
5. **正しいホストで検証する。** WebView のバグにはアプリ内 WebView のエビデンスが、決済ページの指摘にはランタイムスクリプト/PAN 境界のエビデンスが、ビジュアル忠実度にはリファレンス/レンダリングのキャプチャが必要です。フォーム/a11y の指摘には、可能な限りリグレッションテストを用意します。

<a id="skills"></a>

## スキル

対象とするフロントエンドの失敗の種類ごとにグループ化された 41 個のスキルです。レポートが雑多だったり複数のドメインにまたがったりする場合は、`frontend-report-triage` から始めてください。

実践的な優先順位:

- **デフォルトで価値の高いチェック:** SSR/ディープリンクのルーティング、フォームバリデーション、日時、認証/セキュリティ、決済/エクスポートの境界、オーバーレイ、アクセシビリティ、セマンティック HTML。よくあるバグや、リリース後に高くつくバグを捕まえます。
- **ホスト/プロダクト固有のチェック:** WebView、ブラウザの iframe/embed、CJK/IME、i18n/RTL、決済ページのエビデンスは、プロダクトが実際にそれらのサーフェスを出荷している場合に最も価値があります。
- **品質/メンテナンスのチェック:** デザイン忠実度とコンポーネント抽出は、レビューの悩みがランタイムのバグではなく、ビジュアルのずれ、AI 生成 UI、早すぎる抽象化である場合に役立ちます。

ソースの方針: README にはルーティングとエビデンスのドキュメントを列挙し、詳細な引用は各スキルの `## Sources` ブロックまたは `references/*.md` ファイルに置いています。README がすべてのアップストリーム URL を重複して持たないためです。

### まずはここから

| スキル | 使いどころ |
| --- | --- |
| [`frontend-report-triage`](./skills/frontend-report-triage/SKILL.md) | 曖昧または複数症状のフロントエンドバグレポートをパック全体でトリアージし、可能性の高い失敗クラス、エビデンスのギャップ、フォローアップに最適な 1〜3 個のスキルを返します。 |

### ランタイムホストのエッジケース

| スキル | 使いどころ |
| --- | --- |
| [`webview-bridge-pages`](./skills/webview-bridge-pages/SKILL.md) | ネイティブ WebView 内に読み込まれるページの構築・デバッグ: ブリッジのコントラクト、セーフエリア/ビューポートのレイアウト、ライフサイクル、ヒットテスト vs ペイント/コンポジット、アプリホスト固有の癖。 |
| [`iframe-embed-contracts`](./skills/iframe-embed-contracts/SKILL.md) | ブラウザの iframe/widget の構築・デバッグ: 親-ゲスト間メッセージ、埋め込み許可ヘッダー、sandbox/Permissions Policy、READY/init ハンドシェイク、動的サイズ、分割ストレージ、破棄。 |
| [`browser-page-lifecycle-bfcache-contracts`](./skills/browser-page-lifecycle-bfcache-contracts/SKILL.md) | 戻る/進むナビゲーション後にページが停止したり古い接続・タイマー・状態を再利用したりする場合: `pageshow`/`pagehide`、bfcache 復元、一時停止/再開、保存適格性。 |
| [`history-scroll-restoration-contracts`](./skills/history-scroll-restoration-contracts/SKILL.md) | SPA の戻る/進む、または同一文書内の hash ナビゲーション後に誤った位置へ復元される、非同期レンダリング後に二重スクロールする、fragment 対象を見失う場合: history entry の識別、復元の所有者、描画準備。 |
| [`media-capture-device-contracts`](./skills/media-capture-device-contracts/SKILL.md) | 権限拒否、デバイス切替、track の中断、終了後にカメラ/マイクが失敗する場合: `getUserMedia`、デバイス列挙/変更、track 状態、クリーンアップ、再取得。 |
| [`deeplink-hydration`](./skills/deeplink-hydration/SKILL.md) | ルーターのハイドレーション準備が整う前にクエリパラメータを失ったり、誤った状態に着地したりする SPA/SSR ディープリンクのデバッグ。 |
| [`ssr-hydration-mismatch`](./skills/ssr-hydration-mismatch/SKILL.md) | ロケール/時刻/乱数/ブラウザ専用 API、ストレージ、認証状態、レスポンシブ分岐、データレースに起因するハイドレーション不一致の診断。 |
| [`realtime-transport-contracts`](./skills/realtime-transport-contracts/SKILL.md) | 接続断をまたぐ WebSocket/SSE クライアントのデバッグ: 再接続のバックオフ/ジッター、SSE の Last-Event-ID/カーソルによる再開、順序乱れ/重複/欠落のあるデルタ、ハートビート/ゾンビ検出、bufferedAmount によるバックプレッシャー、オープン中のソケットでの認証更新。 |

### マークアップ、アクセシビリティ、オーバーレイ

| スキル | 使いどころ |
| --- | --- |
| [`semantic-markup-contracts`](./skills/semantic-markup-contracts/SKILL.md) | ネイティブ HTML 構造のレビュー: ボタン vs リンク、見出し、ランドマーク、ラベル、テーブル/リスト、不正なインタラクティブ要素のネスト、ARIA より先にネイティブで直す修正。 |
| [`overlay-focus-scroll-contracts`](./skills/overlay-focus-scroll-contracts/SKILL.md) | モーダル、ドロワー、シート、ポップオーバー、メニュー、コマンドパレットのランタイムコントラクトのレビュー: フォーカストラップ/復元、inert/aria-hidden のタイミング、ネストされたスタック、スクロールロックのクリーンアップ。 |
| [`pointer-gesture-contracts`](./skills/pointer-gesture-contracts/SKILL.md) | 単一ポインターのドラッグ、スワイプ、リサイズ、描画が停止/キャンセルする、要素外で入力を失う、ページスクロールと競合する場合: active pointer の所有、イベント配信/capture、キャンセル、`touch-action`、クリーンアップ。実際のピンチ、回転、複数接点の幾何計算は対象外です。 |
| [`a11y-contract-testing`](./skills/a11y-contract-testing/SKILL.md) | アクセシビリティのセマンティクスをリグレッションテストに変換: ロール、名前、状態、フォーカス、ダイアログ、メニュー、コンボボックス、タブ。 |
| [`view-transitions-contracts`](./skills/view-transitions-contracts/SKILL.md) | サイレントに中断する、古いスナップショットで固まる、reduced-motion を無視する、ゴーストが残る View Transitions API アニメーションのレビュー — 再実装ガイドではなく、レビュー/PR に値するかを見るレンズです。 |
| [`css-transition-animation-contracts`](./skills/css-transition-animation-contracts/SKILL.md) | ダイアログ/ポップオーバー/トップレイヤーの enter/exit トランジション（`@starting-style`、`allow-discrete`、`overlay`）と、トランジション完了を条件にしたクリーンアップ（`transitionend` vs `getAnimations().finished`）のレビュー。 |
| [`responsive-image-contracts`](./skills/responsive-image-contracts/SKILL.md) | レスポンシブ画像マークアップのレビュー: `srcset`/`sizes` と実際のレイアウトの対応、内在幅（intrinsic width）のラベル、LCP の eager/`fetchpriority`、`picture` によるアートディレクション、CLS のための `width`/`height`。 |

### 入力、コンテンツ、日時

| スキル | 使いどころ |
| --- | --- |
| [`contenteditable-selection-contracts`](./skills/contenteditable-selection-contracts/SKILL.md) | contenteditable またはリッチテキスト編集ホストでキャレット/選択が失われる・飛ぶ、編集が重複する、元に戻す/やり直しが壊れる、貼り付け/ドロップ位置がずれる、再レンダー中のコンポジションや破棄後のフォーカス/選択復元が壊れる場合。 |
| [`cjk-text-and-input`](./skills/cjk-text-and-input/SKILL.md) | 韓国語・日本語・中国語のテキスト/入力の取り扱い: 折り返し、IME コンポジション、Enter の扱い、書記素セーフな長さ、バリデーションのタイミング。 |
| [`i18n-copy-and-layout`](./skills/i18n-copy-and-layout/SKILL.md) | ローカライズのコピー/レイアウトのレビュー: 複数形処理、文字数の膨張、bidi/RTL、ロケール別フォーマット、翻訳キーのコントラクト。 |
| [`datetime-correctness`](./skills/datetime-correctness/SKILL.md) | 日付/時刻コードの監査: タイムゾーン、DST、パース、フォーマット、`datetime-local`、相対時刻、サーバー/クライアントの時計の問題。 |
| [`money-and-precision-contracts`](./skills/money-and-precision-contracts/SKILL.md) | 金額/数量の算術: 浮動小数点の誤差（`0.1 + 0.2`）、整数の最小単位 vs decimal ライブラリ、`toFixed`/丸めモードの落とし穴、合計/税計算の順序、`Intl` の通貨出力 vs ローカライズされた金額のパース。 |

### フォーム、認証、セキュリティ、決済

| スキル | 使いどころ |
| --- | --- |
| [`constraint-validation-contracts`](./skills/constraint-validation-contracts/SKILL.md) | ネイティブ HTML Constraint Validation API のコントラクト: `setCustomValidity`、`reportValidity`、`:user-invalid`、invalid から valid へのライフサイクル。 |
| [`js-form-validation-contracts`](./skills/js-form-validation-contracts/SKILL.md) | React Hook Form、Formik、Final Form、vee-validate、Valibot、カスタム JS フォームフロー: 古いエラーの残留、無効化されたままの送信ボタン、非同期/サーバーのレース、サーバーのフィールドエラーのマッピング。 |
| [`frontend-auth-flow-contracts`](./skills/frontend-auth-flow-contracts/SKILL.md) | ブラウザ向け認証の堅牢化: returnTo リダイレクト、OAuth/パスキー/autocomplete、OTP、機密操作前の再認証コントラクト。 |
| [`user-activation-contracts`](./skills/user-activation-contracts/SKILL.md) | ユーザークリック後に `window.open()`、クリップボード、フルスクリーン、ファイル選択が拒否される場合: 一時的/持続的ユーザーアクティベーション、非同期境界、消費する API。 |
| [`frontend-security-baseline`](./skills/frontend-security-baseline/SKILL.md) | フロントエンドの XSS、DOM インジェクション、サニタイザーの誤用、CSP、サードパーティスクリプト、ストレージ、URL パースの基本のチェック。 |
| [`bff-proxy-security-contracts`](./skills/bff-proxy-security-contracts/SKILL.md) | フロントエンド所有の BFF/API プロキシをレビュー: クライアント選択ターゲットの SSRF、route/method/auth capability allowlist、別 ingress のドリフト、multipart の上限と boundary、redirect/error 処理、upstream の business-flow 責任。 |
| [`payment-page-client-security`](./skills/payment-page-client-security/SKILL.md) | チェックアウト/決済ページのクライアントエビデンスのレビュー: ホステッドフィールド vs 直接の PAN 取り扱い、ランタイムスクリプトのインベントリ、サードパーティスクリプトのリスク、CSP/SRI/ヘッダーのエビデンス、PCI DSS エビデンスのギャップ。 |
| [`optimistic-update-rollback-contracts`](./skills/optimistic-update-rollback-contracts/SKILL.md) | 楽観的 UI ミューテーション: サーバー確認前の変更適用、一時 ID vs サーバー ID、失敗時のロールバック、refetch/invalidation との整合、レスポンスとバックグラウンド refetch のレース。 |
| [`file-ingest-contracts`](./skills/file-ingest-contracts/SKILL.md) | ドラッグ&ドロップ、ファイル入力、ペーストによるページへのファイル取り込み: drop イベントのキャンセル/`dropEffect`、dragenter/leave のちらつき、`DataTransfer` の items vs files、ディレクトリアップロード、`accept`/`file.type` の信頼、オブジェクト URL プレビューのライフサイクル。 |

### 出力、デザイン、抽象化、メンテナンス

| スキル | 使いどころ |
| --- | --- |
| [`download-export-safety`](./skills/download-export-safety/SKILL.md) | CSV/Excel エクスポート、Blob/オブジェクト URL ダウンロード、クリップボード書き込み、生成されるファイル名、エクスポート固有のデータ境界のレビュー。 |
| [`design-to-code-fidelity`](./skills/design-to-code-fidelity/SKILL.md) | エクスポート、キャプチャ、ビジュアル差分、エビデンスのグレーディングによる、実装とデザインリファレンスの比較。 |
| [`component-extraction-judgment`](./skills/component-extraction-judgment/SKILL.md) | 繰り返し現れる UI を共有コンポーネント、ラッパー、フック、トークンにすべきか、それとも別々のままにすべきかの判断。 |
| [`client-error-observability-contracts`](./skills/client-error-observability-contracts/SKILL.md) | フロントエンドのエラーキャプチャの配線: `window.onerror`/`unhandledrejection`、エラーバウンダリの限界、クロスオリジンで情報が消える `Script error.`、ソースマップの同梱 vs アップロード、グルーピング、PII のスクラビング。 |

### パフォーマンス、データ、オフライン

| スキル | 使いどころ |
| --- | --- |
| [`core-web-vitals-performance-contracts`](./skills/core-web-vitals-performance-contracts/SKILL.md) | 修正の前に、悪化した Core Web Vitals（LCP、CLS、INP、TTFB）を特定の要素、レイアウトシフト、メインスレッドタスクに帰属させます — スコアだけでなく、ページ全体のバジェット管理。 |
| [`frontend-data-fetching-cache-contracts`](./skills/frontend-data-fetching-cache-contracts/SKILL.md) | ミューテーション後に古いデータを表示するクライアントデータキャッシュ（React Query、SWR、RTK Query、Apollo）、リクエストのウォーターフォール、オーバー/アンダーフェッチ、ページネーション/再検証のキャッシュバグ。 |
| [`browser-storage-durability-contracts`](./skills/browser-storage-durability-contracts/SKILL.md) | ブラウザローカルデータが保存済みと表示された後に消える、IndexedDB スキーマ更新がブロックされる、トランザクションが非アクティブ化/中止される、quota/persistence の証拠や復旧文言が耐久性を誇張する場合。 |
| [`async-effect-race-contracts`](./skills/async-effect-race-contracts/SKILL.md) | 生の非同期エフェクトの誤動作: 依存変更時フェッチのレース（古いレスポンスが勝つ）、クリーンアップ/`AbortController` の欠落、StrictMode の二重実行、インターバル/サブスクリプション内の古いクロージャ。 |
| [`pwa-offline-cache-contracts`](./skills/pwa-offline-cache-contracts/SKILL.md) | サービスワーカー/オフラインキャッシュの不具合: デプロイ後の古いビルド、`ChunkLoadError`、プリキャッシュの抜け、キャッシュのバージョニング/破棄、SW 更新ライフサイクル、認証済みレスポンスのキャッシュ。 |
| [`large-list-data-grid-contracts`](./skills/large-list-data-grid-contracts/SKILL.md) | スクロール位置が飛ぶ・失われる仮想化リスト/グリッド、画面外の行がアンマウントされることで壊れるページ内検索/スクリーンリーダーの件数/フォーカス、固定カラム/ヘッダーのずれ。 |
| [`resize-observer-layout-contracts`](./skills/resize-observer-layout-contracts/SKILL.md) | `ResizeObserver loop` エラー、不安定な自動サイズ調整、測定と書き込みのフィードバックがある場合: 監視対象、box オプション、配信タイミング、書き込みのバッチ化、クリーンアップ。 |

## 症状マップ

グループ化されたスキル一覧に目を通したあとに使ってください。失敗シグナルから出発し、まず最も具体的なランタイムエビデンスを選び、必要に応じて関連スキルに引き継ぎます。

| 失敗シグナル | 最初に使うスキル | 最初に問うべきこと |
| --- | --- | --- |
| ページが React Native WebView、WKWebView、Android WebView、Flutter WebView、アプリ内ブラウザで動作しており、セーフエリア、キーボード、復帰（resume）、ブリッジ、ペイントがデスクトップ Chrome と異なる。 | `webview-bridge-pages` | これはレイアウト、ヒットテスト、ペイント/コンポジット、ブリッジのタイミング、ホストのライフサイクルのどれか？ |
| ブラウザの iframe/widget が空になる、偽装メッセージを受ける、READY/init を失う、サイズ変更でちらつく、必要な機能が使えない、または埋め込みログインが消える。 | `iframe-embed-contracts` | 正確な親/ゲスト origin、配信された frame ポリシー、認証済みメッセージのハンドシェイク、サイズプロトコル、ストレージモードは何か？ |
| 戻る/進む操作の後でページが停止する、または古いソケット・タイマー・状態を再利用する。 | `browser-page-lifecycle-bfcache-contracts` | 新規ロードか bfcache 復元か、どのリソースを一時停止・再開すべきか？ |
| SPA の戻る/進む、または同一文書内の hash ナビゲーションで誤ったスクロール位置に戻る、コンテンツ描画後に二重スクロールする、または fragment 対象を表示できない。 | `history-scroll-restoration-contracts` | どの same-document history entry が位置を所有し、誰が復元し、対象レイアウトはいつ安定するか？ |
| カメラやマイクが最初は動作するが、権限変更、デバイス切替、track の中断、キャプチャ UI の再表示後に失敗する。 | `media-capture-device-contracts` | 権限、選択デバイス、track 状態、終了処理、再取得の遷移はどうなっているか？ |
| HTML 構造そのものが疑わしい: div ボタン、誤ったリンク、ラベル/見出し/リスト、不正なインタラクティブ要素のネスト。 | `semantic-markup-contracts` | ARIA、CSS、JavaScript の前に、ネイティブ HTML でこれを表現できるか？ |
| モーダル、ドロワー、シート、ポップオーバー、メニュー、コマンドパレットの見た目は正しいのに、フォーカス、背景の操作、Escape/バックドロップ、スクロールロックが機能しない。 | `overlay-focus-scroll-contracts` | 開いたとき、ネストして開いたとき、閉じたとき、アンマウント時、ルート変更時に何が起きるか？ |
| 単一ポインターのドラッグ、スワイプ、リサイズ、描画が固まる、要素境界で入力を失う、またはネイティブスクロールと競合する。 | `pointer-gesture-contracts` | シーケンスは 1 つの active `pointerId`、意図したイベント配信/capture 経路、終了時のクリーンアップ、`touch-action` を保つか？ ピンチ、回転、複数接点の幾何計算は別のワークフローへ送ります。 |
| ダイアログ、メニュー、コンボボックス、タブ、カスタムウィジェットにアクセシビリティのリグレッションカバレッジが必要。 | `a11y-contract-testing` | テストでロール、名前、状態、フォーカスのコントラクトをアサートできるか？ |
| contenteditable またはリッチテキスト編集で選択が失われる/反転する、1 回の意図が二重に適用される、元に戻すが壊れる、貼り付け/ドロップ位置がずれる、再マウント後に古い Range が復元される。 | `contenteditable-selection-contracts` | どの live editing host が選択を所有し、この `beforeinput`/`input` トランザクションと履歴をブラウザとアプリのどちらが所有するか？ |
| 韓国語・日本語・中国語のテキスト/入力が正しく動かない: IME の Enter、コンポジション、書記素の長さ、折り返し、切り詰め。 | `cjk-text-and-input` | コードがコンポジション中のテキスト、確定済みテキスト、表示テキストを混同していないか？ |
| 翻訳されたコピーがレイアウト、複数形処理、bidi/RTL、数値/日付フォーマット、翻訳キーのコントラクトを壊す。 | `i18n-copy-and-layout` | バグはコピー、レイアウト、ロケール挙動、入力コンポジションのどれか？ |
| ディープリンク、認証リダイレクト、SPA/SSR ルート、クエリパラメータが誤った画面を初期化する。 | `deeplink-hydration` | ルーターの準備完了、ハイドレーション、認証バウンスの前の URL 状態はどうなっているか？ |
| WebSocket または SSE クライアントが接続断をまたいで壊れる: 再接続ストーム、イベントの重複/欠落、順序の乱れたデルタ、OPEN なのに死んでいるソケットで固まる UI、バッファの肥大化、ハンドシェイク後に期限切れになったトークン。 | `realtime-transport-contracts` | これは再接続/バックオフ、再開/カーソル、デルタの畳み込み、生存確認/ハートビート、バックプレッシャー、ソケットの再認証のどれか？ |
| ブラウザ向け認証 UI に returnTo、OAuth/パスキー、autocomplete、OTP、機密操作前の再認証の問題がある。 | `frontend-auth-flow-contracts` | 認証フローが守るべきブラウザのコントラクトは何か？ |
| クリックハンドラーから始めたポップアップ、クリップボード、フルスクリーン、ファイル選択が非同期処理後に拒否される。 | `user-activation-contracts` | API 呼び出し時に一時的ユーザーアクティベーションが残っているか、先の呼び出しが消費していないか？ |
| 決済ページの外で、生の HTML、サニタイザー、CSP、opener、ストレージ、URL パース、サードパーティスクリプトのリスクが現れる。 | `frontend-security-baseline` | ブラウザセキュリティ上の具体的な source-to-sink 経路があるか？ |
| フロントエンド所有のサーバールートがクライアント選択の path、upload、header、business action を upstream API にプロキシする。 | `bff-proxy-security-contracts` | どの route-method-auth capability が公開され、別 ingress から迂回できるか？ |
| チェックアウト/決済ページにクライアントサイドのエビデンスが必要: ホステッドフィールド、直接の PAN/CVV 取り扱い、ランタイムスクリプト、CSP/SRI/ヘッダーの制御。 | `payment-page-client-security` | 決済データの境界とランタイムスクリプトサーフェスを示すエビデンスは何か？ |
| CSV/Excel エクスポート、ファイルダウンロード、Blob URL、クリップボード書き込み、生成されるファイル名、エクスポートスキーマが関係している。 | `download-export-safety` | 何がブラウザの外に出るのか、そしてスプレッドシートのセル、オブジェクト URL、クリップボードの失敗、ファイル名はどう処理されているか？ |
| 日付のずれ、タイムゾーン/DST の問題、日付のみの入力、`datetime-local` のラウンドトリップ、相対時刻、サーバー/クライアントの時計の不一致。 | `datetime-correctness` | その値はインスタント、ローカル日時、日付のみの値、フォーマット済み表示文字列のどれか？ |
| 金額/数量の合計が端数や 1 セント単位でずれる、丸めがおかしい、ローカライズされた金額が正しくパースされない。 | `money-and-precision-contracts` | 値は二進浮動小数点で計算されているか、そして計算はどの丸めモードと最小単位表現を使っているか？ |
| ネイティブの Constraint Validation API が関係している: `setCustomValidity`、`reportValidity`、`:user-invalid`、invalid から valid へのライフサイクル。 | `constraint-validation-contracts` | ネイティブの validity は正しいタイミングでクリアされ、報告されているか？ |
| React Hook Form、Formik、Final Form、vee-validate、Valibot、カスタム JS バリデーションに古いエラー、無効化されたままの送信、非同期/サーバーのレースがある。 | `js-form-validation-contracts` | エラー、validity、送信、サーバーフィールドのマッピングを所有しているのはどのライブラリ状態か？ |
| ハイドレーション警告またはサーバー/クライアントの不一致に、ロケール、時刻、乱数、ブラウザ専用 API、ストレージ、認証状態、レスポンシブ分岐が関わっている。 | `ssr-hydration-mismatch` | 最初のクライアントレンダリングで決定論的でなければならないものは何か？ |
| 実装が Figma、スクリーンショット、デザインリファレンス、ビジュアル仕様と一致しているべき。 | `design-to-code-fidelity` | 主観的なレビューの前に、リファレンスをエクスポートし、レンダリングをキャプチャして差分を取れるか？ |
| 繰り返し現れる UI をコンポーネント、ラッパー、フック、トークンにすべきか、それとも別々のままにすべきか迷っている。 | `component-extraction-judgment` | その重複は、プロダクト上の差異を隠さずに抽出できるほど安定しているか？ |
| サーバー確認前に適用された楽観的 UI 更新が誤動作する: ちらつき、二重適用、ロールバックされない失敗ミューテーション、レスポンスと refetch のレース後の古いデータ。 | `optimistic-update-rollback-contracts` | 適用 -> 確認/ロールバック -> 整合のコントラクトはどうなっていて、一時/サーバー ID と並行ミューテーションはどう順序付けられているか？ |
| ページに取り込んだファイルが誤動作する: ドロップゾーンのハイライトがちらつく、ドロップしたファイルでページが遷移してしまう、ドロップしたフォルダから何も得られない、誤った型のファイルが通ってしまう、画像ペーストが壊れる、プレビュー URL がリークする。 | `file-ingest-contracts` | どの取り込み経路が壊れているか: ドラッグイベントのキャンセル、`DataTransfer` の items vs files、型の信頼、ペースト、オブジェクト URL のライフサイクルのどれか？ |
| フロントエンドのエラーがダッシュボードに現れない、読めない（ミニファイ済み / `Script error.`）、エラーバウンダリがあるのにアプリがホワイトスクリーンになる。 | `client-error-observability-contracts` | キャプチャは非同期/rejection に配線されているか、クロスオリジン/ソースマップの設定は正しいか、送信前に何がスクラビングされているか？ |
| View Transitions のアニメーションが誤動作する: 発火しないことがある（サイレント中断）、古いフレームで固まる、reduced-motion を無視する、ゴーストモーフが残る。 | `view-transitions-contracts` | `view-transition-name` の重複、未ペイントのスナップショット（Suspense/デコード）、reduced-motion ブロックの欠落、誤った Transition のラップのどれか？ |
| ダイアログ/ポップオーバーの enter/exit アニメーションが途中で切れる、またはトランジションが「完了」しないためにクリーンアップ/フォーカス/アンマウントが詰まる。 | `css-transition-animation-contracts` | トランジションに `display`/`overlay`（`allow-discrete` 付き）が欠けていないか、発火しない `transitionend` を条件にコードがゲートされていないか？ |
| 誤った画像ファイルが配信される、画像が過剰にダウンロードされる、ヒーロー画像が遅延読み込みになっている、画像がレイアウトシフトを引き起こす。 | `responsive-image-contracts` | `srcset` に実際のレイアウトと一致する `sizes`、正しい幅記述子、LCP の `eager`/`fetchpriority`、`width`/`height` があるか？ |
| ページの LCP/CLS/INP が悪化していて、スコアを報告するだけでなく原因への帰属が必要。 | `core-web-vitals-performance-contracts` | LCP の要素はどれか（発見可能で優先されているか？）、各レイアウトシフトの発生源は何か、どの長いタスクが INP を膨らませているか？ |
| ミューテーション後にクライアントキャッシュのデータが古いまま、またはリクエストがウォーターフォール/過剰フェッチになっている（React Query/SWR/RTK Query/Apollo）。 | `frontend-data-fetching-cache-contracts` | どのクエリキーを無効化すべきか、読み取りは正しい stale/gc タイミングで並列化されているか？ |
| ブラウザローカルのレコードが消える、別タブのため IndexedDB 更新が止まる、保存済み表示の後で後続要求がトランザクションを中止する、または persistence を永久バックアップと説明している。 | `browser-storage-durability-contracts` | 失敗した段階は open/upgrade の所有、トランザクションの活性、commit/abort、quota/persistence、予期しない close、復旧のどれか？ |
| 非同期エフェクトが誤ったデータを表示する、二重に発火する、リークする、古い値を読む。 | `async-effect-race-contracts` | take-latest/`AbortController` + クリーンアップはあるか、エフェクトは StrictMode 下で冪等か？ |
| デプロイ後にユーザーへ古いビルドが配信される、`ChunkLoadError` が出る、サービスワーカーがオフラインで誤った/古いバイト列を返す。 | `pwa-offline-cache-contracts` | SW の更新フロー、完全なプリキャッシュ、キャッシュのバージョニング、認証済み HTML/API をキャッシュしないルールはあるか？ |
| 仮想化されたリスト/グリッドでスクロールが飛ぶ・失われる、仮想化のせいで Ctrl+F / スクリーンリーダーの件数 / フォーカスが壊れる。 | `large-list-data-grid-contracts` | `estimateSize`/オーバースキャンは適切か、アンマウントされた行に `aria-setsize`/`aria-posinset`（または `aria-rowcount`）が設定されているか？ |
| `ResizeObserver loop` エラーが出る、自動サイズ調整ウィジェットが揺れる、測定コールバックが再びサイズ変更を起こす。 | `resize-observer-layout-contracts` | どの対象と box を測定し、同じ配信サイクルでどの DOM 書き込みがサイズを変えているか？ |
| レポートが曖昧、複数のドメインにまたがる、どの専門スキルが担当すべきかわからない。 | `frontend-report-triage` | 可能性の高い失敗クラスの上位 1〜3 個は何か、それらを見分けるにはどんなエビデンスが必要か？ |

## エビデンス

このリポジトリは、grep のヒットをそのままバグとして扱いません。ドキュメントでは、確認済みの実例、候補段階のリード、ポジティブコントロール、既知の偽陽性を区別しています。

エビデンスの所在:

- [`docs/oss-validation-cases.md`](./docs/oss-validation-cases.md) — スキルの境界と PR の形をサニティチェックするために使った公開 OSS の事例。
- [`docs/oss-maintainer-candidate-backlog.md`](./docs/oss-maintainer-candidate-backlog.md) — ファイル/行のエビデンス付きの公開 OSS リサーチ候補。報告する前に、現在のデフォルトブランチを再確認し、ローカルで再現してください。
- [`docs/why-webview-bridge-pages.md`](./docs/why-webview-bridge-pages.md) — WebView 固有の先行事例、ブリッジライブラリ、ホスト挙動のリファレンス、エコシステムのメモ。
- [`docs/public-skill-landscape.md`](./docs/public-skill-landscape.md) — このパックと直接重なる、近い、または補完関係にある公開スキルパックを実際に開いて比較し、維持/分割/保留の判断を記録した資料。
- [`docs/skill-evidence-coverage.md`](./docs/skill-evidence-coverage.md) — 各スキルの裏付けが、検証済みの事例、候補段階のリード、一次情報のリファレンス、ルーティング例のどれに由来するかを示すスキル別マップ。
- [`docs/skill-quality-standard.md`](./docs/skill-quality-standard.md) — このパックにおける「良いスキル」の基準と、新規採用・既存メンテナンスのゲート。
- [`docs/frontend-report-triage.md`](./docs/frontend-report-triage.md) — 統合レポートトリアージのコントラクトと例。
- `skills/*/SKILL.md` と `skills/*/references/*.md` — スキルごとの公式ドキュメント、先行事例、例、偽陽性のメモ、実装固有のエビデンス。

候補段階の OSS の指摘は、現在のブランチを再確認し、ローカルで再現し、メンテナーに受け入れられるか失敗するテストで裏付けられるまで、確認済みのアップストリームバグでは**ありません**。

## 開発チェック

リポジトリローカルのチェックは、直接実行することも lefthook 経由で実行することもできます:

```bash
./scripts/pre-push-checks.sh

# Optional: install Git hooks after installing lefthook locally.
lefthook install
lefthook run pre-push
```

`lefthook.yml` はリポジトリのスクリプトに委譲するだけなので、コントリビューターは lefthook なしでも同じチェックを実行できます。このスクリプトは、スキルのメタデータ、README のリンク/カウント、プラグインマニフェスト、ローカルの markdown リンク、必須の品質コントラクト（PR 価値ゲート・弱い指摘の却下・出力形式）、直接リンクされたリファレンス、任意の eval セット、誇大表現の文言、同梱スクリプトの構文を監査します。あわせて `git diff --check` を実行し、push 対象の markdown に含まれるソースリンクを検証します（オフライン時はスキップ、`SKIP_LINK_CHECK=1` で強制スキップ）。すべての外部 URL を検査するには `python3 scripts/audit-skill-pack.py --check-links` を実行してください。`.github/workflows/link-check.yml` がこれを毎週実行し、切れた引用が見つかると `link-rot` issue を作成します。リンク差し替えの手順は [docs/skill-evidence-coverage.md](./docs/skill-evidence-coverage.md) にあり、`.github/workflows/checks.yml` が push と pull request のたびにパックチェックを実行します。

## FAQ

### これは汎用のフロントエンドチェックリストですか？

いいえ。これらのスキルは、汎用の UI レビューが見落としがちなフロントエンドのエッジに焦点を当てています: WebView ホストの挙動、ネイティブ HTML 構造、IME/CJK 入力、アクセシビリティのコントラクト、ハイドレーション、フォーム、日時、認証、決済ページのクライアントエビデンス、エクスポート、オーバーレイ、デザイン忠実度。

### `payment-page-client-security` は PCI のスコープを決めますか？

いいえ。フロントエンドのエビデンスを収集するだけです: 決済ページのスクリプトインベントリ、PAN/CVV の境界、CSP/SRI/ヘッダーの制御、PCI DSS 6.4.3/11.6.1 の論点。スコープとコンプライアンスを決めるのは QSA、アクワイアラー、決済オーナー、セキュリティオーナーです。

### プロジェクトローカルのルールの置き換えになりますか？

いいえ。プロジェクトローカルの規約はそのまま維持してください: ルーティング、コンポーネント、デザイントークン、認証モデル、テストランナー、ブラウザ/デバイスマトリクス、リリースゲート。これらのスキルは、問題別のプレイブックとして使ってください。

### なぜ 1 つの巨大なスキルにしないのですか？

小さなスキルはコンテキストの焦点を保ちます。雑多なレポートのために `frontend-report-triage` がありますが、これはすべてのスキルを読み込むのではなく、有用な最小のセットにルーティングするためのものです。

## ライセンス

Apache-2.0 © [voidmatcha](https://github.com/voidmatcha)。[LICENSE](./LICENSE) を参照してください。
