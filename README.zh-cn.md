<div align="center">
<img src="docs/assets/hero.png" alt="frontend-niche-skills — frontend edge-case agent skills for WebView, IME, semantic markup, hydration, forms, dates, auth, payment pages, a11y, and design drift." width="100%" />
</div>

<h1 align="center">Frontend Niche Skills</h1>

<p align="center">
<a href="https://github.com/voidmatcha/frontend-niche-skills/actions/workflows/checks.yml"><img alt="Checks" src="https://github.com/voidmatcha/frontend-niche-skills/actions/workflows/checks.yml/badge.svg" /></a>
<a href="#skills"><img alt="Agent Skills" src="https://img.shields.io/badge/Agent_Skills-41-1FC07C?style=flat-square&amp;labelColor=black" /></a>
<a href="https://claude.com/product/claude-code"><img alt="Claude Code" src="https://img.shields.io/badge/Claude_Code-compatible-D97757?style=flat-square&amp;labelColor=black&amp;logo=anthropic&amp;logoColor=white" /></a>
<a href="https://github.com/openai/codex"><img alt="Codex" src="https://img.shields.io/badge/Codex-compatible-412991?style=flat-square&amp;labelColor=black&amp;logo=openai&amp;logoColor=white" /></a>
<a href="#skills"><img alt="Frontend edge cases" src="https://img.shields.io/badge/WebView_%7C_IME_%7C_a11y_%7C_payment-included-37B0E6?style=flat-square&amp;labelColor=black" /></a>
<a href="./LICENSE"><img alt="License" src="https://img.shields.io/badge/License-Apache--2.0-37B0E6?style=flat-square&amp;labelColor=black" /></a>
</p>

<p align="center">
<a href="README.md">🇺🇸 English</a> | <a href="README.ko.md">🇰🇷 한국어</a> | <a href="README.ja.md">🇯🇵 日本語</a> | <strong>🇨🇳 简体中文</strong>
</p>

<p align="center">
<a href="#skills">41 个技能</a> ·
<a href="./evals/routing/results/2026-07-31-targeted-metadata-comparison/">盲测路由对比，138 例中的 16 例</a> ·
<a href="./evals/behavioral/">两次自测行为实验，均为平局</a> ·
<a href="./docs/oss-validation-cases.md">锚定 commit 的开源案例集</a> ·
<a href="#development-checks">173 条评估用例规格</a> ·
<a href="./.github/workflows/link-check.yml">CI 校验的引用</a>
</p>

**面向宽泛检查清单常常漏掉的前端边缘情况的 Agent Skills——WebView 页面、语义化标记、浮层生命周期、IME/CJK 输入、水合、表单、鉴权、支付页面、导出、日期、视觉还原度以及报告分诊。**

`frontend-niche-skills` 为 Claude Code、Codex 以及其他兼容 `AGENTS.md` 的编码智能体提供聚焦的行动手册，专门针对那些正确修复取决于区分证据类型的缺陷：布局与绘制、DOM 与可访问性树、浏览器与原生 WebView 宿主、服务端渲染与客户端水合、支付页面数据边界与运行时脚本暴露面、导出文件与电子表格/Blob/剪贴板行为。

这些技能不能替代项目约定、安全审查、QSA/法务决策或真实的浏览器/设备测试。它们帮助智能体在套用看似合理却过于通用的修复之前，先索要正确的证据。

## 目录

[为什么先路由再修复](#为什么先路由再修复) · [快速示例](#快速示例) · [免安装试用一个技能](#免安装试用一个技能) · [适用范围](#适用范围) · [症状对照表](#症状对照表) · [技能](#技能) · [安装](#安装) · [工作流](#工作流) · [证据](#证据) · [开发检查](#开发检查) · [参与贡献](#参与贡献) · [常见问题](#常见问题) · [许可证](#许可证)

## 为什么先路由再修复

同一份报告，两种回答方式：

```diff
  "The CTA is still clickable after app resume, but its label disappeared."

- Add a re-render on AppState change and a 300ms delay before painting.
+ The box still receives taps, so hit-test passes and paint does not.
+ That rules out bridge routing and re-render timing, and points at
+ compositing: isolation boundary, child z-index, layer promotion.
```

这个循环你多半见过。报告说按钮点了没反应。智能体加了一个 `await`，还是不行；加了重试，还是不行；再加 300ms 延时，那次刷新恰好正常，补丁就这样合入了。从头到尾没有人确认过：按钮究竟是根本点不到、点得到但没绘制出来，还是点到了却静默失败。这三种情况除了被同一句话描述之外毫无共同点，而其中只有一种真的是时序问题。

代价最高的失败正是这一种。问题不在于补丁写得差，而在于它看起来合理、却瞄准了一个被误读的症状；它能通过评审，只因为没有人核对过究竟是哪条边界断了。

智能体修复方向的研究也指向同一点：定位缺陷会吃掉智能体相当大的一部分预算，而定位环节交给修复环节的只是一个位置，没有诊断上下文的修复只能靠猜（[arXiv:2606.24820](https://arxiv.org/abs/2606.24820)、[arXiv:2502.00350](https://arxiv.org/abs/2502.00350)）。这两项研究面向的是 Python 仓库而不是浏览器，可以从中借鉴的是机制，而不是数字。

所以这里的一个技能不是一份检查清单。它是一条边界，外加把它与相邻边界区分开的证据：命中测试通过而绘制没有通过意味着什么，从未发出 `READY` 的桥接与消息被丢弃的桥接有何区别，其中哪些能靠一张截图定论、哪些不能。这正是智能体无法从缺陷报告里推断出来的部分，也正是决定下一个补丁有没有瞄准真实问题的部分。

## 快速示例

上述对比背后的完整对话。它是为展示输出形态而写的，并非从真实会话中记录； 已记录的实验见 [`evals/behavioral/`](./evals/behavioral/)：

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

该模式的价值：让智能体在套用又一个通用补丁之前，先验证正确的假设。

## 免安装试用一个技能

把下面这段粘贴给任何能抓取 URL 的智能体。它不花钱，大约一分钟就能跑完。

```text
Read https://raw.githubusercontent.com/voidmatcha/frontend-niche-skills/main/skills/cjk-text-and-input/SKILL.md
and then diagnose this report: our Korean search box runs the search twice when
the user presses Enter, only for some users, and a 300ms debounce reduced it but
did not stop it.
```

这份报告和上面链接的行为评估用的是同一份，所以你可以把自己智能体的回答与[两个已记录的条件](./evals/behavioral/2026-08-01-ime-enter-double-submit/)做对比。

## 适用范围

在以下情况使用 `frontend-niche-skills`：

- 报告只说出了症状，比如某块区域空白、界面停留在旧状态、或者静默失败，却没有说明是哪条边界断了。
- 智能体反复给出看似合理的通用补丁，重试、延时、多加一次重渲染，但都撑不住。
- 问题只在某一个宿主里复现：应用内 WebView、第三方 iframe、某一个浏览器引擎、某一种 locale。
- 你希望智能体在改代码之前，先说明什么证据能证实或排除某个成因。

不要把它当作：

- 在缺陷真正出现的宿主里运行应用的替代品；
- 通用的前端 lint 预设或代码风格规则集；
- 合规结论，支付页面的发现只是证据，范围由 QSA、收单机构或支付负责人决定；
- 项目本地约定的替代品：路由、设计令牌、鉴权模型、测试运行器、浏览器与设备矩阵。

## 症状对照表

浏览完分组技能列表后再使用本表。从失败信号出发，优先选取最具体的运行时证据，再按需移交给相邻技能。

| 失败信号 | 起始技能 | 首先要问的问题 |
| --- | --- | --- |
| 页面运行在 React Native WebView、WKWebView、Android WebView、Flutter WebView 或应用内浏览器中；安全区域、键盘、恢复（resume）、桥接或绘制与桌面 Chrome 表现不同。 | `webview-bridge-pages` | 这是布局、命中测试、绘制/合成、桥接时序，还是宿主生命周期问题？ |
| 浏览器 iframe/widget 为空、接受伪造消息、丢失 READY/init、调整尺寸时闪烁、缺少所需能力，或丢失嵌入式登录状态。 | `iframe-embed-contracts` | 准确的父页/客体 origin、实际下发的 frame 策略、已认证消息握手、尺寸协议和存储模式分别是什么？ |
| 浏览器返回/前进恢复出了陈旧或私密的界面，或者返回后计时器/套接字/observer 已失效或被重复创建。 | `browser-page-lifecycle-bfcache-contracts` | 这是不是一次 persisted 恢复？哪些状态/资源需要幂等地重新校准？真实的历史遍历又显示了什么？ |
| SPA 返回/前进或同一文档内 hash 导航后落在错误滚动位置、内容渲染后滚动两次，或无法显示 fragment 目标。 | `history-scroll-restoration-contracts` | 哪个 same-document history entry 拥有位置、由谁执行恢复、目标布局何时稳定？ |
| 摄像头或麦克风首次可用，但在权限变化、设备切换、track 中断或关闭并重新打开采集界面后失败。 | `media-capture-device-contracts` | 权限、所选设备、track 状态、清理和重新获取之间如何转换？ |
| HTML 结构本身可疑：div 按钮、用错的链接、标签/标题/列表问题、非法的交互元素嵌套。 | `semantic-markup-contracts` | 在动用 ARIA、CSS 或 JavaScript 之前，原生 HTML 能否表达这个语义？ |
| 模态框、抽屉、Sheet、Popover、菜单或命令面板看起来正常，但焦点、背景交互、Escape/遮罩或滚动锁定失效。 | `overlay-focus-scroll-contracts` | 在打开、嵌套打开、关闭、卸载和路由切换时分别发生了什么？ |
| 单个 pointer 的拖拽、滑动、调整尺寸或绘制卡住、在元素边界丢失输入，或与原生滚动冲突。 | `pointer-gesture-contracts` | 序列是否保持一个 active `pointerId`、预期的事件传递/capture 路径、终止清理和 `touch-action`？双指缩放、旋转和多点接触几何应交给其他工作流。 |

<details>
<summary>其余 33 个信号</summary>

| 失败信号 | 起始技能 | 首先要问的问题 |
| --- | --- | --- |
| 对话框、菜单、组合框、标签页或自定义控件需要可访问性回归覆盖。 | `a11y-contract-testing` | 测试能否断言角色、名称、状态和焦点契约？ |
| contenteditable 或富文本编辑器丢失/反转选区、一次意图被应用两次、撤销失效、粘贴/拖放插入到错误光标位置，或重新挂载后恢复了陈旧 Range。 | `contenteditable-selection-contracts` | 哪个 live editing host 拥有选区？这次 `beforeinput`/`input` 事务及其历史由浏览器还是应用拥有？ |
| 韩文、日文或中文文本/输入行为异常：IME 的 Enter、组合输入、字素长度、换行、截断。 | `cjk-text-and-input` | 代码是否混淆了组合中文本、已提交文本和显示文本？ |
| 翻译后的文案破坏了布局、复数规则、双向文本/RTL、数字/日期格式化或翻译键契约。 | `i18n-copy-and-layout` | 这个缺陷属于文案、布局、locale 行为，还是输入组合问题？ |
| 深链接、鉴权重定向、SPA/SSR 路由或查询参数初始化到了错误的界面。 | `deeplink-hydration` | 在路由器就绪、水合和鉴权跳转之前，URL 状态是什么？ |
| WebSocket 或 SSE 客户端在连接中断后出问题：重连风暴、事件重复/丢失、乱序增量、套接字状态为 OPEN 实际已死导致 UI 冻结、缓冲区增长，或握手后 token 过期。 | `realtime-transport-contracts` | 这是重连/退避、续传/游标、增量折叠、存活/心跳、背压，还是套接字重新鉴权问题？ |
| 面向浏览器的鉴权 UI 存在 returnTo、OAuth/passkey、autocomplete、OTP 过期/重试、安全错误提示或敏感操作前重新验证的问题。 | `frontend-auth-flow-contracts` | 鉴权流程应当保持哪个浏览器契约？ |
| 弹窗、剪贴板、分享、文件选择器、全屏或支付 API 在直接点击时可用，却在异步工作或另一个受限调用之后失败。 | `user-activation-contracts` | 哪个 API 受用户激活限制？瞬时激活在哪里过期或被消耗？ |
| 在支付页面之外出现原始 HTML、sanitizer、CSP、opener、存储、URL 解析或第三方脚本风险。 | `frontend-security-baseline` | 是否存在具体的浏览器安全 source-to-sink 路径？ |
| 前端拥有的服务器路由把客户端选择的 path、upload、header 或 business action 代理到 upstream API。 | `bff-proxy-security-contracts` | 暴露了哪个 route-method-auth capability，其他 ingress 能否绕过它？ |
| 结账/支付页面需要客户端证据：托管字段、直接处理 PAN/CVV、运行时脚本、CSP/SRI/响应头控制。 | `payment-page-client-security` | 什么证据能展示支付数据边界和运行时脚本暴露面？ |
| 涉及 CSV/Excel 导出、文件下载、Blob URL、剪贴板写入、生成的文件名或导出模式（schema）。 | `download-export-safety` | 什么数据离开了浏览器？电子表格单元格、Object URL、剪贴板失败和文件名是如何处理的？ |
| 日期偏移、时区/夏令时问题、仅日期输入、`datetime-local` 往返转换、相对时间，或服务端/客户端时钟不一致。 | `datetime-correctness` | 这个值是时间瞬间（instant）、本地日期时间、仅日期值，还是格式化后的显示字符串？ |
| 金额/数量合计差了一个零头或一分钱、舍入看起来不对，或本地化金额解析错误。 | `money-and-precision-contracts` | 这个值是否用二进制浮点数计算？运算使用了哪种舍入模式和最小货币单位表示？ |
| 涉及原生 Constraint Validation API：`setCustomValidity`、`reportValidity`、`:user-invalid`、从无效到有效的生命周期。 | `constraint-validation-contracts` | 原生有效性状态是否在正确的时机清除并报告？ |
| React Hook Form、Formik、Final Form、vee-validate、Valibot 或自定义 JS 校验出现陈旧错误、提交按钮被禁用或异步/服务端竞态。 | `js-form-validation-contracts` | 错误、有效性、提交和服务端字段映射分别归哪个库状态所有？ |
| 水合警告或服务端/客户端不匹配，涉及 locale、时间、随机性、仅浏览器 API、存储、鉴权状态或响应式分支。 | `ssr-hydration-mismatch` | 首次客户端渲染时哪些内容必须是确定性的？ |
| 实现需要与 Figma、截图、设计参考或视觉规范保持一致。 | `design-to-code-fidelity` | 能否在主观审查之前先导出参考图、截取渲染结果并做视觉对比？ |
| 重复的 UI 可能要抽成组件、包装器、Hook、令牌，或者应该保持独立。 | `component-extraction-judgment` | 这处重复是否足够稳定，可以在不掩盖产品差异的前提下提取？ |
| 在服务器确认前应用的乐观 UI 更新行为异常：闪烁、重复应用、失败的变更从不回滚，或响应与重新获取竞态后留下陈旧数据。 | `optimistic-update-rollback-contracts` | 应用 -> 确认/回滚 -> 协调的契约是什么？临时/服务端 ID 和并发变更如何排序？ |
| 带入页面的文件行为异常：拖放区高亮闪烁、拖入文件导致页面跳转、拖入文件夹得不到任何内容、类型错误的文件通过了校验、粘贴图片失效，或预览 URL 泄漏。 | `file-ingest-contracts` | 是哪个环节出了问题：拖拽事件取消、`DataTransfer` 的 items 与 files、类型信任、粘贴，还是 Object URL 生命周期？ |
| 前端错误没有出现在监控面板上、不可读（被压缩 / `Script error.`），或应用在有错误边界的情况下仍然白屏。 | `client-error-observability-contracts` | 是否为异步错误/Promise 拒绝接好了捕获？跨域/source map 设置是否正确？发送前脱敏了哪些内容？ |
| View Transitions 动画行为异常：随机不触发（静默中止）、冻结在陈旧/旧帧上、忽略 reduced-motion，或留下鬼影变形。 | `view-transitions-contracts` | 是重复的 `view-transition-name`、未绘制的快照（Suspense/解码）、缺失的 reduced-motion 分支，还是错误的 Transition 包裹方式？ |
| 对话框/Popover 的进入或退出动画被截断，或因为某个过渡从未“结束”，导致清理/焦点/卸载卡住。 | `css-transition-animation-contracts` | 是过渡里缺了 `display`/`overlay`（配合 `allow-discrete`），还是代码依赖了一个永远不会触发的 `transitionend`？ |
| 发布了错误的图片文件、图片下载过大、首屏主图被懒加载，或图片导致布局偏移。 | `responsive-image-contracts` | `srcset` 是否配有与真实布局匹配的 `sizes`、正确的宽度描述符、LCP 的 `eager`/`fetchpriority` 以及 `width`/`height`？ |
| 页面的 LCP/CLS/INP 不达标，你需要做归因，而不只是报告分数。 | `core-web-vitals-performance-contracts` | LCP 元素是哪个（可发现/已提权？）、每次布局偏移的来源是什么、哪些长任务推高了 INP？ |
| 客户端缓存的数据在变更后仍然陈旧，或请求出现瀑布/过度获取（React Query/SWR/RTK Query/Apollo）。 | `frontend-data-fetching-cache-contracts` | 哪个查询键应当失效？读取是否并行化，stale/gc 时序是否正确？ |
| 浏览器本地记录消失、IndexedDB 升级被另一个标签页卡住、UI 显示已保存之后请求却中止，或把 persistence 描述成永久备份。 | `browser-storage-durability-contracts` | 失败发生在哪一阶段：open/upgrade 所有权、事务活性、commit/abort、quota/persistence、意外 close，还是恢复？ |
| 异步 effect 展示了错误的数据、触发两次、泄漏，或读到陈旧值。 | `async-effect-race-contracts` | 是否有 take-latest/`AbortController` 加清理逻辑？该 effect 在 StrictMode 下是否幂等？ |
| 部署后用户拿到的仍是旧构建、出现 `ChunkLoadError`，或 Service Worker 在离线时返回错误/陈旧的字节。 | `pwa-offline-cache-contracts` | 是否有 SW 更新流程、完整的预缓存、缓存版本化，以及对带鉴权 HTML/API 的不缓存规则？ |
| 虚拟化列表/网格跳动或丢失滚动位置，或 Ctrl+F/屏幕阅读器总数/焦点在虚拟化下损坏。 | `large-list-data-grid-contracts` | `estimateSize`/overscan 是否正确？是否为已卸载的行设置了 `aria-setsize`/`aria-posinset`（或 `aria-rowcount`）？ |
| `ResizeObserver` 报告未送达的通知、画面抖动、尺寸无限增长、测量了错误的 box，或在重新挂载后仍观察陈旧元素。 | `resize-observer-layout-contracts` | 哪次回调中的写入又反馈回了被观察的尺寸？setup/cleanup 是否持有当前的目标元素？ |
| 报告含糊不清、跨越多个领域，或你不确定该由哪个专门技能负责。 | `frontend-report-triage` | 最可能的 1-3 个失败类别是什么？什么证据能把它们区分开？ |

</details>

<a id="skills"></a>

## 技能

41 个技能，按其针对的前端失败类型分组。如果报告混乱或跨越多个领域，从 `frontend-report-triage` 开始。

实用优先级：

- **默认高价值检查：** SSR/深链接路由、表单校验、日期时间、鉴权/安全、支付/导出边界、浮层、可访问性以及语义化 HTML。这些检查捕捉的缺陷要么常见，要么发布后代价高昂。
- **宿主/产品特定检查：** WebView、浏览器 iframe/embed、CJK/IME、i18n/RTL 以及支付页面证据，在产品确实交付这些界面时最有价值。
- **质量/维护检查：** 设计还原度和组件提取判断适用于审查痛点是视觉漂移、AI 生成的 UI 或过早抽象，而非运行时缺陷的情况。

来源模型：README 列出路由与证据文档；详细引用位于每个技能的 `## Sources` 块或其 `references/*.md` 文件中，因此 README 不会重复每个上游 URL。

### 从这里开始

| 技能 | 适用场景 |
| --- | --- |
| [`frontend-report-triage`](./skills/frontend-report-triage/SKILL.md) | 在整个技能包范围内分诊模糊或多症状的前端缺陷报告；返回可能的失败类别、证据缺口以及 1-3 个最合适的后续技能。 |

### 运行时宿主的边缘情况

| 技能 | 适用场景 |
| --- | --- |
| [`webview-bridge-pages`](./skills/webview-bridge-pages/SKILL.md) | 构建或调试加载在原生 WebView 内的页面：桥接契约、安全区域/视口布局、生命周期、命中测试与绘制/合成的区别、应用宿主的各种怪癖。 |
| [`iframe-embed-contracts`](./skills/iframe-embed-contracts/SKILL.md) | 构建或调试浏览器 iframe/widget：父页-客体消息、可嵌入响应头、sandbox/Permissions Policy、READY/init 握手、动态尺寸、分区存储与销毁。 |
| [`browser-page-lifecycle-bfcache-contracts`](./skills/browser-page-lifecycle-bfcache-contracts/SKILL.md) | 调试顶层浏览器的返回/前进恢复：陈旧的鉴权/数据/界面、重复或被暂停的资源、`pageshow.persisted`、bfcache 资格，以及幂等恢复。 |
| [`history-scroll-restoration-contracts`](./skills/history-scroll-restoration-contracts/SKILL.md) | SPA 返回/前进或同一文档内 hash 导航后恢复到错误位置、异步渲染后滚动两次，或找不到 fragment 目标时：history entry 标识、恢复责任和渲染就绪。 |
| [`media-capture-device-contracts`](./skills/media-capture-device-contracts/SKILL.md) | 权限拒绝、设备切换、track 中断或结束后摄像头/麦克风采集失败时：`getUserMedia`、设备枚举/变化、track 状态、清理和重新获取。 |
| [`deeplink-hydration`](./skills/deeplink-hydration/SKILL.md) | 调试在路由器水合就绪之前丢失查询参数或落在错误状态的 SPA/SSR 深链接。 |
| [`ssr-hydration-mismatch`](./skills/ssr-hydration-mismatch/SKILL.md) | 诊断由 locale/时间/随机性/仅浏览器 API、存储、鉴权状态、响应式分支或数据竞态引起的水合不匹配。 |
| [`realtime-transport-contracts`](./skills/realtime-transport-contracts/SKILL.md) | 调试经历连接中断的 WebSocket/SSE 客户端：重连退避/抖动、SSE Last-Event-ID/游标续传、乱序/重复/有缺口的增量、心跳/僵尸连接检测、bufferedAmount 背压，以及在已打开的套接字上刷新鉴权。 |

### 标记、可访问性与浮层

| 技能 | 适用场景 |
| --- | --- |
| [`semantic-markup-contracts`](./skills/semantic-markup-contracts/SKILL.md) | 审查原生 HTML 结构：按钮与链接的取舍、标题、地标、标签、表格/列表、非法的交互元素嵌套、先原生后 ARIA 的修复。 |
| [`overlay-focus-scroll-contracts`](./skills/overlay-focus-scroll-contracts/SKILL.md) | 审查模态框、抽屉、Sheet、Popover、菜单和命令面板的运行时契约：焦点陷阱/恢复、inert/aria-hidden 时序、嵌套堆叠、滚动锁定清理。 |
| [`pointer-gesture-contracts`](./skills/pointer-gesture-contracts/SKILL.md) | 单个 pointer 的拖拽、滑动、调整尺寸或绘制卡住/取消、在元素外丢失输入或与页面滚动冲突时：active pointer 所有权、事件传递/capture、取消、`touch-action` 和清理。真正的双指缩放、旋转和多点接触几何不在范围内。 |
| [`a11y-contract-testing`](./skills/a11y-contract-testing/SKILL.md) | 把可访问性语义转化为回归测试：角色、名称、状态、焦点、对话框、菜单、组合框、标签页。 |
| [`view-transitions-contracts`](./skills/view-transitions-contracts/SKILL.md) | 审查静默中止、冻结在陈旧快照上、忽略 reduced-motion 或产生鬼影的 View Transitions API 动画——这是审查/判断是否值得提 PR 的视角，而非重新实现指南。 |
| [`css-transition-animation-contracts`](./skills/css-transition-animation-contracts/SKILL.md) | 审查对话框/Popover/顶层（top-layer）的进入/退出过渡（`@starting-style`、`allow-discrete`、`overlay`），以及依赖过渡结束才执行的清理逻辑（`transitionend` 与 `getAnimations().finished` 的取舍）。 |
| [`responsive-image-contracts`](./skills/responsive-image-contracts/SKILL.md) | 审查响应式图片标记：`srcset`/`sizes` 与真实布局的匹配、固有宽度标注、LCP 的 eager/`fetchpriority`、`picture` 艺术指导，以及用于 CLS 的 `width`/`height`。 |

### 输入、内容与时间

| 技能 | 适用场景 |
| --- | --- |
| [`contenteditable-selection-contracts`](./skills/contenteditable-selection-contracts/SKILL.md) | contenteditable 或富文本编辑宿主丢失/跳动光标或选区、重复编辑、破坏撤销/重做、把粘贴/拖放内容插入错误位置、在重新渲染时破坏输入组合，或在销毁后恢复陈旧焦点/选区时。 |
| [`cjk-text-and-input`](./skills/cjk-text-and-input/SKILL.md) | 处理韩文、日文或中文文本/输入：换行、IME 组合、Enter 键处理、字素安全的长度计算、校验时机。 |
| [`i18n-copy-and-layout`](./skills/i18n-copy-and-layout/SKILL.md) | 审查本地化文案/布局：复数规则、文本膨胀、双向文本/RTL、locale 格式化、翻译键契约。 |
| [`datetime-correctness`](./skills/datetime-correctness/SKILL.md) | 审计日期/时间代码：时区、夏令时（DST）、解析、格式化、`datetime-local`、相对时间、服务端/客户端时钟问题。 |
| [`money-and-precision-contracts`](./skills/money-and-precision-contracts/SKILL.md) | 金额/数量运算：浮点漂移（`0.1 + 0.2`）、整数最小货币单位与十进制库的取舍、`toFixed`/舍入模式的意外行为、求和/税额计算顺序、`Intl` 货币输出与解析本地化金额的区别。 |

### 表单、鉴权、安全与支付

| 技能 | 适用场景 |
| --- | --- |
| [`constraint-validation-contracts`](./skills/constraint-validation-contracts/SKILL.md) | 原生 HTML Constraint Validation API 契约：`setCustomValidity`、`reportValidity`、`:user-invalid`、从无效到有效的生命周期。 |
| [`js-form-validation-contracts`](./skills/js-form-validation-contracts/SKILL.md) | React Hook Form、Formik、Final Form、vee-validate、Valibot 或自定义 JS 表单流程：陈旧的错误信息、被禁用的提交按钮、异步/服务端竞态、服务端字段错误映射。 |
| [`frontend-auth-flow-contracts`](./skills/frontend-auth-flow-contracts/SKILL.md) | 加固面向浏览器的鉴权流程：returnTo 重定向、OAuth/passkey/autocomplete 契约、OTP 过期/重试、安全的错误提示，以及敏感操作前的重新验证。 |
| [`user-activation-contracts`](./skills/user-activation-contracts/SKILL.md) | 调试弹窗、剪贴板、分享、文件选择器、全屏和支付调用：它们在异步工作或另一个消耗激活的 API 之后丢失了瞬时用户激活。 |
| [`frontend-security-baseline`](./skills/frontend-security-baseline/SKILL.md) | 检查前端 XSS、DOM 注入、sanitizer 误用、CSP、第三方脚本、存储以及 URL 解析基础。 |
| [`bff-proxy-security-contracts`](./skills/bff-proxy-security-contracts/SKILL.md) | 审查前端拥有的 BFF/API 代理：客户端选择目标造成的 SSRF、route/method/auth capability allowlist、替代 ingress 漂移、multipart 限额与 boundary、redirect/error 处理，以及 upstream business-flow 责任。 |
| [`payment-page-client-security`](./skills/payment-page-client-security/SKILL.md) | 审查结账/支付页面的客户端证据：托管字段与直接处理 PAN 的区别、运行时脚本清单、第三方脚本风险、CSP/SRI/响应头证据、PCI DSS 证据缺口。 |
| [`optimistic-update-rollback-contracts`](./skills/optimistic-update-rollback-contracts/SKILL.md) | 乐观 UI 变更：在服务器确认前先应用改动、临时 ID 与服务端 ID、失败时回滚、通过重新获取/失效进行协调，以及响应与后台重新获取之间的竞态。 |
| [`file-ingest-contracts`](./skills/file-ingest-contracts/SKILL.md) | 通过拖放、文件输入框或粘贴把文件带入页面：drop 事件取消/`dropEffect`、dragenter/leave 闪烁、`DataTransfer` 的 items 与 files 之别、目录上传、对 `accept`/`file.type` 的信任问题，以及 Object URL 预览的生命周期。 |

### 输出、设计、抽象与维护

| 技能 | 适用场景 |
| --- | --- |
| [`download-export-safety`](./skills/download-export-safety/SKILL.md) | 审查 CSV/Excel 导出、Blob/Object URL 下载、剪贴板写入、生成的文件名、导出特有的数据边界。 |
| [`design-to-code-fidelity`](./skills/design-to-code-fidelity/SKILL.md) | 通过导出、截图、视觉对比和证据分级，将实现与设计参考进行比对。 |
| [`component-extraction-judgment`](./skills/component-extraction-judgment/SKILL.md) | 判断重复出现的 UI 应该抽成共享组件、包装器、Hook、令牌，还是保持独立。 |
| [`client-error-observability-contracts`](./skills/client-error-observability-contracts/SKILL.md) | 接入前端错误捕获：`window.onerror`/`unhandledrejection`、错误边界的局限、`Script error.` 跨域信息屏蔽、随包发布与仅上传 source map 的取舍、错误分组，以及 PII 脱敏。 |

### 性能、数据与离线

| 技能 | 适用场景 |
| --- | --- |
| [`core-web-vitals-performance-contracts`](./skills/core-web-vitals-performance-contracts/SKILL.md) | 在修复之前，把不达标的 Core Web Vitals 指标（LCP、CLS、INP、TTFB）归因到具体元素、布局偏移或主线程任务——做整页预算，而不只是看分数。 |
| [`frontend-data-fetching-cache-contracts`](./skills/frontend-data-fetching-cache-contracts/SKILL.md) | 客户端数据缓存（React Query、SWR、RTK Query、Apollo）在变更后展示陈旧数据、请求瀑布、过度/不足获取，或分页/重新验证的缓存缺陷。 |
| [`browser-storage-durability-contracts`](./skills/browser-storage-durability-contracts/SKILL.md) | 浏览器本地数据被标记为已保存后却消失、IndexedDB 模式升级受阻、事务失活或中止、quota/persistence 证据被误读，或恢复文案夸大持久性时。 |
| [`async-effect-race-contracts`](./skills/async-effect-race-contracts/SKILL.md) | 原始异步 effect 行为异常：依赖变化触发请求的竞态（陈旧响应胜出）、缺失清理/`AbortController`、StrictMode 双重调用，或定时器/订阅中的陈旧闭包。 |
| [`pwa-offline-cache-contracts`](./skills/pwa-offline-cache-contracts/SKILL.md) | Service Worker/离线缓存出错：部署后仍是旧构建、`ChunkLoadError`、预缓存缺口、缓存版本化/淘汰、SW 更新生命周期，或缓存了带鉴权的响应。 |
| [`large-list-data-grid-contracts`](./skills/large-list-data-grid-contracts/SKILL.md) | 虚拟化列表/网格跳动或丢失滚动位置，或因屏幕外行被卸载导致页内查找/屏幕阅读器总数/焦点损坏；固定列/表头漂移。 |
| [`resize-observer-layout-contracts`](./skills/resize-observer-layout-contracts/SKILL.md) | `ResizeObserver` 的尺寸反馈循环、未送达通知错误、测错 box、画面抖动，以及重新挂载后仍在观察的陈旧目标。 |

## 安装

安装 [`skills` CLI](https://www.skills.sh/)。这些技能遵循 [`SKILL.md` 格式](https://agentskills.io/specification)。

这些技能面向遵循规范中 `description` 1024 字符上限的 Claude Code、Codex 等代理，并把这些字符用于触发词，以便正确的技能被激活。Claude.ai 的上传路径将 `description` 限制为 200 字符，因此直接上传会失败（[Claude 文档](https://claude.com/docs/skills/how-to)）。

下面的 `voidmatcha/frontend-niche-skills` 命令假设公开仓库或插件市场条目已经可用。若使用本地或预发布检出，请改用本节中的本地检出命令。

```bash
# Claude Code + Codex via skills CLI
npx skills add voidmatcha/frontend-niche-skills --skill '*' -g -a claude-code -a codex

# Other agents supported by the installed skills CLI
npx skills add voidmatcha/frontend-niche-skills --skill '*' -g --agent '*'
```

### Claude Code 插件

```bash
/plugin marketplace add voidmatcha/frontend-niche-skills
/plugin install frontend-niche-skills@voidmatcha
```

### Codex 插件本地检出

本仓库包含 `.codex-plugin/plugin.json` 和 Claude 插件清单。在本地检出中：

```bash
codex plugin marketplace add "$(pwd)"
codex plugin add frontend-niche-skills@frontend-niche-skills
```

安装或更新后请开启新的 Codex 或 Claude Code 会话，以便刷新捆绑的技能。

## 工作流

1. **选定症状对应的技能。** 使用失败模式与该缺陷匹配的最窄技能。
2. **阅读仓库上下文。** 将技能与项目路由、设计令牌、i18n、测试以及浏览器/设备支持范围结合使用。
3. **区分证据类型。** 布局、绘制、命中测试、DOM 结构、可访问性树、网络、水合、locale 行为、运行时脚本和导出文件之间可能互相矛盾。
4. **修复原因，而不是症状。** 优先移除脆弱的时序或重复的逻辑，而不是添加重试。
5. **在正确的宿主中验证。** WebView 缺陷需要应用内 WebView 的证据；支付页面发现需要运行时脚本/PAN 边界的证据；视觉还原需要参考图/渲染截图对比；表单/可访问性发现应尽可能配上回归测试。

## 证据

- [`evals/behavioral/`](./evals/behavioral/) — 本技能包实测自身核心主张的两次记录： 同一个缺陷，分别在提供和不提供相关技能的情况下让智能体去诊断。评分标准都在运行前 提交。两个案例均为平局，因此在这两份报告上，技能没有产生任何预先登记的标准能够 观测到的差异。第二份记录写明了一处标准之外、技能一方更正确的差异，以及事后才发现 它为什么不算证据。
- [`.github/workflows/checks.yml`](./.github/workflows/checks.yml)——41 个技能中有 4 个的浏览器夹具在每次推送时重跑：3 套在 Chromium、Firefox、WebKit 上运行，1 套仅在 Chromium 上。它们验证相关技能所描述的浏览器行为是否属实，但不测量本技能包是否改变智能体的输出。由于同一套件同时把关推送，失败的运行会阻断推送，而不会留下可见的负面记录。

本仓库避免把一次 grep 命中当作缺陷。每一项主张都对应 [`docs/skill-evidence-coverage.md`](./docs/skill-evidence-coverage.md) 中证据阶梯的一个层级：**E1 已测量**、**E2 源码核实**、**E3 引用一手来源**、**E4 路由示例**。层级记录的是实际做了什么，而不是有多确信。截至 2026-08-01，OSS 案例集中没有任何一条被上报给上游、在本地复现，或被维护者接受。

证据所在位置：

- [`docs/oss-validation-cases.md`](./docs/oss-validation-cases.md)——用于校验技能边界和 PR 形态的公开开源案例。
- [`skills/webview-bridge-pages/references/why-webview-bridge-pages.md`](./skills/webview-bridge-pages/references/why-webview-bridge-pages.md)——WebView 相关的既有成果、桥接库、宿主行为参考和生态笔记。
- [`docs/public-skill-landscape.md`](./docs/public-skill-landscape.md)——实际打开并比较与本技能包直接重叠、近似或互补的公开技能包，并记录保留/拆分/暂缓结论。
- [`docs/skill-evidence-coverage.md`](./docs/skill-evidence-coverage.md)——证据阶梯本身，以及按技能划分、显示每个技能的支撑位于哪一层级的映射表。
- [`docs/skill-quality-standard.md`](./docs/skill-quality-standard.md)——本技能包采用的可移植格式、路由、工作流、证据、输出、评估以及新技能准入标准。
- `skills/*/SKILL.md` 和 `skills/*/references/*.md`——每个技能的官方文档、既有成果、示例、误报说明和特定实现的证据。

候选的开源发现在重新核对当前分支、本地复现，并被维护者接受或有失败测试支撑之前，**不算**已确认的上游缺陷。

<a id="development-checks"></a>

## 开发检查

仓库本地检查可以直接运行，也可以通过 lefthook 运行：

```bash
./scripts/pre-push-checks.sh

# Optional: install Git hooks after installing lefthook locally.
lefthook install
lefthook run pre-push
```

通过时的输出如下：

```console
$ python3 scripts/audit-skill-pack.py
Skill pack audit: PASS
Root: /path/to/frontend-niche-skills
Skills: 41
Local markdown refs checked: 335
Sources sections checked: 50
Skill contracts checked: 40
Eval files checked: 41
Eval cases checked: 173
Reference files checked: 36
README skill orders checked: 4
README symptom maps checked: 4
Scripts syntax checked: 16
```

`lefthook.yml` 只是委托给仓库脚本，因此贡献者不装 lefthook 也能运行同样的检查。该脚本审计技能元数据与质量章节、直接引用的参考资料是否可达、eval 文件结构、README 链接与数量、插件清单、本地 Markdown 链接、夸大措辞以及捆绑脚本的语法。它还会运行 `git diff --check`，并校验本次 push 涉及的 markdown 中的来源链接（离线时跳过，`SKIP_LINK_CHECK=1` 可强制跳过）。若要改为检查全部外部 URL，请运行 `python3 scripts/audit-skill-pack.py --check-links`；`.github/workflows/link-check.yml` 每周运行该检查，并在引用失效时创建 `link-rot` issue。链接替换流程见 [docs/skill-evidence-coverage.md](./docs/skill-evidence-coverage.md)，`.github/workflows/checks.yml` 会在每次 push 和 pull request 时运行打包检查。

## 参与贡献

新技能按 [docs/skill-quality-standard.md](./docs/skill-quality-standard.md) 中的六问门槛准入：这个失败是否会反复出现、是否在单个产品或组件之外依然成立、通用编码智能体是否会做错、是否已有相邻技能负责该路由、是否可测试，以及该技能能否拒绝薄弱的发现。工作流以及 push 前运行的检查见 [CONTRIBUTING.md](./CONTRIBUTING.md)。

## 常见问题

### 这和前端评审检查清单或 ESLint 配置有什么不同？

不同之处在于关注点。这些技能聚焦于通用 UI 审查常常漏掉的前端边缘：WebView 宿主行为、原生 HTML 结构、IME/CJK 输入、可访问性契约、水合、表单、日期时间、鉴权、支付页面客户端证据、导出、浮层和设计还原度。

### 智能体能决定支付页面的 PCI DSS 范围吗？

不能。它只收集前端证据：支付页面脚本清单、PAN/CVV 边界、CSP/SRI/响应头控制，以及 PCI DSS 6.4.3/11.6.1 的讨论要点。范围与合规由 QSA、收单机构、支付负责人或安全负责人决定。

### 这些技能会取代项目自己的约定和 lint 规则吗？

不会。请保留项目本地约定：路由、组件、设计令牌、鉴权模型、测试运行器、浏览器/设备矩阵和发布关卡。把这些技能当作针对具体问题的行动手册来用。

### 为什么是 41 个独立技能，而不是一个大而全的前端技能？

更小的技能能让上下文保持聚焦。`frontend-report-triage` 是为混乱的报告准备的，但它应当路由到最小的有用集合，而不是加载所有技能。

### 为什么页面在桌面 Chrome 上正常，在应用内 WebView 里却出问题？

因为不同的是宿主，而不是标记。安全区域与 viewport inset、桥接就绪时机、恢复时渲染进程被回收、合成行为，这些都是宿主契约，不是页面缺陷。`webview-bridge-pages` 覆盖这些内容，而证据必须来自应用内 WebView，不能来自桌面浏览器。

### 哪些编码智能体可以使用这些技能？

任何能读取 [`SKILL.md` 格式](https://agentskills.io/specification)的智能体。Claude Code 和 Codex 各自有专门的插件市场，[`skills` CLI](https://www.skills.sh/) 则可以把整个技能包装进它支持的其他智能体。参见[安装](#安装)。

## 许可证

Apache-2.0 © [voidmatcha](https://github.com/voidmatcha)。见 [LICENSE](./LICENSE)。
