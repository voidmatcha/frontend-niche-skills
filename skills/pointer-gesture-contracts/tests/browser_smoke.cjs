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
  <title>Pointer ownership fixture</title>
  <style>
    body { margin: 0; min-height: 900px; }
    #blocker { width: 260px; height: 180px; padding: 20px; background: #eee; }
    #handle { width: 44px; height: 44px; background: #2563eb; touch-action: pan-y pinch-zoom; }
    #handle.active { background: #dc2626; }
  </style>
</head>
<body>
  <div id="blocker"><div id="handle"></div></div>
  <script>
  (() => {
    const handle = document.querySelector('#handle');
    const blocker = document.querySelector('#blocker');
    const state = {
      activeId: null,
      moves: 0,
      blockerStops: 0,
      documentBubbleEvents: 0,
      gotCapture: 0,
      terminals: [],
      commits: 0,
      cancels: 0,
      pointerObservations: [],
    };

    function cleanup(reason, commit) {
      if (state.activeId === null) return;
      const pointerId = state.activeId;
      state.activeId = null;
      handle.classList.remove('active');
      state.terminals.push(reason);
      if (commit) state.commits += 1;
      else state.cancels += 1;
      if (reason !== 'lostpointercapture' && handle.hasPointerCapture(pointerId)) {
        handle.releasePointerCapture(pointerId);
      }
    }

    handle.addEventListener('pointerdown', (event) => {
      if (event.button !== 0 || state.activeId !== null) return;
      state.pointerObservations.push({
        phase: 'down',
        pointerType: event.pointerType,
        isTrusted: event.isTrusted,
      });
      state.activeId = event.pointerId;
      handle.classList.add('active');
      handle.setPointerCapture(event.pointerId);
    });
    handle.addEventListener('gotpointercapture', () => {
      state.gotCapture += 1;
    });
    handle.addEventListener('pointermove', (event) => {
      if (event.pointerId !== state.activeId) return;
      if (event.buttons === 0) {
        cleanup('zero-buttons', false);
        return;
      }
      state.moves += 1;
    });
    handle.addEventListener('pointerup', (event) => {
      if (event.pointerId === state.activeId) {
        state.pointerObservations.push({
          phase: 'up',
          pointerType: event.pointerType,
          isTrusted: event.isTrusted,
        });
        cleanup('pointerup', true);
      }
    });
    handle.addEventListener('pointercancel', (event) => {
      if (event.pointerId === state.activeId) cleanup('pointercancel', false);
    });
    handle.addEventListener('lostpointercapture', (event) => {
      if (event.pointerId === state.activeId) cleanup('lostpointercapture', false);
    });

    for (const type of ['pointermove', 'pointerup', 'pointercancel']) {
      blocker.addEventListener(type, (event) => {
        state.blockerStops += 1;
        event.stopPropagation();
      });
      document.addEventListener(type, () => {
        state.documentBubbleEvents += 1;
      });
    }

    window.contract = {
      snapshot() {
        return {
          ...state,
          active: handle.classList.contains('active'),
          hasCapture: state.activeId !== null
            && handle.hasPointerCapture(state.activeId),
        };
      },
      activePointerId() {
        return state.activeId;
      },
      dispatchTerminal(type, buttons = 0) {
        const pointerId = state.activeId;
        if (pointerId === null) throw new Error('no active pointer');
        handle.dispatchEvent(new PointerEvent(type, {
          bubbles: true,
          pointerId,
          pointerType: 'mouse',
          button: type === 'pointermove' ? -1 : 0,
          buttons,
        }));
      },
      releaseCapture() {
        const pointerId = state.activeId;
        if (pointerId === null) throw new Error('no active pointer');
        handle.releasePointerCapture(pointerId);
      },
    };
  })();
  </script>
</body>
</html>`;

function startServer() {
  const server = http.createServer((request, response) => {
    if (request.url === '/pointer') {
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

async function startPointer(page) {
  const box = await page.locator('#handle').boundingBox();
  assert.ok(box);
  const capturesBefore = await page.evaluate(() =>
    window.contract.snapshot().gotCapture
  );
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.mouse.down();
  await page.mouse.move(box.x + box.width / 2 + 2, box.y + box.height / 2);
  await page.waitForFunction((before) =>
    window.contract.snapshot().hasCapture
      && window.contract.snapshot().gotCapture > before
  , capturesBefore);
  return box;
}

function assertCleanTerminal(snapshot, reason, expectedCommits, expectedCancels) {
  assert.equal(snapshot.active, false);
  assert.equal(snapshot.hasCapture, false);
  assert.equal(snapshot.activeId, null);
  assert.equal(snapshot.terminals.at(-1), reason);
  assert.equal(snapshot.commits, expectedCommits);
  assert.equal(snapshot.cancels, expectedCancels);
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
    const context = await browser.newContext({
      viewport: { width: 900, height: 700 },
    });
    const page = await context.newPage();
    await page.goto(`http://127.0.0.1:${address.port}/pointer`, {
      waitUntil: 'load',
    });

    const handleBox = await startPointer(page);
    await page.mouse.move(handleBox.x + 620, handleBox.y + 400, { steps: 4 });
    await page.mouse.up();
    const afterUp = await page.evaluate(() => window.contract.snapshot());
    assertCleanTerminal(afterUp, 'pointerup', 1, 0);
    assert.ok(afterUp.moves > 0);
    assert.ok(afterUp.blockerStops > 0);
    assert.equal(afterUp.documentBubbleEvents, 0);

    await startPointer(page);
    await page.evaluate(() => window.contract.dispatchTerminal('pointercancel'));
    await page.mouse.up();
    const afterCancel = await page.evaluate(() => window.contract.snapshot());
    assertCleanTerminal(afterCancel, 'pointercancel', 1, 1);

    const captureLossBox = await startPointer(page);
    await page.evaluate(() => window.contract.releaseCapture());
    await page.mouse.move(
      captureLossBox.x + captureLossBox.width / 2 + 4,
      captureLossBox.y + captureLossBox.height / 2,
    );
    await page.waitForFunction(() =>
      window.contract.snapshot().terminals.at(-1) === 'lostpointercapture'
    );
    await page.mouse.up();
    const afterCaptureLoss = await page.evaluate(() => window.contract.snapshot());
    assertCleanTerminal(afterCaptureLoss, 'lostpointercapture', 1, 2);

    await startPointer(page);
    await page.evaluate(() => window.contract.dispatchTerminal('pointermove', 0));
    await page.mouse.up();
    const afterZeroButtons = await page.evaluate(() => window.contract.snapshot());
    assertCleanTerminal(afterZeroButtons, 'zero-buttons', 1, 3);

    const touchContext = await browser.newContext({
      viewport: { width: 900, height: 700 },
      hasTouch: true,
    });
    const touchPage = await touchContext.newPage();
    await touchPage.goto(`http://127.0.0.1:${address.port}/pointer`, {
      waitUntil: 'load',
    });
    const touchBox = await touchPage.locator('#handle').boundingBox();
    assert.ok(touchBox);
    await touchPage.touchscreen.tap(
      touchBox.x + touchBox.width / 2,
      touchBox.y + touchBox.height / 2,
    );
    const afterTouchTap = await touchPage.evaluate(() => window.contract.snapshot());
    assertCleanTerminal(afterTouchTap, 'pointerup', 1, 0);
    const trustedMouseBoundaryDrag =
      afterUp.pointerObservations.length === 2
      && afterUp.pointerObservations.every((observation) =>
        observation.pointerType === 'mouse'
        && observation.isTrusted === true
      )
      && afterUp.pointerObservations[0].phase === 'down'
      && afterUp.pointerObservations[1].phase === 'up'
      && afterUp.moves > 0
      && afterUp.blockerStops > 0;
    const emulatedTouchTap =
      afterTouchTap.pointerObservations.length === 2
      && afterTouchTap.pointerObservations.every((observation) =>
        observation.pointerType === 'touch'
        && observation.isTrusted === true
      )
      && afterTouchTap.pointerObservations[0].phase === 'down'
      && afterTouchTap.pointerObservations[1].phase === 'up';
    await touchContext.close();

    const payload = {
      status: 'pass',
      browserName,
      emulatedTouchTap,
      deliveryPastBlocker:
        afterUp.moves > 0
        && afterUp.blockerStops > 0
        && afterUp.documentBubbleEvents === 0,
      captureObserved: afterZeroButtons.gotCapture === 4,
      allTerminalPathsClean:
        afterZeroButtons.terminals.join(',') ===
          'pointerup,pointercancel,lostpointercapture,zero-buttons'
        && afterZeroButtons.commits === 1
        && afterZeroButtons.cancels === 3
        && afterZeroButtons.active === false
        && afterZeroButtons.hasCapture === false,
      coverage: {
        trustedMouseBoundaryDrag,
        syntheticPointerCancel: true,
        programmaticCaptureLoss: true,
        syntheticZeroButtonsRecovery: true,
        emulatedTouchTap: true,
        emulatedTouchDrag: false,
        physicalTouch: false,
        physicalPen: false,
        pressure: false,
        osGestureArbitration: false,
      },
      emulatedTouch: afterTouchTap,
      final: afterZeroButtons,
    };

    assert.equal(payload.browserName, browserName);
    assert.equal(payload.coverage.trustedMouseBoundaryDrag, true);
    assert.equal(payload.emulatedTouchTap, true);
    assert.equal(payload.deliveryPastBlocker, true);
    assert.equal(payload.captureObserved, true);
    assert.equal(payload.allTerminalPathsClean, true);
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
