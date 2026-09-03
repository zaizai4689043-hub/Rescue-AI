import { chromium } from 'playwright';

/* Task #11 自测：WP1/WP2/WP3/WP4/WP5/WP10/WP11 冒烟（四种 URL 徽标文案 / 角标 / 页脚 / 派遣确认 / 上报） */
const URL = 'http://localhost:8010/';
const sleep = ms => new Promise(r => setTimeout(r, ms));
let fail = 0;
const pass = m => console.log('[PASS] ' + m);
const FAIL = m => { fail++; console.log('[FAIL] ' + m); };

const browser = await chromium.launch({ headless: true });

async function newPage(extraRoute) {
  const page = await (await browser.newContext({ viewport: { width: 1440, height: 1200 } })).newPage();
  const errs = [];
  page.on('pageerror', e => errs.push(String(e)));
  page.on('console', m => {
    if (m.type() !== 'error') return;
    const t = m.text();
    /* 环境豁免：静态服务器无代理后端，/ai/proxy POST 501 与 /seismic/feed、/icl/warnings 404 属预期降级路径（页面自动走离线兜底）；真实 pageerror 仍计入 */
    if (t.includes('Failed to load resource') && (t.includes('501') || t.includes('404'))) return;
    if (t.includes('net::ERR')) return;
    errs.push(t);
  });
  return { page, errs };
}

/* ---------- 1. 默认 LIVE 模式 ---------- */
{
  const { page, errs } = await newPage();
  await page.goto(URL, { waitUntil: 'load' });
  await sleep(1500);
  const badge = await page.textContent('#modeBadge');
  (badge === 'LIVE · 真实数据流（离线自动兜底）') ? pass('WP1 LIVE 徽标文案精确匹配') : FAIL('LIVE 徽标异常: ' + badge);
  const r = await page.evaluate(() => {
    const t = document.body.textContent;
    return {
      tag1: t.includes('数字孪生推演样本 · 人员与设备非真实'),
      tag2: t.includes('数字孪生仿真驱动 · 遥测协议已预留（DJI Cloud API / MAVLink）'),
      tag4: t.includes('仿真投送动画 · 目标=优先级引擎第一名区域（真实引擎结果）'),
      note: t.includes('沙盘推演中的被困者为数字孪生推演样本，与真实数据边界清晰标注。'),
      wp3: (() => { const n = document.getElementById('ovSocialNote'); return n && n.offsetParent !== null && n.textContent.includes('词典定位') && n.textContent.includes('0.85') && n.textContent.includes('0.4'); })(),
      reportBtns: document.querySelectorAll('.rpReportBtn').length,
      advisorTag: t.includes('Qwen3.8-Max · ?sim=1 走预录兜底 ｜ 建议类输出，供救援指挥参考，不替代专业判断。')
    };
  });
  r.tag1 ? pass('WP2 角标① 队列区「数字孪生推演样本 · 人员与设备非真实」') : FAIL('WP2 角标①缺失');
  r.tag2 ? pass('WP2 角标② 无人机遥测「数字孪生仿真驱动 · 遥测协议已预留」') : FAIL('WP2 角标②缺失');
  r.tag4 ? pass('WP2 角标④ 物资投送「仿真投送动画 · 目标=优先级引擎第一名区域」') : FAIL('WP2 角标④缺失');
  r.note ? pass('WP2 统一脚注句') : FAIL('WP2 统一脚注缺失');
  r.wp3 ? pass('WP3 ovSocial 图层标注可见且含 词典定位/0.85/0.4') : FAIL('WP3 标注异常');
  (r.reportBtns > 0) ? pass('WP11 P0/P1 上报按钮存在 ×' + r.reportBtns) : FAIL('WP11 上报按钮缺失');
  r.advisorTag ? pass('WP4 决策助手静态来源徽标') : FAIL('WP4 静态徽标缺失');

  /* WP11 上报点击 → 状态 + 日志 */
  await page.click('.rpReportBtn');
  await sleep(300);
  const rep = await page.evaluate(() => ({
    status: document.body.textContent.includes('已上报 · 待现场指挥部批复'),
    log: document.getElementById('logBox').textContent.includes('已提交现场指挥部，等待人工批复')
  }));
  (rep.status && rep.log) ? pass('WP11 上报后状态文案 + 日志行均出现') : FAIL('WP11 上报流异常 ' + JSON.stringify(rep));

  /* WP5 页脚展开 */
  await page.evaluate(() => { document.getElementById('capabilityFooter').open = true; });
  await sleep(200);
  const f = await page.evaluate(() => {
    const el = document.getElementById('capabilityFooter');
    const t = el.textContent;
    return {
      legend: t.includes('真实数据验证') && t.includes('历史重演') && t.includes('仿真动画'),
      table: t.includes('us7000pn9s') && t.includes('chinaeew.cn') && t.includes('lost_contact.json') && t.includes('曼德勒真实卫星影像') && t.includes('53,340') && t.includes('新华社'),
      s7: t.includes('RescueAI 是辅助决策系统，不替代专业救援判断。系统输出的一切简报、评分、优先级与建议，均为辅助参考信息。')
        && t.includes('一切救援行动以现场指挥部与专业救援力量的判断为准；系统不承担任何行动指令职能。')
        && t.includes('震级 CENC 中国地震台网 7.9 级 / USGS Mw 7.7（双口径并列，引用须注明来源）；死亡人数截至 3/29 晚通报 1,644 人，持续更新中')
        && t.includes('沙盘推演中的被困者为数字孪生推演样本，与真实数据边界清晰标注。'),
      tail: t.trimEnd().endsWith('RescueAI 是辅助决策系统，不替代专业救援判断。'),
      wf: t.includes('完整审批工作流：决赛后随平台化推进')
    };
  });
  f.legend ? pass('WP5 三类能力图例') : FAIL('WP5 图例缺失');
  f.table ? pass('WP5 真实数据来源表六行关键词全命中') : FAIL('WP5 来源表不全');
  f.s7 ? pass('WP5 §7 四条责任边界声明逐字命中') : FAIL('WP5 §7 声明不全');
  f.tail ? pass('WP5 尾行（§7.1）') : FAIL('WP5 尾行缺失');
  f.wf ? pass('WP11 完整审批工作流排期表述') : FAIL('审批排期表述缺失');

  /* WP10 派遣确认流：取消 → 不派遣；确认 → 五阶段 + 徽标 */
  await page.click('#btnScan');
  await page.waitForFunction(() => survivors.some(s => s.discovered), { timeout: 60000 });
  await page.click('[data-go]:not([disabled])');
  await sleep(200);
  const modalVisible = await page.evaluate(() => document.getElementById('dispatchModal').style.display === 'flex');
  const modalText = await page.evaluate(() => document.getElementById('dispatchModal').textContent);
  modalVisible ? pass('WP10 点击派遣先出弹窗') : FAIL('WP10 弹窗未出现');
  modalText.includes('最终决定权在现场指挥部') ? pass('WP10 弹窗含「最终决定权在现场指挥部」逐字串') : FAIL('WP10 弹窗文案异常');
  await page.click('#btnDispatchCancel');
  await sleep(200);
  const noTeam = await page.evaluate(() => S.teams.length === 0 && document.getElementById('dispatchModal').style.display === 'none');
  noTeam ? pass('WP10 「再想想」不触发五阶段') : FAIL('WP10 取消仍派遣');
  await page.click('[data-go]:not([disabled])');
  await page.click('#btnDispatchConfirm');
  await sleep(400);
  const confirmed = await page.evaluate(() => ({
    team: S.teams.length === 1,
    badge: document.getElementById('queueBox').textContent.includes('已确认（人工）· 推演中'),
    tag3: document.body.textContent.includes('推演样本 · 五阶段状态机演示'),
    confLog: document.getElementById('logBox').textContent.includes('派遣已经人工确认')
  }));
  confirmed.team ? pass('WP10 确认后进入五阶段推演') : FAIL('WP10 确认后未派遣');
  confirmed.badge ? pass('WP10 确认状态徽标「已确认（人工）· 推演中」') : FAIL('WP10 确认徽标缺失');
  confirmed.tag3 ? pass('WP2 角标③ 五阶段状态条「推演样本 · 五阶段状态机演示」') : FAIL('WP2 角标③缺失');
  confirmed.confLog ? pass('WP10 人工确认日志') : FAIL('WP10 确认日志缺失');

  /* 滚动 800px 后徽标仍可见（sticky 顶栏） */
  await page.evaluate(() => window.scrollTo(0, 800));
  await sleep(300);
  const sticky = await page.evaluate(() => { const b = document.getElementById('modeBadge'); const r = b.getBoundingClientRect(); return r.top >= 0 && r.bottom <= window.innerHeight; });
  sticky ? pass('WP1 滚动 800px 后徽标仍可见') : FAIL('WP1 徽标非常驻');
  console.log('LIVE 模式页面错误:', errs.length ? errs : '无');
  errs.length ? FAIL('LIVE 模式存在页面错误') : pass('LIVE 模式无页面错误');
  await page.close();
}

/* ---------- 2. 四种 URL 徽标文案 ---------- */
for (const [qs, expect] of [
  ['?replay=1', 'REPLAY · 历史重演（真实时间轴 ×90 压缩）'],
  ['?sim=1', 'SIM · 纯仿真保险丝（0 AI 请求 · 0 网络依赖）'],
  ['?replay=1&sim=1', 'REPLAY + SIM · 历史重演 × 仿真兜底']
]) {
  const { page, errs } = await newPage();
  const proxyReqs = [];
  page.on('request', r => { if (r.url().includes('/ai/proxy')) proxyReqs.push(r.url()); });
  await page.goto(URL + qs, { waitUntil: 'load' });
  await sleep(2500);
  const badge = await page.textContent('#modeBadge');
  (badge === expect) ? pass('WP1 徽标文案精确匹配: ' + expect) : FAIL('徽标异常 [' + qs + ']: ' + badge);
  const tags = await page.evaluate(() => {
    const t = document.body.textContent;
    return t.includes('数字孪生推演样本 · 人员与设备非真实') && t.includes('仿真投送动画 · 目标=优先级引擎第一名区域（真实引擎结果）');
  });
  tags ? pass('WP2 角标在 ' + qs + ' 可检索') : FAIL('WP2 角标在 ' + qs + ' 缺失');
  const footerOk = await page.evaluate(() => { document.getElementById('capabilityFooter').open = true; return document.getElementById('capabilityFooter').textContent.includes('责任边界'); });
  footerOk ? pass('WP5 页脚在 ' + qs + ' 可展开') : FAIL('WP5 页脚在 ' + qs + ' 异常');
  if (qs === '?sim=1') {
    const advTag = await page.evaluate(() => document.body.textContent.includes('Qwen3.8-Max 预录兜底 · ?sim=1 走预录兜底'));
    advTag ? pass('WP4 sim 下决策助手徽标显示「预录兜底」') : FAIL('WP4 sim 徽标异常');
    (proxyReqs.length === 0) ? pass('sim 模式外部 /ai/proxy 请求 = 0') : FAIL('sim 模式发出请求 ×' + proxyReqs.length);
  }
  console.log(qs + ' 页面错误:', errs.length ? errs : '无');
  errs.length ? FAIL(qs + ' 存在页面错误') : pass(qs + ' 无页面错误');
  await page.close();
}

await browser.close();
console.log('=== Task#11 自测 ' + (fail === 0 ? '全部 PASS' : '存在 ' + fail + ' 项 FAIL') + ' ===');
process.exit(fail === 0 ? 0 : 1);
