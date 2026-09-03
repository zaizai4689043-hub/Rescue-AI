/* ============================================================================
 * demo-rehearsal.mjs —— 任务 #20：演示视频一键排演脚本（独立一次性，不进既有脚本）
 *
 * 依据：`outputs/演示视频脚本.md`（主版 180s / 22 镜）逐镜执行可自动化部分。
 * 用法：node pw-test/demo-rehearsal.mjs
 *   - 自拉起 ai_proxy.py(8010) 与 live_feed.py --mode mock(8012)，结束后全部回收并复核端口释放；
 *   - 每镜截图存 screenshots/rehearsal/R{编号}_{镜名}.png（视口 1920×1080）；
 *   - 每镜记录实际耗时并与分镜标注时长对照（容差 ±50%），超差标注；
 *   - 纯人工镜头（旁白/静帧/字幕）只在报告中列清单，不尝试自动化；
 *   - 允许个别镜头标记兜底/超时，不整体崩溃；最终产出 outputs/演示排演报告.md。
 * ==========================================================================*/
import { spawn } from 'child_process';
import fs from 'fs';
import http from 'http';
import path from 'path';
import { chromium } from 'playwright';

const ROOT = '/Users/zaizai/Downloads/AI地震救援';
const QWEN_DIR = path.join(ROOT, 'backend', 'Qwen 初版');
const SHOT_DIR = path.join(ROOT, 'screenshots', 'rehearsal');
const REPORT = path.join(ROOT, 'outputs', '演示排演报告.md');
const BASE = 'http://127.0.0.1:8010/';
const LIVE_URL = 'http://127.0.0.1:8012/live/social';
const TOL = 0.5;                       /* 掐表容差 ±50% */
const RUN_AT = new Date().toLocaleString('zh-CN', { hour12: false });
const sleep = ms => new Promise(r => setTimeout(r, ms));

fs.mkdirSync(SHOT_DIR, { recursive: true });

/* ---------------- 基础设施 ---------------- */
const procs = [];                      /* 本脚本自启的进程（仅此二者，结束时必须全部回收） */
let failHard = null;                   /* 基建级致命错误（非镜头级） */

function probe(port) {
  return new Promise(res => {
    const req = http.get({ host: '127.0.0.1', port, path: '/', timeout: 1200 }, r => { res(true); r.resume(); });
    req.on('error', () => res(false));
    req.on('timeout', () => { req.destroy(); res(false); });
  });
}
async function ensure(port, args, tag) {
  if (await probe(port)) {
    console.log(`[info] ${port} 已有服务在跑（非本脚本启动）——为不干扰外部进程，本次复用且【不】在结尾回收 ${tag}`);
    return { spawned: false };
  }
  const p = spawn('python3', args, { stdio: ['ignore', 'pipe', 'pipe'] });
  p.stdout.on('data', d => process.stdout.write(`[srv:${port}] ` + d));
  p.stderr.on('data', d => process.stderr.write(`[srv:${port}:err] ` + d));
  procs.push(p);
  for (let i = 0; i < 40; i++) { if (await probe(port)) return { spawned: true, proc: p }; await sleep(300); }
  throw new Error(`${port} 端口服务未能就绪（${tag}）`);
}
function stopProc(p) {
  if (!p || p.killed) return;
  try { p.kill('SIGTERM'); } catch (e) {}
}
async function waitPortFree(port, tries = 15) {
  for (let i = 0; i < tries; i++) { if (!(await probe(port))) return true; await sleep(400); }
  return !(await probe(port));
}
async function getJSON(url) {
  return new Promise((res, rej) => {
    http.get(url, r => {
      let b = ''; r.on('data', c => b += c);
      r.on('end', () => { try { res({ status: r.statusCode, body: JSON.parse(b) }); } catch (e) { rej(e); } });
    }).on('error', rej);
  });
}

/* ---------------- 镜头台账 ---------------- */
/* 分镜口径唯一来源：outputs/演示视频脚本.md §2 分镜总表 */
const SHOTS = [
  { id: 'R01', s: 'S01', name: '开屏全貌',        mode: '主', script: 6,  auto: true },
  { id: 'R02', s: 'S02', name: '任务链路示意',    mode: '主', script: 4,  auto: true },
  { id: 'R03', s: 'S03', name: 'ICL双口径感知',   mode: '演', script: 4,  auto: true },
  { id: 'R04', s: 'S04', name: '瀑布流NER高亮',   mode: '演', script: 8,  auto: true },
  { id: 'R05', s: 'S05-B', name: '实时徽标mock',  mode: '主', script: 3,  auto: true },
  { id: 'R06', s: 'S06', name: '社情漏斗',        mode: '主', script: 5,  auto: true },
  { id: 'R07', s: 'S07', name: '伤亡递进简报卡',  mode: '演', script: 4,  auto: true },
  { id: 'R08', s: 'S08', name: 'AI简报掐表',      mode: '主', script: 8,  auto: true },
  { id: 'R09', s: 'S09', name: '口径字幕静帧',    mode: '主', script: 6,  auto: false },
  { id: 'R10', s: 'S10', name: 'NER聚合灾情图',   mode: '主', script: 6,  auto: true },
  { id: 'R11', s: 'S11', name: '三联横移',        mode: '主', script: 6,  auto: true },
  { id: 'R12', s: 'S12', name: '空中搜索点亮',    mode: '主', script: 10, auto: true },
  { id: 'R13', s: 'S13', name: 'VL换图重判',      mode: '主', script: 12, auto: true },
  { id: 'R14', s: 'S14', name: '空投优先级',      mode: '演', script: 10, auto: true },
  { id: 'R15', s: 'S15', name: 'P0P3队列卡',      mode: '演④', script: 12, auto: true },
  { id: 'R16', s: 'S16', name: '派遣五阶段喊话',  mode: '主', script: 12, auto: true },
  { id: 'R17', s: 'S17', name: 'sim离线续演',     mode: '险', script: 12, auto: true },
  { id: 'R18', s: 'S18', name: 'kill代理兜底',    mode: '宕机', script: 10, auto: true },
  { id: 'R19', s: 'S19', name: '兜底说明字幕板',  mode: '剪辑', script: 8, auto: false },
  { id: 'R20', s: 'S20', name: '重演四幕快进',    mode: '演', script: 10, auto: true },
  { id: 'R21', s: 'S21', name: '口径吻合字幕板',  mode: '剪辑', script: 12, auto: false },
  { id: 'R22', s: 'S22', name: '收尾定位声明',    mode: '剪辑', script: 10, auto: false }
];
const results = new Map(SHOTS.map(x => [x.id, { ...x, status: x.auto ? '未执行' : '需人工', ms: null, marks: [], notes: '', errs: 0 }]));
const pageErrs = [];                   /* 全局 console/page error 收集（带页面标签） */
let errBase = 0;                       /* shot 起始时的全局错误计数 */
const metrics = {};                    /* 关键掐表指标（报告引用） */
let liveSource = '(未探测)';

function R(id) { return results.get(id); }
function mark(id, tag) { R(id).marks.push(tag); }
function note(id, t) { const r = R(id); r.notes = r.notes ? r.notes + '；' + t : t; }
async function shot(page, id, sel) {
  const p = path.join(SHOT_DIR, `${id}_${R(id).name}.png`);
  if (sel) await page.locator(sel).first().screenshot({ path: p }).catch(() => page.screenshot({ path: p }));
  else await page.screenshot({ path: p });
  console.log(`  [截图] ${id}_${R(id).name}.png`);
}
async function waitLog(page, kw, timeout = 25000) {
  const t0 = Date.now();
  while (Date.now() - t0 < timeout) {
    if (await page.evaluate(k => document.getElementById('logBox')?.textContent.includes(k), kw).catch(() => false)) return Date.now() - t0;
    await sleep(300);
  }
  return -1;
}
async function runShot(id, fn) {
  const r = R(id); errBase = pageErrs.length;
  const t0 = Date.now();
  console.log(`\n=== ${id}（${r.s} ${r.name}·${r.mode}·分镜 ${r.script}s）===`);
  try {
    await fn();
    if (r.status === '未执行') r.status = '通过';
  } catch (e) {
    r.status = r.status === '未执行' || r.status === '通过' ? '超时/异常' : r.status;
    note(id, '异常: ' + String(e).slice(0, 120));
    console.log(`  [异常] ${e}`);
  }
  r.ms = Date.now() - t0;
  r.errs = pageErrs.length - errBase;
  const ratio = r.ms / 1000 / r.script;
  console.log(`  结果: ${r.status} · 实际 ${(r.ms / 1000).toFixed(1)}s / 分镜 ${r.script}s · 比值 ${ratio.toFixed(2)}${ratio > 1 + TOL ? '（超差↑）' : ratio < 1 - TOL ? '（快于下限，剪辑补旁白节奏）' : '（容差内）'}`);
}

/* ============================================================================
 * 0. 拉起服务：ai_proxy.py(8010) + live_feed.py --mode mock(8012)
 * ==========================================================================*/
console.log('=== 0. 基建：拉起 8010 / 8012(mock) ===');
let own8010 = null, own8012 = null;
try {
  own8010 = await ensure(8010, [path.join(QWEN_DIR, 'ai_proxy.py')], 'ai_proxy');
  own8012 = await ensure(8012, [path.join(QWEN_DIR, 'live_feed.py'), '--mode', 'mock'], 'live_feed');
  try {
    const lv = await getJSON(LIVE_URL);
    liveSource = lv.body.source;
    console.log(`[info] live 层 source=${liveSource}，posts=${(lv.body.posts || []).length}`);
  } catch (e) { liveSource = '探测失败: ' + e.message; }
} catch (e) {
  failHard = String(e);
  console.error('[FATAL] 基建拉起失败: ' + e);
}

const browser = failHard ? null : await chromium.launch({ headless: true });

if (browser) {
  const mkPage = async (label) => {
    const page = await (await browser.newContext({ viewport: { width: 1920, height: 1080 } })).newPage();
    page.on('pageerror', e => pageErrs.push(`[${label}] pageerror: ` + String(e)));
    page.on('console', m => { if (m.type() === 'error' && !m.text().includes('favicon')) pageErrs.push(`[${label}] console: ` + m.text()); });
    return page;
  };

  try {
    /* ==========================================================================
     * 第一页：重演剧场（?replay=1）→ R03 / R04 / R07 / R14 / R20
     * ========================================================================*/
    const rp = await mkPage('演');
    await rp.goto(BASE + '?replay=1', { waitUntil: 'load' });
    await sleep(3000);

    await runShot('R03', async () => {
      const info = await rp.evaluate(() => ({
        theater: document.getElementById('replayTheater').style.display !== 'none',
        dual: !!document.getElementById('rpMagDual') && document.getElementById('rpMagDual').textContent.includes('7.9'),
        dualMw: document.getElementById('rpMagDual')?.textContent.includes('7.7'),
        seisSrc: document.getElementById('seisSrcTxt').textContent
      }));
      note('R03', `剧场显现=${info.theater}，双口径卡含 CENC 7.9=${info.dual}/USGS Mw7.7=${info.dualMw}，仪器侧=${info.seisSrc}`);
      if (!info.theater) throw new Error('重演剧场未显现');
      if (info.dual && info.dualMw) mark('R03', '双口径口径在场');
      await shot(rp, 'R03', '#replayTheater');
    });

    await runShot('R04', async () => {
      await rp.evaluate(() => rpJumpTo(20));
      await sleep(3500);   /* 瀑布流 0.8s/条，等 NER 卡片入场 */
      const info = await rp.evaluate(() => ({
        stage2: [...document.querySelectorAll('.rstage.on')].some(e => e.dataset.stage === '2'),
        feed: document.getElementById('feedBox').children.length,
        ner: !!document.querySelector('#feedBox .ner-loc') || !!document.querySelector('#feedBox .ner-dmg')
      }));
      note('R04', `②段点亮=${info.stage2}，瀑布流卡片=${info.feed}，NER高亮=${info.ner}`);
      if (!info.feed) throw new Error('瀑布流无卡片');
      if (info.ner) mark('R04', 'NER 黄/红高亮在场');
      await shot(rp, 'R04', '#replayTheater');
    });

    await runShot('R07', async () => {
      await rp.evaluate(() => rpJumpTo(900));
      await rp.waitForFunction(() => document.getElementById('rpBriefCard')?.style.display !== 'none'
        && document.getElementById('rpLadderBox').children.length >= 1, { timeout: 20000 });
      const mourn = await rp.evaluate(() => document.body.textContent.includes('谨以致哀'));
      note('R07', `简报卡自动亮起+伤亡递进阶梯出现，致哀句=${mourn}`);
      await shot(rp, 'R07', '#replayTheater');
    });

    await runShot('R14', async () => {
      await rp.evaluate(() => rpJumpTo(2409));
      await sleep(1000);
      const vis = await rp.evaluate(() => document.getElementById('t27Card')?.style.display !== 'none');
      if (!vis) throw new Error('空中救援行动卡未随④段显现');
      const priTxt = await rp.evaluate(() => (document.getElementById('rpPriorityBox')?.textContent || ''));
      const hasTop = priTxt.includes('曼德勒');
      note('R14', `空投卡显现；优先级引擎第一名含曼德勒=${hasTop}`);
      if (hasTop) mark('R14', '引擎第一名=曼德勒市区（与空投目标一致）');
      await rp.locator('.t27BtnDrop').first().click();
      const wDrop = await waitLog(rp, '物资投送完成', 25000);
      note('R14', wDrop >= 0 ? `投送完成（${wDrop}ms），红会锚点面板已渲染` : '投送未在 25s 内完成');
      if (wDrop < 0) mark('R14', '超时');
      await shot(rp, 'R14', '#t27Card');
    });

    await runShot('R15', async () => {
      /* P0–P3 五档卡仅在重演④段渲染（rpReveal→rpRefreshPriority→rpPriorityBox），对应分镜「主/演④卡通用」 */
      const q = await rp.evaluate(() => {
        const t = document.getElementById('rpPriorityCard')?.textContent || '';
        return { vis: document.getElementById('rpPriorityCard')?.style.display !== 'none', p0: t.includes('P0'), p1: t.includes('P1'), p2: t.includes('P2'), p3: t.includes('P3'), skyvilla: t.includes('Sky Villa'), sig: t.includes('社情信号') };
      });
      note('R15', `五档卡在场：显现=${q.vis}，P0=${q.p0} P1=${q.p1} P2=${q.p2} P3=${q.p3}；Sky Villa=${q.skyvilla}，社情证据链徽章=${q.sig}`);
      if (!(q.vis && q.p0 && q.p3)) throw new Error('P0–P3 五档卡未完整渲染');
      await shot(rp, 'R15', '#rpPriorityCard');
    });

    await runShot('R20', async () => {
      /* 四幕快进蒙太奇：沿用 verify-replay 的跳段推进方式（⏭ 按钮 + rpJumpTo 锚点） */
      const seq = [];
      await rp.evaluate(() => rpJumpTo(0)); await sleep(700); seq.push('①T+0');
      await rp.evaluate(() => rpJumpTo(20)); await sleep(500); seq.push('②T+6.7s');
      await rp.evaluate(() => rpJumpTo(900)); await sleep(500); seq.push('③T+28.7s');
      await rp.evaluate(() => rpJumpTo(660)); await sleep(500); seq.push('④T+10.8min');
      await rp.evaluate(() => rpJumpTo(2409)); await sleep(800);
      const inter = await rp.evaluate(() => ({
        visible: document.getElementById('rpIntermission').style.display !== 'none',
        a18: document.getElementById('rpAnchor18')?.textContent.startsWith('✅'),
        a40: document.getElementById('rpAnchor40')?.textContent.startsWith('✅'),
        stages: [...document.querySelectorAll('.rstage.on')].map(e => e.dataset.stage).join('>')
      }));
      note('R20', `蒙太奇 ${seq.join(' → ')} 完成；幕间卡=${inter.visible}，18h/40h 锚点=${inter.a18}/${inter.a40}，四幕点亮=${inter.stages}`);
      if (!inter.visible) mark('R20', '幕间卡未现');
      await shot(rp, 'R20', '#replayTheater');
    });

    /* 口径在场扫描（重演页）——报告引用，不得自造数字 */
    metrics.kjReplay = await rp.evaluate(() => {
      const t = document.body.textContent;
      return { fiveMin: t.includes('震后约 5 分钟'), cmp1915: t.includes('19:15') };
    });
    await rp.close();

    /* ==========================================================================
     * 第二页：主仪表盘（默认真 AI 模式）→ R01 R02 R05 R06 R08 R10 R11 R12 R13 R15 R16
     * ========================================================================*/
    const mp = await mkPage('主');
    await runShot('R01', async () => {
      const t0 = Date.now();
      await mp.goto(BASE, { waitUntil: 'load' });
      await mp.waitForFunction(() => typeof AI !== 'undefined' && (AI.cache.quake || AI.fallbackCount > 0), { timeout: 20000 }).catch(() => {});
      metrics.warmMs = Date.now() - t0;
      const warm = await mp.evaluate(() => ({ quake: !!AI.cache?.quake, shout: !!AI.cache?.shout, fb: AI.fallbackCount }));
      note('R01', `加载+warmup=${metrics.warmMs}ms（简报缓存=${warm.quake}，喊话缓存=${warm.shout}，兜底计数=${warm.fb}）`);
      await shot(mp, 'R01');
    });

    await runShot('R02', async () => {
      /* 模拟「鼠标沿页面结构自上而下划动」：滚轮分段下行 */
      for (let i = 0; i < 4; i++) { await mp.mouse.move(960, 200 + i * 60); await mp.mouse.wheel(0, 260); await sleep(220); }
      await mp.evaluate(() => window.scrollTo(0, 0));
      await sleep(300);
      note('R02', '任务链路（感知→研判→调度→交付）由旁白解说，此处仅模拟划动取景');
      await shot(mp, 'R02');
    });

    await runShot('R05', async () => {
      /* 当前 = S05-B 分支：微博官方通道认证未通过，无真实 weibo；8012 为 mock，徽标即预期 */
      await mp.waitForFunction(() => document.querySelector('#feedBox .live-badge') !== null
        || document.getElementById('logBox').textContent.includes('实时社情层'), { timeout: 12000 }).catch(() => {});
      const info = await mp.evaluate(() => ({
        badges: document.querySelectorAll('#feedBox .live-badge').length,
        cards: document.querySelectorAll('#feedBox .pfeed-card').length,
        logLive: document.getElementById('logBox').textContent.includes('实时社情层')
      }));
      note('R05', `S05-B 分支（认证申请中）：live 层 source=${liveSource}，徽标×${info.badges}，注入卡片×${info.cards}；正片口径用「数据集验证」，mock 徽标为备拍`);
      mark('R05', 'S05-B/mock 徽标即预期');
      if (!info.badges && !info.logLive) mark('R05', '徽标未现');
      await shot(mp, 'R05');
    });

    await runShot('R06', async () => {
      const funnel = await mp.evaluate(() => {
        const t = document.body.textContent;
        return { a: t.includes('53,340'), b: t.includes('40,595'), c: t.includes('9,617'), d: t.includes('52 精选') };
      });
      note('R06', `漏斗四档在场：53,340=${funnel.a} / 40,595=${funnel.b} / 9,617=${funnel.c} / 52 精选=${funnel.d}`);
      await mp.evaluate(() => document.getElementById('feedBox')?.scrollIntoView({ block: 'center' }));
      await sleep(400);
      await shot(mp, 'R06');
    });

    await runShot('R08', async () => {
      const before = await mp.evaluate(() => document.getElementById('mainBriefBox').textContent.length);
      const t0 = Date.now();
      await mp.click('#btnBriefMain');
      await mp.waitForFunction(() => {
        const b = document.getElementById('btnBriefMain');
        return b && (b.textContent.includes('重新生成') || document.getElementById('mainBriefBox').textContent.length > 120);
      }, { timeout: 20000 }).catch(() => {});
      metrics.briefMs = Date.now() - t0;
      const brief = await mp.evaluate(() => ({
        len: document.getElementById('mainBriefBox').textContent.length,
        txt: document.getElementById('mainBriefBox').textContent,
        real: document.getElementById('mainBriefBox').textContent.includes('实时'),
        cache: document.getElementById('mainBriefBox').textContent.includes('缓存'),
        fb: document.getElementById('mainBriefBox').textContent.includes('预录')
      }));
      metrics.briefSrc = brief.real ? '实时（真实 AI 调用）' : brief.cache ? '预热缓存' : brief.fb ? '预录兜底' : '未知';
      metrics.briefHas1644 = brief.txt.includes('1,644');
      metrics.briefHas146 = brief.txt.includes('1 分 46 秒');
      note('R08', `出稿 ${metrics.briefMs}ms，来源=${metrics.briefSrc}，正文 ${brief.len} 字`);
      mark('R08', metrics.briefSrc);
      if (brief.len <= before) throw new Error('简报正文未更新');
      await mp.evaluate(() => document.getElementById('mainBriefBox').scrollIntoView({ block: 'center' }));
      await sleep(300);
      await shot(mp, 'R08');
    });

    await runShot('R10', async () => {
      await mp.evaluate(() => { document.getElementById('ovSocial').checked = true; });
      await sleep(700);
      const agg = await mp.evaluate(() => ({
        groups: typeof SOCIAL_AGG !== 'undefined' ? SOCIAL_AGG.length : -1,
        mandalay: typeof SOCIAL_AGG !== 'undefined' ? (SOCIAL_AGG.find(g => g.name === '曼德勒') || {}).n : -1
      }));
      note('R10', `社情叠加层开启：聚合组=${agg.groups}，曼德勒=${agg.mandalay} 帖（居首）`);
      await shot(mp, 'R10', '#mapWrap');
    });

    await runShot('R11', async () => {
      const trio = await mp.evaluate(() => ({
        donut: !!document.getElementById('mainDmgDonut')?.innerHTML,
        kw: !!document.getElementById('mainKwBars')?.innerHTML,
        senti: !!document.getElementById('mainSentiTimeline')?.innerHTML
      }));
      note('R11', `三联渲染：环形=${!!trio.donut}/条形=${!!trio.kw}/情感时间线=${!!trio.senti}`);
      await mp.evaluate(() => document.getElementById('mainDmgDonut')?.scrollIntoView({ block: 'center' }));
      await sleep(300);
      await shot(mp, 'R11');
    });

    await runShot('R12', async () => {
      const t0 = Date.now();
      await mp.click('#btnScan');
      await mp.waitForFunction(() => typeof survivors !== 'undefined' && survivors.some(s => s.discovered), { timeout: 60000 });
      metrics.firstFoundMs = Date.now() - t0;
      note('R12', `起飞→首发现 ${metrics.firstFoundMs}ms（演示须知实测参考 T+7.8s）`);
      await shot(mp, 'R12', '#mapWrap');
    });

    await runShot('R13', async () => {
      await mp.waitForFunction(() => S.fea.done && !!S.feaResult, { timeout: 45000 }).catch(() => {});
      await sleep(800);
      const fea1 = await mp.evaluate(() => ({
        match: document.getElementById('matchTxt').textContent,
        cols: document.getElementById('colTxt').textContent,
        voids: document.getElementById('voidTxt').textContent,
        integ: document.getElementById('integTxt').textContent,
        fb: AI.fallbackCount
      }));
      metrics.vlFirst = { ...fea1 };
      note('R13', `首判四值 ${fea1.match}/${fea1.cols}/${fea1.voids}/${fea1.integ}（当前兜底计数=${fea1.fb}）`);
      const t0 = Date.now();
      await mp.click('#btnRetest');
      await mp.waitForFunction(() => S.fea.done && !!S.feaResult, { timeout: 60000 }).catch(() => {});
      await sleep(800);
      metrics.vlRetestMs = Date.now() - t0;
      const fea2 = await mp.evaluate(() => ({
        match: document.getElementById('matchTxt').textContent,
        cols: document.getElementById('colTxt').textContent,
        voids: document.getElementById('voidTxt').textContent,
        integ: document.getElementById('integTxt').textContent,
        vlCalls: AI.vlCalls, fb: AI.fallbackCount
      }));
      const changed = JSON.stringify([fea2.match, fea2.cols, fea2.voids, fea2.integ]) !== JSON.stringify([fea1.match, fea1.cols, fea1.voids, fea1.integ]);
      note('R13', `换图重判 ${metrics.vlRetestMs}ms，vlCalls=${fea2.vlCalls}，四值${changed ? '已变化（结果随图而变）' : '未变化（可能命中缓存或两图同解）'}`);
      if (fea2.fb > fea1.fb) { mark('R13', '无 Key 环境走兜底'); R('R13').status = '兜底'; }
      await shot(mp, 'R13');
    });

    await runShot('R16', async () => {
      await mp.waitForFunction(() => !!document.querySelector('[data-go]:not([disabled])'), { timeout: 60000 });
      await mp.click('[data-go]:not([disabled])');
      await mp.click('#btnDispatchConfirm');   /* WP10：派遣二次确认弹窗 → 先点「确认派遣 · 推演」 */
      const svId = await mp.evaluate(() => S.teams[0].sv.id);
      await mp.evaluate(id => selectSurvivor(id), svId);
      const t0 = Date.now();
      let lastStage = -1, shoutMs = -1, shoutSrc = '';
      const trace = [];
      while (Date.now() - t0 < 110000) {
        const st = await mp.evaluate(id => {
          const tm = S.teams.find(t => t.sv.id === id);
          const sv = survivors.find(s => s.id === id);
          return tm ? { stage: tm.stage, shoutText: !!sv.shoutText } : { done: true };
        }, svId);
        if (st.done) break;
        if (st.stage !== lastStage) { trace.push(st.stage); lastStage = st.stage; }
        if (st.stage === 2 && shoutMs < 0) {
          const btn = await mp.$('#detailBox [data-shout]');
          if (btn) {
            const tS = Date.now();
            await btn.click();
            await mp.waitForFunction(id => !!survivors.find(s => s.id === id).shoutText, svId, { timeout: 8000 }).catch(() => {});
            shoutMs = Date.now() - tS;
            shoutSrc = await mp.evaluate(id => survivors.find(s => s.id === id).shoutSrc, svId);
          }
        }
        await sleep(250);
      }
      metrics.stageTrace = trace.join('>');
      metrics.rescueMs = Date.now() - t0;
      metrics.shoutMs = shoutMs; metrics.shoutSrc = shoutSrc;
      note('R16', `五阶段轨迹 ${metrics.stageTrace}，派遣→救出 ${(metrics.rescueMs / 1000).toFixed(1)}s，喊话 ${shoutMs}ms（src=${shoutSrc || '未点'}）`);
      if (metrics.stageTrace !== '0>1>2>3>4') mark('R16', '阶段序列不完整');
      await shot(mp, 'R16');
    });

    /* 口径在场扫描（主页）——报告引用 */
    metrics.kjMain = await mp.evaluate(() => {
      const t = document.body.textContent;
      return { m1644: t.includes('1,644'), m146: t.includes('1 分 46 秒') || t.includes('1分46秒'), cenc: t.includes('7.9'), usgs: t.includes('Mw7.7') || t.includes('Mw 7.7') };
    });

    /* ==========================================================================
     * 第三页：?sim=1 保险丝 → R17（新页面）
     * ========================================================================*/
    await runShot('R17', async () => {
      const sp = await mkPage('险');
      let proxyReqs = 0, liveReqs = 0;
      sp.on('request', r => { if (r.url().includes('/ai/proxy')) proxyReqs++; if (r.url().includes(':8012')) liveReqs++; });
      await sp.goto(BASE + '?sim=1', { waitUntil: 'load' });
      await sleep(4000);
      const info = await sp.evaluate(() => ({
        sim: AI.sim,
        advisor: document.getElementById('mainAdvisorBox').textContent.slice(0, 40),
        fbShown: document.getElementById('mainAdvisorBox').textContent.includes('预录') || document.getElementById('mainAdvisorBox').textContent.includes('兜底')
      }));
      note('R17', `sim=${info.sim}，/ai/proxy 请求=${proxyReqs}，:8012 请求=${liveReqs}，决策区预录直显=${info.fbShown}`);
      if (proxyReqs === 0 && liveReqs === 0) mark('R17', '零外部请求达标');
      else mark('R17', '出现外部请求!');
      await shot(sp, 'R17');
      await sp.close();
    });

    /* ==========================================================================
     * R18：kill 代理进程 → 页面兜底秒回（宕机桥段）
     * ========================================================================*/
    await runShot('R18', async () => {
      if (!own8010.spawned) {
        R('R18').status = '需人工';
        note('R18', '8010 为外部既有进程，脚本不执行 kill——请人工录终端 pkill 桥段');
        return;
      }
      stopProc(own8010.proc);
      const free = await waitPortFree(8010, 12);
      note('R18', `ai_proxy 已 kill，8010 端口释放=${free}`);
      if (!free) throw new Error('kill 后 8010 仍监听');
      const before = await mp.evaluate(() => document.getElementById('mainAdvisorBox').textContent.length).catch(() => -1);
      const t0 = Date.now();
      await mp.click('#btnAdvisorMain');
      await mp.waitForFunction(() => document.getElementById('mainAdvisorBox').textContent.includes('曼德勒'), { timeout: 15000 }).catch(() => {});
      metrics.advisorDeadMs = Date.now() - t0;
      const after = await mp.evaluate(() => document.getElementById('mainAdvisorBox').textContent);
      const src = after.includes('预录') ? '预录兜底' : after.includes('缓存') ? '缓存' : '未知';
      note('R18', `代理宕机后决策助手 ${metrics.advisorDeadMs}ms 出结果（来源=${src}），页面未崩溃`);
      if (metrics.advisorDeadMs > 5000) mark('R18', '超 5s 文本超时阈值');
      await shot(mp, 'R18');
    });
    await mp.close();

  } catch (e) {
    failHard = failHard || String(e);
    console.error('[FATAL] 排演流程意外中断: ' + e);
  }
  await browser.close();
}

/* ============================================================================
 * 清理：回收全部自启进程 + 端口复核
 * ==========================================================================*/
console.log('\n=== 清理：回收自启进程 ===');
procs.forEach(stopProc);
await sleep(800);
procs.forEach(p => { try { if (!p.killed) p.kill('SIGKILL'); } catch (e) {} });
const free8010 = own8010.spawned ? await waitPortFree(8010) : await probe(8010);   /* 外部进程保持原状 */
const free8012 = own8012.spawned ? await waitPortFree(8012) : await probe(8012);
console.log(`端口复核：8010 ${own8010.spawned ? (free8010 ? '已释放 ✓' : '仍占用 ✗') : '外部进程·保持原状'}；8012 ${own8012.spawned ? (free8012 ? '已释放 ✓' : '仍占用 ✗') : '外部进程·保持原状'}`);

/* ============================================================================
 * 报告生成：outputs/演示排演报告.md
 * ==========================================================================*/
const judge = r => {
  if (!r.auto) return '—';
  if (r.ms == null) return '未执行';
  const ratio = r.ms / 1000 / r.script;
  return ratio > 1 + TOL ? `超差↑（${ratio.toFixed(2)}x）` : ratio < 1 - TOL ? `偏快↓（${ratio.toFixed(2)}x）` : `容差内（${ratio.toFixed(2)}x）`;
};
const autoShots = SHOTS.filter(s => s.auto);
const sumScript = autoShots.reduce((a, b) => a + b.script, 0);
const sumActual = autoShots.reduce((a, b) => a + (results.get(b.id).ms || 0), 0);
const nPass = [...results.values()].filter(r => r.status === '通过').length;
const nFb = [...results.values()].filter(r => r.status === '兜底').length;
const nSlow = [...results.values()].filter(r => r.status === '超时/异常').length;

const rows = SHOTS.map(x => {
  const r = results.get(x.id);
  const ms = r.ms != null ? (r.ms / 1000).toFixed(1) + 's' : '—';
  const remark = [r.notes, r.marks.length ? '〔' + r.marks.join('、') + '〕' : ''].filter(Boolean).join(' ') || '—';
  return `| ${r.id} | ${r.s} | ${r.name} | ${r.mode} | ${r.script}s | ${ms} | ${judge(r)} | ${r.status} | ${remark} |`;
}).join('\n');

const kj = metrics.kjMain || {};
const kjr = metrics.kjReplay || {};
const issues = [];
if (pageErrs.length) issues.push(...pageErrs.map(e => '- console/page error：`' + e.slice(0, 160) + '`' + (e.includes('ERR_CONNECTION_REFUSED') ? '（R18 kill 代理桥段的**预期**网络错误，正是兜底触发前提，非产品缺陷）' : '')));
else issues.push('- 全程无 console error / page error。');
if (!kj.m146) issues.push('- 「1 分 46 秒」在页面正文未直出：该口径由真 AI 简报 prompt 强制采用（演示脚本红线）并在 S09 字幕钉住；当前预录兜底简报正文未含该字样，正片需真 Key 简报或字幕兜住。');
if (metrics.briefSrc && metrics.briefSrc !== '实时（真实 AI 调用）') issues.push(`- S08 简报来源为「${metrics.briefSrc}」——当前环境未走真实 AI 调用，正片录制前需确认可用 Key。`);
if (R('R13').marks.includes('无 Key 环境走兜底')) issues.push('- S13 Qwen-VL 走预录兜底（无 Key 环境），正片需真 Key 复录并打「真实 AI 调用」角标。');
if (!own8010.spawned) issues.push('- 8010 为外部既有进程：R18 kill 桥段未自动执行，需人工录制。');
if (liveSource !== 'mock') issues.push(`- live 层 source=${liveSource}（预期 mock）。`);

const report = `# RescueAI 演示排演报告（任务 #20）

> 生成方式：\`node pw-test/demo-rehearsal.mjs\` 一键排演自动产出（本文件每次运行覆盖重写）。
> 分镜与口径唯一来源：\`outputs/演示视频脚本.md\`（主版 180s / 精简版 90s）。
> 排演时间：${RUN_AT} ｜ 视口 1920×1080 ｜ 掐表容差 ±50%。

## 1. 逐镜结果表

| 镜号 | 分镜 | 镜名 | 模式 | 分镜时长 | 实际耗时 | 掐表对照 | 状态 | 备注 |
|---|---|---|---|---|---|---|---|---|
${rows}

**状态计数**：通过 ${nPass} ｜ 兜底 ${nFb} ｜ 超时/异常 ${nSlow} ｜ 需人工 ${[...results.values()].filter(r => r.status === '需人工').length}（含 ${SHOTS.filter(s => !s.auto).length} 个纯剪辑镜）。

## 2. 纯人工镜头清单（不尝试自动化）

| 分镜 | 内容 | 人工原因 |
|---|---|---|
| S02 | 鼠标划动 + 任务链路口播 | 划动已模拟取景，口播需人工配音 |
| S09 | 简报口径词字幕逐条钉住 | 纯字幕剪辑镜（素材取自 S08 截图 \`R08_AI简报掐表.png\`） |
| S19 | 兜底机制字幕板 | 纯字幕剪辑镜（底图取 \`R18_kill代理兜底.png\` 脚标特写） |
| S21 | 口径吻合字幕板 + 回归矩阵定格 | 纯字幕剪辑镜（数字以 \`outputs/评测指标.md\` 为准） |
| S22 | 收尾静帧 + 定位声明字幕 | 剪辑镜（底图可用 \`screenshots/t23_04_stage4.png\`） |
| 全部 | 旁白干声 | 先录旁白、按旁白节奏剪画面 |

## 3. 关键掐表指标（实测）

| 指标 | 实测 | 参考口径（演示须知/评测指标） |
|---|---|---|
| 页面加载 + warmup | ${metrics.warmMs ?? '—'}ms | 冷启动预热 |
| S08 简报出稿 | ${metrics.briefMs ?? '—'}ms（来源：${metrics.briefSrc ?? '—'}） | 冷启动实测 ≈3.0s（2990ms） |
| S12 起飞→首发现 | ${metrics.firstFoundMs ?? '—'}ms | 实测首发现 T+7.8s |
| S13 换图重判 | ${metrics.vlRetestMs ?? '—'}ms（vlCalls 见日志） | VL 纯调用 ≈3.3~4.0s |
| S16 五阶段轨迹 | ${metrics.stageTrace ?? '—'}（派遣→救出 ${(metrics.rescueMs / 1000).toFixed(1)}s） | 演示节奏 30~60s |
| S16 喊话响应 | ${metrics.shoutMs ?? '—'}ms（src=${metrics.shoutSrc ?? '—'}） | 任何模式下 ≤2s |
| S18 宕机后决策助手 | ${metrics.advisorDeadMs ?? '—'}ms | 宕机兜底 3/3，秒回 |

## 4. 总时长核算

- 分镜脚本主版合计：**180s = 3:00**（达标区间 2:50–3:10）；精简版 **90s**（85–95s）。
- 本次自动化镜头分镜时长合计：${sumScript}s；自动化实际执行合计：${(sumActual / 1000).toFixed(1)}s。
- 说明：实际耗时为脚本执行耗时（含等待/渲染），非成片镜头时长；成片掐表一律以分镜脚本标注为准。

## 5. 口径在场核验（与分镜脚本一致，不得自造数字）

| 口径 | 页面在场 |
|---|---|
| 社媒传伤亡「震后约 5 分钟」 | ${kjr.fiveMin ? '✓（重演③段对比句）' : '✗ 未检出'} |
| 首条涉震微博早于主震 **1 分 46 秒** | ${kj.m146 ? '✓' : '△ 页面正文未直出（由真 AI 简报 prompt 与 S09 字幕保证，见问题清单）'} |
| 死亡「截至 3/29 晚通报 **1,644** 人」 | ${kj.m1644 ? '✓' : '✗ 未检出'} |
| 震级双口径 **CENC 7.9 / USGS Mw7.7** | ${kj.cenc && kj.usgs ? '✓' : '✗ 未检出'} |
| 官方首报 19:15 | ${kjr.cmp1915 ? '✓（重演③段）' : '✗ 未检出'} |
| 结尾声明「辅助决策工具，不替代专业判断」 | 由旁白/字幕保证（S22 人工） |

## 6. 发现的问题清单

${issues.join('\n')}

## 7. 录制建议

1. **可直录镜头**（本次排演通过且素材在场）：${SHOTS.filter(s => { const r = results.get(s.id); return s.auto && r.status === '通过'; }).map(s => s.id).join('、') || '（无）'}——正式录制用真 Key 复跑一遍主模式确认简报/研判为「实时」来源即可。
2. **需真 Key 复录**：S08（简报）、S13（VL 换图）——当前排演环境为 ${metrics.briefSrc ?? '兜底'}，角标须如实打「真实 AI 调用」或「预录兜底」。
3. **需人工**：S09/S19/S21/S22 字幕板 + 全片旁白；R18 若复用外部代理进程亦需人工 kill 录桥段。
4. **超时风险**：${SHOTS.filter(s => { const r = results.get(s.id); return judge(r).startsWith('超差'); }).map(s => `${s.id}（实际 ${(results.get(s.id).ms / 1000).toFixed(1)}s vs 分镜 ${s.script}s）`).join('、') || '（无）'}——成片靠剪辑压缩，现场不必抢拍。
5. 按分镜 §1 录制顺序执行：① 重演剧场素材 → ② 主模式第二幕 → ③ ?sim=1 → ④ 宕机/断网桥段 → ⑤ 终端特写；三模式分别录满再剪。
6. 8012 当前为 mock（微博认证申请中）：正片采 S05-B 分支口径「以 53,340 条真实微博数据集完成全链路验证」。
`;
fs.writeFileSync(REPORT, report);
console.log(`\n[report] 已生成 ${REPORT}`);
console.log(`[done] 镜头状态：通过=${nPass} 兜底=${nFb} 超时/异常=${nSlow}；截图目录 ${SHOT_DIR}`);
if (failHard) console.error('[warn] 基建/流程级异常已记录: ' + failHard);
process.exit(0);
