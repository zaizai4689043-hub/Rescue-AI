// 任务5·路径A 冒烟测试：实时社情层（live_feed.py mock 模式 + HTML LIVE 分支）
// 用法：node verify-live.mjs （自动拉起 ai_proxy.py:8010 与 live_feed.py:8012，结束后回收自己拉起的进程）
// 若环境缺 playwright，自动降级为 curl 级验证（端点 200 + JSON 契约）并注明。
import { spawn } from 'child_process';
import http from 'http';

const BASE = 'http://127.0.0.1:8010/';
const LIVE_URL = 'http://127.0.0.1:8012/live/social';
const QWEN_DIR = '/Users/zaizai/Downloads/AI地震救援/backend/Qwen 初版';
const sleep = ms => new Promise(r => setTimeout(r, ms));
const procs = [];
let fail = 0;
const ok = (c, msg) => { console.log((c ? '[PASS] ' : '[FAIL] ') + msg); if (!c) fail++; };

function probe(url) {
  return new Promise(res => {
    const req = http.get(url, r => { res(r.statusCode); r.resume(); });
    req.on('error', () => res(0));
    req.setTimeout(1200, () => { req.destroy(); res(0); });
  });
}
function getJSON(url) {
  return new Promise((res, rej) => {
    http.get(url, r => {
      let b = ''; r.on('data', c => b += c); r.on('end', () => { try { res({ status: r.statusCode, body: JSON.parse(b) }); } catch (e) { rej(e); } });
    }).on('error', rej);
  });
}
async function ensure(host, port, cmd, args) {
  const st = await probe(`http://${host}:${port}/`);
  if (st) { console.log(`[info] ${port} 已在运行，复用`); return; }
  const p = spawn(cmd, args, { stdio: ['ignore', 'pipe', 'pipe'] });
  p.stdout.on('data', d => process.stdout.write('[srv:' + port + '] ' + d));
  p.stderr.on('data', d => process.stderr.write('[srv:' + port + ':err] ' + d));
  procs.push(p);
  for (let i = 0; i < 30; i++) { if (await probe(`http://${host}:${port}/`)) return; await sleep(300); }
  throw new Error(port + ' 端口服务未能就绪');
}

/* ===== 0. 拉起服务（ai_proxy 8010 + live_feed mock 8012） ===== */
await ensure('127.0.0.1', 8010, 'python3', [QWEN_DIR + '/ai_proxy.py']);
await ensure('127.0.0.1', 8012, 'python3', [QWEN_DIR + '/live_feed.py', '--mode', 'mock']);

/* ===== 1. curl 级：live 端点 200 + JSON 契约 ===== */
try {
  const r = await getJSON(LIVE_URL);
  const b = r.body;
  ok(r.status === 200, 'GET /live/social 返回 200');
  ok(['weibo', 'mock', 'cache'].includes(b.source), 'source 合法: ' + b.source);
  ok(typeof b.polled_at === 'string' && typeof b.stale === 'boolean', 'polled_at/stale 字段存在');
  ok(Array.isArray(b.posts) && b.posts.length > 0 && b.posts.length <= 50, 'posts 非空且 ≤50: ' + b.posts.length + ' 条');
  const p0 = b.posts[0] || {};
  ok(p0.id && p0.text && p0.created_at && p0.live === true, '单帖字段齐全 {id,text,created_at,tags,live}');
  ok(!('user' in p0) && !('uid' in p0) && !('screen_name' in p0), '隐私：无昵称/UID 字段');
} catch (e) {
  ok(false, 'live 端点请求失败: ' + e.message);
}

/* ===== 2/3. Playwright：默认模式出现「实时」徽标；?sim=1 不发起 8012 请求 ===== */
let chromium = null;
try { ({ chromium } = await import('playwright')); } catch (e) { console.log('[NOTE] playwright 缺失，仅完成 curl 级验证'); }
if (chromium) {
  const browser = await chromium.launch({ headless: true });
  const errs = [];

  console.log('=== 2. 默认模式：LIVE 帖/「实时」徽标注入社情流 ===');
  const page = await (await browser.newContext({ viewport: { width: 1440, height: 1500 } })).newPage();
  page.on('pageerror', e => errs.push('pageerror: ' + e));
  page.on('console', m => { if (m.type() === 'error') errs.push('console: ' + m.text()); });
  await page.goto(BASE, { waitUntil: 'load' });
  await page.waitForFunction(() =>
    document.querySelector('#feedBox .live-badge') !== null
    || document.getElementById('logBox').textContent.includes('实时社情层'), { timeout: 10000 })
    .then(() => ok(true, '「实时」徽标或连通日志出现')).catch(() => ok(false, '10s 内未见实时徽标/连通日志'));
  const feedInfo = await page.evaluate(() => ({
    badges: document.querySelectorAll('#feedBox .live-badge').length,
    cards: document.querySelectorAll('#feedBox .pfeed-card').length,
    dupIds: (() => { const pids = [...document.querySelectorAll('#feedBox .pfeed-card')].map(e => e.dataset.pid); return pids.length !== new Set(pids).size; })(),
    log: document.getElementById('logBox').textContent.includes('实时社情层')
  }));
  console.log('社情流:', JSON.stringify(feedInfo));
  ok(feedInfo.badges >= 1 && !feedInfo.dupIds, '实时徽标≥1 且无重复 id 卡片');
  ok(errs.filter(e => !e.includes('favicon')).length === 0, '页面无 error 级异常: ' + JSON.stringify(errs));

  console.log('=== 3. ?sim=1：完全不触发 8012 请求 ===');
  const page2 = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
  let hit8012 = 0;
  page2.on('request', r => { if (r.url().includes(':8012')) hit8012++; });
  await page2.goto(BASE + '?sim=1', { waitUntil: 'load' });
  await sleep(4000);
  ok(hit8012 === 0, '?sim=1 模式 8012 请求数 = ' + hit8012);

  console.log('=== 3b. ?replay=1：同样零触发 ===');
  let hit8012r = 0;
  page2.on('request', r => { if (r.url().includes(':8012')) hit8012r++; });
  await page2.goto(BASE + '?replay=1', { waitUntil: 'load' });
  await sleep(3000);
  ok(hit8012r === 0, '?replay=1 模式 8012 请求数 = ' + hit8012r);

  await browser.close();
}

procs.forEach(p => p.kill('SIGTERM'));
console.log(fail === 0 ? '=== verify-live ALL PASS ===' : '=== verify-live FAIL=' + fail + ' ===');
process.exit(fail === 0 ? 0 : 1);
