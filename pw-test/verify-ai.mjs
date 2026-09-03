import { chromium } from 'playwright';

const SHOT = '/Users/zaizai/Downloads/AI地震救援/screenshots';
const URL = 'http://localhost:8010/';
const results = { consoleErrors: [], pageErrors: [] };

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function shot(page, name) {
  const p = `${SHOT}/${name}.png`;
  await page.screenshot({ path: p, fullPage: true });
  console.log(`[截图] ${p}`);
  return p;
}

async function waitLog(page, keyword, timeout = 25000) {
  const t0 = Date.now();
  while (Date.now() - t0 < timeout) {
    const hit = await page.evaluate(k => document.getElementById('logBox').textContent.includes(k), keyword);
    if (hit) return Date.now() - t0;
    await sleep(500);
  }
  return -1;
}

async function readFea(page) {
  return page.evaluate(() => ({
    match: document.getElementById('matchTxt').textContent,
    cols: document.getElementById('colTxt').textContent,
    voids: document.getElementById('voidTxt').textContent,
    integ: document.getElementById('integTxt').textContent,
    feaDone: !!S.fea.done, hasResult: !!S.feaResult,
    aiReasons: survivors.filter(s => s.aiReason).map(s => s.id + ': ' + s.aiReason),
    fallbackCount: AI.fallbackCount, cacheQuake: !!AI.cache.quake
  }));
}

const browser = await chromium.launch({ headless: true });
const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
await page.route(u => String(u).includes(':8012'), r => r.abort());   /* 环境隔离：阻断实时社情层 8012，结果与 live_feed 是否在跑无关 */
await page.addInitScript(() => {
  window.__fetchLog = [];
  const orig = window.fetch.bind(window);
  window.fetch = async (url, opt) => {
    let tag = 'GET';
    if (opt && opt.body) {
      const m = opt.body.match(/"id":"(S-\d\d)"/);
      tag = m ? m[1] : (opt.body.includes('结构专家') ? 'VL' : (opt.body.includes('指挥参谋') ? 'QUAKE' : '?'));
    }
    const e = { tag, t0: Math.round(performance.now()), end: null, ok: null };
    window.__fetchLog.push(e);
    try { const r = await orig(url, opt); e.end = Math.round(performance.now()); e.ok = r.status; return r; }
    catch (err) { e.end = Math.round(performance.now()); e.ok = 'ERR:' + err.name; throw err; }
  };
  window.__disc = [];
  setInterval(() => {
    try {
      if (typeof survivors !== 'undefined') survivors.forEach(s => {
        if (s.discovered && !window.__disc.some(d => d.id === s.id)) window.__disc.push({ id: s.id, t: Math.round(performance.now()) });
      });
    } catch (e) {}
  }, 200);
});
page.on('console', m => { if (m.type() === 'error') results.consoleErrors.push(m.text()); });
page.on('console', m => { const t = m.text(); if (t.includes('[RescueAI] Qwen-VL')) results.vlMarks.push(t); });   /* 观测点：结构研判真实调用标记（任务#15，仅增不减断言） */
results.vlMarks = [];
page.on('pageerror', e => results.pageErrors.push(String(e)));

console.log('=== 0. 页面加载 ===');
const tLoad = Date.now();
await page.goto(URL, { waitUntil: 'load' });
await sleep(3000); // 等 warmup / 预载
console.log(`加载耗时 ${Date.now() - tLoad}ms，warmup缓存=${await page.evaluate(() => !!AI.cache.quake)}，imgB64 a/b=${await page.evaluate(() => (!!AI.imgB64.a) + '/' + (!!AI.imgB64.b))}`);
await shot(page, 't3_00_initial');

console.log('=== 1. T3 启动空中搜索 → 多模态结构研判 ===');
const tScan = Date.now();
await page.click('#btnScan');
const wAI = await waitLog(page, '[AI] Qwen-VL', 30000);
const wFEA = await waitLog(page, '建筑结构坍塌推演完成', 30000);
// 确保 uiTick 已渲染（进度 done 且结果存在后才写四值）
await page.waitForFunction(() => S.fea.done && !!S.feaResult, { timeout: 30000 }).catch(() => {});
await sleep(1500);
console.log(`AI研判日志到达 ${wAI}ms，FEA进度完成 ${wFEA}ms，总耗时 ${Date.now() - tScan}ms`);
const fea1 = await readFea(page);
console.log('四值:', JSON.stringify(fea1, null, 1));
if (fea1.match === '92%' && fea1.cols === '47' && fea1.voids === '4') console.log('[FAIL] 仍是硬编码默认值！');
else console.log('[PASS] 四值已由 AI 结果渲染');
await shot(page, 't3_01_ai_result');

console.log('=== 2. T3 换图重测 ===');
const logsBefore = await page.evaluate(() => document.getElementById('logBox').textContent.split('[AI] Qwen-VL').length);
const tRe = Date.now();
await page.click('#btnRetest');
// 等新一次研判日志（计数增加）
await page.waitForFunction(n => document.getElementById('logBox').textContent.split('[AI] Qwen-VL').length > n || document.getElementById('logBox').textContent.includes('采用保守评估'), logsBefore, { timeout: 30000 }).catch(() => {});
await page.waitForFunction(() => S.fea.done && !!S.feaResult, { timeout: 30000 }).catch(() => {});
await sleep(1500);
console.log(`换图重测总耗时 ${Date.now() - tRe}ms`);
const fea2 = await readFea(page);
console.log('重测四值:', JSON.stringify({ match: fea2.match, cols: fea2.cols, voids: fea2.voids, integ: fea2.integ }));
const vlStats = await page.evaluate(() => ({ vlCalls: AI.vlCalls, lastStructKey: AI.lastStructKey, seq: AI.seq }));
console.log('换图真实调用证据: vlCalls=' + vlStats.vlCalls + ' lastKey=' + vlStats.lastStructKey + ' seq=' + vlStats.seq);
console.log('研判请求标记:', JSON.stringify(results.vlMarks, null, 1));
const freshMarks = results.vlMarks.filter(s => s.includes('换图绕过缓存'));
console.log(freshMarks.length >= 2 ? '[PASS] 首次+换图均为绕过缓存的真实调用（' + freshMarks.length + ' 条标记）' : '[WARN] 换图绕过缓存标记不足: ' + freshMarks.length);
const changed = [fea2.match, fea2.cols, fea2.voids, fea2.integ].join() !== [fea1.match, fea1.cols, fea1.voids, fea1.integ].join();
console.log(changed ? '[PASS] 换图后数值已变化' : '[WARN] 换图后数值未变化（若上方真实调用证据齐全，则为两图 AI 输出恰好相同，非缓存命中）');
await shot(page, 't3_02_retest');

console.log('=== 3. T4-1 决策理由（随发现自动生成） ===');
console.log('已生成理由:', JSON.stringify(fea2.aiReasons, null, 1));
await shot(page, 't4_01_priority_reason');

console.log('=== 4. T4-2 余震指挥建议 ===');
const tQ = Date.now();
await page.evaluate(() => triggerQuake(4.2, '4.2 级余震'));
const wQ = await waitLog(page, '[AI] 指挥参谋', 15000);
console.log(`指挥参谋日志到达 ${wQ}ms`);
const advice = await page.evaluate(() => {
  const els = [...document.getElementById('logBox').children];
  const hit = els.find(e => e.textContent.includes('[AI] 指挥参谋'));
  return hit ? hit.textContent : '(未找到)';
});
console.log('日志条目:', advice);
await shot(page, 't4_02_aftershock');

console.log('=== 5. 错误汇总 ===');
console.log('等待全域扫描完成（S-05/S-07 在最后两行）…');
await page.waitForFunction(() => survivors.every(s => s.discovered), { timeout: 90000 }).catch(() => console.log('[WARN] 90s 内未完成全域扫描'));
await page.waitForFunction(() => survivors.every(s => s.aiReason), { timeout: 20000 }).catch(() => {});
await sleep(2000);
const finalReasons = await page.evaluate(() => survivors.map(s => s.id + (s.aiReason ? '✓' : '✗')).join(' '));
console.log('最终决策理由覆盖:', finalReasons);
await shot(page, 't4_03_full_queue');
console.log('fetch 日志(tag t0→end ok):', await page.evaluate(() => window.__fetchLog.map(e => `${e.tag} ${e.t0}→${e.end} ${e.ok}`).join(' | ')));
console.log('发现时间:', await page.evaluate(() => window.__disc.map(d => `${d.id}@${d.t}`).join(' | ')));
console.log('console errors:', results.consoleErrors.length ? results.consoleErrors : '无');
console.log('page errors:', results.pageErrors.length ? results.pageErrors : '无');
console.log('fallbackCount:', await page.evaluate(() => AI.fallbackCount));

await browser.close();
