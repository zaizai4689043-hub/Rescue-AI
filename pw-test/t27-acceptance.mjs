/* T27 验收：?replay=1 两按钮全流程（投送到引擎第一名区域、航拍研判出结果）；?sim=1&replay=1 零外部请求 */
import { chromium } from 'playwright';

const SHOT = '/Users/zaizai/Downloads/AI地震救援/screenshots';
const BASE = 'http://localhost:8010/';
const sleep = ms => new Promise(r => setTimeout(r, ms));
const errs = [];

const browser = await chromium.launch({ headless: true });
const page = await (await browser.newContext({ viewport: { width: 1440, height: 1600 } })).newPage();
await page.route(u => String(u).includes(':8012'), r => r.abort());   /* 环境隔离：阻断实时社情层 8012，结果与 live_feed 是否在跑无关 */
page.on('pageerror', e => errs.push('pageerror: ' + String(e)));
page.on('console', m => { if (m.type() === 'error') errs.push('console: ' + m.text()); });

console.log('=== 1. ?replay=1 跳到④段，T27 卡片显现 ===');
await page.goto(BASE + '?replay=1', { waitUntil: 'load' });
await sleep(2500);
await page.evaluate(() => rpJumpTo(2409));   /* ④段 */
await sleep(1000);
const t27Visible = await page.evaluate(() => {
  const c = document.getElementById('t27Card');
  return c && c.style.display !== 'none';
});
console.log(t27Visible ? '[PASS] T27 空中救援行动卡随④段显现' : '[FAIL] T27 卡未显现');

console.log('=== 2. 物资投送：目标=优先级引擎第一名区域 ===');
const topInfo = await page.evaluate(() => {
  const top = t27TopArea();
  return { match: top.r.match, area: top.r.area.replace(/（.*?）/g, '').trim(), score: +top.sc.score.toFixed(1) };
});
console.log('引擎第一名:', JSON.stringify(topInfo));
await page.locator('.t27BtnDrop').first().click();
await page.waitForFunction(() => document.getElementById('logBox').textContent.includes('物资投送完成'), { timeout: 25000 })
  .then(() => console.log('[PASS] 投送完成日志出现')).catch(() => console.log('[FAIL] 投送未完成'));
const dropInfo = await page.evaluate(() => ({
  log: document.getElementById('logBox').textContent,
  dropBox: document.querySelector('.t27DropBox').textContent,
  flyState: T27.drop.phase
}));
const dropOk = dropInfo.log.includes('目标：' + topInfo.area) && dropInfo.log.includes('中国红十字会首批援助明细') && dropInfo.dropBox.includes('本架次装载') && dropInfo.dropBox.includes('援助锚点') && dropInfo.flyState === null;
console.log(dropOk ? '[PASS] 投送目标=引擎第一名 + 载重面板(红会锚点) + 动画归位' : '[FAIL] 投送链路异常 ' + JSON.stringify(dropInfo));
await page.locator('#mapWrap').screenshot({ path: SHOT + '/t27_01_drop.png' });
await page.locator('#t27Card').screenshot({ path: SHOT + '/t27_01_drop_card.png' });

console.log('=== 3. 灾情航拍研判：巡航+拍摄+AI 结果 ===');
await page.locator('.t27BtnRecon').first().click();
await page.waitForFunction(() => document.getElementById('logBox').textContent.includes('拍摄第 1/3 帧'), { timeout: 20000 })
  .then(() => console.log('[PASS] 巡航拍摄开始')).catch(() => console.log('[FAIL] 未见拍摄日志'));
await page.waitForFunction(() => document.getElementById('logBox').textContent.includes('灾情航拍研判完成'), { timeout: 45000 })
  .then(() => console.log('[PASS] 航拍研判完成')).catch(() => console.log('[FAIL] 航拍研判未完成'));
const reconInfo = await page.evaluate(() => ({
  box: document.querySelector('.t27ReconBox').textContent,
  shots: T27.recon.shots.length
}));
const reconOk = reconInfo.box.includes('AI 路线研判 · 供救援指挥参考') && reconInfo.box.includes('侦察影像同步回传指挥中心') && reconInfo.box.length > 60;
console.log(reconOk ? '[PASS] 研判结果面板渲染（标签+脚注）' : '[FAIL] 研判面板异常 ' + JSON.stringify(reconInfo));
console.log('拍摄帧数:', reconInfo.shots);
await page.locator('#mapWrap').screenshot({ path: SHOT + '/t27_02_recon.png' });

console.log('=== 4. ?sim=1&replay=1 零外部请求 ===');
const page2 = await browser.newPage();
await page2.route(u => String(u).includes(':8012'), r => r.abort());   /* 环境隔离：阻断实时社情层 8012 */
let proxyReqs = 0;
page2.on('request', r => { if (r.url().includes('/ai/proxy')) proxyReqs++; });
await page2.goto(BASE + '?sim=1&replay=1', { waitUntil: 'load' });
await sleep(3000);
await page2.evaluate(() => rpJumpTo(2409));
await sleep(800);
await page2.locator('.t27BtnDrop').first().click();
await page2.waitForFunction(() => document.getElementById('logBox').textContent.includes('物资投送完成'), { timeout: 25000 });
await page2.locator('.t27BtnRecon').first().click();
await page2.waitForFunction(() => document.getElementById('logBox').textContent.includes('灾情航拍研判完成'), { timeout: 30000 });
const simRecon = await page2.evaluate(() => document.querySelector('.t27ReconBox').textContent);
console.log('sim 模式 /ai/proxy 请求数:', proxyReqs);
console.log(proxyReqs === 0 ? '[PASS] sim 零外部请求' : '[FAIL] sim 出现 AI 请求');
console.log(simRecon.includes('预录兜底') && simRecon.includes('AI 路线研判') ? '[PASS] sim 直显预录研判' : '[FAIL] sim 研判异常: ' + simRecon.slice(0, 80));

console.log('=== 5. 冻结回归：btnScan 链路 / T14 区块 / 漏斗串 / chip ===');
const frozen = await page.evaluate(() => ({
  btnScan: document.getElementById('btnScan').textContent.includes('空中救援'),
  telemetryIntact: typeof applyTelemetry === 'function' && String(applyTelemetry).includes('frame.heading'),
  funnel: document.body.textContent.includes('53,340 原始') && document.body.textContent.includes('52 精选'),
  chip: document.querySelector('header').textContent.includes('Qwen3.7-Plus') && document.querySelector('header').textContent.includes('v2.7'),
  t26Coords: typeof PLACE_COORDS === 'object' && PLACE_COORDS['曼德勒'][0] === 470
}));
console.log(JSON.stringify(frozen));
console.log(Object.values(frozen).every(Boolean) ? '[PASS] 冻结断言完好' : '[FAIL] 冻结断言被破坏');

console.log('=== 6. 错误汇总 ===');
console.log(errs.length ? errs : '无页面错误');
await browser.close();
console.log('=== 完成 ===');
