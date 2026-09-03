import { chromium } from 'playwright';

const SHOT = '/Users/zaizai/Downloads/AI地震救援/screenshots';
const URL = 'http://localhost:8010/';
const sleep = ms => new Promise(r => setTimeout(r, ms));
const errs = [];

const browser = await chromium.launch({ headless: true });
const page = await (await browser.newContext({ viewport: { width: 1440, height: 1500 } })).newPage();
await page.route(u => String(u).includes(':8012'), r => r.abort());   /* 环境隔离：阻断实时社情层 8012（回放本已门禁，此处为一致性兼顾） */
page.on('pageerror', e => errs.push('pageerror: ' + String(e)));
page.on('console', m => { if (m.type() === 'error') errs.push('console: ' + m.text()); });

console.log('=== 1. ?replay=1 加载 ===');
await page.goto(URL + '?replay=1', { waitUntil: 'load' });
await sleep(3000);
const info = await page.evaluate(() => ({
  theaterVisible: document.getElementById('replayTheater').style.display !== 'none',
  clock: document.getElementById('rpClockTxt').textContent,
  seisSrc: document.getElementById('seisSrcTxt').textContent,
  seisRows: document.getElementById('seisList').children.length,
  events: document.getElementById('rpEventFeed').children.length,
  topics: document.getElementById('rpTopicList').children.length,
  stagesOn: [...document.querySelectorAll('.rstage.on')].map(e => e.dataset.stage),
  btnTxt: document.getElementById('btnReplayTheater').textContent,
  frozenV27: document.querySelector('header').textContent.includes('v2.7'),
  frozenChip: document.querySelector('header').textContent.includes('Qwen3.7-Plus')
}));
console.log('初始状态:', JSON.stringify(info, null, 1));
console.log(info.theaterVisible && info.seisSrc.includes('历史目录回放') && info.frozenV27 && info.frozenChip ? '[PASS] 剧场显示+仪器侧历史回放+冻结断言完好' : '[FAIL] 初始状态异常');

console.log('=== 2. 等待主震锚点(t=0)与强余震 M6.7(t=+11.2min≈7.5s) ===');
await page.waitForFunction(() => document.getElementById('logBox').textContent.includes('主震 M7.7 锚点'), { timeout: 20000 }).then(() => console.log('[PASS] 主震锚点日志出现')).catch(() => console.log('[FAIL] 主震锚点未出现'));
await page.waitForFunction(() => document.getElementById('logBox').textContent.includes('强余震 M6.7'), { timeout: 25000 }).then(() => console.log('[PASS] M6.7 强余震触发')).catch(() => console.log('[FAIL] M6.7 未触发'));
const shakeInfo = await page.evaluate(() => ({
  aftersList: document.getElementById('rpAftersList').children.length,
  quakeTxt: document.getElementById('quakeTxt').textContent,
  aiAdviceInLog: document.getElementById('logBox').textContent.includes('[AI] 指挥参谋')
}));
console.log('余震列表条数:', shakeInfo.aftersList, '震情chip:', shakeInfo.quakeTxt, '重演期间AI参谋抢戏:', shakeInfo.aiAdviceInLog);
console.log(shakeInfo.aftersList >= 1 && !shakeInfo.aiAdviceInLog ? '[PASS] 余震点亮且未调 AI 参谋' : '[FAIL] 余震逻辑异常');
await page.locator('#replayTheater').screenshot({ path: SHOT + '/t12_01_stage1.png' });

console.log('=== 3. ②段：词条滚动 + 曲线 + 瀑布流加速 ===');
await page.evaluate(() => rpJumpTo(20));   /* 定位②段中段（M6.7 等待已过②段起点，属预期） */
await sleep(1500);
const s2 = await page.evaluate(() => ({
  elapsed: Math.round(REPLAY.elapsed*10)/10,
  stagesOn: [...document.querySelectorAll('.rstage.on')].map(e => e.dataset.stage),
  topicTop: document.getElementById('rpTop0') ? document.getElementById('rpTop0').textContent : null,
  volSvg: document.getElementById('rpVolBox').querySelector('svg') != null,
  feedCards: document.getElementById('feedBox').children.length
}));
console.log('②段:', JSON.stringify(s2));
console.log(s2.stagesOn.includes('2') && s2.volSvg && s2.feedCards >= 2 ? '[PASS] ②段点亮+曲线+瀑布流加速' : '[FAIL] ②段异常');

console.log('=== 4. 跳到③段：致哀句 + 阶梯 + 损毁卡 ===');
await page.click('#rpBtnNext');
await sleep(600);
await page.evaluate(() => rpJumpTo(900));   /* 推进到首档+二档官方通报后，验证阶梯逐档出现 */
await page.waitForFunction(() => document.getElementById('rpLadderBox').children.length >= 1, { timeout: 10000 });
const s3 = await page.evaluate(() => ({
  stagesOn: [...document.querySelectorAll('.rstage.on')].map(e => e.dataset.stage),
  mourn: document.body.textContent.includes('谨以致哀'),
  ladder: document.getElementById('rpLadderBox').children.length,
  ladderTxt: document.getElementById('rpLadderBox').textContent.slice(0, 60),
  cmp: document.body.textContent.includes('官方首报 03-28 19:15') && document.body.textContent.includes('震后约 5 分钟社媒已在传伤亡数字'),
  dmgCards: document.getElementById('rpDmgCards').style.display
}));
console.log('③段:', JSON.stringify(s3));
console.log(s3.mourn && s3.ladder >= 1 && s3.cmp ? '[PASS] ③段致哀+阶梯+对比论证句' : '[FAIL] ③段异常');
await page.locator('#replayTheater').screenshot({ path: SHOT + '/t12_02_stage3.png' });

console.log('=== 5. 跳到④段并到 40h 锚点 → 幕间卡 ===');
await page.click('#rpBtnNext');
await sleep(600);
await page.evaluate(() => rpJumpTo(2409));   /* 直接推进到 40h 锚点验证幕间卡 */
await sleep(800);
const s4 = await page.evaluate(() => ({
  stagesOn: [...document.querySelectorAll('.rstage.on')].map(e => e.dataset.stage),
  a18: document.getElementById('rpAnchor18').textContent.startsWith('✅'),
  a40: document.getElementById('rpAnchor40').textContent.startsWith('✅'),
  interVisible: document.getElementById('rpIntermission').style.display !== 'none',
  interBtn: document.getElementById('rpGoCmd').textContent
}));
console.log('④段:', JSON.stringify(s4));
console.log(s4.a18 && s4.a40 && s4.interVisible && s4.interBtn.includes('数字孪生') ? '[PASS] 锚点点亮+幕间卡出现' : '[FAIL] ④段/幕间异常');
await page.click('#rpGoCmd');
await sleep(1200);
const goLog = await page.evaluate(() => document.getElementById('logBox').textContent.includes('已进入第二幕'));
console.log(goLog ? '[PASS] 幕间按钮可点并提示沙盘就绪' : '[FAIL] 幕间按钮异常');
await page.screenshot({ path: SHOT + '/t12_03_intermission.png', fullPage: true });

console.log('=== 6. 暂停/继续 ===');
await page.click('#rpBtnPause');
const c1 = await page.evaluate(() => document.getElementById('rpClockTxt').textContent);
await sleep(1500);
const c2 = await page.evaluate(() => document.getElementById('rpClockTxt').textContent);
await page.click('#rpBtnPause');
console.log(c1 === c2 ? '[PASS] 暂停时时钟冻结' : '[FAIL] 暂停失效 ' + c1 + ' → ' + c2);

console.log('=== 7. 错误汇总 ===');
console.log(errs.length ? errs : '无页面错误');
await browser.close();
console.log('=== 完成 ===');
