/* Run after scripts/preview_mandarin_card.py. Requires Playwright + Chromium.
 * NODE_PATH may point to an existing Playwright installation.
 * Usage: node tests/browser/mandarin_interaction.cjs [preview-directory]
 */
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { chromium } = require('playwright');

const directory = path.resolve(process.argv[2] || 'output/previews/mandarin');
const colors = {
  1: 'rgb(255, 133, 145)', 2: 'rgb(241, 209, 120)', 3: 'rgb(130, 219, 171)',
  4: 'rgb(142, 186, 255)', 5: 'rgb(193, 199, 211)',
};

(async () => {
  const browser = await chromium.launch({ headless: true });
  const results = [];
  try {
    for (const width of [1280, 390, 320]) {
      const page = await browser.newPage({ viewport: { width, height: 950 } });
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await page.route(/^https?:/, route => {
        errors.push(`Unexpected network request: ${route.request().url()}`);
        return route.abort();
      });
      for (const side of ['front', 'back']) {
        await page.goto(pathToFileURL(path.join(directory, `${side}.html`)).href);
        await page.evaluate(() => document.fonts.ready);
        const readings = page.locator('.exampleSentenceText .mandarin-ruby');
        const first = readings.first();
        const opacities = () => readings.locator('rt').evaluateAll(
          nodes => nodes.map(node => getComputedStyle(node).opacity),
        );
        assert.equal(await readings.count(), 8);
        assert.deepEqual(await opacities(), Array(8).fill('1'), 'All pinyin starts visible');
        const before = await page.locator('.exampleSentenceText').boundingBox();
        await first.hover();
        assert.deepEqual(await opacities(), Array(8).fill('1'), 'Hover keeps every reading visible');
        assert.equal(await first.locator('rt').textContent(), 'tā');
        assert.deepEqual(await page.locator('.exampleSentenceText').boundingBox(), before, 'No layout shift');
        await page.screenshot({ path: path.join(directory, `${side}-hover-${width}.png`), fullPage: true });
        await page.mouse.move(0, 0);
        assert.deepEqual(await opacities(), Array(8).fill('1'), 'Pinyin stays visible on mouse leave');
        const palette = await first.evaluate(node => {
          const sample = node.cloneNode(true);
          node.parentNode.append(sample);
          const result = {};
          for (let tone = 1; tone <= 5; tone++) {
            sample.className = `mandarin-ruby tone-${tone}`;
            result[tone] = getComputedStyle(sample).color;
            if (getComputedStyle(sample.querySelector('rt')).color !== result[tone]) {
              throw new Error('Pinyin and character colors differ');
            }
          }
          sample.remove();
          return result;
        });
        assert.deepEqual(palette, colors);
        assert.equal(await page.locator('#translation').isVisible(), side === 'back');
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
        await page.screenshot({ path: path.join(directory, `${side}-${width}.png`), fullPage: true });
        results.push({ width, side, pinyinAlwaysVisible: true, colors: palette });
      }
      assert.deepEqual(errors, []);
      await page.close();
    }
    const touch = await browser.newPage({ viewport: { width: 390, height: 950 }, hasTouch: true });
    await touch.goto(pathToFileURL(path.join(directory, 'front.html')).href);
    const tapped = touch.locator('.mandarin-ruby').first();
    assert.equal(await tapped.locator('rt').evaluate(node => getComputedStyle(node).opacity), '1');
    await tapped.tap();
    assert.equal(await tapped.locator('rt').evaluate(node => getComputedStyle(node).opacity), '1');
    await touch.locator('.header').first().tap();
    assert.equal(await tapped.locator('rt').evaluate(node => getComputedStyle(node).opacity), '1');
    await touch.close();
    const noScript = await browser.newPage({ javaScriptEnabled: false });
    await noScript.goto(pathToFileURL(path.join(directory, 'front.html')).href);
    assert.deepEqual(await noScript.locator('.mandarin-ruby rt').evaluateAll(
      nodes => nodes.map(node => getComputedStyle(node).opacity),
    ), Array(8).fill('1'), 'Pinyin remains readable without JavaScript');
    await noScript.close();
    await fs.writeFile(path.join(directory, 'interaction-check.json'), JSON.stringify({ results, touch: true }, null, 2) + '\n');
    process.stdout.write('Mandarin: permanent pinyin, colors, touch and layout passed on both sides at 3 widths, including without JavaScript.\n');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
