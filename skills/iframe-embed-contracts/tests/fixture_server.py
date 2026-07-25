#!/usr/bin/env python3
"""Serve a parent and guest on distinct origins for the iframe contract smoke test."""

from __future__ import annotations

import json
import signal
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


PARENT_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Iframe contract parent fixture</title>
  <style>iframe { display: block; width: 420px; border: 0; }</style>
</head>
<body>
  <pre id="result" data-status="running">running</pre>
  <script>
  (() => {
    const guestOrigin = __GUEST_ORIGIN_JSON__;
    const blockedExpected = new URLSearchParams(location.search).get('expect') === 'blocked';
    const result = document.querySelector('#result');
    const instanceId = 'fixture-main';
    const state = {
      acceptedReady: 0,
      acceptedResize: 0,
      ackCount: 0,
      initSent: 0,
      rejected: 0,
      seen: 0,
      lastSeq: -1,
      maxAppliedHeight: 0,
      finalHeight: 0,
      crossOriginBlocked: false,
      titlePresent: false,
      teardownSilent: false,
    };

    const finish = (status, details = {}) => {
      document.documentElement.dataset.status = status;
      result.dataset.status = status;
      result.textContent = JSON.stringify({ status, ...state, ...details });
    };

    const frame = document.createElement('iframe');
    frame.title = 'Cross-origin contract fixture';
    frame.style.height = '120px';
    frame.sandbox = 'allow-scripts allow-same-origin';
    document.body.append(frame);

    const attacker = document.createElement('iframe');
    attacker.hidden = true;
    attacker.title = 'Wrong source fixture';
    attacker.sandbox = 'allow-scripts allow-same-origin';
    document.body.append(attacker);

    let cleanupStarted = false;
    const validEnvelope = (data) => data && data.protocol === 'fixture-embed'
      && data.version === 1 && data.instanceId === instanceId
      && typeof data.type === 'string';

    const onMessage = (event) => {
      state.seen += 1;
      const data = event.data;
      if (event.origin !== guestOrigin || event.source !== frame.contentWindow || !validEnvelope(data)) {
        state.rejected += 1;
        return;
      }

      if (data.type === 'READY') {
        state.acceptedReady += 1;
        if (state.initSent === 0) {
          frame.contentWindow.postMessage({
            protocol: 'fixture-embed', version: 1, instanceId, type: 'INIT', payload: { theme: 'dark' },
          }, guestOrigin);
          state.initSent += 1;
        }
      } else if (data.type === 'ACK') {
        state.ackCount += 1;
      } else if (data.type === 'RESIZE' && Number.isFinite(data.seq) && Number.isFinite(data.height)) {
        if (data.seq > state.lastSeq) {
          state.lastSeq = data.seq;
          const bounded = Math.max(80, Math.min(500, Math.round(data.height)));
          frame.style.height = `${bounded}px`;
          state.acceptedResize += 1;
          state.finalHeight = bounded;
          state.maxAppliedHeight = Math.max(state.maxAppliedHeight, bounded);
        }
      } else {
        state.rejected += 1;
      }
    };

    window.addEventListener('message', onMessage);
    const parentOrigin = location.origin;
    frame.src = `${guestOrigin}/guest?mode=main&parent=${encodeURIComponent(parentOrigin)}&instance=${instanceId}`;
    attacker.src = `${guestOrigin}/guest?mode=attacker&parent=${encodeURIComponent(parentOrigin)}&instance=${instanceId}`;

    if (blockedExpected) {
      setTimeout(() => {
        window.removeEventListener('message', onMessage);
        if (state.acceptedReady === 0 && state.initSent === 0) {
          finish('pass', { frameAncestorsBlocked: true });
        } else {
          finish('fail', { reason: 'disallowed parent received guest messages' });
        }
      }, 900);
      return;
    }

    // A real same-window postMessage has the parent origin/source and must be rejected.
    window.postMessage({ protocol: 'fixture-embed', version: 1, instanceId, type: 'READY' }, parentOrigin);

    const poll = setInterval(() => {
      try {
        void frame.contentWindow.document;
      } catch {
        state.crossOriginBlocked = true;
      }
      state.titlePresent = frame.title === 'Cross-origin contract fixture';

      const contractPassed = state.acceptedReady >= 2
        && state.initSent === 1
        && state.ackCount === 1
        && state.rejected >= 3
        && state.acceptedResize >= 3
        && state.maxAppliedHeight === 500
        && state.finalHeight === 180
        && state.crossOriginBlocked
        && state.titlePresent;

      if (!contractPassed || cleanupStarted) return;
      cleanupStarted = true;
      clearInterval(poll);
      window.removeEventListener('message', onMessage);
      frame.remove();
      const seenBeforeTeardownProbe = state.seen;
      attacker.contentWindow.postMessage({ type: 'POST_AFTER_TEARDOWN' }, guestOrigin);
      setTimeout(() => {
        state.teardownSilent = state.seen === seenBeforeTeardownProbe;
        if (state.teardownSilent) finish('pass');
        else finish('fail', { reason: 'message listener survived teardown' });
      }, 120);
    }, 25);

    setTimeout(() => {
      if (result.dataset.status === 'running') {
        clearInterval(poll);
        window.removeEventListener('message', onMessage);
        finish('fail', { reason: 'contract timeout' });
      }
    }, 3500);
  })();
  </script>
</body>
</html>
"""


GUEST_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Iframe contract guest fixture</title>
  <style>html, body { margin: 0; } #content { width: 100%; height: 120px; }</style>
</head>
<body>
  <div id="content">guest</div>
  <script>
  (() => {
    const params = new URLSearchParams(location.search);
    const parentOrigin = params.get('parent');
    const instanceId = params.get('instance');
    const mode = params.get('mode');
    const envelope = (type, extra = {}) => ({
      protocol: 'fixture-embed', version: 1, instanceId, type, ...extra,
    });
    const send = (type, extra) => parent.postMessage(envelope(type, extra), parentOrigin);

    if (mode === 'attacker') {
      setTimeout(() => send('READY'), 35);
      addEventListener('message', (event) => {
        if (event.origin === parentOrigin && event.source === parent && event.data?.type === 'POST_AFTER_TEARDOWN') {
          send('READY');
        }
      });
      return;
    }

    let initCount = 0;
    addEventListener('message', (event) => {
      const data = event.data;
      if (event.origin !== parentOrigin || event.source !== parent) return;
      if (!data || data.protocol !== 'fixture-embed' || data.version !== 1
          || data.instanceId !== instanceId || data.type !== 'INIT') return;
      initCount += 1;
      send('ACK', { initCount });
    });

    // READY is replayed; the parent must still initialize only once.
    send('READY');
    setTimeout(() => send('READY'), 60);
    setTimeout(() => parent.postMessage({ protocol: 'wrong', type: 'READY' }, parentOrigin), 80);

    let seq = 0;
    const content = document.querySelector('#content');
    const observer = new ResizeObserver((entries) => {
      seq += 1;
      const entry = entries[0];
      const borderBox = entry.borderBoxSize?.[0];
      const height = borderBox?.blockSize ?? entry.contentRect.height;
      send('RESIZE', { seq, height });
    });
    observer.observe(content);
    setTimeout(() => { content.style.height = '640px'; }, 120);
    setTimeout(() => { content.style.height = '180px'; }, 240);
  })();
  </script>
</body>
</html>
"""


class FixtureHandler(BaseHTTPRequestHandler):
    server_version = "IframeContractFixture/1.0"

    def log_message(self, _format: str, *_args: object) -> None:
        return

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        parsed = urlparse(self.path)
        if self.server.role == "parent" and parsed.path in {"/", "/parent"}:
            body = PARENT_HTML.replace("__GUEST_ORIGIN_JSON__", json.dumps(self.server.guest_origin))
            self._send(200, body, "text/html; charset=utf-8")
            return
        if self.server.role == "guest" and parsed.path == "/guest":
            # Parsing here ensures malformed fixture URLs fail rather than silently weakening the test.
            query = parse_qs(parsed.query)
            if not {"mode", "parent", "instance"}.issubset(query):
                self._send(400, "missing fixture query", "text/plain; charset=utf-8")
                return
            headers = {
                "Content-Security-Policy": f"frame-ancestors {self.server.allowed_parent_origin}",
                "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
                "Cache-Control": "no-store",
            }
            self._send(200, GUEST_HTML, "text/html; charset=utf-8", headers)
            return
        self._send(404, "not found", "text/plain; charset=utf-8")

    def _send(self, status: int, body: str, content_type: str, headers: dict[str, str] | None = None) -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(encoded)


def make_server(role: str) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
    server.role = role
    return server


def main() -> None:
    guest = make_server("guest")
    parent = make_server("parent")
    parent_origin = f"http://127.0.0.1:{parent.server_port}"
    guest_origin = f"http://127.0.0.1:{guest.server_port}"
    parent.guest_origin = guest_origin
    guest.allowed_parent_origin = parent_origin

    threads = [
        threading.Thread(target=server.serve_forever, daemon=True)
        for server in (guest, parent)
    ]
    for thread in threads:
        thread.start()

    print(json.dumps({
        "allowed_url": f"{parent_origin}/parent",
        "blocked_url": f"http://localhost:{parent.server_port}/parent?expect=blocked",
        "guest_url": f"{guest_origin}/guest",
    }), flush=True)

    stopped = threading.Event()

    def stop(_signum: int, _frame: object) -> None:
        stopped.set()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    stopped.wait()
    for server in (guest, parent):
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
