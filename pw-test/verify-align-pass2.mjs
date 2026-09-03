/* 第二遍自查：讲稿对齐改造实机走查（普通模式 ?sim=1 开屏 + 新元素断言 + 整页截图） */
import { chromium } from 'playwright';
import { readFileSync } from 'fs';

const SRC_HTML = readFileSync('/Users/zaizai/Downloads/AI地震救援/backend/Qwen 初版/代码1.2-ai.html', 'utf8');

const SHOT = '/Users/zaizai/Downloads/AI地震救援/screenshots';
const sleep = ms => new Promise(r => setTimeout(r, ms));
let pass = 0, fail = 0;
const ok = (cond, name, extra = '') => { console.log((cond ? '✅' : '❌') + ' ' + name + (extra ? ' · ' + extra : '')); cond ? pass++ : fail++; };

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1720, height: 1080 } });
await page.route(u => String(u).includes(':8012'), r => r.abort());   /* 环境隔离：阻断实时社情层 8012，结果与 live_feed 是否在跑无关 */
const errs = [];
page.on('pageerror', e => errs.push(String(e)));
page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });

await page.goto('http://127.0.0.1:8010/?sim=1', { waitUntil: 'load' });
await sleep(2500);

const probe = await page.evaluate(() => {
  const txt = id => (document.getElementById(id) || {}).textContent || '';
  const heat = document.getElementById('mapCanvas');   /* 社情热力已并入主地图「社情感知」图层 */
  let heatPx = 0;
  if (heat && heat.width) {
    const c = document.createElement('canvas'); c.width = heat.width; c.height = heat.height;
    const x = c.getContext('2d'); x.drawImage(heat, 0, 0);
    const d = x.getImageData(0, 0, c.width, c.height).data;
    for (let i = 3; i < d.length; i += 4) if (d[i] > 0) heatPx++;
  }
  return {
    heatPx,
    ovSocialChecked: document.getElementById('ovSocial').checked,
    funnelDash: txt('analysisRow').includes('53,340 原始'.replace(/\s/g, '')) || document.querySelector('#analysisRow').textContent.replace(/\s/g, '').includes('53,340原始→40,595去重→9,617词条初筛→65AI甄别→52精选'),
    fourLayerDash: document.querySelector('#analysisRow').textContent.includes('噪声过滤四层：去重 → 辟谣 → 机器人识别 → 地理围栏'),
    fourLayerFeed: document.getElementById('dualSrcSection') ? document.getElementById('dualSrcSection').textContent.includes('噪声过滤四层') : document.body.textContent.includes('噪声过滤四层：去重 → 辟谣'),
    iclNote: document.body.textContent.includes('检测到任何地震信号 → 立即启动微博关键词监测'),
    priChildren: document.getElementById('mainPriorityBox').children.length,
    advisorNote: document.body.textContent.includes('五区分数表 + 8 历史案例匹配'),
    advisorDesc: 1,   /* sim 开屏预录结果会替换占位描述，改在 Node 端断言源码 */
    briefDesc: 1,
    pipelineNote: (() => { const el = document.querySelector('#rpPipeline .rpseg[data-k="flt"]'); return el ? el.title || el.textContent : null; })(),
    advisorCases8: document.documentElement.outerHTML.includes('⑧缅甸2025 M7.7') ? 1 : 0
  };
});
ok(probe.heatPx > 500, '主地图开屏已绘制（含社情热力图层）', '非空像素 ' + probe.heatPx);
ok(probe.ovSocialChecked, '社情感知图层默认勾选（热力图并入主地图）');
ok(probe.funnelDash, '仪表盘漏斗对齐 funnel.json（去重/词条初筛）');
ok(probe.fourLayerDash, '仪表盘四层过滤注脚');
ok(probe.fourLayerFeed, '双源感知四层过滤注脚');
ok(probe.iclNote, 'ICL 预警通道主界面注脚');
ok(probe.priChildren === 5, '区域优先级 P0-P3 五区开屏', 'children=' + probe.priChildren);
ok(probe.advisorNote, '决策助手卡注脚=8 历史案例匹配');
ok(SRC_HTML.includes('8 个历史相似地震案例'), '决策助手描述含 8 案例库清单（源码）');
ok(SRC_HTML.includes('供定期内部通报'), '简报描述含定期内部通报（源码）');
ok(probe.pipelineNote && probe.pipelineNote.includes('四层'), '剧场管线 flt 段含四层口径', String(probe.pipelineNote).slice(0, 30));
ok(probe.advisorCases8 === 1, 'ADVISOR_CASES 含⑧缅甸（8 案例完整）');
ok(errs.length === 0, '无 JS 错误', errs.slice(0, 2).join(' | '));

await page.screenshot({ path: SHOT + '/check2_main_full.png', fullPage: true });
await page.locator('#analysisRow').screenshot({ path: SHOT + '/check2_analysis_row.png' }).catch(() => {});
console.log('截图: check2_main_full.png / check2_analysis_row.png');
console.log(`\n=== 第二遍自查 ${pass} 通过 / ${fail} 失败 ===`);
await browser.close();
process.exit(fail ? 1 : 0);
