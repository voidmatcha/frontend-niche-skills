---
name: realtime-transport-contracts
description: "Use when a WebSocket or SSE client misbehaves across a connection drop: a reconnect storm after a server restart (fixed-interval retry, no jitter), a socket OPEN but silently dead (zombie, close code 1006, proxy idle-timeout), events duplicated or missing after reconnect (no SSE Last-Event-ID or server cursor), deltas applied out-of-order/gapped, unbounded buffering (bufferedAmount climbing) forcing a close, an EventSource that reconnects forever, or a socket running on a token that expired after the handshake. Also covers socket handshake hygiene (wss://, Origin allowlist, token-in-URL logging). Token issuance and refresh mechanics belong to the app's auth/session layer, outside this pack; snapshot-vs-stream hydration see ssr-hydration-mismatch; the native WebView postMessage bridge is webview-bridge-pages."
---

# Realtime transport contracts

A realtime client's happy path (connect, receive, render) always works; the defects live in the seams around a dropped connection — reconnect, resume, dedupe, liveness, backpressure, and re-auth. Treat the connection as unreliable and every delta as potentially duplicated, reordered, or missing, and make each recovery step an explicit contract rather than a framework default.

## Checklist (lead with the trap; details in references/)

→ [transport-resilience](./references/transport-resilience.md)

1. **Reconnect with capped exponential backoff + jitter, and stop on non-retryable closes.** A fixed-interval (or un-jittered) retry turns a server restart into a synchronized thundering herd; AWS's measurements show full jitter — `sleep = random(0, min(cap, base * 2**attempt))` — cuts both contention and total recovery time. Reset the attempt counter only after a connection *stays up* past a stability window, or a flapping server resets your backoff every few seconds. Do not blindly retry every close: retry transient codes (1006 abnormal, 1011 server error, 1012 restart, 1013 try-again-later); do not loop on auth/policy (1008, app-level 4xxx) or protocol errors (1002/1003). `EventSource` reconnects on its own, so the bug is the opposite — call `.close()` when you mean to stop, and know a `204` response tells the browser to stop retrying.
2. **Resume the stream, do not restart it.** After reconnect you must re-subscribe to channels *and* resume from a position. SSE sends the `Last-Event-ID` header automatically — but only if the server emitted `id:` lines and you did not reset the id, and only if the server actually honors the header and replays from it. For WebSocket you own resume: send your last-applied server cursor/sequence on reconnect. Without resume you either gap (dropped events) or blindly re-request a fresh snapshot and double-count.
3. **Fold deltas defensively: dedupe, order, detect gaps.** Deltas arrive duplicated (replay after reconnect), out of order, or gapped. Key every delta by a monotonic server sequence/version: drop `seq <= lastApplied` (idempotent apply), hold `seq > expected` in a small reorder buffer until the gap fills, and treat an unfillable gap as "resnapshot", never "interpolate". A `Map`/last-writer-wins merge that ignores sequence silently applies a stale delta over a newer one.
4. **Reconcile the initial snapshot against the live stream on one cursor.** The snapshot (REST/SSR) and the stream must share a version axis — apply only deltas newer than the snapshot version and backfill the gap between them, or you double-apply or drop the overlap. (For the SSR/first-render side of this seam see ssr-hydration-mismatch.)
5. **Add heartbeat + liveness; an OPEN socket can be dead.** `readyState === OPEN` (and even a live TCP socket) can be a zombie after a network drop or a proxy idle-timeout — the classic silent 1006. Browser JS cannot send or observe protocol-level ping/pong (the WHATWG WebSockets Standard says RFC 6455 Ping and Pong frames "are not currently exposed in the API"), so run an application-level ping and expect a pong within a timeout, or watch for a server-sent application heartbeat; on miss, close and reconnect. Server-initiated protocol pings that the browser auto-pongs keep proxies from idling out and let the *server* reap dead clients, but they give client JavaScript no signal, so they do not replace the client-side timeout. Gate reconnects on `navigator.onLine`/`offline` and Page Visibility so a backgrounded or offline tab does not spin.
6. **Bound the buffers; the send path has no automatic backpressure.** `WebSocket.bufferedAmount` climbs when you `send()` faster than the socket drains; per the WHATWG spec a full send buffer forces the browser to *close* the connection. Poll `bufferedAmount` and throttle/coalesce outgoing messages above a threshold; bound the inbound queue too and coalesce or shed rather than growing memory unbounded (or adopt a stream-backpressured transport where supported).
7. **Refresh auth on a long-lived socket.** Authentication at the handshake establishes identity only at that instant; hours later the token may be expired or revoked while the socket keeps processing messages. Refresh before expiry — in-band (push a fresh token over the open socket, server re-validates, no drop) or reconnect-with-new-token — and define an explicit reauth-required signal, since the protocol has no built-in "auth expired" response. How the token itself is issued, refreshed, or rotated belongs to the app's auth/session layer, outside this pack; this skill owns when and how a fresh token re-enters the socket.
8. **Check the handshake's security contract.** Use `wss://`, never `ws://`, in production. Browsers send cookies with the WebSocket handshake, so a cookie-authenticated socket is open to cross-site WebSocket hijacking unless the server validates `Origin` against an explicit allowlist on every handshake (RFC 6455 §10.2: servers "SHOULD verify the |Origin| field is an origin they expect", else respond 403). `EventSource` accepts only a URL and `withCredentials`, so it cannot set an `Authorization` header, and tokens often ride in the query string; OWASP notes that query-string tokens "will appear in access logs and should be redacted", and that passing the token in a message after the connection opens avoids log exposure.
9. **Test the failure sequence, not the happy path.** Assert: reconnect after a drop resumes with no gap and no duplicate; backoff carries jitter and caps; an auth/policy close is not retried; a missed heartbeat triggers reconnect; duplicated/out-of-order/gapped deltas converge to the same state; an expired token is refreshed without tearing the stream down.

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
- Socket handshake hygiene (`wss://`, `Origin` allowlist, token-in-URL logging) stays in this skill: neither **frontend-security-baseline** nor **frontend-auth-flow-contracts** covers WebSocket or SSE handshakes. Use **frontend-security-baseline** only for the app-wide token-storage and cookie/CSRF stance.
- Token issuance, refresh, and rotation mechanics belong to the app's auth/session layer, outside this pack; **frontend-auth-flow-contracts** covers login, OTP, passkey, `returnTo`, and step-up flows, not token refresh.
- Use **frontend-data-fetching-cache-contracts** for how a received update is written into the client query cache — which key it targets, and `setQueryData` versus invalidate — including deltas that arrive on a healthy transport but never write to or invalidate the query-cache entry the UI renders. This skill owns the transport up to delivery: reconnect, resume cursor, and dedupe/order/gap folding of deltas.
- Use **bff-proxy-security-contracts** when the frontend repo's own server terminates or relays the socket: its ingress inventory and capability matrix belong there, while the `Origin`/`wss://`/token-in-URL handshake contract stays here.
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
- **Handshake**: a cookie-authenticated socket whose server accepts any `Origin`, a production `ws://` URL, or a long-lived token in a query string that reaches access logs unredacted.

Reject weak findings: a gap in a contract that the client library (Socket.IO, Phoenix Channels, Ably, Pusher, `@microsoft/signalr`) is configured to own. Libraries own only *some* of backoff, jitter, resume, and heartbeat, so check the configuration per contract before claiming or dismissing a gap: for example, SignalR's JavaScript client does not reconnect by default, and `withAutomaticReconnect()` with no arguments waits 0, 2, 10, and 30 seconds, with no jitter, then stops. Also reject: a short-lived request-scoped socket where reconnect/resume is irrelevant; a "missing" client heartbeat when the server sends an application-level heartbeat that the client already times out on (server protocol pings alone do not count, because client JavaScript cannot see them); `bufferedAmount` used correctly as a pacing gate. Minimal useful PR: one failing reconnect-resume test (drop mid-stream, assert no gap/no dup) plus the smallest change — a jittered backoff helper, a cursor on the resubscribe, a sequence guard in the reducer, a heartbeat timeout, or an in-band token refresh.

## Output shape

Return compact findings:

- **Contract**: reconnect-backoff / resume-cursor / delta-fold / heartbeat-liveness / backpressure / socket-reauth / handshake-security.
- **Evidence**: file/line and the connect/apply path; the close code or symptom if known.
- **Risk**: server herd, dropped/duplicated events, corrupted client state, frozen UI on a dead socket, memory/force-close, or messages on an expired token.
- **Fix**: the smallest helper or call-site change.
- **Verification**: the failure-sequence test that would catch the regression.

## Sources

- MDN, Using server-sent events — `id`/`retry` fields, automatic reconnection, `Last-Event-ID`, and `.close()` / `204` to stop: <https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events>
- WHATWG HTML Living Standard §9.2 Server-sent events — normative `Last-Event-ID`, `id`/`retry`, reconnection: <https://html.spec.whatwg.org/multipage/server-sent-events.html>
- MDN, WebSocket.bufferedAmount — queued send bytes and network-rate pacing: <https://developer.mozilla.org/en-US/docs/Web/API/WebSocket/bufferedAmount>
- WHATWG WebSockets Standard — full send buffer must close the connection; API-level behavior: <https://websockets.spec.whatwg.org/>
- WHATWG WebSockets Standard §5 Ping and Pong frames — "These are not currently exposed in the API": <https://websockets.spec.whatwg.org/#ping-and-pong-frames>
- MDN, CloseEvent.code — close-code table, including the locally-generated 1006 abnormal closure (the retry/do-not-retry split in the checklist is this skill's design advice, not MDN's): <https://developer.mozilla.org/en-US/docs/Web/API/CloseEvent/code>
- MDN, Writing WebSocket client applications — an example app that sends application-level "ping" messages and listens for "pong" replies: <https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API/Writing_WebSocket_client_applications>
- RFC 6455, The WebSocket Protocol — Ping/Pong control frames, close codes, and §10.2 Origin Considerations (servers "SHOULD verify the |Origin| field"): <https://www.rfc-editor.org/rfc/rfc6455.html>
- OWASP, WebSocket Security Cheat Sheet — `wss://` only, Origin allowlist against CSWSH, query-string tokens "will appear in access logs and should be redacted", token rotation on long-lived connections: <https://cheatsheetseries.owasp.org/cheatsheets/WebSocket_Security_Cheat_Sheet.html>
- MDN, EventSource() constructor — options are limited to `withCredentials`: <https://developer.mozilla.org/en-US/docs/Web/API/EventSource/EventSource>
- Microsoft Learn, ASP.NET Core SignalR JavaScript client — no automatic reconnect by default; `withAutomaticReconnect()` waits 0, 2, 10, and 30 seconds, then stops: <https://learn.microsoft.com/en-us/aspnet/core/signalr/javascript-client>
- AWS Architecture Blog, Exponential Backoff And Jitter — full/equal/decorrelated jitter and thundering-herd measurements: <https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/>
- WebSocket.org, WebSocket Authentication — in-band token refresh vs reconnect for token expiry on long-lived connections: <https://websocket.org/guides/authentication/>
