#!/usr/bin/env node

const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');

function loadPlaywright() {
  const cli = process.env.PLAYWRIGHT_CLI;
  if (!cli) throw new Error('PLAYWRIGHT_CLI is required');
  const packageRoot = path.dirname(fs.realpathSync(cli));
  return require(packageRoot);
}

const fixtureHtml = String.raw`<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Same-document history restoration fixture</title>
  <style>
    html, body { margin: 0; }
    #route { min-height: 1px; }
    .skeleton { height: 120px; background: #eee; }
    .async-content { height: 2800px; background: linear-gradient(#fff, #ddd); }
  </style>
</head>
<body>
  <main id="route"></main>
  <script>
  (() => {
    history.scrollRestoration = 'manual';

    const route = document.querySelector('#route');
    const documentToken = crypto.randomUUID();
    const positions = new Map();
    const state = {
      documentToken,
      pageShows: [],
      layoutReadySignals: 0,
      popEntries: [],
      writes: [],
      stableSamples: [],
    };

    addEventListener('pageshow', (event) => {
      state.pageShows.push({ persisted: event.persisted, documentToken });
    });

    const nextFrame = () => new Promise((resolve) => requestAnimationFrame(resolve));

    function renderReady(routeName) {
      route.innerHTML = '<section class="async-content" data-route="' + routeName
        + '" data-layout-ready="true"></section>';
    }

    async function renderAfterAsyncLayout(routeName, entryKey) {
      route.innerHTML = '<section class="skeleton" data-route="' + routeName
        + '" data-entry="' + entryKey + '" data-layout-ready="false"></section>';
      const maximumBeforeReady = Math.max(
        0,
        document.documentElement.scrollHeight - innerHeight,
      );

      await nextFrame();
      renderReady(routeName);
      state.layoutReadySignals += 1;
      return maximumBeforeReady;
    }

    function saveCurrentEntry() {
      const key = history.state?.entryKey;
      if (key) positions.set(key, scrollY);
    }

    async function restoreEntry(entryState) {
      const savedOffset = positions.get(entryState.entryKey);
      assertFinite(savedOffset, 'missing saved offset for ' + entryState.entryKey);
      const maximumBeforeReady = await renderAfterAsyncLayout(
        entryState.route,
        entryState.entryKey,
      );
      const readyBeforeWrite =
        route.firstElementChild?.dataset.layoutReady === 'true';

      scrollTo(0, savedOffset);
      const appliedOffset = scrollY;
      state.writes.push({
        entryKey: entryState.entryKey,
        url: location.pathname + location.search + location.hash,
        savedOffset,
        appliedOffset,
        maximumBeforeReady,
        readyBeforeWrite,
      });

      await nextFrame();
      const firstFinalFrame = scrollY;
      await nextFrame();
      const secondFinalFrame = scrollY;
      state.stableSamples.push({
        entryKey: entryState.entryKey,
        appliedOffset,
        firstFinalFrame,
        secondFinalFrame,
      });
      dispatchEvent(new CustomEvent('fixture-restored', {
        detail: { entryKey: entryState.entryKey },
      }));
    }

    function assertFinite(value, message) {
      if (!Number.isFinite(value)) throw new Error(message);
    }

    addEventListener('popstate', (event) => {
      const entryState = event.state;
      state.popEntries.push({
        entryKey: entryState?.entryKey,
        route: entryState?.route,
        documentToken,
      });
      restoreEntry(entryState).catch((error) => {
        window.__fixtureError = error.stack || String(error);
      });
    });

    async function setEntryPosition(offset) {
      scrollTo(0, offset);
      await nextFrame();
      positions.set(history.state.entryKey, scrollY);
    }

    async function pushEntry(routeName, entryKey, offset) {
      saveCurrentEntry();
      history.pushState(
        { route: routeName, entryKey },
        '',
        '/history?route=' + routeName,
      );
      renderReady(routeName);
      await setEntryPosition(offset);
    }

    function traverse(delta) {
      return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error(window.__fixtureError || 'history traversal timeout'));
        }, 5000);
        addEventListener('fixture-restored', (event) => {
          clearTimeout(timeout);
          resolve(event.detail);
        }, { once: true });
        history.go(delta);
      });
    }

    history.replaceState(
      { route: 'a', entryKey: 'route-a:first' },
      '',
      '/history?route=a',
    );
    renderReady('a');

    window.contract = {
      async run() {
        await setEntryPosition(620);
        await pushEntry('b', 'route-b:only', 80);
        await pushEntry('a', 'route-a:second', 1180);

        await traverse(-1);
        await traverse(-1);
        await traverse(1);
        await traverse(1);

        const firstA = state.writes.find((write) => write.entryKey === 'route-a:first');
        const secondA = state.writes.find((write) => write.entryKey === 'route-a:second');
        const noSecondJump = state.stableSamples.every((sample) =>
          sample.appliedOffset === sample.firstFinalFrame
          && sample.firstFinalFrame === sample.secondFinalFrame
        );
        const readyBeforeEveryWrite = state.writes.every((write) =>
          write.readyBeforeWrite
          && write.maximumBeforeReady < write.savedOffset
          && write.appliedOffset === write.savedOffset
        );
        const bfcacheResumes = state.pageShows.filter((event) => event.persisted).length;
        const sameDocumentOnly =
          performance.getEntriesByType('navigation').length === 1
          && state.pageShows.length === 1
          && bfcacheResumes === 0
          && state.popEntries.every((entry) => entry.documentToken === documentToken);

        return {
          status: 'pass',
          entrySpecific:
            firstA?.url === secondA?.url
            && firstA?.savedOffset === 620
            && secondA?.savedOffset === 1180,
          readyBeforeEveryWrite,
          noSecondJump,
          sameDocumentOnly,
          bfcacheResumes,
          layoutReadySignals: state.layoutReadySignals,
          writes: state.writes,
          stableSamples: state.stableSamples,
          popEntries: state.popEntries,
        };
      },
    };
  })();
  </script>
</body>
</html>`;

function startServer() {
  const server = http.createServer((request, response) => {
    if (request.url?.startsWith('/history')) {
      response.writeHead(200, {
        'Content-Type': 'text/html; charset=utf-8',
        'Cache-Control': 'no-store',
      });
      response.end(fixtureHtml);
      return;
    }
    response.writeHead(404);
    response.end('not found');
  });

  return new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', () => resolve(server));
  });
}

async function main() {
  const browserName = process.argv[2] || 'chromium';
  const playwright = loadPlaywright();
  const browserType = playwright[browserName];
  if (!['chromium', 'firefox', 'webkit'].includes(browserName) || !browserType) {
    throw new Error(`unsupported Playwright browser engine: ${browserName}`);
  }
  const server = await startServer();
  const address = server.address();
  let browser;

  try {
    browser = await browserType.launch({ headless: true });
    const page = await browser.newPage({ viewport: { width: 900, height: 700 } });
    await page.goto(`http://127.0.0.1:${address.port}/history`, {
      waitUntil: 'load',
    });
    const payload = await page.evaluate(() => window.contract.run());
    payload.browserName = browserName;

    assert.equal(payload.browserName, browserName);
    assert.equal(payload.entrySpecific, true);
    assert.equal(payload.readyBeforeEveryWrite, true);
    assert.equal(payload.noSecondJump, true);
    assert.equal(payload.sameDocumentOnly, true);
    assert.equal(payload.bfcacheResumes, 0);
    assert.equal(payload.layoutReadySignals, 4);
    assert.deepEqual(
      payload.writes.map(({ entryKey, savedOffset }) => [entryKey, savedOffset]),
      [
        ['route-b:only', 80],
        ['route-a:first', 620],
        ['route-b:only', 80],
        ['route-a:second', 1180],
      ],
    );
    process.stdout.write(`${JSON.stringify(payload)}\n`);
  } finally {
    if (browser) await browser.close();
    await new Promise((resolve, reject) => {
      server.close((error) => error ? reject(error) : resolve());
    });
  }
}

main().catch((error) => {
  console.error(error.stack || error);
  process.exitCode = 1;
});
