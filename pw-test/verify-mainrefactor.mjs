// 主界面改造验收：①普通模式开屏即现（热力图/仪表盘/区域优先级/AI 决策区）
//                ②按钮闭环（简报/决策助手主界面入口）③?replay=1 剧场无回归
// 用法：node verify-mainrefactor.mjs （需 8010 端口 ai_proxy 在跑）
import { chromium } from 'playwright';

const BASE = 'http://127.0.0.1:8010/';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fail = 0;
const ok = (name, cond, extra = '') => {
  console.log((cond ? '✅' : '❌') + ' ' + name + (extra ? ' · ' + extra : ''));
  if (!cond) fail++;
};

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1720, height: 1100 } });
await page.route(u => String(u).includes(':8012'), r => r.abort());   /* 环境隔离：阻断实时社情层 8012，结果与 live_feed 是否在跑无关 */
const errs = [];
page.on('pageerror', (e) => errs.push('pageerror: ' + e.message));
page.on('console', (m) => { if (m.type() === 'error') errs.push('console: ' + m.text()); });

/* ===== 1) 普通模式（sim 零请求） ===== */
await page.goto(BASE + '?sim=1', { waitUntil: 'load' });
await sleep(2500);

const snap = await page.evaluate(() => ({
  heatCanvas: !!document.getElementById('mapCanvas') && document.getElementById('mapCanvas').width > 100,   /* 社情热力已并入主地图 */
  ovSocialChecked: document.getElementById('ovSocial').checked,
  heatPixels: (() => {
    const c = document.getElementById('mapCanvas');
    const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
    let n = 0; for (let i = 3; i < d.length; i += 4) if (d[i] > 0) n++;
    return n;
  })(),
  priChildren: document.getElementById('mainPriorityBox').children.length,
  priText: document.getElementById('mainPriorityBox').textContent,
  donut: document.getElementById('mainDmgDonut').innerHTML.includes('<svg'),
  kw: document.getElementById('mainKwBars').innerHTML.includes('<svg'),
  senti: document.getElementById('mainSentiTimeline').innerHTML.includes('<svg'),
  briefSim: document.getElementById('mainBriefBox').textContent,
  advisorSim: document.getElementById('mainAdvisorBox').textContent,
  queueEmpty: document.getElementById('queueBox').textContent,
  btnScan: document.getElementById('btnScan').textContent,
  rpPriEmpty: document.getElementById('rpPriorityBox').innerHTML === '',
  analysisRow: !!document.getElementById('analysisRow'),
}));
ok('普通模式 · 主地图已绘制且社情感知图层默认勾选', snap.heatCanvas && snap.ovSocialChecked && snap.heatPixels > 5000, `非空像素 ${snap.heatPixels}`);
ok('普通模式 · 区域优先级开屏 5 区渲染', snap.priChildren === 5, `children=${snap.priChildren}`);
ok('普通模式 · 优先级含 P0/P1 档位与评分', snap.priText.includes('P0') && snap.priText.includes('评分'), '');
ok('普通模式 · 优先级证据链（社情信号）', snap.priText.includes('社情信号'), '');
ok('普通模式 · 仪表盘三联渲染', snap.donut && snap.kw && snap.senti, `donut=${snap.donut} kw=${snap.kw} senti=${snap.senti}`);
ok('普通模式 · sim 简报预录兜底自动展示', snap.briefSim.includes('预录兜底') && snap.briefSim.includes('1,644'), '');
ok('普通模式 · sim 决策助手预录兜底自动展示', snap.advisorSim.includes('预录兜底') && snap.advisorSim.includes('曼德勒'), '');
ok('普通模式 · 个人队列新空态文案', snap.queueEmpty.includes('区域优先级由社情呼救信号驱动'), '');
ok('普通模式 · 顶栏按钮改名「空中救援」（悬浮于地图面板）', snap.btnScan.includes('空中救援'), snap.btnScan);
ok('普通模式 · 剧场优先级盒保持空白（未进重演）', snap.rpPriEmpty, '');

/* ===== 2) 主界面按钮闭环（sim：点击走兜底，双端同步） ===== */
await page.click('#btnBriefMain');
await sleep(800);
const click1 = await page.evaluate(() => ({
  main: document.getElementById('mainBriefBox').textContent.slice(0, 30),
  theater: document.getElementById('rpBriefBox').textContent.slice(0, 30),
  btnTxt: document.getElementById('btnBriefMain').textContent,
}));
ok('按钮闭环 · 主界面简报点击生成（sim 秒回）', click1.main.startsWith('2025年3月28日'), click1.main);
ok('按钮闭环 · 剧场简报盒同步更新', click1.theater === click1.main, '');
ok('按钮闭环 · 简报按钮变为「重新生成」', click1.btnTxt === '重新生成', click1.btnTxt);

await page.click('#btnAdvisorMain');
await sleep(800);
const click2 = await page.evaluate(() => ({
  main: document.getElementById('mainAdvisorBox').textContent.slice(0, 30),
  theater: document.getElementById('rpAdvisorBox').textContent.slice(0, 30),
}));
ok('按钮闭环 · 主界面决策助手点击生成', click2.main.includes('曼德勒'), click2.main);
ok('按钮闭环 · 剧场决策助手盒同步更新', click2.theater === click2.main, '');

/* ===== 3) 重演模式回归（?replay=1&sim=1） ===== */
await page.goto(BASE + '?replay=1&sim=1', { waitUntil: 'load' });
await sleep(2500);
const theaterVisible = await page.evaluate(() => document.getElementById('replayTheater').style.display !== 'none');
ok('重演模式 · 剧场正常显示', theaterVisible, '');
for (let i = 0; i < 3; i++) { await page.click('#rpBtnNext'); await sleep(900); }   /* 逐段跳至④ */
const rp = await page.evaluate(() => ({
  stage: document.querySelector('#rpClockTxt') ? document.getElementById('rpClockTxt').textContent : '',
  priChildren: document.getElementById('rpPriorityBox').children.length,
  priVisible: document.getElementById('rpPriorityCard').style.display !== 'none',
  briefShown: document.getElementById('rpBriefCard').style.display !== 'none',
  briefTxt: document.getElementById('rpBriefBox').textContent.slice(0, 20),
  mainBriefSync: document.getElementById('mainBriefBox').textContent.slice(0, 20),
  t27Visible: document.getElementById('t27Card').style.display !== 'none',
  charts: document.getElementById('rpDmgDonut').innerHTML.includes('<svg'),
}));
ok('重演模式 · ④段优先级引擎 5 区渲染', rp.priChildren === 5 && rp.priVisible, `children=${rp.priChildren}`);
ok('重演模式 · ③段简报卡出现且已生成', rp.briefShown && rp.briefTxt.length > 10, rp.briefTxt);
ok('重演模式 · 简报双端同步（主界面盒同号）', rp.mainBriefSync === rp.briefTxt, '');
ok('重演模式 · ④段空中救援行动卡出现', rp.t27Visible, '');
ok('重演模式 · 剧场图表三联正常', rp.charts, '');

ok('全程无 JS 错误', errs.length === 0, errs.slice(0, 3).join(' | '));
await browser.close();
console.log(fail === 0 ? '\n🎉 主界面改造验收全部通过' : `\n⚠️ ${fail} 项未通过`);
process.exit(fail === 0 ? 0 : 1);
