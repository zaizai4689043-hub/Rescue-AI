/* T26 验收：管线点亮 / NER 灾情图 / 地点中文化 / 决策助手 / 简报自动触发 / sim 零请求（经 8010 代理） */
import { chromium } from 'playwright';

const SHOT = '/Users/zaizai/Downloads/AI地震救援/screenshots';
const URL = 'http://localhost:8010/';
const sleep = ms => new Promise(r => setTimeout(r, ms));
const errs = [];

const browser = await chromium.launch({ headless: true });
const page = await (await browser.newContext({ viewport: { width: 1440, height: 1600 } })).newPage();
await page.route(u => String(u).includes(':8012'), r => r.abort());   /* 环境隔离：阻断实时社情层 8012，结果与 live_feed 是否在跑无关 */
page.on('pageerror', e => errs.push('pageerror: ' + String(e)));
page.on('console', m => { if (m.type() === 'error') errs.push('console: ' + m.text()); });

console.log('=== 1. ?replay=1 加载 + 管线初始 ===');
await page.goto(URL + '?replay=1', { waitUntil: 'load' });
await sleep(2500);
const p0 = await page.evaluate(() => ({
  segs: document.getElementById('rpPipeline') ? [...document.querySelectorAll('#rpPipeline .rpseg')].map(e => ({ k: e.dataset.k, lit: !!e.dataset.lit })) : null
}));
console.log('管线初始(应全灭):', JSON.stringify(p0.segs));
console.log(p0.segs && p0.segs.length === 4 && p0.segs.every(s => !s.lit) ? '[PASS] 管线四段初始未亮' : '[FAIL] 管线初始异常');

console.log('=== 2. 推进②段 → 管线逐段点亮 ===');
await page.evaluate(() => rpJumpTo(20));
await sleep(4000);   /* 瀑布流 0.8s/条，等 NER 卡片出现 */
const p1 = await page.evaluate(() => ({
  lit: [...document.querySelectorAll('#rpPipeline .rpseg')].map(e => e.dataset.k + (e.dataset.lit ? '✓' : '✗')),
  nerInFeed: !!document.querySelector('#feedBox .ner-loc')
}));
console.log('②段管线:', p1.lit.join(' '), 'NER高亮:', p1.nerInFeed);
console.log(p1.lit.every(s => s.endsWith('✓')) && p1.nerInFeed ? '[PASS] 管线四段全部点亮' : '[FAIL] 管线点亮异常');

console.log('=== 3. 地点中文化 placeZh ===');
const zh = await page.evaluate(() => ({
  a: placeZh('Near Mandalay, Myanmar'),
  b: placeZh('Sagaing Region, Myanmar'),
  c: placeZh('Naypyidaw, Myanmar'),
  d: placeZh('Yunnan, China'),
  e: placeZh('Bangkok, Thailand'),
  f: placeZh('云南德宏（离线样例）'),
  list: document.getElementById('seisList').textContent
}));
console.log('placeZh:', zh.a, '|', zh.b, '|', zh.c, '|', zh.d, '|', zh.e, '|', zh.f);
const okZh = zh.a.includes('曼德勒') && zh.b.includes('实皆') && zh.c.includes('内比都') && zh.d.includes('云南') && zh.e.includes('曼谷')
  && !/Myanmar|Mandalay|Sagaing|Naypyidaw|Bangkok/.test(zh.list);
console.log(okZh ? '[PASS] 中文化映射+震情列表无英文地名' : '[FAIL] 中文化异常');

console.log('=== 4. NER 聚合灾情图 ===');
const agg = await page.evaluate(() => ({
  groups: SOCIAL_AGG.length,
  mandalay: (SOCIAL_AGG.find(g => g.name === '曼德勒') || {}).n,
  sosGroups: SOCIAL_AGG.filter(g => g.sos > 0).map(g => g.name + '(' + g.sos + ')'),
  wmax: SOCIAL_WMAX,
  coords: PLACE_COORDS['实皆省']
}));
console.log('聚合组数:', agg.groups, '曼德勒帖数:', agg.mandalay, '呼救地名:', agg.sosGroups.join(','), '实皆省坐标:', agg.coords);
console.log(agg.groups >= 10 && agg.mandalay === 12 && agg.sosGroups.length >= 2 ? '[PASS] NER聚合+呼救标记数据正确' : '[FAIL] 聚合数据异常');
await page.evaluate(() => { const c = document.getElementById('ovSocial'); c.checked = true; });
await sleep(600);
await page.locator('#mapWrap').screenshot({ path: SHOT + '/t26_01_ner_map.png' });
console.log('截图: t26_01_ner_map.png');

console.log('=== 5. ③段简报自动触发（不手动点按钮） ===');
await page.evaluate(() => rpJumpTo(900));
await page.waitForFunction(() => { const b = document.getElementById('btnBrief'); return b && b.textContent === '重新生成'; }, { timeout: 15000 })
  .then(() => console.log('[PASS] 简报自动触发完成（按钮变「重新生成」）'))
  .catch(() => console.log('[FAIL] 简报未自动触发'));
const briefTxt = await page.evaluate(() => document.getElementById('rpBriefBox').textContent.slice(0, 40));
console.log('简报内容前40字:', briefTxt);

console.log('=== 6. ④段决策助手 ===');
await page.evaluate(() => rpJumpTo(2409));
await sleep(800);
const adv0 = await page.evaluate(() => document.getElementById('rpPriorityCard').style.display !== 'none');
console.log(adv0 ? '[PASS] ④段优先级卡显现' : '[FAIL] 优先级卡未显现');
await page.click('#btnAdvisor');
await page.waitForFunction(() => document.getElementById('rpAdvisorBox').textContent.length > 50, { timeout: 15000 })
  .then(() => console.log('[PASS] 决策助手结果已渲染'))
  .catch(() => console.log('[FAIL] 决策助手未出结果'));
const adv = await page.evaluate(() => ({
  txt: document.getElementById('rpAdvisorBox').textContent,
  src: document.getElementById('rpAdvisorBox').textContent.includes('预录兜底') || document.getElementById('rpAdvisorBox').textContent.includes('缓存') || document.getElementById('rpAdvisorBox').textContent.includes('实时')
}));
console.log('决策助手:', adv.txt.slice(0, 80), '…');
console.log(adv.txt.includes('曼德勒') && adv.src ? '[PASS] 决策助手内容含地区+来源标注' : '[FAIL] 决策助手内容异常');
await page.locator('#rpPriorityCard').screenshot({ path: SHOT + '/t26_02_advisor.png' });
console.log('截图: t26_02_advisor.png');

const sentiLine = await page.evaluate(() => document.getElementById('rpSentiTimeline').querySelector('polyline') != null);
console.log(sentiLine ? '[PASS] 情感时间线 hopeful 折线存在' : '[FAIL] 折线缺失');

console.log('=== 7. ?sim=1&replay=1 零外部请求 ===');
const page2 = await (await browser.newContext({ viewport: { width: 1440, height: 1600 } })).newPage();
await page2.route(u => String(u).includes(':8012'), r => r.abort());   /* 环境隔离：阻断实时社情层 8012 */
const reqs = [];
page2.on('request', r => { const u = r.url(); if (/\/ai\/proxy|\/seismic\/feed|\/icl\/warnings/.test(u)) reqs.push(u); });
page2.on('pageerror', e => errs.push('sim pageerror: ' + String(e)));
await page2.goto(URL + '?sim=1&replay=1', { waitUntil: 'load' });
await sleep(2500);
await page2.evaluate(() => rpJumpTo(2409));
await sleep(1500);
await page2.click('#btnAdvisor');
await sleep(1200);
const sim = await page2.evaluate(() => ({
  advisorTxt: document.getElementById('rpAdvisorBox').textContent.slice(0, 30),
  briefTxt: document.getElementById('rpBriefBox').textContent.slice(0, 30),
  pipelineLit: [...document.querySelectorAll('#rpPipeline .rpseg')].filter(e => e.dataset.lit).length
}));
console.log('sim 决策助手:', sim.advisorTxt, '| sim 简报:', sim.briefTxt, '| 管线亮段:', sim.pipelineLit);
console.log(reqs.length === 0 ? '[PASS] sim 模式零外部请求' : '[FAIL] sim 出现外部请求: ' + reqs.join(','));
console.log(sim.advisorTxt.includes('曼德勒') && sim.briefTxt.length > 10 ? '[PASS] sim 预录直显（决策助手+简报）' : '[FAIL] sim 预录异常');
await page2.locator('#mapWrap').screenshot({ path: SHOT + '/t26_03_sim_check.png' }).catch(() => {});

console.log('=== 8. 错误汇总 ===');
console.log(errs.length ? errs : '无页面错误');
await browser.close();
console.log('=== T26 验收完成 ===');
