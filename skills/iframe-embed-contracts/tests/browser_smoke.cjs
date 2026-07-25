#!/usr/bin/env node

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

function loadPlaywright() {
  const cli = process.env.PLAYWRIGHT_CLI;
  if (!cli) throw new Error('PLAYWRIGHT_CLI is required');
  const packageRoot = path.dirname(fs.realpathSync(cli));
  return require(packageRoot);
}

async function readResult(page, url) {
  await page.goto(url, { waitUntil: 'domcontentloaded' });
  const result = page.locator('#result');
  await result.waitFor({ state: 'attached' });
  await page.waitForFunction(() => {
    const node = document.querySelector('#result');
    return node?.dataset.status === 'pass' || node?.dataset.status === 'fail';
  }, null, { timeout: 6_000 });
  const status = await result.getAttribute('data-status');
  const payload = JSON.parse(await result.textContent());
  assert.equal(status, 'pass', JSON.stringify(payload));
  assert.equal(payload.status, 'pass');
  return payload;
}

async function main() {
  const [, , infoPath, mode] = process.argv;
  if (!infoPath || !['allowed', 'blocked'].includes(mode)) {
    throw new Error('usage: browser_smoke.cjs <server-info.json> <allowed|blocked>');
  }

  const info = JSON.parse(fs.readFileSync(infoPath, 'utf8'));
  const { chromium } = loadPlaywright();
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage();
    const payload = await readResult(page, mode === 'allowed' ? info.allowed_url : info.blocked_url);
    if (mode === 'allowed') {
      assert.equal(payload.initSent, 1);
      assert.equal(payload.ackCount, 1);
      assert.ok(payload.acceptedReady >= 2);
      assert.ok(payload.rejected >= 3);
      assert.equal(payload.maxAppliedHeight, 500);
      assert.equal(payload.finalHeight, 180);
      assert.equal(payload.crossOriginBlocked, true);
      assert.equal(payload.titlePresent, true);
      assert.equal(payload.teardownSilent, true);
    } else {
      assert.equal(payload.frameAncestorsBlocked, true);
      assert.equal(payload.acceptedReady, 0);
      assert.equal(payload.initSent, 0);
    }
    process.stdout.write(`${JSON.stringify(payload)}\n`);
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error.stack || error);
  process.exitCode = 1;
});
