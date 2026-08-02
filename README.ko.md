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
<a href="README.md">🇺🇸 English</a> | <strong>🇰🇷 한국어</strong> | <a href="README.ja.md">🇯🇵 日本語</a> | <a href="README.zh-cn.md">🇨🇳 简体中文</a>
</p>

<p align="center">
<a href="#skills">skill 41개</a> ·
<a href="./evals/routing/results/2026-07-31-targeted-metadata-comparison/">블라인드 라우팅 비교, 138건 중 16건</a> ·
<a href="./evals/behavioral/">자체 실행 행동 시험 두 건, 모두 동률</a> ·
<a href="./docs/oss-validation-cases.md">커밋을 고정한 OSS 사례집</a> ·
<a href="#개발-검사">eval 케이스 명세 173개</a> ·
<a href="./.github/workflows/link-check.yml">CI가 검사하는 인용</a>
</p>

**광범위한 체크리스트가 자주 놓치는 프론트엔드 엣지 케이스를 위한 Agent Skills. WebView 페이지, 시맨틱 마크업, 오버레이 생명주기, IME/CJK 입력, 하이드레이션, 폼, 인증, 결제 페이지, 내보내기, 날짜, 시각적 충실도, 리포트 트리아지까지.**

`frontend-niche-skills`는 Claude Code, Codex를 비롯한 `AGENTS.md` 호환 코딩 에이전트에게, 올바른 수정이 증거 유형의 구분에 달려 있는 버그를 위한 집중된 플레이북을 제공합니다: 레이아웃 vs 페인트, DOM vs 접근성 트리, 브라우저 vs 네이티브 WebView 호스트, 서버 렌더 vs 클라이언트 하이드레이션, 결제 페이지 데이터 경계 vs 런타임 스크립트 표면, 내보내기 파일 vs 스프레드시트/Blob/클립보드 동작.

이 skill들은 프로젝트 컨벤션, 보안 리뷰, QSA/법무 결정, 실제 브라우저/기기 테스트를 대체하지 않습니다. 그럴듯하지만 범용적인 수정을 적용하기 전에 에이전트가 올바른 증거를 먼저 요구하도록 돕습니다.

## 목차

[라우팅이 먼저인 이유](#라우팅이-먼저인-이유) · [빠른 예시](#빠른-예시) · [설치 없이 skill 하나 시험해 보기](#설치-없이-skill-하나-시험해-보기) · [적합한 경우](#적합한-경우) · [증상 맵](#증상-맵) · [Skills](#skills) · [설치](#설치) · [Workflow](#workflow) · [증거](#증거) · [개발 검사](#개발-검사) · [기여하기](#기여하기) · [FAQ](#faq) · [라이선스](#라이선스)

## 라우팅이 먼저인 이유

같은 리포트에 대한 두 가지 답변입니다.

```diff
  "The CTA is still clickable after app resume, but its label disappeared."

- Add a re-render on AppState change and a 300ms delay before painting.
+ The box still receives taps, so hit-test passes and paint does not.
+ That rules out bridge routing and re-render timing, and points at
+ compositing: isolation boundary, child z-index, layer promotion.
```

익숙한 흐름일 겁니다. 리포트에는 버튼이 아무 반응도 하지 않는다고 적혀 있습니다. 에이전트가 `await`를 추가합니다. 그대로입니다. 재시도를 넣습니다. 그대로입니다. 300ms 지연을 넣자 그 새로고침이 우연히 동작하고, 패치는 그대로 배포됩니다. 버튼이 애초에 클릭되지 않는 상태였는지, 클릭은 되지만 paint가 되지 않은 상태였는지, 클릭은 되었지만 조용히 실패한 것인지는 아무도 확인하지 않았습니다. 이 셋은 같은 문장으로 설명되었다는 것 말고는 공통점이 없고, 그중 타이밍 버그였던 것은 하나뿐입니다.

비용이 큰 실패는 바로 여기입니다. 나쁜 패치가 아니라, 잘못 읽은 증상을 겨냥한 그럴듯한 패치입니다. 실제로 어느 경계가 깨졌는지 아무도 확인하지 않았기 때문에 리뷰까지 통과합니다.

에이전트 수리 연구도 같은 방향을 가리킵니다. 결함 위치를 찾는 데 에이전트 예산의 상당 부분이 들어가고, 진단 맥락 없이 위치만 넘겨받은 수리 단계는 결국 추측에 기댑니다 ([arXiv:2606.24820](https://arxiv.org/abs/2606.24820), [arXiv:2502.00350](https://arxiv.org/abs/2502.00350)). 다만 이들은 브라우저가 아니라 파이썬 리포지터리를 다룬 연구이므로, 가져올 것은 메커니즘이지 수치가 아닙니다.

그래서 여기의 skill은 체크리스트가 아닙니다. 하나의 경계와, 그 경계를 바로 옆 경계와 갈라놓는 증거입니다. hit-test는 통과하는데 paint는 되지 않는다는 것이 무슨 뜻인지, `READY`를 한 번도 보내지 않은 bridge와 메시지가 유실된 bridge가 어떻게 다른지, 그중 무엇을 스크린샷으로 판별할 수 있고 무엇은 판별할 수 없는지를 다룹니다. 이것이 에이전트가 버그 리포트만으로는 알아낼 수 없는 부분이고, 다음 패치가 실재하는 무언가를 겨냥하는지를 결정하는 부분입니다.

## 빠른 예시

앞의 대비 뒤에 있는 전체 대화입니다. 출력의 형태를 보여주려고 작성한 것이지 실제 세션에서 기록한 것이 아닙니다. 기록된 실행은 [`evals/behavioral/`](./evals/behavioral/)에 있습니다.

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

이 패턴은 에이전트가 또 하나의 범용 패치를 적용하기 전에 올바른 가설부터 검증하게 만듭니다.

## 설치 없이 skill 하나 시험해 보기

URL을 가져올 수 있는 에이전트에 아래 내용을 그대로 붙여 넣으세요. 비용은 들지 않고 1분 정도면 끝납니다.

```text
Read https://raw.githubusercontent.com/voidmatcha/frontend-niche-skills/main/skills/cjk-text-and-input/SKILL.md
and then diagnose this report: our Korean search box runs the search twice when
the user presses Enter, only for some users, and a 300ms debounce reduced it but
did not stop it.
```

위에 링크한 행동 평가 실행에 쓴 것과 같은 리포트이므로, 여러분의 에이전트가 내놓은 답을 [기록된 두 조건](./evals/behavioral/2026-08-01-ime-enter-double-submit/)과 비교해 볼 수 있습니다.

## 적합한 경우

`frontend-niche-skills`는 이럴 때 쓰세요.

- 리포트가 빈 영역, 오래된 화면, 조용한 실패 같은 증상만 말하고 어느 경계가 깨졌는지는 말하지 않을 때.
- 에이전트가 재시도, 지연, 추가 리렌더 같은 그럴듯한 범용 패치를 계속 내놓지만 어느 것도 문제를 해결하지 못할 때.
- 실패가 특정 호스트에서만 재현될 때. 앱 WebView, 서드파티 iframe, 하나의 브라우저 엔진, 하나의 로케일 같은 경우입니다.
- 에이전트가 코드를 고치기 전에 어떤 증거가 원인을 확인하거나 기각하는지 먼저 말하게 하고 싶을 때.

다음 용도로는 쓰지 마세요.

- 버그가 실제로 나타나는 호스트에서 앱을 직접 실행해 보는 일의 대체재,
- 범용 프론트엔드 lint 프리셋이나 코드 스타일 규칙 모음,
- 컴플라이언스 판단. 결제 페이지에서 나온 발견은 증거일 뿐이고 범위는 QSA, 매입사(acquirer), 결제 담당자가 결정합니다,
- 프로젝트 로컬 컨벤션의 대체재. 라우팅, 디자인 토큰, 인증 모델, 테스트 runner, 브라우저와 기기 매트릭스는 그대로 유지하세요.

## 증상 맵

그룹별 skill 목록을 훑어본 뒤에 사용하세요. 실패 신호에서 출발해 가장 구체적인 런타임 증거를 먼저 고르고, 필요하면 이웃 skill로 넘기세요.

| 실패 신호 | 시작할 skill | 먼저 물어볼 질문 |
| --- | --- | --- |
| 페이지가 React Native WebView, WKWebView, Android WebView, Flutter WebView 또는 인앱 브라우저 안에서 실행되며, safe area, 키보드, 재개(resume), bridge, 페인트가 데스크톱 Chrome과 다릅니다. | `webview-bridge-pages` | 레이아웃, 히트 테스트, 페인트/컴포지팅, bridge 타이밍, 호스트 생명주기 중 무엇의 문제인가? |
| 브라우저 iframe/widget이 비어 있거나, 위조 메시지를 받거나, READY/init을 놓치거나, 크기 조절 중 깜빡이거나, 필요한 권한이 없거나, 임베드 로그인 상태를 잃습니다. | `iframe-embed-contracts` | 정확한 부모/게스트 origin, 전달된 frame 정책, 인증된 메시지 핸드셰이크, 크기 프로토콜, 스토리지 모드는 무엇인가? |
| 브라우저 뒤로/앞으로 이동이 오래되었거나 사적인 UI를 복원하거나, 돌아온 뒤 타이머, 소켓, observer가 죽어 있거나 중복됩니다. | `browser-page-lifecycle-bfcache-contracts` | 이것이 persisted 복원이었는가, 어떤 상태와 자원이 멱등하게 재조정되어야 하는가, 실제 history 이동은 무엇을 보여 주는가? |
| SPA 뒤로/앞으로 또는 같은 문서의 hash 탐색 뒤 잘못된 스크롤 위치로 돌아가거나, 콘텐츠 렌더링 뒤 두 번 스크롤하거나, fragment 대상을 보여 주지 못합니다. | `history-scroll-restoration-contracts` | 어느 same-document history entry가 위치를 소유하고, 누가 복원하며, 대상 레이아웃은 언제 안정되는가? |
| 카메라나 마이크가 처음에는 동작하지만 권한 변경, 장치 전환, track 중단, 캡처 UI를 닫았다 다시 연 뒤 실패합니다. | `media-capture-device-contracts` | 권한, 선택 장치, track 상태, 정리, 재획득 전이는 어떻게 이어지는가? |
| HTML 구조 자체가 의심스럽습니다: div 버튼, 잘못된 링크, 레이블/제목/목록, 잘못된 인터랙티브 중첩. | `semantic-markup-contracts` | ARIA, CSS, JavaScript보다 먼저 네이티브 HTML로 표현할 수 있는가? |
| 모달, 드로어, 시트, 팝오버, 메뉴, 커맨드 팔레트가 겉보기에는 멀쩡한데 포커스, 배경 상호작용, Escape/backdrop, 스크롤 잠금이 실패합니다. | `overlay-focus-scroll-contracts` | 열기, 중첩 열기, 닫기, unmount, 라우트 변경 시 각각 무슨 일이 일어나는가? |
| 단일 포인터 드래그, 스와이프, 리사이즈, 그리기가 멈추거나, 요소 경계에서 입력을 잃거나, 네이티브 스크롤과 충돌합니다. | `pointer-gesture-contracts` | 시퀀스가 하나의 활성 `pointerId`, 의도한 이벤트 전달/capture 경로, 종료 정리, `touch-action`을 지키는가? 핀치, 회전, 다중 접촉 geometry는 다른 워크플로로 보내십시오. |

<details>
<summary>나머지 신호 33개</summary>

| 실패 신호 | 시작할 skill | 먼저 물어볼 질문 |
| --- | --- | --- |
| 다이얼로그, 메뉴, 콤보박스, 탭, 커스텀 위젯에 접근성 회귀 커버리지가 필요합니다. | `a11y-contract-testing` | 테스트가 role, name, state, 포커스 계약을 assert할 수 있는가? |
| contenteditable 또는 rich-text 편집기에서 선택 영역이 사라지거나 반전되고, 한 번의 입력이 두 번 적용되고, 실행 취소가 깨지며, 붙여넣기와 드롭 위치가 틀리거나 리마운트 뒤 오래된 Range가 복원됩니다. | `contenteditable-selection-contracts` | 어느 live editing host가 선택 영역을 소유하며, 이 `beforeinput`/`input` 트랜잭션과 이력을 브라우저와 애플리케이션 중 누가 소유하는가? |
| 한국어, 일본어, 중국어 텍스트/입력이 잘못 동작합니다: IME Enter, 조합(composition), grapheme 길이, 줄바꿈, 말줄임. | `cjk-text-and-input` | 코드가 조합 중 텍스트, 확정된 텍스트, 표시되는 텍스트를 뒤섞고 있는가? |
| 번역된 카피가 레이아웃, 복수형 처리, bidi/RTL, 숫자/날짜 포맷팅, 번역 키 계약을 깨뜨립니다. | `i18n-copy-and-layout` | 버그가 카피, 레이아웃, 로케일 동작, 입력 조합 중 어디에 있는가? |
| 딥링크, 인증 리다이렉트, SPA/SSR 라우트, 쿼리 파라미터가 잘못된 화면으로 초기화됩니다. | `deeplink-hydration` | 라우터 준비, 하이드레이션, 인증 바운스 이전의 URL 상태는 무엇인가? |
| WebSocket 또는 SSE 클라이언트가 연결 끊김을 넘기지 못합니다: 재연결 폭풍, 중복/누락 이벤트, 순서가 뒤바뀐 델타, OPEN이지만 죽은 소켓에서 멈춘 UI, 버퍼 증가, 핸드셰이크 후 만료된 토큰. | `realtime-transport-contracts` | 재연결/backoff, 재개/커서, delta folding, liveness/heartbeat, backpressure, 소켓 재인증 중 무엇의 문제인가? |
| 브라우저를 향한 인증 UI에 returnTo, OAuth/passkey, autocomplete, OTP 만료와 재시도, 안전한 오류, 재인증 문제가 있습니다. | `frontend-auth-flow-contracts` | 인증 플로우가 지켜야 할 브라우저 계약은 무엇인가? |
| 팝업, 클립보드, 공유, 파일 선택기, 전체 화면, 결제 API가 직접 클릭에서는 동작하지만 비동기 작업이나 다른 게이트된 호출 뒤에는 실패합니다. | `user-activation-contracts` | 어떤 API가 활성화 게이트를 받으며, 일시적 활성화는 어디에서 만료되거나 소비되는가? |
| 결제 페이지 밖에서 raw HTML, sanitizer, CSP, opener, 스토리지, URL 파싱, 서드파티 스크립트 위험이 나타납니다. | `frontend-security-baseline` | 구체적인 브라우저 보안 source-to-sink 경로가 있는가? |
| 프론트엔드 소유 서버 라우트가 클라이언트가 고른 path, upload, header, business action을 upstream API로 프록시합니다. | `bff-proxy-security-contracts` | 어떤 route-method-auth capability가 노출되고, 다른 ingress가 정책을 우회할 수 있는가? |
| 체크아웃/결제 페이지에 클라이언트 측 증거가 필요합니다: hosted field, 직접 PAN/CVV 처리, 런타임 스크립트, CSP/SRI/헤더 통제. | `payment-page-client-security` | 결제 데이터 경계와 런타임 스크립트 표면을 보여 주는 증거는 무엇인가? |
| CSV/Excel 내보내기, 파일 다운로드, Blob URL, 클립보드 쓰기, 생성된 파일명, 내보내기 스키마가 관련되어 있습니다. | `download-export-safety` | 브라우저를 떠나는 것은 무엇이고, 스프레드시트 셀, Object URL, 클립보드 실패, 파일명은 어떻게 처리되는가? |
| 날짜가 밀리거나, 시간대/DST 문제, 날짜 전용 입력, `datetime-local` 왕복, 상대 시간, 서버/클라이언트 시계 불일치가 있습니다. | `datetime-correctness` | 그 값은 instant인가, 로컬 date-time인가, 날짜 전용 값인가, 포맷된 표시 문자열인가? |
| 돈/수량 합계가 소수점이나 최소 화폐 단위에서 어긋나거나, 반올림이 이상해 보이거나, 현지화된 금액이 잘못 파싱됩니다. | `money-and-precision-contracts` | 값이 이진 부동소수점으로 계산되는가, 그리고 계산이 어떤 반올림 모드와 최소 단위 표현을 쓰는가? |
| 네이티브 Constraint Validation API가 관련되어 있습니다: `setCustomValidity`, `reportValidity`, `:user-invalid`, invalid에서 valid로의 생명주기. | `constraint-validation-contracts` | 네이티브 validity가 올바른 시점에 해제되고 보고되는가? |
| React Hook Form, Formik, Final Form, vee-validate, Valibot 또는 커스텀 JS 검증에 오래된 오류, 비활성화된 제출, 비동기/서버 경쟁이 있습니다. | `js-form-validation-contracts` | 어느 라이브러리 상태가 오류, 유효성, 제출, 서버 필드 매핑을 소유하는가? |
| 하이드레이션 경고나 서버/클라이언트 불일치에 로케일, 시간, 난수, 브라우저 전용 API, 스토리지, 인증 상태, 반응형 분기가 얽혀 있습니다. | `ssr-hydration-mismatch` | 첫 클라이언트 렌더에서 deterministic해야 하는 것은 무엇인가? |
| 구현이 Figma, 스크린샷, 디자인 레퍼런스, 시각 스펙과 일치해야 합니다. | `design-to-code-fidelity` | 주관적인 리뷰 전에 레퍼런스를 내보내고, 렌더를 캡처하고, diff할 수 있는가? |
| 반복되는 UI를 컴포넌트, 래퍼, 훅, 토큰으로 만들지, 분리된 채로 둘지 고민됩니다. | `component-extraction-judgment` | 제품 간 차이를 숨기지 않고 추출할 만큼 중복이 안정적인가? |
| 서버 확인 전에 적용된 낙관적 UI 업데이트가 잘못 동작합니다: 깜빡임, 이중 적용, 롤백되지 않는 실패한 뮤테이션, 응답이 refetch와 경쟁한 뒤 남는 오래된 데이터. | `optimistic-update-rollback-contracts` | apply -> confirm/rollback -> reconcile 계약은 무엇이고, 임시/서버 ID와 동시 뮤테이션은 어떻게 순서가 정해지는가? |
| 페이지로 들여온 파일이 오동작합니다: 드롭 존 하이라이트가 깜빡이거나, 드롭한 파일이 페이지를 다른 곳으로 이동시키거나, 드롭한 폴더에서 아무것도 나오지 않거나, 잘못된 타입의 파일이 통과하거나, 이미지 붙여넣기가 깨지거나, 미리보기 URL이 누수됩니다. | `file-ingest-contracts` | ingest 단계 중 어디가 실패하는가: drag 이벤트 취소, `DataTransfer` items vs files, 타입 신뢰, 붙여넣기, object URL 생명주기? |
| 프론트엔드 오류가 대시보드에서 누락되거나, 읽을 수 없거나(minified / `Script error.`), error boundary가 있는데도 앱이 흰 화면이 됩니다. | `client-error-observability-contracts` | 비동기/rejection까지 수집이 연결되어 있는가, cross-origin/source map 설정이 올바른가, 전송 전에 무엇이 스크러빙되는가? |
| View Transitions 애니메이션이 오동작합니다: 무작위로 실행되지 않거나(silent abort), 오래된 프레임에서 멈추거나, reduced-motion을 무시하거나, 고스트 잔상이 남습니다. | `view-transitions-contracts` | 중복된 `view-transition-name`인가, 페인트되지 않은 snapshot(Suspense/decode)인가, 누락된 reduced-motion 블록인가, 잘못된 Transition 래핑인가? |
| 다이얼로그/팝오버의 진입 또는 이탈 애니메이션이 끊기거나, 트랜지션이 결코 완료되지 않아 정리/포커스/unmount가 멈춰 있습니다. | `css-transition-animation-contracts` | 트랜지션에 `display`/`overlay`(및 `allow-discrete`)가 빠져 있는가, 아니면 결코 발생하지 않는 `transitionend`에 코드가 걸려 있는가? |
| 잘못된 이미지 파일이 배포되거나, 이미지가 과도하게 다운로드되거나, 히어로 이미지가 lazy 로딩되거나, 이미지가 레이아웃 이동을 일으킵니다. | `responsive-image-contracts` | `srcset`에 실제 레이아웃과 일치하는 `sizes`, 올바른 너비 서술자, LCP `eager`/`fetchpriority`, `width`/`height`가 있는가? |
| 페이지의 LCP/CLS/INP가 실패하고, 점수 보고가 아니라 원인을 특정해야 합니다. | `core-web-vitals-performance-contracts` | LCP 요소는 무엇이고(발견 가능한가/우선순위가 잡혔는가), 각 레이아웃 이동의 출처는 무엇이며, 어떤 long task가 INP를 부풀리는가? |
| 뮤테이션 후 클라이언트 캐시 데이터가 오래되었거나, 요청이 워터폴을 이루거나 과다 fetch합니다(React Query/SWR/RTK Query/Apollo). | `frontend-data-fetching-cache-contracts` | 어느 query key를 무효화해야 하고, 읽기가 올바른 stale/gc 타이밍으로 병렬화되어 있는가? |
| 브라우저 로컬 레코드가 사라지거나, IndexedDB 업그레이드가 다른 탭 때문에 멈추거나, UI가 저장 완료를 표시한 뒤 후속 요청이 중단되거나, persistence를 영구 백업으로 설명합니다. | `browser-storage-durability-contracts` | 실패한 단계는 open/upgrade 소유권, 트랜잭션 활성 상태, commit/abort, quota/persistence, 예기치 않은 close, 복구 중 무엇인가? |
| 비동기 effect가 잘못된 데이터를 보여 주거나, 두 번 실행되거나, 누수되거나, 오래된 값을 읽습니다. | `async-effect-race-contracts` | take-latest/`AbortController` + cleanup이 있는가, 그리고 effect가 StrictMode에서 멱등한가? |
| 배포 후 사용자에게 오래된 빌드가 전달되거나, `ChunkLoadError`가 나거나, service worker가 오프라인에서 잘못된/오래된 바이트를 제공합니다. | `pwa-offline-cache-contracts` | SW 업데이트 플로우, 완전한 precache, 캐시 버전 관리, 인증된 HTML/API에 대한 캐시 금지 규칙이 있는가? |
| 가상화된 리스트/그리드가 튀거나 스크롤을 잃거나, 가상화 아래에서 Ctrl+F / 스크린 리더 총계 / 포커스가 깨집니다. | `large-list-data-grid-contracts` | `estimateSize`/overscan이 올바른가, 그리고 unmount된 행에 `aria-setsize`/`aria-posinset`(또는 `aria-rowcount`)가 설정되어 있는가? |
| `ResizeObserver`가 전달되지 않은 알림을 보고하거나, 깜빡이거나, 끝없이 커지거나, 잘못된 box를 측정하거나, 리마운트 뒤 오래된 요소를 관찰합니다. | `resize-observer-layout-contracts` | 어떤 콜백 쓰기가 관찰 중인 크기로 되먹임되며, setup과 cleanup이 현재 대상을 소유하는가? |
| 리포트가 모호하거나, 여러 도메인에 걸쳐 있거나, 어떤 전문 skill이 맡아야 할지 확신이 없습니다. | `frontend-report-triage` | 가능성 높은 실패 유형 상위 1-3개는 무엇이고, 이를 구별해 줄 증거는 무엇인가? |

</details>

## Skills

41개의 skill을, 각 skill이 겨냥하는 프론트엔드 실패 유형별로 묶었습니다. 리포트가 어수선하거나 여러 도메인에 걸쳐 있다면 `frontend-report-triage`부터 시작하세요.

실용적인 우선순위:

- **기본 우선순위 검사:** SSR/딥링크 라우팅, 폼 검증, 날짜/시간, 인증/보안, 결제/내보내기 경계, 오버레이, 접근성, 시맨틱 HTML. 흔하거나 릴리스 후 비용이 큰 버그를 잡아냅니다.
- **호스트/제품 특화 검사:** WebView, 브라우저 iframe/embed, CJK/IME, i18n/RTL, 결제 페이지 증거는 제품이 해당 기능을 실제로 제공할 때 가장 가치가 큽니다.
- **품질/유지보수 검사:** 디자인 충실도와 컴포넌트 추출 판단은 리뷰에서 문제가 되는 것이 런타임 버그가 아니라 어긋난 화면, AI가 생성한 UI, 성급한 추상화일 때 유용합니다.

출처 관리 방식: README에는 라우팅 문서와 증거 문서만 나열하고, 상세한 인용은 각 skill의 `## Sources` 블록 또는 `references/*.md` 파일에 둡니다. README에 모든 upstream URL을 중복해서 담지 않기 위해서입니다.

### 여기서 시작

| Skill | 사용 시점 |
| --- | --- |
| [`frontend-report-triage`](./skills/frontend-report-triage/SKILL.md) | 모호하거나 증상이 여럿인 프론트엔드 버그 리포트를 팩 전체에 걸쳐 트리아지합니다. 가능성 높은 실패 유형, 증거 공백, 가장 적합한 후속 skill 1-3개를 돌려줍니다. |

### 런타임 호스트 엣지

| Skill | 사용 시점 |
| --- | --- |
| [`webview-bridge-pages`](./skills/webview-bridge-pages/SKILL.md) | 네이티브 WebView 안에서 로드되는 페이지를 만들거나 디버깅할 때: bridge 계약, safe-area/뷰포트 레이아웃, 생명주기, 히트 테스트 vs 페인트/컴포지팅, 앱 호스트별 특이 동작. |
| [`iframe-embed-contracts`](./skills/iframe-embed-contracts/SKILL.md) | 브라우저 iframe/widget을 만들거나 디버깅할 때: 부모-게스트 메시지, 임베드 허용 헤더, sandbox/Permissions Policy, READY/init 핸드셰이크, 동적 크기, partitioned 스토리지, 리스너 정리(teardown). |
| [`browser-page-lifecycle-bfcache-contracts`](./skills/browser-page-lifecycle-bfcache-contracts/SKILL.md) | 최상위 브라우저 뒤로/앞으로 복원을 디버깅할 때: 오래된 인증, 데이터, UI 상태, 중복되거나 일시 중지된 자원, `pageshow.persisted`, bfcache 적격성, 멱등한 재개. |
| [`history-scroll-restoration-contracts`](./skills/history-scroll-restoration-contracts/SKILL.md) | SPA 뒤로/앞으로 또는 같은 문서의 hash 탐색 뒤 잘못된 위치로 복원되거나, 비동기 렌더링 뒤 두 번 스크롤하거나, fragment 대상을 놓칠 때: history entry 식별, 복원 책임, 렌더 준비 상태. |
| [`media-capture-device-contracts`](./skills/media-capture-device-contracts/SKILL.md) | 권한 거부, 장치 전환, track 중단, 종료 뒤 카메라와 마이크 캡처가 실패할 때: `getUserMedia`, 장치 열거/변경, track 상태, 정리, 재획득. |
| [`deeplink-hydration`](./skills/deeplink-hydration/SKILL.md) | 라우터 하이드레이션이 준비되기 전에 쿼리 파라미터를 잃거나 잘못된 상태에 도달하는 SPA/SSR 딥링크를 디버깅할 때. |
| [`ssr-hydration-mismatch`](./skills/ssr-hydration-mismatch/SKILL.md) | 로케일/시간/난수/브라우저 전용 API, 스토리지, 인증 상태, 반응형 분기, 데이터 경쟁에서 비롯된 하이드레이션 불일치를 진단할 때. |
| [`realtime-transport-contracts`](./skills/realtime-transport-contracts/SKILL.md) | 연결 끊김을 넘나드는 WebSocket/SSE 클라이언트를 디버깅할 때: 재연결 backoff/jitter, SSE Last-Event-ID/커서 재개, delta 순서 뒤바뀜/중복/누락, heartbeat/좀비 감지, `bufferedAmount` backpressure, 열린 소켓에서의 인증 갱신. |

### 마크업, 접근성, 오버레이

| Skill | 사용 시점 |
| --- | --- |
| [`semantic-markup-contracts`](./skills/semantic-markup-contracts/SKILL.md) | 네이티브 HTML 구조를 리뷰할 때: 버튼 vs 링크, 제목(heading), 랜드마크, 레이블, 표/목록, 잘못된 인터랙티브 중첩, ARIA보다 네이티브를 우선하는 수정. |
| [`overlay-focus-scroll-contracts`](./skills/overlay-focus-scroll-contracts/SKILL.md) | 모달, 드로어, 시트, 팝오버, 메뉴, 커맨드 팔레트의 런타임 계약을 리뷰할 때: 포커스 트랩/복원, inert/aria-hidden 타이밍, 중첩 스택, 스크롤 잠금 정리. |
| [`pointer-gesture-contracts`](./skills/pointer-gesture-contracts/SKILL.md) | 단일 포인터 드래그, 스와이프, 리사이즈, 그리기가 멈추거나 취소되고, 요소 밖에서 입력을 잃거나 페이지 스크롤과 충돌할 때: 활성 pointer 소유권, 이벤트 전달/capture, 취소, `touch-action`, 정리. 실제 핀치, 회전, 다중 접촉 geometry는 범위 밖입니다. |
| [`a11y-contract-testing`](./skills/a11y-contract-testing/SKILL.md) | 접근성 시맨틱을 회귀 테스트로 바꿀 때: role, name, state, 포커스, 다이얼로그, 메뉴, 콤보박스, 탭. |
| [`view-transitions-contracts`](./skills/view-transitions-contracts/SKILL.md) | 조용한 중단(silent abort), 오래된 스냅샷, reduced-motion 무시, 고스트 잔상이 발생하는 View Transitions API 애니메이션을 리뷰할 때. 재구현 가이드가 아니라 리뷰와 PR 가치 판단용입니다. |
| [`css-transition-animation-contracts`](./skills/css-transition-animation-contracts/SKILL.md) | 다이얼로그/팝오버/top-layer의 진입/이탈 트랜지션(`@starting-style`, `allow-discrete`, `overlay`)과 트랜지션 완료에 걸어 둔 정리 로직(`transitionend` vs `getAnimations().finished`)을 리뷰할 때. |
| [`responsive-image-contracts`](./skills/responsive-image-contracts/SKILL.md) | 반응형 이미지 마크업을 리뷰할 때: 실제 레이아웃 대비 `srcset`/`sizes`, 고유 픽셀 너비(`w` descriptor), LCP eager/`fetchpriority`, `picture` 아트 디렉션, CLS를 위한 `width`/`height`. |

### 입력, 콘텐츠, 시간

| Skill | 사용 시점 |
| --- | --- |
| [`contenteditable-selection-contracts`](./skills/contenteditable-selection-contracts/SKILL.md) | contenteditable 또는 rich-text 편집기에서 캐럿과 선택 영역이 사라지거나 이동하고, 편집이 중복되거나, 실행 취소와 다시 실행이 깨지고, 붙여넣기와 드롭 위치가 틀리거나, 리렌더링 중 조합 입력 또는 종료 뒤 포커스와 선택 복원이 손상될 때. |
| [`cjk-text-and-input`](./skills/cjk-text-and-input/SKILL.md) | 한국어, 일본어, 중국어 텍스트/입력을 다룰 때: 줄바꿈, IME 조합(composition), Enter 처리, grapheme 안전 길이, 검증 타이밍. |
| [`i18n-copy-and-layout`](./skills/i18n-copy-and-layout/SKILL.md) | 현지화 카피/레이아웃을 리뷰할 때: 복수형 처리, 텍스트 확장, bidi/RTL, 로케일 포맷팅, 번역 키 계약. |
| [`datetime-correctness`](./skills/datetime-correctness/SKILL.md) | 날짜/시간 코드를 감사할 때: 시간대, DST, 파싱, 포맷팅, `datetime-local`, 상대 시간, 서버/클라이언트 시계 문제. |
| [`money-and-precision-contracts`](./skills/money-and-precision-contracts/SKILL.md) | 돈/수량 연산: 부동소수점 드리프트(`0.1 + 0.2`), 정수 최소 단위 vs decimal 라이브러리, `toFixed`/반올림 모드의 함정, 합산/세금 계산 순서, `Intl` 통화 출력 vs 현지화된 금액 파싱. |

### 폼, 인증, 보안, 결제

| Skill | 사용 시점 |
| --- | --- |
| [`constraint-validation-contracts`](./skills/constraint-validation-contracts/SKILL.md) | 네이티브 HTML Constraint Validation API 계약: `setCustomValidity`, `reportValidity`, `:user-invalid`, invalid에서 valid로 이어지는 생명주기. |
| [`js-form-validation-contracts`](./skills/js-form-validation-contracts/SKILL.md) | React Hook Form, Formik, Final Form, vee-validate, Valibot 또는 커스텀 JS 폼 플로우: 오래된 오류 상태, 비활성화된 제출 버튼, 비동기/서버 경쟁, 서버 필드 오류 매핑. |
| [`frontend-auth-flow-contracts`](./skills/frontend-auth-flow-contracts/SKILL.md) | 브라우저를 향한 인증 플로우를 강화할 때: returnTo 리다이렉트, OAuth/passkey/autocomplete 계약, OTP 만료와 재시도, 안전한 오류 메시지, 민감한 작업 전 재인증. |
| [`user-activation-contracts`](./skills/user-activation-contracts/SKILL.md) | 팝업, 클립보드, 공유, 파일 선택기, 전체 화면, 결제 호출이 비동기 작업이나 다른 소비 API 뒤에 일시적 사용자 활성화를 잃을 때 디버깅. |
| [`frontend-security-baseline`](./skills/frontend-security-baseline/SKILL.md) | 프론트엔드 XSS, DOM 주입, sanitizer 오용, CSP, 서드파티 스크립트, 스토리지, URL 파싱 기본기를 점검할 때. |
| [`bff-proxy-security-contracts`](./skills/bff-proxy-security-contracts/SKILL.md) | 프론트엔드가 소유한 BFF/API 프록시를 점검할 때: 클라이언트가 target을 고르는 SSRF, route/method/auth capability allowlist, 우회 유입 경로(ingress), multipart 예산/boundary, redirect/오류 처리, upstream 비즈니스 플로우 책임 구분. |
| [`payment-page-client-security`](./skills/payment-page-client-security/SKILL.md) | 체크아웃/결제 페이지의 클라이언트 증거를 리뷰할 때: hosted field vs 직접 PAN 처리, 런타임 스크립트 인벤토리, 서드파티 스크립트 위험, CSP/SRI/헤더 증거, PCI DSS 증거 공백. |
| [`optimistic-update-rollback-contracts`](./skills/optimistic-update-rollback-contracts/SKILL.md) | 낙관적 UI 업데이트: 서버 확인 전에 변경 적용, 임시 ID vs 서버 ID, 실패 시 롤백, refetch/invalidation과의 재조정, 응답과 백그라운드 refetch 사이의 경쟁. |
| [`file-ingest-contracts`](./skills/file-ingest-contracts/SKILL.md) | 드래그 앤 드롭, 파일 입력, 붙여넣기로 파일을 페이지에 들여올 때: drop 이벤트 취소/`dropEffect`, dragenter/leave 깜빡임, `DataTransfer` items vs files, 디렉터리 업로드, `accept`/`file.type` 신뢰 문제, object URL 미리보기 생명주기. |

### 출력, 디자인, 추상화, 유지보수

| Skill | 사용 시점 |
| --- | --- |
| [`download-export-safety`](./skills/download-export-safety/SKILL.md) | CSV/Excel 내보내기, Blob/Object URL 다운로드, 클립보드 쓰기, 생성된 파일명, 내보내기 특유의 데이터 경계를 리뷰할 때. |
| [`design-to-code-fidelity`](./skills/design-to-code-fidelity/SKILL.md) | 내보내기, 캡처, 시각적 diff, 증거 등급화를 통해 구현을 디자인 레퍼런스와 비교할 때. |
| [`component-extraction-judgment`](./skills/component-extraction-judgment/SKILL.md) | 반복되는 UI를 공유 컴포넌트, 래퍼, 훅, 토큰으로 만들지, 아니면 분리된 채로 둘지 판단할 때. |
| [`client-error-observability-contracts`](./skills/client-error-observability-contracts/SKILL.md) | 프론트엔드 오류 수집을 연결할 때: `window.onerror`/`unhandledrejection`, error boundary의 한계, cross-origin에서 발생하는 `Script error.` 블랙아웃, source map 배포 vs 업로드, 그룹핑, PII 스크러빙. |

### 성능, 데이터, 오프라인

| Skill | 사용 시점 |
| --- | --- |
| [`core-web-vitals-performance-contracts`](./skills/core-web-vitals-performance-contracts/SKILL.md) | Core Web Vitals(LCP, CLS, INP) 또는 TTFB가 나쁠 때, 수정에 앞서 원인을 특정 요소, 레이아웃 이동, 메인 스레드 작업으로 좁힙니다. 점수 확인이 아니라 페이지 전체 성능 예산을 관리하기 위한 skill입니다. |
| [`frontend-data-fetching-cache-contracts`](./skills/frontend-data-fetching-cache-contracts/SKILL.md) | 클라이언트 데이터 캐시(React Query, SWR, RTK Query, Apollo)가 뮤테이션 후 오래된 데이터를 보여 주거나, 요청 워터폴, 과다/과소 fetch, 페이지네이션/재검증 캐시 버그가 있을 때. |
| [`browser-storage-durability-contracts`](./skills/browser-storage-durability-contracts/SKILL.md) | 브라우저 로컬 데이터가 저장됐다고 표시된 뒤 사라지고, IndexedDB 스키마 업그레이드가 막히고, 트랜잭션이 비활성화되거나 중단되며, quota/persistence 증거 또는 복구 문구가 실제 내구성을 과장할 때. |
| [`async-effect-race-contracts`](./skills/async-effect-race-contracts/SKILL.md) | 직접 작성한 async Effect가 오동작할 때: 의존성 변경 시 발생하는 fetch 경쟁(오래된 응답이 이기는 경우), 누락된 cleanup/`AbortController`, StrictMode 이중 호출, interval과 구독에 남는 오래된 클로저. |
| [`pwa-offline-cache-contracts`](./skills/pwa-offline-cache-contracts/SKILL.md) | Service Worker/오프라인 캐싱이 잘못될 때: 배포 후 오래된 빌드, `ChunkLoadError`, precache 공백, 캐시 버전 관리/축출(cache eviction), SW 업데이트 생명주기, 인증된 응답 캐싱. |
| [`large-list-data-grid-contracts`](./skills/large-list-data-grid-contracts/SKILL.md) | 가상화된 리스트/그리드가 튀거나 스크롤 위치를 잃을 때, 또는 화면 밖 행이 unmount되어 페이지 내 찾기 / 스크린 리더 총계 / 포커스가 깨질 때; 고정 컬럼/헤더 드리프트. |
| [`resize-observer-layout-contracts`](./skills/resize-observer-layout-contracts/SKILL.md) | `ResizeObserver` 크기 피드백 루프, 전달되지 않은 알림 오류, 잘못된 box 측정, 깜빡임, 리마운트 뒤 오래된 관찰 대상. |

## 설치

[`skills` CLI](https://www.skills.sh/)를 설치하세요. skill은 [`SKILL.md` 포맷](https://agentskills.io/specification)을 따릅니다.

이 skill들은 명세의 `description` 1024자 상한을 지키는 Claude Code, Codex를 비롯한 에이전트를 대상으로 하며, 알맞은 skill이 실행되도록 그 분량을 트리거 표현에 씁니다. Claude.ai 업로드 경로는 `description`을 200자로 제한하므로 그대로 올리면 실패합니다 ([Claude 문서](https://claude.com/docs/skills/how-to)).

아래의 `voidmatcha/frontend-niche-skills` 명령은 공개 저장소 또는 plugin marketplace 항목이 있다는 것을 전제합니다. 로컬 또는 사전 릴리스 checkout에서는 이 섹션의 로컬 checkout 명령을 대신 사용하세요.

```bash
# Claude Code + Codex via skills CLI
npx skills add voidmatcha/frontend-niche-skills --skill '*' -g -a claude-code -a codex

# Other agents supported by the installed skills CLI
npx skills add voidmatcha/frontend-niche-skills --skill '*' -g --agent '*'
```

### Claude Code plugin

```bash
/plugin marketplace add voidmatcha/frontend-niche-skills
/plugin install frontend-niche-skills@voidmatcha
```

### Codex plugin 로컬 checkout

이 저장소에는 `.codex-plugin/plugin.json`과 Claude plugin manifest가 포함되어 있습니다. 로컬 checkout에서:

```bash
codex plugin marketplace add "$(pwd)"
codex plugin add frontend-niche-skills@frontend-niche-skills
```

설치하거나 업데이트한 뒤에는 번들 skill이 갱신되도록 새 Codex 또는 Claude Code 세션을 시작하세요.

## Workflow

1. **증상에 맞는 skill을 고릅니다.** 버그와 실패 유형이 일치하는 가장 좁은 skill을 사용하세요.
2. **저장소 컨텍스트를 읽습니다.** skill을 프로젝트의 라우팅, 디자인 토큰, i18n, 테스트, 브라우저/기기 지원과 함께 사용하세요.
3. **증거 유형을 구분합니다.** 레이아웃, 페인트, 히트 테스트, DOM 구조, 접근성 트리, 네트워크, 하이드레이션, 로케일 동작, 런타임 스크립트, 내보낸 파일은 서로 다르게 말할 수 있습니다.
4. **증상이 아니라 원인을 고칩니다.** 재시도를 추가하기보다 취약한 타이밍이나 중복된 로직을 제거하는 쪽을 우선하세요.
5. **올바른 호스트에서 검증합니다.** WebView 버그에는 앱 WebView 증거가, 결제 페이지 검토에는 런타임 스크립트/PAN 경계 증거가, 시각적 충실도에는 레퍼런스/렌더 캡처가 필요하며, 폼/접근성 이슈는 가능하면 회귀 테스트로 남기세요.

## 증거

- [`evals/behavioral/`](./evals/behavioral/) — 이 팩이 자기 중심 주장을 실제로 측정한 두 번입니다. 같은 버그를 해당 skill을 주고/주지 않고 진단하게 했습니다. 채점 기준은 매번 실행 전에 커밋했습니다. 두 사례 모두 동률이라, 이 두 리포트에서는 사전 등록한 기준으로 볼 수 있는 차이를 skill이 만들지 못했습니다. 두 번째 기록에는 기준 밖에서 skill 쪽이 옳았던 차이 하나와, 그것을 나중에 알아챈 것이 왜 증거가 아닌지가 적혀 있습니다.
- [`.github/workflows/checks.yml`](./.github/workflows/checks.yml): 41개 skill 중 4개의 브라우저 픽스처를 푸시마다 다시 실행합니다. 세 개는 Chromium, Firefox, WebKit에서, 하나는 Chromium에서만 돕니다. 해당 skill이 서술하는 브라우저 동작이 사실인지를 확인할 뿐, 이 팩이 에이전트의 출력을 바꾸는지는 측정하지 않습니다. 같은 스위트가 푸시를 막기 때문에, 실패한 실행은 기록으로 남는 대신 푸시를 차단합니다.

이 저장소는 grep 매치를 곧 버그로 취급하지 않습니다. 모든 주장은 [`docs/skill-evidence-coverage.md`](./docs/skill-evidence-coverage.md)의 증거 ladder에서 등급 하나를 답니다. **E1 측정됨**, **E2 소스 확인됨**, **E3 1차 출처 인용**, **E4 라우팅 예시**입니다. 등급은 실제로 무엇을 했는지를 기록하며, 얼마나 확신하는지는 기록하지 않습니다. 2026-08-01 기준 OSS casebook의 어떤 항목도 upstream에 제보되거나, 로컬에서 재현되거나, 메인테이너에게 수용된 적이 없습니다.

증거의 위치:

- [`docs/oss-validation-cases.md`](./docs/oss-validation-cases.md): skill 경계와 PR 형태를 점검(sanity-check)하는 데 사용한 공개 OSS 사례.
- [`skills/webview-bridge-pages/references/why-webview-bridge-pages.md`](./skills/webview-bridge-pages/references/why-webview-bridge-pages.md): WebView 특화 선행 사례, bridge 라이브러리, 호스트 동작 레퍼런스, 생태계 노트.
- [`docs/public-skill-landscape.md`](./docs/public-skill-landscape.md): 이 팩과 직접 겹치거나, 거의 비슷하거나, 상호 보완적인 공개 skill pack을 실제로 열어 비교하고 유지/분리/보류 판단을 기록한 문서.
- [`docs/skill-evidence-coverage.md`](./docs/skill-evidence-coverage.md): 증거 ladder 자체와, skill별로 근거가 어느 등급에 있는지 보여 주는 맵.
- [`docs/skill-quality-standard.md`](./docs/skill-quality-standard.md): 이 팩이 사용하는 이식 가능한 포맷, 라우팅, 워크플로, 증거, 출력, 평가, 신규 skill 채택 기준.
- `skills/*/SKILL.md` 및 `skills/*/references/*.md`: skill별 공식 문서, 선행 사례, 예시, 오탐 노트, 구현 특화 증거.

후보 OSS 발견은 현재 브랜치를 다시 확인하고, 로컬에서 재현하고, 메인테이너가 수락하거나 실패하는 테스트로 뒷받침되기 전까지는 확인된 upstream 버그가 **아닙니다**.

## 개발 검사

저장소 로컬 검사는 직접 실행하거나 lefthook을 통해 실행할 수 있습니다:

```bash
./scripts/pre-push-checks.sh

# Optional: install Git hooks after installing lefthook locally.
lefthook install
lefthook run pre-push
```

통과한 실행은 다음과 같이 보입니다:

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

`lefthook.yml`은 저장소 스크립트에 위임만 하므로, 기여자는 lefthook 없이도 같은 검사를 실행할 수 있습니다. 이 스크립트는 skill 메타데이터와 품질 섹션, 직접 연결된 레퍼런스의 도달 가능성, eval 파일 형태, README 링크와 개수, plugin manifest, 로컬 마크다운 링크, 과장 표현, 번들 스크립트 문법을 감사합니다. `git diff --check`도 실행하고, push하려는 마크다운의 출처 링크를 검사합니다(오프라인이면 건너뛰며, `SKIP_LINK_CHECK=1`로 강제로 건너뛸 수 있습니다). 외부 URL 전체를 검사하려면 `python3 scripts/audit-skill-pack.py --check-links`를 실행하세요. `.github/workflows/link-check.yml`이 이 검사를 매주 실행해 죽은 인용이 발견되면 `link-rot` 이슈를 등록합니다. 링크 교체 절차는 [docs/skill-evidence-coverage.md](./docs/skill-evidence-coverage.md)에 있고, `.github/workflows/checks.yml`이 모든 push와 pull request마다 팩 검사를 실행합니다.

## 기여하기

신규 skill은 [docs/skill-quality-standard.md](./docs/skill-quality-standard.md)의 여섯 가지 질문 게이트를 통과해야 채택됩니다. 그 실패가 반복되는지, 하나의 제품이나 컴포넌트 밖에서도 성립하는지, 범용 코딩 에이전트가 이 문제를 틀리는지, 이웃 skill이 이미 그 경로를 맡고 있는지, 테스트할 수 있는지, 약한 발견을 스스로 거부할 수 있는지를 묻습니다. 작업 흐름과 push 전에 실행되는 검사는 [CONTRIBUTING.md](./CONTRIBUTING.md)를 참고하세요.

## FAQ

### 프론트엔드 리뷰 체크리스트나 ESLint 설정과 무엇이 다른가요?

다릅니다. 이 skill들은 범용 UI 리뷰가 자주 놓치는 프론트엔드 엣지에 집중합니다: WebView 호스트 동작, 네이티브 HTML 구조, IME/CJK 입력, 접근성 계약, 하이드레이션, 폼, 날짜/시간, 인증, 결제 페이지 클라이언트 증거, 내보내기, 오버레이, 디자인 충실도.

### 에이전트가 결제 페이지의 PCI DSS 범위를 판단할 수 있나요?

아니요. 이 skill은 프론트엔드 증거를 수집합니다: 결제 페이지 스크립트 인벤토리, PAN/CVV 경계, CSP/SRI/헤더 통제, PCI DSS 6.4.3/11.6.1 논의 지점. 범위와 컴플라이언스는 QSA, 매입사(acquirer), 결제 담당자, 보안 담당자가 결정합니다.

### 이 skill들이 프로젝트의 컨벤션과 lint 규칙을 대체하나요?

아니요. 프로젝트 로컬 컨벤션은 그대로 유지하세요: 라우팅, 컴포넌트, 디자인 토큰, 인증 모델, 테스트 runner, 브라우저/기기 매트릭스, 릴리스 게이트. 이 skill들은 이슈 특화 플레이북으로 사용하세요.

### 왜 하나의 큰 프론트엔드 skill이 아니라 41개로 나눴나요?

작은 skill이 컨텍스트를 집중시킵니다. 어수선한 리포트를 위해 `frontend-report-triage`가 있지만, 모든 skill을 로드하기보다 가장 작고 유용한 집합으로 라우팅해야 합니다.

### 왜 데스크톱 Chrome에서는 되는 페이지가 앱 WebView에서는 깨지나요?

마크업이 아니라 호스트가 다르기 때문입니다. safe area와 뷰포트 inset, bridge 준비 상태, 재개 시 렌더러 종료, 컴포지팅 동작은 페이지 버그가 아니라 호스트 계약입니다. `webview-bridge-pages`가 이를 다루며, 증거는 데스크톱 브라우저가 아니라 앱 WebView에서 나와야 합니다.

### 어떤 코딩 에이전트에서 이 skill들을 쓸 수 있나요?

[`SKILL.md` 포맷](https://agentskills.io/specification)을 읽는 에이전트라면 무엇이든 가능합니다. Claude Code와 Codex는 전용 plugin marketplace로 지원하고, [`skills` CLI](https://www.skills.sh/)는 이 팩을 자신이 지원하는 다른 에이전트에도 설치해 줍니다. [설치](#설치)를 참고하세요.

## 라이선스

Apache-2.0 © [voidmatcha](https://github.com/voidmatcha). [LICENSE](./LICENSE)를 참고하세요.
