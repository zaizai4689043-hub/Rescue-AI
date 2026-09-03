// 线上部署验收：Vercel 生产地址渲染 + 台风模式已移除 + 抽屉闭环可用
import { chromium } from 'playwright';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const shots = path.resolve(__dirname, '../screenshots');
const BASE = process.argv[2] || 'https://deploy-eight-mocha-43.vercel.app';
const url = BASE.replace(/\/$/, '') + '/semifinal.html';
const results = [];
const check = (name, ok, detail = '') => { results.push({ name, ok }); console.log(`${ok ? '✅' : '❌'} ${name} ${detail}`); };

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
const errors = [];
page.on('pageerror', e => errors.push(e.message));
const resp = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
check('线上页面 HTTP 200', resp && resp.status() === 200, `status=${resp && resp.status()}`);
await page.waitForTimeout(4000);

check('大屏标题渲染', /地 震 应 急 智 能 指 挥 中 心/.test(await page.locator('#center-title').innerText()));
check('预警横幅渲染', /地震预警/.test(await page.locator('#quake-banner').innerText()));
check('顶栏仅地震模式+历史案例', JSON.stringify(await page.locator('.mode-btn').allInnerTexts()) === '["地震模式","📚 历史案例"]', JSON.stringify(await page.locator('.mode-btn').allInnerTexts()));
check('台风模式已彻底移除', (await page.locator('.mode-btn[data-mode="typhoon"]').count()) === 0);
check('左栏评估/简报面板存在', /快速评估结果|AI灾情简报/.test(await page.locator('#leftcol').innerText()));
check('全文无台风字样', !/台风/.test(await page.content()));
check('全文无119/120指挥中心调度令宣称', !/119指挥中心|120指挥中心|指挥中心调度令|120急救中心/.test(await page.content()));
check('地图震中覆盖层存在', (await page.locator('#map-leaflet, #map-svg').count()) > 0);
check('社媒情报流有卡片', (await page.locator('.feed-card').count()) > 0, `cards=${await page.locator('.feed-card').count()}`);
await page.waitForTimeout(12000);
check('Mock点位为缅甸真实地点', /曼德勒|实皆|内比都|仰光|缅甸/.test(await page.locator('#feed-list').innerText()) && !/宁波|鄞州|天一广场/.test(await page.locator('#feed-list').innerText()), (await page.locator('#feed-list').innerText()).slice(0, 40).replace(/\n/g, ' '));
await page.screenshot({ path: path.join(shots, 'deploy_semifinal_03_feed.png') });
await page.screenshot({ path: path.join(shots, 'deploy_semifinal_01_full.png') });

await page.locator('.feed-card').first().click();
await page.waitForTimeout(800);
check('线上抽屉可打开', (await page.locator('#drawer.open').count()) === 1);
await page.screenshot({ path: path.join(shots, 'deploy_semifinal_02_drawer.png') });
const liveTags = page.locator('#drawer-body .vhead .mock-tag');
check('线上抽屉2/3/4节标注(Mock数据)', (await liveTags.count()) === 3, `实际${await liveTags.count()}处`);
check('线上Mock标注文本正确', (await liveTags.first().innerText()).replace(/\s/g, '') === '(Mock数据)');
check('线上源码含工单Mock标注', /通讯员 · 救援对接工单 <span class="mock-tag">\(Mock数据\)<\/span>/.test(await page.content()));
check('线上无页面JS错误', errors.length === 0, errors.slice(0, 2).join(' | '));

// 首页（v4.0）未被破坏
const home = await page.goto(BASE.replace(/\/$/, '') + '/', { waitUntil: 'domcontentloaded', timeout: 60000 });
check('首页仍可访问', home && home.status() === 200, `status=${home && home.status()}`);

await browser.close();
const fail = results.filter(r => !r.ok);
console.log(`\n==== ${results.length - fail.length}/${results.length} 通过 ====`);
console.log('URL:', url);
process.exit(fail.length ? 1 : 0);
