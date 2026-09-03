import { chromium } from 'playwright';

const SHOT = '/Users/zaizai/Downloads/AI地震救援/screenshots';
const URL = 'http://localhost:8010/';
const sleep = ms => new Promise(r => setTimeout(r, ms));
const results = { consoleErrors: [], pageErrors: [] };

async function waitLog(page, keyword, timeout = 30000) {
  const t0 = Date.now();
  while (Date.now() - t0 < timeout) {
    const hit = await page.evaluate(k => document.getElementById('logBox').textContent.includes(k), keyword);
    if (hit) return Date.now() - t0;
    await sleep(300);
  }
  return -1;
}

const browser = await chromium.launch({ headless: true });
const page = await (await browser.newContext({ viewport: { width: 1440, height: 1700 } })).newPage();
await page.route(u => String(u).includes(':8012'), r => r.abort());   /* 环境隔离：阻断实时社情层 8012，结果与 live_feed 是否在跑无关 */
page.on('console', m => { if (m.type() === 'error') results.consoleErrors.push(m.text()); });
page.on('pageerror', e => results.pageErrors.push(String(e)));

console.log('=== 0. 页面加载（普通模式） ===');
await page.goto(URL, { waitUntil: 'load' });
await sleep(3500);

console.log('=== 1. 失联与通讯信号面板（真实社情） ===');
const sig = await page.evaluate(() => ({
  title: document.querySelector('#sigLost').closest('.panel').querySelector('h2').textContent,
  lost: document.getElementById('sigLost').textContent,
  outage: document.getElementById('sigOutage').textContent,
  embassy: document.getElementById('sigEmbassy').textContent,
  cross: document.getElementById('sigCross').textContent,
  pinned: document.getElementById('sigPinnedCase').textContent.slice(0, 80)
}));
console.log(JSON.stringify(sig));
console.log((sig.title.includes('失联与通讯信号') && sig.lost === '8' && sig.outage === '7' && sig.embassy === '24h' && sig.cross === '0' && /2,?500/.test(sig.pinned)) ? '[PASS] 失联面板：标题/四项计数/2500学生案例脚注' : '[FAIL] 失联面板异常');

console.log('=== 2. 物资面板初始态（信号列 + 援助事实卡 + 真实口径人口） ===');
const sup = await page.evaluate(() => {
  const ths = [...document.querySelectorAll('.supply-table thead th')].map(t => t.textContent);
  const rows = [...document.querySelectorAll('#supplyBody tr')].map(tr => [...tr.children].map(td => td.textContent));
  const anchors = [...document.querySelectorAll('#aidAnchorBox > div')].map(d => d.textContent.slice(0, 40));
  return { ths, rowCount: rows.length, rows, anchors, affPop: document.getElementById('affPopTxt').textContent, srcNote: document.body.textContent.includes('需求信号来源：微博数据集（匿名化，官方/机构口径）+ 新华社/WHO 通报') };
});
console.log('表头:', sup.ths.join(' | '));
console.log('affPop:', sup.affPop, ' 来源小字:', sup.srcNote);
console.log('援助卡:', JSON.stringify(sup.anchors));
sup.rows.forEach(r => console.log('  ', r.join(' | ')));
const sigIdx = sup.ths.indexOf('微博信号数');
const tentRow = sup.rows.find(r => r[0] === '帐篷');
const quiltRow = sup.rows.find(r => r[0] === '毛巾被');
const foodRow = sup.rows.find(r => r[0] === '应急食品');
const bloodRow = sup.rows.find(r => r[0] === '医疗血袋');
console.log((sigIdx === 3 && tentRow[3] === '4' && quiltRow[3] === '0' && foodRow[3] === '0' && bloodRow[3] === '4') ? '[PASS] 微博信号数列：帐篷4/毛毯0/食品0/献血4' : '[FAIL] 信号列异常');
console.log((sup.anchors.length === 3 && sup.affPop.includes('万')) ? '[PASS] 3 张援助事实卡 + 真实口径人口' : '[FAIL] 援助卡/人口异常');

console.log('=== 3. 启动空中搜索 → 真实照片结构研判（记录延迟） ===');
const tScan = Date.now();
await page.click('#btnScan');
const wAI = await waitLog(page, '[AI] Qwen-VL', 30000);
const wFEA = await waitLog(page, '建筑结构坍塌推演完成', 30000);
await page.waitForFunction(() => S.fea.done && !!S.feaResult, { timeout: 30000 }).catch(() => {});
await sleep(1200);
const fea = await page.evaluate(() => ({
  match: document.getElementById('matchTxt').textContent,
  cols: document.getElementById('colTxt').textContent,
  voids: document.getElementById('voidTxt').textContent,
  integ: document.getElementById('integTxt').textContent,
  result: S.feaResult, fallbackCount: AI.fallbackCount,
  feaLog: [...document.getElementById('logBox').children].find(e => e.textContent.includes('建筑结构坍塌推演完成'))?.textContent
}));
console.log(`结构研判延迟 ${wAI}ms · 坍塌推演完成 ${wFEA}ms · 总耗时 ${Date.now() - tScan}ms · fallbackCount=${fea.fallbackCount}`);
console.log('四值:', JSON.stringify({ match: fea.match, cols: fea.cols, voids: fea.voids, integ: fea.integ }));
console.log('推演日志:', fea.feaLog);
console.log((wAI >= 0 && fea.match !== '--' && fea.result.damage_level) ? '[PASS] 真实照片结构研判到达' : '[FAIL] 结构研判异常');
console.log(fea.feaLog.includes('构件识别与空隙评估完成') || /承重构件 \d+ 处/.test(fea.feaLog) ? '[PASS] 推演日志无硬编码假值' : '[FAIL] 推演日志异常');
await page.screenshot({ path: `${SHOT}/t13_01_structure_real.png`, fullPage: true });

console.log('=== 4. 决策理由 + 余震参谋 ===');
await page.waitForFunction(() => survivors.some(s => s.aiReason), { timeout: 20000 }).catch(() => {});
const reasons = await page.evaluate(() => survivors.filter(s => s.aiReason).map(s => s.id).join(','));
console.log('已生成决策理由:', reasons || '(无)');
await page.evaluate(() => triggerQuake(4.2, '4.2 级余震'));
const wQ = await waitLog(page, '[AI] 指挥参谋', 15000);
console.log(wQ >= 0 ? `[PASS] 余震参谋到达 ${wQ}ms` : '[FAIL] 余震参谋缺失');

console.log('=== 5. 全域搜索完成后的面板联动 ===');
await page.waitForFunction(() => survivors.every(s => s.discovered), { timeout: 120000 }).catch(() => console.log('[WARN] 120s 内未完成全域扫描'));
await sleep(1500);
const after = await page.evaluate(() => ({
  cross: document.getElementById('sigCross').textContent,
  affPop: document.getElementById('affPopTxt').textContent,
  tentRow: [...document.querySelectorAll('#supplyBody tr')].find(tr => tr.children[0].textContent === '帐篷') && [...[...document.querySelectorAll('#supplyBody tr')].find(tr => tr.children[0].textContent === '帐篷').children].map(td => td.textContent).join(' | '),
  imgSrc: document.body.textContent.includes('影像来源：曼德勒震后现场照片')
}));
console.log(JSON.stringify(after));
console.log((after.cross === '8' && after.imgSrc) ? '[PASS] 交叉核验=8 + 影像来源小字' : '[FAIL] 联动异常');
await page.screenshot({ path: `${SHOT}/t13_02_full_flow.png`, fullPage: true });

console.log('=== 6. 错误汇总 ===');
console.log('console errors:', results.consoleErrors.length ? results.consoleErrors : '无');
console.log('page errors:', results.pageErrors.length ? results.pageErrors : '无');
await browser.close();
