#!/usr/bin/env node
// render-capture.mjs — screenshot a rendered web page as the implementation image for
// design-to-code comparison.
//
// Usage: node render-capture.mjs <url> <out.png> [width=360] [height=780] [scale=2]
// Env:
//   CAPTURE_MODE=viewport|fullPage        Default: viewport
//   ALLOW_ANIMATION=1                     Preserve motion: skip the animation/transition kill switch
//                                         so CSS animations/transitions keep running. The ONLY switch
//                                         that keeps motion — set it for dynamic/transition-fidelity
//                                         capture; leave unset for deterministic static parity.
//   INIT_SCRIPT='<js>'                    Runs before app scripts; useful for Date/time fixtures.
//   NEUTRALIZE_CSS='<css>'                Injected before screenshot.
//   WAIT_FOR_SELECTOR='<selector>'        Wait until selector is visible/attached.
//   WAIT_FOR_TEXT='<text>'                Wait until text appears in body.
//   WAIT_UNTIL=load|domcontentloaded|networkidle|commit  Default: load
//   WAIT_TIMEOUT_MS=30000                 Navigation/wait timeout.
//   EXTRA_WAIT_MS=0                       Last-resort post-ready delay.
//   STORAGE_STATE=/path/state.json        Playwright storageState.
//   LOCALE=en-US                          Browser locale.
//   TIMEZONE_ID=Asia/Seoul                Browser timezone.
//   COLOR_SCHEME=light|dark|no-preference Browser color scheme.
//   REDUCED_MOTION=reduce|no-preference   Browser reduced motion.

import { createRequire } from 'node:module';
import fs from 'node:fs/promises';
import path from 'node:path';

const [url, out, w = '360', h = '780', scale = '2'] = process.argv.slice(2);
if (!url || !out) {
  console.error('Usage: node render-capture.mjs <url> <out.png> [width] [height] [scale]');
  process.exit(2);
}

const [W, H, S] = [w, h, scale].map(Number);
if (![W, H, S].every((n) => Number.isFinite(n) && n > 0)) {
  console.error('ERROR: width/height/scale must be positive numbers');
  process.exit(2);
}

const captureMode = process.env.CAPTURE_MODE || 'viewport';
if (!['viewport', 'fullPage'].includes(captureMode)) {
  console.error('ERROR: CAPTURE_MODE must be viewport or fullPage');
  process.exit(2);
}

const timeout = Number(process.env.WAIT_TIMEOUT_MS || 30000);
if (!Number.isFinite(timeout) || timeout <= 0) {
  console.error('ERROR: WAIT_TIMEOUT_MS must be a positive number');
  process.exit(2);
}

const requireFromCwd = createRequire(path.join(process.cwd(), 'package.json'));
let chromium;
for (const pkg of ['@playwright/test', 'playwright']) {
  try {
    const mod = await import(requireFromCwd.resolve(pkg));
    chromium = mod.chromium ?? mod.default?.chromium;
    if (chromium) break;
  } catch {
    // try next package
  }
}
if (!chromium) {
  console.error('ERROR: @playwright/test (or playwright) not installed in cwd');
  process.exit(2);
}

const contextOptions = {
  viewport: { width: W, height: H },
  deviceScaleFactor: S,
  ignoreHTTPSErrors: true,
};

if (process.env.STORAGE_STATE) contextOptions.storageState = process.env.STORAGE_STATE;
if (process.env.LOCALE) contextOptions.locale = process.env.LOCALE;
if (process.env.TIMEZONE_ID) contextOptions.timezoneId = process.env.TIMEZONE_ID;
if (process.env.COLOR_SCHEME) contextOptions.colorScheme = process.env.COLOR_SCHEME;
if (process.env.REDUCED_MOTION) contextOptions.reducedMotion = process.env.REDUCED_MOTION;

const browser = await chromium.launch();
try {
  const ctx = await browser.newContext(contextOptions);
  const page = await ctx.newPage();
  page.setDefaultTimeout(timeout);
  page.setDefaultNavigationTimeout(timeout);

  if (process.env.INIT_SCRIPT) {
    await page.addInitScript({ content: process.env.INIT_SCRIPT });
  }

  const waitUntil = process.env.WAIT_UNTIL || 'load';
  await page.goto(url, { waitUntil, timeout });

  if (process.env.WAIT_FOR_SELECTOR) {
    await page.waitForSelector(process.env.WAIT_FOR_SELECTOR, { timeout });
  }
  if (process.env.WAIT_FOR_TEXT) {
    const escaped = JSON.stringify(process.env.WAIT_FOR_TEXT);
    await page.waitForFunction(
      `document.body && document.body.innerText.includes(${escaped})`,
      null,
      { timeout },
    );
  }

  // Disable CSS animations/transitions after app load unless the test intentionally captures motion.
  if (!process.env.ALLOW_ANIMATION) {
    await page.addStyleTag({
      content: '*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important}',
    });
  }
  if (process.env.NEUTRALIZE_CSS) {
    await page.addStyleTag({ content: process.env.NEUTRALIZE_CSS });
  }

  // Let web fonts settle when available; otherwise continue without failing older browsers.
  await page.evaluate(async () => {
    if (document.fonts?.ready) await document.fonts.ready;
  });

  const extraWait = Number(process.env.EXTRA_WAIT_MS || 0);
  if (extraWait > 0) await page.waitForTimeout(extraWait);

  await fs.mkdir(path.dirname(path.resolve(out)), { recursive: true });
  await page.screenshot({ path: out, fullPage: captureMode === 'fullPage' });
  console.log(`saved ${out} (${W}x${H}@${S}, mode=${captureMode})`);
} finally {
  await browser.close();
}
