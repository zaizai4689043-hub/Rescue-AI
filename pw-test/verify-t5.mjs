import { chromium } from 'playwright';

const SHOT = '/Users/zaizai/Downloads/AI地震救援/screenshots';
const URL = 'http://localhost:8010/';
const results = { consoleErrors: [], pageErrors: [] };
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function shot(page, name, locator) {
  const p = `${SHOT}/${name}.png`;
  if (locator) await locator.screenshot({ path: p });
  else await page.screenshot({ path: p, fullPage: true });
  console.log(`[截图] ${p}`);
}

async function waitLog(page, keyword, timeout = 30000) {
  const t0 = Date.now();
  while (Date.now() - t0 < timeout) {
    const hit = await page.evaluate(k => document.getElementById('logBox').textContent.includes(k), keyword);
    if (hit) return Date.now() - t0;
    await sleep(400);
  }
  return -1;
}

const browser = await chromium.launch({ headless: true });

/* ================= 主模式（真实 AI） ================= */
{
  const page = await (await browser.newContext({ viewport: { width: 1440, height: 1600 } })).newPage();
  await page.route(u => String(u).includes(':8012'), r => r.abort());   /* 环境隔离：阻断实时社情层 8012，结果与 live_feed 是否在跑无关 */
  page.on('console', m => { if (m.type() === 'error') results.consoleErrors.push(m.text()); });
  page.on('pageerror', e => results.pageErrors.push(String(e)));

  console.log('=== 1. 页面加载与双源面板渲染 ===');
  await page.goto(URL, { waitUntil: 'load' });
  await sleep(3500);
  const seisInfo = await page.evaluate(() => ({
    src: document.getElementById('seisSrcTxt').textContent,
    listRows: document.getElementById('seisList').children.length,
    cnt: document.getElementById('seisCntTxt').textContent,
    version: document.querySelector('header').textContent.includes('v2.7'),
    modelChip: document.querySelector('header').textContent.includes('Qwen3.7-Plus'),
    panelTitle: document.body.textContent.includes('Qwen-VL 多模态结构研判'),
    funnel: document.getElementById('dualSrcSection').textContent.replace(/\s/g, '').includes('53,340原始→40,595去噪→9,617初筛→65AI甄别→52精选')
  }));
  console.log('仪器侧:', JSON.stringify(seisInfo));
  console.log(seisInfo.listRows > 0 ? '[PASS] 仪器侧有数据（实时或离线样例）' : '[FAIL] 仪器侧无数据');
  console.log((seisInfo.version && seisInfo.modelChip && seisInfo.panelTitle) ? '[PASS] T5 文案包装全部生效' : '[FAIL] 文案缺失');
  console.log(seisInfo.funnel ? '[PASS] 漏斗数字可见' : '[FAIL] 漏斗缺失');

  console.log('=== 2. 瀑布流自动播放 + NER 高亮 ===');
  await page.waitForFunction(() => document.getElementById('feedBox').children.length >= 3, { timeout: 15000 });
  const feedInfo = await page.evaluate(() => ({
    cards: document.getElementById('feedBox').children.length,
    nerLoc: document.querySelectorAll('#feedBox .ner-loc').length,
    nerDmg: document.querySelectorAll('#feedBox .ner-dmg').length,
    kpi: document.getElementById('kpiSocial').textContent,
    offsets: [...document.querySelectorAll('#feedBox .pfeed-card')].map(c => c.textContent.match(/\+(\d+)min/)?.[1])
  }));
  console.log('瀑布流:', JSON.stringify(feedInfo));
  console.log((feedInfo.nerLoc > 0 && feedInfo.nerDmg > 0) ? '[PASS] NER 高亮可见（黄=地点/红=灾情词）' : '[FAIL] 无 NER 高亮');
  console.log(feedInfo.offsets.join(',') === [...feedInfo.offsets].sort((a, b) => a - b).join(',') ? '[PASS] 按震后时间升序播放' : '[FAIL] 顺序异常');

  console.log('=== 3. [社情] 闭环日志 + 已转入处置标记 ===');
  const w1 = await waitLog(page, '[社情]', 15000);
  console.log(w1 >= 0 ? `[PASS] [社情] 甄别日志出现（${w1}ms）` : '[FAIL] 无 [社情] 日志');
  const closedMarks = await page.evaluate(() => document.querySelectorAll('#feedBox .pfeed-card').length && [...document.querySelectorAll('#feedBox .pfeed-card')].filter(c => c.textContent.includes('已转入处置')).length);
  console.log('已转入处置标记数:', closedMarks);

  console.log('=== 4. 社情感知图层开关 → 地图画布像素差异 + 瀑布流卡数增长 ===');
  const snapCanvas = () => page.evaluate(() => {
    const cv = document.getElementById('mapCanvas');
    const d = cv.getContext('2d').getImageData(0, 0, cv.width, cv.height).data;
    let sum = 0; for (let i = 0; i < d.length; i += 40) sum += d[i] + d[i + 1] + d[i + 2];   /* 步长采样求和，作为像素统计 */
    return { sum, w: cv.width, h: cv.height };
  });
  await page.evaluate(() => { document.getElementById('ovSocial').checked = false; });   /* 先关图层 */
  await sleep(1500);                                                                      /* 等主循环重绘 */
  const before = await snapCanvas();
  await page.check('#ovSocial');                                                          /* 再开图层 */
  await sleep(4000);
  const after = await snapCanvas();
  const checked = await page.evaluate(() => document.getElementById('ovSocial').checked);
  const pixDiff = Math.abs(after.sum - before.sum);
  console.log('图层关/开像素统计:', JSON.stringify(before), JSON.stringify(after), 'checked=' + checked, 'diff=' + pixDiff);
  console.log(pixDiff > 0 ? '[PASS] 社情图层开关引起 mapCanvas 像素差异>0（真实读端生效）' : '[FAIL] 图层开关无像素变化');
  /* 瀑布流播放过程中卡片数增长（真实读端：DOM 渲染） */
  const cards0 = await page.evaluate(() => document.getElementById('feedBox').children.length);
  await sleep(3000);
  const cards1 = await page.evaluate(() => document.getElementById('feedBox').children.length);
  console.log(`feedBox 卡数 ${cards0} → ${cards1}`);
  console.log(cards1 > cards0 ? '[PASS] 瀑布流播放中卡片数增长' : '[FAIL] 卡片数未增长');

  console.log('=== 5. 截图（双源面板/瀑布流/热力圈） ===');
  await page.locator('#dualSrcSection').scrollIntoViewIfNeeded();
  await sleep(800);
  await shot(page, 't5_01_dual_panel', page.locator('#dualSrcSection'));
  await shot(page, 't5_02_feed_ner', page.locator('#feedBox').locator('..'));
  await page.locator('#mapWrap').scrollIntoViewIfNeeded();
  await sleep(1200);
  await shot(page, 't5_03_heat_layer', page.locator('#mapWrap'));

  console.log('=== 6. 回归：多模态评估 + 余震参谋（前一任务成果） ===');
  await page.click('#btnScan');
  const wAI = await waitLog(page, '[AI] Qwen-VL', 30000);
  await page.waitForFunction(() => S.fea.done && !!S.feaResult, { timeout: 30000 }).catch(() => {});
  await sleep(1500);
  const fea = await page.evaluate(() => ({
    match: document.getElementById('matchTxt').textContent,
    cols: document.getElementById('colTxt').textContent,
    voids: document.getElementById('voidTxt').textContent,
    integ: document.getElementById('integTxt').textContent
  }));
  console.log(`AI研判日志 ${wAI}ms，四值:`, JSON.stringify(fea));
  console.log(wAI >= 0 && fea.match !== '--' ? '[PASS] 多模态评估回归正常' : '[FAIL] 多模态评估异常');
  await page.evaluate(() => triggerQuake(4.2, '4.2 级余震'));
  const wQ = await waitLog(page, '[AI] 指挥参谋', 15000);
  console.log(wQ >= 0 ? `[PASS] 余震参谋回归正常（${wQ}ms）` : '[FAIL] 余震参谋异常');
  await sleep(1500);
  await shot(page, 't5_04_regression');

  console.log('=== 7. 错误汇总（主模式） ===');
  console.log('console errors:', results.consoleErrors.length ? results.consoleErrors : '无');
  console.log('page errors:', results.pageErrors.length ? results.pageErrors : '无');
  await page.close();
}

/* ================= ?sim=1 保险丝模式 ================= */
{
  const page = await (await browser.newContext({ viewport: { width: 1440, height: 1600 } })).newPage();
  await page.route(u => String(u).includes(':8012'), r => r.abort());   /* 环境隔离：阻断实时社情层 8012 */
  const simErrs = [];
  page.on('pageerror', e => simErrs.push(String(e)));
  console.log('=== 8. ?sim=1 模式双源面板 ===');
  await page.goto(URL + '?sim=1', { waitUntil: 'load' });
  await sleep(6000);
  const simInfo = await page.evaluate(() => ({
    src: document.getElementById('seisSrcTxt').textContent,
    listRows: document.getElementById('seisList').children.length,
    cards: document.getElementById('feedBox').children.length,
    ner: document.querySelectorAll('#feedBox .ner-loc').length + document.querySelectorAll('#feedBox .ner-dmg').length
  }));
  console.log('sim 模式:', JSON.stringify(simInfo));
  console.log(simInfo.src.includes('离线样例') ? '[PASS] sim 模式仪器侧用离线样例' : '[FAIL] sim 仪器侧异常: ' + simInfo.src);
  console.log(simInfo.cards >= 2 ? '[PASS] sim 模式瀑布流正常播放' : '[FAIL] sim 瀑布流异常');
  console.log('sim page errors:', simErrs.length ? simErrs : '无');
  await page.close();
}

await browser.close();
console.log('=== 完成 ===');
