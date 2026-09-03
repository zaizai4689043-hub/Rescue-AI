// 任务一验收：点击社媒卡片 → 核实闭环抽屉 → 推送属地救援队 → 追踪反馈
import { chromium } from 'playwright';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const file = 'file://' + path.resolve(__dirname, '../GOAI复赛/rescueai-dashboard.html');
const shots = path.resolve(__dirname, '../screenshots');
const results = [];
const check = (name, ok, detail = '') => { results.push({ name, ok }); console.log(`${ok ? '✅' : '❌'} ${name} ${detail}`); };

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
const errors = [];
page.on('pageerror', e => errors.push(e.message));
await page.goto(file);
await page.waitForTimeout(2500);

// 0. 参考图UI元素
check('预警横幅存在', /地震预警/.test(await page.locator('#quake-banner').innerText()));
check('居中大标题存在', /地 震 应 急 智 能 指 挥 中 心/.test(await page.locator('#center-title').innerText()));
check('主震信息面板存在', /M 7.9/.test(await page.locator('#quake-info').innerText()));
check('底部影响统计三格', (await page.locator('#stats-row .stat-cell').count()) === 3);
check('灾情概览+评估/简报面板', /烈度面积/.test(await page.locator('#leftcol').innerText()) && /快速评估结果|AI灾情简报/.test(await page.locator('#leftcol').innerText()));
check('震中距离详情面板已移除', !/震中距离详情/.test(await page.locator('#rightcol').innerText()));
check('地震专题图已移除', (await page.locator('.theme-map').count()) === 0);
check('台风模式按钮已移除', (await page.locator('.mode-btn[data-mode="typhoon"]').count()) === 0);
check('真实时钟走动', /\d{2}:\d{2}:\d{2}/.test(await page.locator('#real-clock').innerText()));
await page.screenshot({ path: path.join(shots, 'drawer_00_ui.png') });

// 1. 等待首条社媒卡片并点击 → 抽屉打开
await page.waitForSelector('.feed-card', { timeout: 30000 });
await page.locator('.feed-card').first().click();
await page.waitForTimeout(600);
check('点击社媒卡片弹出抽屉', await page.locator('#drawer.open').count() === 1);
const bodyTxt = await page.locator('#drawer-body').innerText();
check('抽屉含原始线索+AI初筛', /原始线索/.test(bodyTxt) && /AI 智能初筛/.test(bodyTxt) && /已完成/.test(bodyTxt));
check('抽屉含5项多源核实', /1\. 私信联系发帖人/.test(bodyTxt) && /5\. 同区域多源交叉印证/.test(bodyTxt));
check('推送按钮初始禁用', await page.locator('.vpush[disabled]').count() === 1);
check('推送/追踪区初始锁定', /需先完成多源核实/.test(bodyTxt) && /需先推送至救援队/.test(bodyTxt));
const mockTags = page.locator('#drawer-body .vhead .mock-tag');
check('抽屉2/3/4节均标注(Mock数据)', (await mockTags.count()) === 3, `实际${await mockTags.count()}处`);
check('Mock标注文本为(Mock数据)', (await mockTags.first().innerText()).replace(/\s/g, '') === '(Mock数据)', await mockTags.first().innerText());
check('Mock标注可见且未撑破标题行', await page.evaluate(() => [...document.querySelectorAll('#drawer-body .vhead')].every(h => h.getBoundingClientRect().height < 45) && [...document.querySelectorAll('#drawer-body .mock-tag')].every(t => { const b = t.getBoundingClientRect(); return b.width > 0 && b.height > 0; })));
await page.screenshot({ path: path.join(shots, 'drawer_01_open.png') });

// 2. 等待核实推进完成（5项×3.2s）
await page.waitForTimeout(17000);
const body2 = await page.locator('#drawer-body').innerText();
check('核实进度100%', /核实完成 100%/.test(body2));
check('推送按钮就绪', await page.locator('.vpush.ready').count() === 1);
await page.screenshot({ path: path.join(shots, 'drawer_02_verified.png') });

// 3. 推送至属地公益救援队
await page.locator('.vpush').click();
await page.waitForTimeout(800);
const body3 = await page.locator('#drawer-body').innerText();
check('推送成功展示救援队', /已推送/.test(body3) && /对接通道/.test(body3));
check('追踪反馈时间线启动', /推送至|确认接收/.test(body3.split('4. 追踪反馈')[1] || ''));
check('产品定位说明存在', /不自建救援队伍/.test(body3));
check('推送后Mock标注仍在', (await page.locator('#drawer-body .vhead .mock-tag').count()) === 3);
check('推送通道不含119/120指挥中心调度令宣称', !/119指挥中心|120指挥中心|指挥中心调度令|120急救中心/.test(body3));
await page.screenshot({ path: path.join(shots, 'drawer_03_pushed.png') });

// 4. 追踪反馈逐步回音 → 闭环
await page.waitForTimeout(24000);
const body4 = await page.locator('#drawer-body').innerText();
check('追踪反馈闭环(现场反馈)', /现场反馈/.test(body4) && /已闭环/.test(body4));
await page.screenshot({ path: path.join(shots, 'drawer_04_closed.png') });

// 5. 震中距离表已随面板移除
check('震中距离表DOM已移除', (await page.locator('#dist-table').count()) === 0);

// 6. 关闭抽屉回归主屏
await page.locator('.dw-close').click();
await page.waitForTimeout(500);
check('抽屉可关闭', await page.locator('#drawer.open').count() === 0);

check('无页面JS错误', errors.length === 0, errors.slice(0, 2).join(' | '));
await browser.close();
const fail = results.filter(r => !r.ok);
console.log(`\n==== ${results.length - fail.length}/${results.length} 通过 ====`);
process.exit(fail.length ? 1 : 0);
