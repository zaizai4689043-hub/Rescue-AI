import { chromium } from 'playwright';
const URL = 'http://localhost:8010/';
const sleep = ms => new Promise(r => setTimeout(r, ms));
const errs = [];
const browser = await chromium.launch({ headless: true });
const page = await (await browser.newContext({ viewport: { width: 1440, height: 1500 } })).newPage();
await page.route(u => String(u).includes(':8012'), r => r.abort());   /* 环境隔离：阻断实时社情层 8012，结果与 live_feed 是否在跑无关 */
page.on('pageerror', e => errs.push('pageerror: ' + String(e)));
page.on('console', m => { if (m.type() === 'error') errs.push('console: ' + m.text()); });
const reqs = [];
page.on('request', r => { if (!r.url().startsWith('http://localhost:8010')) reqs.push(r.url()); });

console.log('=== T25-1: ?replay=1 跳到④段 ===');
await page.goto(URL + '?replay=1', { waitUntil: 'load' });
await sleep(1500);
await page.evaluate(() => { rpJumpTo(2000); });  // 直接进入④段（>969）
await sleep(800);
const info = await page.evaluate(() => {
  const box = document.getElementById('rpPriorityBox');
  const cards = [...box.children];
  return {
    cardShown: document.getElementById('rpPriorityCard').style.display !== 'none',
    n: cards.length,
    rows: cards.map(c => ({
      tier: c.querySelector('b').textContent,
      area: c.querySelectorAll('b')[1].textContent,
      score: (c.querySelector('.ml-auto b') || {}).textContent,
      bar: !!c.querySelector('.h-1\\.5 > div'),
      barW: (c.querySelector('.h-1\\.5 > div') || {}).style?.width,
      border: c.className,
      evBadge: c.querySelector('.rounded-full')?.textContent
    })),
    formula: document.querySelector('#rpPriorityCard').textContent.includes('评分 = 社情严重度'),
    title72: document.querySelector('#rpPriorityCard').textContent.includes('AI 救援优先级引擎')
  };
});
console.log(JSON.stringify(info, null, 1));
const t = Object.fromEntries(info.rows.map(r => [r.area, r.tier]));
const p0ok = (t['曼德勒 Sky Villa 公寓'] === 'P0') && (t['实皆省'] === 'P0');
const evOk = info.rows.some(r => r.evBadge.includes('×2')) && info.rows.some(r => r.evBadge.includes('×10')) && info.rows.some(r => r.evBadge.includes('×16'));
console.log(p0ok ? '[PASS] Sky Villa/实皆 = P0' : '[FAIL] P0 校验失败');
console.log(info.n === 5 && info.rows.every(r => r.bar) ? '[PASS] 五卡评分条渲染' : '[FAIL] 评分条异常');
console.log(evOk ? '[PASS] 证据链徽章 ×2/×10/×16 不变' : '[FAIL] 证据链变化');
console.log(info.formula && info.title72 ? '[PASS] 引擎标题+公式脚注' : '[FAIL] 标注缺失');
const colorOk = info.rows.every(r => (r.tier === 'P0' && r.border.includes('red')) || (r.tier === 'P1' && r.border.includes('orange')) || (r.tier === 'P2' && r.border.includes('amber')) || (r.tier === 'P3' && r.border.includes('slate')));
console.log(colorOk ? '[PASS] 档位颜色与阈值一致' : '[FAIL] 颜色不一致');

console.log('=== T25-2: 时效联动（推进时钟 40 演示秒 → 30s 触发重算）===');
const s1 = await page.evaluate(() => rpEngineElapsed() && document.getElementById('rpPriorityBox').innerHTML.length);
await page.evaluate(() => { rpJumpTo(3800); });
await sleep(500);
const s2 = await page.evaluate(() => document.getElementById('rpPriorityBox').innerHTML.length);
console.log(s1 !== s2 ? '[PASS] 跳段后卡片按新时刻重算' : '[FAIL] 未重算');
await page.screenshot({ path: '/Users/zaizai/Downloads/AI地震救援/screenshots/t25_01_engine_final.png', fullPage: false });
await page.evaluate(() => { document.getElementById('rpPriorityCard').scrollIntoView(); });
await sleep(300);
await page.screenshot({ path: '/Users/zaizai/Downloads/AI地震救援/screenshots/t25_02_engine_card.png', clip: { x: 0, y: 0, width: 1440, height: 1500 } });

console.log('=== T25-3: ?sim=1&replay=1 零外部请求 ===');
await page.goto(URL + '?sim=1&replay=1', { waitUntil: 'load' });
await sleep(1500);
await page.evaluate(() => { rpJumpTo(2000); });
await sleep(800);
const simN = await page.evaluate(() => document.getElementById('rpPriorityBox').children.length);
console.log(simN === 5 ? '[PASS] sim 模式五卡渲染' : '[FAIL] sim 渲染异常 n=' + simN);
console.log(reqs.length === 0 ? '[PASS] 零外部请求' : '[FAIL] 外部请求: ' + reqs.join(','));
console.log('errs:', errs.length ? errs : '无');
await browser.close();
