import { chromium } from 'playwright';
const sleep = ms => new Promise(r => setTimeout(r, ms));
const SHOT = '/Users/zaizai/Downloads/AI地震救援/screenshots';
const browser = await chromium.launch({ headless: true });
const page = await (await browser.newContext({ viewport: { width: 1440, height: 1500 } })).newPage();
await page.route(u => String(u).includes(':8012'), r => r.abort());   /* 环境隔离：阻断实时社情层 8012，结果与 live_feed 是否在跑无关 */

// 1) 普通模式 + replay=1 整页
await page.goto('http://127.0.0.1:8010/', { waitUntil: 'load' });
await sleep(4000);
await page.screenshot({ path: `${SHOT}/bg_gf4_normal.png` });
console.log('saved bg_gf4_normal.png');

await page.goto('http://127.0.0.1:8010/?replay=1', { waitUntil: 'load' });
await sleep(6000);
await page.screenshot({ path: `${SHOT}/bg_gf4_replay.png` });
console.log('saved bg_gf4_replay.png');

// 2) canvas 元素级截图细看底图
for (const [url, out] of [['http://127.0.0.1:8010/', '/tmp/bg_gf4_canvas_normal.png'], ['http://127.0.0.1:8010/?replay=1', '/tmp/bg_gf4_canvas_replay.png']]) {
  await page.goto(url, { waitUntil: 'load' });
  await sleep(4000);
  const box = await page.evaluate(() => {
    const c = document.getElementById('mapCanvas');
    const r = c.getBoundingClientRect();
    return { id: c.id, x: r.x, y: r.y, w: r.width, h: r.height };
  });
  console.log(url, JSON.stringify(box));
  await page.locator('#mapCanvas').screenshot({ path: out });
}

// 3) 普通模式：空中救援 → 热点 → 被困者标记闭环
await page.goto('http://127.0.0.1:8010/', { waitUntil: 'load' });
await sleep(3000);
const btn = await page.evaluate(() => {
  const b = [...document.querySelectorAll('button')].find(x => x.textContent.includes('空中救援'));
  if (b) { b.click(); return b.textContent.trim(); }
  return null;
});
console.log('clicked:', btn);
await sleep(8000);
const state1 = await page.evaluate(() => ({
  located: document.getElementById('locatedTxt')?.textContent,
  drone: document.getElementById('droneStateTxt')?.textContent,
  logTail: document.getElementById('logBox')?.innerText.split('\n').slice(-5).join(' | ')
}));
console.log('t+8s:', JSON.stringify(state1));
await page.locator('#mapCanvas').screenshot({ path: `${SHOT}/bg_gf4_search_mid.png` });
await sleep(15000);
const state2 = await page.evaluate(() => ({
  located: document.getElementById('locatedTxt')?.textContent,
  drone: document.getElementById('droneStateTxt')?.textContent,
  logTail: document.getElementById('logBox')?.innerText.split('\n').slice(-5).join(' | ')
}));
console.log('t+23s:', JSON.stringify(state2));
await page.screenshot({ path: `${SHOT}/bg_gf4_search_flow.png` });
await page.locator('#mapCanvas').screenshot({ path: `${SHOT}/bg_gf4_search_canvas.png` });
console.log('saved search flow shots');

await browser.close();
console.log('done');
