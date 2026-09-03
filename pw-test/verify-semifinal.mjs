// 复赛改造验收：研判伤亡卡 / 卫星通道 / 救援工单闭环
import { chromium } from 'playwright';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const file = 'file://' + path.resolve(__dirname, '../GOAI复赛/rescueai-dashboard.html');
const shots = path.resolve(__dirname, '../screenshots');
const results = [];
const check = (name, ok, detail = '') => { results.push({ name, ok, detail }); console.log(`${ok ? '✅' : '❌'} ${name} ${detail}`); };

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
const errors = [];
page.on('pageerror', e => errors.push(e.message));
await page.goto(file);

// 1. 初始：研判Agent徽章 + 伤亡卡占位 + 旧版拉齐组件
await page.waitForTimeout(2000);
check('研判Agent徽章存在', await page.locator('#agent-analyst').count() === 1);
check('伤亡估计卡占位渲染', (await page.locator('#casualty-card .casualty-box').count()) === 1);
check('ICL预警条存在', (await page.locator('.icl-strip').count()) === 1);
check('AI灾情简报卡存在', /接入有效情报|等待情报/.test(await page.locator('#brief-card').innerText()));
check('救援力量状态板含真实组织', /深圳公益救援队/.test(await page.locator('#force-board').innerText()));
check('AI决策助手存在', (await page.locator('.assistant-box').count()) === 1);
// 历史案例库弹窗
await page.locator('button:has-text("历史案例")').click();
await page.waitForTimeout(300);
check('案例库含6个历史案例', (await page.locator('.case-card').count()) === 6);
await page.locator('.modal-close').click();
// AI决策助手问答
await page.locator('.assistant-chips span').first().click();
await page.waitForTimeout(300);
check('决策助手可作答', (await page.locator('#assistant-answer').innerText()).includes('🤖'));

// 2. 等待真实数据注入（3s/条）触发伤亡估计
await page.waitForTimeout(14000);
const casualtyText = await page.locator('#casualty-card').innerText();
check('伤亡卡出现估计数值', /真值发现估计/.test(casualtyText) && /投影最终/.test(casualtyText), casualtyText.replace(/\n/g, ' ').slice(0, 80));
// 位置细化：街道/乡镇级
const feedText = await page.locator('#feed-list').innerText();
check('定位细化到街道/乡镇级', /·/.test(feedText) && /(镇区|镇|街道|区)/.test(feedText), (feedText.match(/\S+·\S+/) || [''])[0]);

// 3. 卫星线索（14s注入第一条）
await page.waitForTimeout(4000);
check('卫星求救线索进入Feed', (await page.locator('.chan-sat').count()) >= 1);
check('微博通道标签存在', (await page.locator('.chan-weibo').count()) >= 1);
await page.screenshot({ path: shots + '/semifinal_01_casualty_sat.png' });

// 4. 批准一个待批准任务 → 工单生成
await page.waitForTimeout(3000);
const pendingCard = page.locator('#kb-pending .kanban-card').first();
if (await pendingCard.count()) {
  await pendingCard.click();
  await page.waitForTimeout(500);
  check('详情页有返回总览', (await page.locator('.back-link').count()) === 1);
  const approveBtn = page.locator('.desk-btn.approve:not([disabled])');
  if (await approveBtn.count()) {
    await approveBtn.click();
    await page.waitForTimeout(800);
    const ticketText = await page.locator('.ticket-box').innerText().catch(() => '');
    check('批准后生成救援对接工单', /TK-\d+/.test(ticketText) && /对接通道/.test(ticketText), ticketText.split('\n')[0]);
    check('工单含合规脱敏说明', /脱敏/.test(ticketText));
    const ticketTag = page.locator('.detail-label .mock-tag');
    check('通讯员工单标题标注(Mock数据)', (await ticketTag.count()) === 1 && /\(Mock数据\)/i.test((await ticketTag.first().innerText()).replace(/\s/g, '')), await page.locator('.detail-label', { hasText: '救援对接工单' }).innerText().catch(() => ''));
    check('工单Mock标注可见未裁切', await ticketTag.first().isVisible().catch(() => false));
    await page.screenshot({ path: shots + '/semifinal_02_ticket.png' });
    // 5. 等待 dispatched(8s)→verify(3s)→closed，看现场回传与闭环
    await page.waitForTimeout(13000);
    const ticketText2 = await page.locator('.ticket-box').innerText().catch(() => '');
    check('现场回传报告出现', /现场回传/.test(ticketText2));
    check('工单时间线全部完成', (ticketText2.match(/✓/g) || []).length === 4, `完成${(ticketText2.match(/✓/g) || []).length}/4步`);
    await page.screenshot({ path: shots + '/semifinal_03_closed.png' });
    // 6. 返回总览：已核实线索回馈研判
    await page.locator('.back-link').click();
    await page.waitForTimeout(500);
    const overview = await page.locator('#casualty-card').innerText();
    check('闭环后线索标记已核实', /1 条已现场核实|[1-9]\d* 条已现场核实/.test(overview), overview.match(/\d+ 条已现场核实/)?.[0] || '');
    check('总览含4个Agent卡', (await page.locator('.agent-status-card').count()) === 4);
    await page.screenshot({ path: shots + '/semifinal_04_overview.png' });
  } else {
    check('批准按钮可用', false, '未找到可用批准按钮');
  }
} else {
  check('存在待批准任务', false);
}

check('无页面JS错误', errors.length === 0, errors.join('; ').slice(0, 200));
await browser.close();
const failed = results.filter(r => !r.ok);
console.log(`\n===== ${results.length - failed.length}/${results.length} 通过 =====`);
process.exit(failed.length ? 1 : 0);
