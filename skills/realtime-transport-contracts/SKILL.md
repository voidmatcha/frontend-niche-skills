---
name: realtime-transport-contracts
description: "Use when a WebSocket or SSE client misbehaves across a connection drop: a reconnect storm hammering the server after a restart (fixed-interval retry, no jitter), a socket that reports OPEN but is silently dead (zombie / close code 1006, proxy idle-timeout), events duplicated or missing after reconnect (no SSE Last-Event-ID, no server cursor to resume), delta messages applied out-of-order/duplicated/gapped, memory growth or a force-closed socket from unbounded buffering (bufferedAmount climbing), an EventSource that reconnects forever after you meant to stop, or a long-lived socket still running on a token that expired after the handshake. Client transport-resilience scope; for token/session refresh mechanics see frontend-auth-flow-contracts, for token-in-URL-vs-header and origin checks see frontend-security-baseline, for the initial snapshot vs live-stream hydration seam see ssr-hydration-mismatch. Not the native WebView postMessage bridge — see webview-bridge-pages."
---

# Realtime transport contracts

A realtime client's happy path (connect, receive, render) always works; the defects live in the seams around a dropped connection — reconnect, resume, dedupe, liveness, backpressure, and re-auth. Treat the connection as unreliable and every delta as potentially duplicated, reordered, or missing, and make each recovery step an explicit contract rather than a framework default.

## Checklist (lead with the trap; details in references/)

→ [transport-resilience](./references/transport-resilience.md)

1. **Reconnect with capped exponential backoff + jitter, and stop on non-retryable closes.** A fixed-interval (or un-jittered) retry turns a server restart into a synchronized thundering herd; AWS's measurements show full jitter — `sleep = random(0, min(cap, base * 2**attempt))` — cuts both contention and total recovery time. Reset the attempt counter only after a connection *stays up* past a stability window, or a flapping server resets your backoff every few seconds. Do not blindly retry every close: retry transient codes (1006 abnormal, 1011 server error, 1012 restart, 1013 try-again-later); do not loop on auth/policy (1008, app-level 4xxx) or protocol errors (1002/1003). `EventSource` reconnects on its own, so the bug is the opposite — call `.close()` when you mean to stop, and know a `204` response tells the browser to stop retrying.
2. **Resume the stream, do not restart it.** After reconnect you must re-subscribe to channels *and* resume from a position. SSE sends the `Last-Event-ID` header automatically — but only if the server emitted `id:` lines and you did not reset the id, and only if the server actually honors the header and replays from it. For WebSocket you own resume: send your last-applied server cursor/sequence on reconnect. Without resume you either gap (dropped events) or blindly re-request a fresh snapshot and double-count.
3. **Fold deltas defensively: dedupe, order, detect gaps.** Deltas arrive duplicated (replay after reconnect), out of order, or gapped. Key every delta by a monotonic server sequence/version: drop `seq <= lastApplied` (idempotent apply), hold `seq > expected` in a small reorder buffer until the gap fills, and treat an unfillable gap as "resnapshot", never "interpolate". A `Map`/last-writer-wins merge that ignores sequence silently applies a stale delta over a newer one.
4. **Reconcile the initial snapshot against the live stream on one cursor.** The snapshot (REST/SSR) and the stream must share a version axis — apply only deltas newer than the snapshot version and backfill the gap between them, or you double-apply or drop the overlap. (For the SSR/first-render side of this seam see ssr-hydration-mismatch.)
5. **Add heartbeat + liveness; an OPEN socket can be dead.** `readyState === OPEN` (and even a live TCP socket) can be a zombie after a network drop or a proxy idle-timeout — the classic silent 1006. Browser JS cannot send protocol-level ping/pong (RFC 6455 frames are not exposed to the WebSocket API), so run an application-level ping and expect a pong within a timeout; on miss, close and reconnect. Gate reconnects on `navigator.onLine`/`offline` and Page Visibility so a backgrounded or offline tab does not spin.
6. **Bound the buffers; the send path has no automatic backpressure.** `WebSocket.bufferedAmount` climbs when you `send()` faster than the socket drains; per the WHATWG spec a full send buffer forces the browser to *close* the connection. Poll `bufferedAmount` and throttle/coalesce outgoing messages above a threshold; bound the inbound queue too and coalesce or shed rather than growing memory unbounded (or adopt a stream-backpressured transport where supported).
7. **Refresh auth on a long-lived socket.** Authentication at the handshake establishes identity only at that instant; hours later the token may be expired or revoked while the socket keeps processing messages. Refresh before expiry — in-band (push a fresh token over the open socket, server re-validates, no drop) or reconnect-with-new-token — and define an explicit reauth-required signal, since the protocol has no built-in "auth expired" response. (Refresh/rotation mechanics belong to frontend-auth-flow-contracts; `EventSource` cannot set an `Authorization` header, so tokens often ride in the URL/query and get logged — that placement is frontend-security-baseline.)
8. **Test the failure sequence, not the happy path.** Assert: reconnect after a drop resumes with no gap and no duplicate; backoff carries jitter and caps; an auth/policy close is not retried; a missed heartbeat triggers reconnect; duplicated/out-of-order/gapped deltas converge to the same state; an expired token is refreshed without tearing the stream down.

## Quick probes

Use hits as leads, then trace the reconnect/resume/apply path:

```sh
rg -n 'new WebSocket|new EventSource|reconnect|backoff|retry|setTimeout.*connect' src/ app/ packages/ 2>/dev/null
rg -n 'lastEventId|Last-Event-ID|cursor|sequence|seq|version|resume|subscribe' src/ app/ packages/ 2>/dev/null
rg -n 'bufferedAmount|readyState|onclose|CloseEvent|\.code|1006|heartbeat|ping|pong|onLine|visibilitychange' src/ app/ packages/ 2>/dev/null
rg -n 'token|Authorization|refresh|reauth|expires' src/ app/ packages/ 2>/dev/null | rg -i 'socket|ws|sse|eventsource|stream'
```

## Boundary with sibling skills

- Use **realtime-transport-contracts** for reconnect backoff/jitter, SSE `Last-Event-ID`/cursor resume, delta dedupe/order/gap folding, heartbeat/zombie detection, `bufferedAmount` backpressure, and refreshing auth on an already-open socket.
- Use **frontend-auth-flow-contracts** for how the token/session is actually refreshed or rotated (this skill only covers *when and how it re-enters the socket*).
- Use **frontend-security-baseline** for token-in-URL vs header, `wss://`/origin checks, and cross-origin/`Origin`-header trust.
- Use **ssr-hydration-mismatch** when the *initial snapshot* is server-rendered and diverges from the first client render before the stream attaches.
- Use **webview-bridge-pages** for the native app `postMessage` bridge and cold-start/first-message buffering — that is a host-transport contract, not a network socket.

## PR-worthiness gate

Raw `new WebSocket` / `new EventSource` matches are noisy. Count a finding only when a recovery contract is actually violated and a symptom follows:

- **Reconnect**: fixed-interval or un-jittered retry (herd risk), no cap, backoff reset on `open` instead of after a stability window, or a loop that retries an auth/policy/protocol close.
- **Resume**: reconnect that re-subscribes but sends no `Last-Event-ID`/cursor, or a server that ignores the id it emitted — visible as duplicated or missing events after a drop.
- **Delta folding**: apply path with no sequence key — duplicates re-applied, reorder mis-merged, or an unfilled gap silently ignored.
- **Liveness**: no heartbeat/timeout, so a 1006 zombie leaves the UI frozen while `readyState` reads OPEN.
- **Backpressure**: unbounded `send()`/inbound queue with no `bufferedAmount` guard — memory growth or a browser-forced close under load.
- **Auth**: socket authed only at handshake with no in-band refresh or reconnect-on-expiry — messages processed on an expired/revoked token.

Reject weak findings: a library (Socket.IO, Phoenix Channels, Ably, Pusher, `@microsoft/signalr`, TanStack Query streaming) that already owns backoff+jitter, resume, and heartbeat — inspect its config before claiming a gap; a short-lived request-scoped socket where reconnect/resume is irrelevant; a heartbeat "missing" when the server pings and the browser auto-pongs at the protocol level; `bufferedAmount` used correctly as a pacing gate. Minimal useful PR: one failing reconnect-resume test (drop mid-stream, assert no gap/no dup) plus the smallest change — a jittered backoff helper, a cursor on the resubscribe, a sequence guard in the reducer, a heartbeat timeout, or an in-band token refresh.

## Output shape

Return compact findings:

- **Contract**: reconnect-backoff / resume-cursor / delta-fold / heartbeat-liveness / backpressure / socket-reauth.
- **Evidence**: file/line and the connect/apply path; the close code or symptom if known.
- **Risk**: server herd, dropped/duplicated events, corrupted client state, frozen UI on a dead socket, memory/force-close, or messages on an expired token.
- **Fix**: the smallest helper or call-site change.
- **Verification**: the failure-sequence test that would catch the regression.

## Sources

- MDN, Using server-sent events — `id`/`retry` fields, automatic reconnection, `Last-Event-ID`, and `.close()` / `204` to stop: <https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events>
- WHATWG HTML Living Standard §9.2 Server-sent events — normative `Last-Event-ID`, `id`/`retry`, reconnection: <https://html.spec.whatwg.org/multipage/server-sent-events.html>
- MDN, WebSocket.bufferedAmount — queued send bytes and network-rate pacing: <https://developer.mozilla.org/en-US/docs/Web/API/WebSocket/bufferedAmount>
- WHATWG WebSockets Standard — full send buffer must close the connection; API-level behavior: <https://websockets.spec.whatwg.org/>
- MDN, CloseEvent.code — close-code ranges and the locally-generated 1006 abnormal closure: <https://developer.mozilla.org/en-US/docs/Web/API/CloseEvent/code>
- MDN, Writing WebSocket client applications — application-level ping/pong heartbeat pattern: <https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API/Writing_WebSocket_client_applications>
- RFC 6455, The WebSocket Protocol — Ping/Pong control frames and close codes (protocol-level, not exposed to browser JS): <https://www.rfc-editor.org/rfc/rfc6455.html>
- AWS Architecture Blog, Exponential Backoff And Jitter — full/equal/decorrelated jitter and thundering-herd measurements: <https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/>
- WebSocket.org, WebSocket Authentication — in-band token refresh vs reconnect for token expiry on long-lived connections: <https://websocket.org/guides/authentication/>
