# Transport resilience reference

Use this reference only after `realtime-transport-contracts` triggers and the task involves a WebSocket or SSE (`EventSource`) client across a reconnect, resume, delta-apply, heartbeat, backpressure, or socket re-auth path.

## Official references

- MDN, Using server-sent events: `EventSource` auto-reconnects; the server's `retry:` field sets the reconnect delay (ignored if non-integer); an `id:` line sets `lastEventId`, and on reconnect the browser sends the `Last-Event-ID` request header so the server can replay. An `id:` with no value resets it. Call `.close()` to stop reconnecting; an HTTP `204` also stops it. <https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events>
- WHATWG HTML Living Standard, §9.2 Server-sent events: normative behavior for `id`/`retry`, the `Last-Event-ID` header, and reconnection. <https://html.spec.whatwg.org/multipage/server-sent-events.html>
- MDN, `WebSocket.bufferedAmount`: bytes queued by `send()` but not yet transmitted; the standard WebSocket API has no automatic backpressure, so poll this to pace/throttle sends. <https://developer.mozilla.org/en-US/docs/Web/API/WebSocket/bufferedAmount>
- WHATWG WebSockets Standard: if data would need buffering but the send buffer is full, the user agent must fail the WebSocket and close the connection. <https://websockets.spec.whatwg.org/>
- MDN, `CloseEvent.code`: integer 1000-4999; 1006 (abnormal, never sent in a frame — set locally when the connection disappears), 1011 (server error). Retry transient closes (1006/1011/1012/1013); do not loop on auth/policy (1008, 4xxx) or protocol (1002/1003). Some browsers report 1005 vs 1006 for the same drop — handle both. <https://developer.mozilla.org/en-US/docs/Web/API/CloseEvent/code>
- MDN, Writing WebSocket client applications: protocol ping/pong frames are not exposed to the browser API, so implement an application-level ping/pong heartbeat. <https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API/Writing_WebSocket_client_applications>
- RFC 6455, The WebSocket Protocol: Ping/Pong control frames (§5.5.2-5.5.3) and close-code semantics; a peer that does not answer pings within a timeout is treated as dead. <https://www.rfc-editor.org/rfc/rfc6455.html>
- AWS Architecture Blog, Exponential Backoff And Jitter: full jitter `sleep = random(0, min(cap, base*2**attempt))` reduces contention and total time vs un-jittered backoff; equal and decorrelated jitter are alternatives. <https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/>
- WebSocket.org, WebSocket Authentication: the handshake authenticates only at connect time; refresh a long-lived token in-band (push a fresh token over the open socket) or by reconnecting, and define an explicit reauth-required signal since there is no built-in auth-expired response. <https://websocket.org/guides/authentication/>

## Evidence framing

- Treat code-search hits as leads, not findings. Show the concrete symptom (herd, dropped/duplicated event, corrupted state, frozen UI, memory/close, message on an expired token) and the code path that produces it.
- Before claiming a gap, check whether a client library (Socket.IO, Phoenix Channels, Ably, Pusher, `@microsoft/signalr`) already owns backoff+jitter, resume, and heartbeat via config.
- `bufferedAmount` used as a pacing gate is a positive control, not a defect. Server-side pings + browser auto-pong is a valid liveness design from the client's side.
- Distinguish "no resume" (missed/duplicated events) from "no dedupe/order" (mis-applied deltas) — they are separate contracts and separate fixes.

## Test shapes

- Reconnect/resume: open, receive up to seq N, drop the socket mid-stream, reconnect; assert the client re-subscribes, sends `Last-Event-ID`/cursor = N, and converges with no gap and no duplicate.
- Backoff: assert delays grow, cap, carry jitter (not constant), and the attempt counter resets only after a stability window — not on `open`.
- Close handling: a 1008/4xxx auth close does not schedule a retry; a 1006/1011 does.
- Delta folding: feed duplicated, reordered, and gapped sequences; assert idempotent apply, reorder buffering, and resync (not silent skip) on an unfillable gap.
- Liveness: stop pongs; assert the heartbeat timeout closes and reconnects; a backgrounded/offline tab does not spin.
- Auth: advance to just before token expiry; assert an in-band refresh (or reconnect) keeps the stream alive and no message is processed on an expired token.
