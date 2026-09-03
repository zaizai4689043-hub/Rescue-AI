import { chromium } from 'playwright';

/* T15 验收：多阶段救援流程 + 语音联络（五阶段状态机 / 喊话秒回 / 余震暂停破拆） */
const SHOT = '/Users/zaizai/Downloads/AI地震救援/screenshots';
const URL = 'http://localhost:8010/';
const sleep = ms => new Promise(r => setTimeout(r, ms));
let fail = 0;

async function waitLog(page, keyword, timeout = 30000) {
  const t0 = Date.now();
  while (Date.now() - t0 < timeout) {
    const hit = await page.evaluate(k => document.getElementById('logBox').textContent.includes(k), keyword);
    if (hit) return Date.now() - t0;
    await sleep(300);
  }
  return -1;
}
function pass(msg) { console.log('[PASS] ' + msg); }
function FAIL(msg) { fail++; console.log('[FAIL] ' + msg); }

const browser = await chromium.launch({ headless: true });

/* ================= 主模式：五阶段全流程 + 喊话 + 余震暂停 ================= */
{
  const page = await (await browser.newContext({ viewport: { width: 1440, height: 1200 } })).newPage();
  await page.route(u => String(u).includes(':8012'), r => r.abort());   /* 环境隔离：阻断实时社情层 8012，结果与 live_feed 是否在跑无关 */
  const errs = [];
  const aborted8012 = { n: 0, exempted: 0 };
  page.on('requestfailed', r => { if (r.url().includes(':8012')) aborted8012.n++; });   /* 精确登记被阻断的 8012 请求 */
  page.on('pageerror', e => errs.push(String(e)));
  page.on('console', m => {
    if (m.type() !== 'error') return;
    /* 8012 为可选实时社情层服务，上方 page.route 阻断属测试环境控制；
       被阻断请求产生的 net::ERR_FAILED 为隔离机制产物，非产品缺陷——但仅当该失败确属 :8012 请求才豁免：
       console 文本可能不含 URL，故以 requestfailed 登记的 8012 失败数为限逐条抵扣；
       其他来源的 ERR_FAILED 仍照常计入 */
    const t = m.text();
    if (t.includes('net::ERR_FAILED') && (t.includes(':8012') || aborted8012.exempted < aborted8012.n)) {
      aborted8012.exempted++; return;
    }
    /* 环境豁免：纯静态服务器无代理后端时，/ai/proxy POST 501 与 /seismic/feed、/icl/warnings 404 属预期降级路径（页面自动走离线兜底） */
    if (t.includes('Failed to load resource') && (t.includes('501') || t.includes('404'))) return;
    errs.push(t);
  });

  console.log('=== 1. 加载 + warmup 预热（含喊话缓存） ===');
  await page.goto(URL, { waitUntil: 'load' });
  await page.waitForFunction(() => AI.cache.quake || AI.fallbackCount > 0, { timeout: 20000 }).catch(() => {});
  const warm = await page.evaluate(() => ({ quake: !!AI.cache.quake, shout: !!AI.cache.shout, STAGE_T, STAGE_NAMES }));
  console.log('warmup:', JSON.stringify(warm));
  console.log('STAGE_T 固定阶段时长合计 = ' + warm.STAGE_T.slice(1).reduce((a, b) => a + b, 0) + 's（另有开进路径移动时间）');

  console.log('=== 2. 起飞搜索 → 发现 → 派遣 → 五阶段推进 ===');
  await page.click('#btnScan');
  await page.waitForFunction(() => survivors.some(s => s.discovered), { timeout: 60000 });
  await page.click('[data-go]:not([disabled])');
  await page.click('#btnDispatchConfirm');   /* WP10：派遣二次确认弹窗 → 先点「确认派遣 · 推演」 */
  const svId = await page.evaluate(() => S.teams[0].sv.id);
  console.log('派遣目标:', svId);
  await page.evaluate(id => selectSurvivor(id), svId);

  /* 记录阶段推进轨迹 + 阶段2喊话点击 */
  const t0 = Date.now();
  const trace = [];
  let lastStage = -1, shouted = false, shoutMs = -1, shoutSrc = '';
  let team = true;
  while (team && Date.now() - t0 < 120000) {
    const st = await page.evaluate(id => {
      const tm = S.teams.find(t => t.sv.id === id);
      const sv = survivors.find(s => s.id === id);
      return tm ? { stage: tm.stage, stageT: +tm.stageT.toFixed(2), paused: tm.paused, shoutText: !!sv.shoutText } : null;
    }, svId);
    if (!st) { team = false; break; }
    if (st.stage !== lastStage) {
      trace.push({ stage: st.stage, atMs: Date.now() - t0 });
      console.log(`  阶段推进 → ${st.stage}（T+${((Date.now() - t0) / 1000).toFixed(1)}s）`);
      lastStage = st.stage;
    }
    if (!shouted && st.stage === 2) {
      shouted = true;
      const hasBtn = await page.$('#detailBox [data-shout]');
      if (hasBtn) {
        const tS = Date.now();
        await hasBtn.click();
        await page.waitForFunction(id => !!survivors.find(s => s.id === id).shoutText, svId, { timeout: 10000 }).catch(() => {});
        shoutMs = Date.now() - tS;
        shoutSrc = await page.evaluate(id => survivors.find(s => s.id === id).shoutSrc, svId);
      } else FAIL('阶段2未渲染喊话按钮');
    }
    await sleep(250);
  }
  const totalMs = Date.now() - t0;
  console.log('阶段轨迹:', JSON.stringify(trace));
  console.log(`派遣→救出总时长 = ${(totalMs / 1000).toFixed(1)}s`);
  const stageSeq = trace.map(t => t.stage).join('>');
  (stageSeq === '0>1>2>3>4') ? pass('五阶段逐段推进 0>1>2>3>4') : FAIL('阶段序列异常: ' + stageSeq);
  (totalMs >= 28000 && totalMs <= 65000) ? pass('总时长在 30-60s 演示节奏区间附近') : FAIL('总时长超出预期: ' + totalMs + 'ms');
  const wRescue = await waitLog(page, '已成功营救', 5000);
  (wRescue >= 0) ? pass('成功营救日志出现（文案冻结完好）') : FAIL('成功营救日志缺失');
  const anchor = await page.evaluate(() => document.getElementById('logBox').textContent.includes('对照真实战例'));
  anchor ? pass('缅甸化对照锚点小字出现（18h/40h）') : FAIL('缅甸化锚点缺失');

  console.log('=== 3. 喊话气泡（预热缓存秒回验证） ===');
  const bubble = await page.evaluate(id => {
    const sv = survivors.find(s => s.id === id);
    return { text: sv.shoutText, src: sv.shoutSrc, inDetail: document.getElementById('detailBox').textContent.includes(sv.shoutText || '∅') };
  }, svId);
  console.log('喊话气泡:', JSON.stringify(bubble));
  (bubble.text && bubble.inDetail) ? pass('喊话气泡已显示在详情框') : FAIL('气泡缺失');
  console.log(`喊话响应耗时 ${shoutMs}ms（src=${shoutSrc}）`);
  (shoutSrc === 'cache' && shoutMs <= 2000) ? pass('预热缓存命中且 ≤2s 秒回') : (shoutMs <= 2000 ? pass('≤2s 出气泡（src=' + shoutSrc + '）') : FAIL('喊话响应超时 ' + shoutMs + 'ms'));
  await page.screenshot({ path: SHOT + '/t15_01_rescued.png', fullPage: false });

  console.log('=== 4. 余震联动：手动4.2不暂停 / M6.7 暂停破拆 ===');
  await page.waitForFunction(() => survivors.some(s => s.discovered && !s.rescued && !s.team), { timeout: 90000 });
  await page.evaluate(() => { const sv = survivors.find(s => s.discovered && !s.rescued && !s.team); dispatch(sv); });
  const id2 = await page.evaluate(() => S.teams[S.teams.length - 1].sv.id);
  console.log('第二目标:', id2);
  await page.waitForFunction(id => { const tm = S.teams.find(t => t.sv.id === id); return tm && tm.stage === 3; }, id2, { timeout: 60000 });
  await page.evaluate(() => triggerQuake(4.2, '4.2 级余震'));
  await sleep(600);
  const p1 = await page.evaluate(id => S.teams.find(t => t.sv.id === id).paused, id2);
  (!p1) ? pass('手动 4.2 级余震不触发暂停') : FAIL('4.2 级误触发暂停');
  const stBefore = await page.evaluate(id => S.teams.find(t => t.sv.id === id).stageT, id2);
  await page.evaluate(() => triggerQuake(6.7, '测试强余震', false));
  await sleep(400);
  const p2 = await page.evaluate(id => { const tm = S.teams.find(t => t.sv.id === id); return { paused: tm.paused, stageT: tm.stageT }; }, id2);
  const wPause = await waitLog(page, '破拆作业暂停', 3000);
  (p2.paused && wPause >= 0) ? pass('M6.7 触发破拆暂停 + 日志出现') : FAIL('M6.7 未暂停 ' + JSON.stringify(p2));
  await sleep(1200);
  const stMid = await page.evaluate(id => S.teams.find(t => t.sv.id === id).stageT, id2);
  (Math.abs(stMid - stBefore) < 0.05) ? pass('暂停期间 stageT 冻结') : FAIL(`stageT 仍在增长 ${stBefore}→${stMid}`);
  const cardPause = await page.evaluate(() => document.getElementById('queueBox').textContent.includes('余震暂停'));
  cardPause ? pass('卡片显示余震暂停标记') : FAIL('卡片无暂停标记');
  await page.waitForFunction(id => { const tm = S.teams.find(t => t.sv.id === id); return !tm || !tm.paused; }, id2, { timeout: 6000 });
  const wResume = await waitLog(page, '破拆支护作业恢复', 3000);
  const stAfter = await page.evaluate(id => { const tm = S.teams.find(t => t.sv.id === id); return tm ? tm.stageT : -1; }, id2);
  (wResume >= 0 && stAfter > stMid) ? pass('约 3s 后自动恢复作业') : FAIL('恢复异常');
  await page.screenshot({ path: SHOT + '/t15_02_quake_pause.png', fullPage: false });

  console.log('主模式页面错误:', errs.length ? errs : '无');
  errs.length ? FAIL('主模式存在页面错误') : pass('主模式无页面错误');
  await page.close();
}

/* ================= ?sim=1 保险丝：喊话走 FALLBACK、零网络请求、未点击置信度↓ ================= */
{
  const page = await (await browser.newContext({ viewport: { width: 1440, height: 1200 } })).newPage();
  await page.route(u => String(u).includes(':8012'), r => r.abort());   /* 环境隔离：阻断实时社情层 8012，结果与 live_feed 是否在跑无关 */
  const errs = [];
  const proxyReqs = [];
  const aborted8012 = { n: 0, exempted: 0 };
  page.on('requestfailed', r => { if (r.url().includes(':8012')) aborted8012.n++; });
  page.on('pageerror', e => errs.push(String(e)));
  page.on('console', m => {
    if (m.type() !== 'error') return;
    /* 与主块同口径：仅豁免被 page.route 阻断的 :8012 请求产生的 net::ERR_FAILED（按登记数逐条抵扣） */
    const t = m.text();
    if (t.includes('net::ERR_FAILED') && (t.includes(':8012') || aborted8012.exempted < aborted8012.n)) {
      aborted8012.exempted++; return;
    }
    /* 环境豁免：同主块口径（静态服务器无代理后端的 501/404 属预期降级路径） */
    if (t.includes('Failed to load resource') && (t.includes('501') || t.includes('404'))) return;
    errs.push(t);
  });
  page.on('request', r => { if (r.url().includes('/ai/proxy')) proxyReqs.push(r.url()); });

  console.log('=== 5. ?sim=1：派遣 + 喊话 FALLBACK + 未点击置信度↓ ===');
  await page.goto(URL + '?sim=1', { waitUntil: 'load' });
  await sleep(2000);
  await page.click('#btnScan');
  await page.waitForFunction(() => survivors.some(s => s.discovered), { timeout: 60000 });
  await page.click('[data-go]:not([disabled])');
  await page.click('#btnDispatchConfirm');   /* WP10：派遣二次确认弹窗 → 先点「确认派遣 · 推演」 */
  const svId = await page.evaluate(() => S.teams[0].sv.id);
  await page.evaluate(id => selectSurvivor(id), svId);
  /* 阶段2点击喊话 → FALLBACK 气泡 */
  await page.waitForFunction(id => { const tm = S.teams.find(t => t.sv.id === id); return tm && tm.stage === 2; }, svId, { timeout: 60000 });
  const tS = Date.now();
  await page.click('#detailBox [data-shout]');
  await page.waitForFunction(id => !!survivors.find(s => s.id === id).shoutText, svId, { timeout: 8000 });
  const simShout = await page.evaluate(id => ({ text: survivors.find(s => s.id === id).shoutText, src: survivors.find(s => s.id === id).shoutSrc, dt: Date.now() }), svId);
  console.log('sim 喊话:', JSON.stringify({ ...simShout, ms: Date.now() - tS }));
  (simShout.src === 'fallback') ? pass('sim 模式喊话走 FALLBACK 兜底文案') : FAIL('sim 喊话 src 异常: ' + simShout.src);
  await page.screenshot({ path: SHOT + '/t15_03_sim_fallback.png', fullPage: false });
  /* A 走完流程 */
  await waitLog(page, '已成功营救', 90000);
  await page.waitForFunction(id => !S.teams.some(t => t.sv.id === id), svId, { timeout: 90000 });
  /* B：不点击喊话 → 未建立有效回应 + 联络置信度↓ */
  await page.waitForFunction(() => survivors.some(s => s.discovered && !s.rescued && !s.team), { timeout: 90000 });
  await page.evaluate(() => { const sv = survivors.find(s => s.discovered && !s.rescued && !s.team); dispatch(sv); });
  const idB = await page.evaluate(() => S.teams[S.teams.length - 1].sv.id);
  const wNo = await waitLog(page, '未建立有效回应', 60000);
  (wNo >= 0) ? pass('未点击喊话 → 按预案继续作业日志出现') : FAIL('无「未建立有效回应」日志');
  await sleep(500);
  const lowConf = await page.evaluate(() => document.getElementById('queueBox').textContent.includes('联络置信度↓'));
  lowConf ? pass('卡片标注「联络置信度↓」') : FAIL('卡片缺少联络置信度↓');
  (proxyReqs.length === 0) ? pass('sim 模式零 /ai/proxy 网络请求') : FAIL('sim 模式发出网络请求: ' + proxyReqs.length);
  console.log('sim 页面错误:', errs.length ? errs : '无');
  errs.length ? FAIL('sim 模式存在页面错误') : pass('sim 模式无页面错误');
  await page.close();
}

await browser.close();
console.log('=== T15 验收' + (fail === 0 ? '全部 PASS' : '存在 ' + fail + ' 项 FAIL') + ' ===');
process.exit(fail === 0 ? 0 : 1);
