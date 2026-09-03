import { chromium } from 'playwright';

const SCREENSHOT_DIR = '/Users/zaizai/Downloads/AI地震救援/screenshots';
const BASE_URL = 'http://localhost:5173';
const issues = [];

function log(msg) { console.log(`[E2E] ${msg}`); }
function logIssue(msg) { issues.push(msg); console.log(`[ISSUE] ${msg}`); }

async function screenshot(page, name) {
  const path = `${SCREENSHOT_DIR}/${name}.png`;
  await page.screenshot({ path, fullPage: true });
  log(`截图: ${name}.png`);
  return path;
}

async function waitForPageLoad(page) {
  await page.waitForLoadState('networkidle').catch(() => {});
  await page.waitForTimeout(1000);
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  // ============ 1. 注册和登录 ============
  log('=== 1. 注册和登录 ===');
  
  // 打开页面
  await page.goto(BASE_URL);
  await waitForPageLoad(page);
  
  // 检查是否跳转到登录页
  const currentUrl = page.url();
  log(`当前URL: ${currentUrl}`);
  if (currentUrl.includes('/login')) {
    log('✅ 自动跳转到登录页面');
  } else {
    logIssue('未自动跳转到登录页面');
  }
  
  await screenshot(page, '01_login_page');

  // 切换到注册标签
  await page.click('text=注册');
  await page.waitForTimeout(500);
  await screenshot(page, '02_register_tab');

  // 填写注册信息
  // 用户名
  const registerInputs = await page.locator('.el-tab-pane:visible input').all();
  log(`注册表单输入框数量: ${registerInputs.length}`);
  
  // 使用placeholder定位
  await page.locator('input[placeholder="用户名"]').fill('testadmin');
  await page.locator('input[placeholder="密码"]').first().fill('test123456');
  await page.locator('input[placeholder="确认密码"]').fill('test123456');
  await page.locator('input[placeholder="姓名"]').fill('测试管理员');
  await page.locator('input[placeholder="手机号"]').fill('13800138000');
  
  // 选择角色 - 管理员
  await page.click('.el-select:visible');
  await page.waitForTimeout(300);
  await page.click('text=管理员');
  await page.waitForTimeout(300);
  
  await screenshot(page, '03_register_filled');

  // 点击注册按钮
  await page.click('button:has-text("注 册")');
  await page.waitForTimeout(2000);
  await screenshot(page, '04_register_result');

  // 切换到登录标签并登录
  await page.click('text=登录');
  await page.waitForTimeout(500);
  
  // 检查用户名是否已自动填入
  const loginUsername = page.locator('.el-tab-pane:visible input[placeholder="用户名"]');
  const usernameValue = await loginUsername.inputValue().catch(() => '');
  if (!usernameValue || usernameValue === '') {
    await loginUsername.fill('testadmin');
  }
  
  const loginPassword = page.locator('.el-tab-pane:visible input[placeholder="密码"]');
  await loginPassword.fill('test123456');
  
  await screenshot(page, '05_login_filled');

  // 点击登录
  await page.click('button:has-text("登 录")');
  await page.waitForTimeout(3000);
  await waitForPageLoad(page);
  
  log(`登录后URL: ${page.url()}`);
  await screenshot(page, '06_login_success');

  // ============ 2. 仪表盘 ============
  log('=== 2. 仪表盘 ===');
  
  if (page.url().includes('/dashboard')) {
    log('✅ 成功跳转到仪表盘');
  } else {
    logIssue(`登录后未跳转到仪表盘，当前: ${page.url()}`);
    await page.goto(`${BASE_URL}/dashboard`);
    await waitForPageLoad(page);
  }
  
  await page.waitForTimeout(2000);
  await screenshot(page, '07_dashboard');

  // 检查统计卡片
  const statCards = await page.locator('.stat-card, .el-card').count();
  log(`仪表盘卡片数量: ${statCards}`);
  if (statCards === 0) logIssue('仪表盘未显示统计卡片');

  // ============ 3. 灾情上报 ============
  log('=== 3. 灾情上报 ===');
  
  await page.click('text=灾情上报');
  await waitForPageLoad(page);
  await screenshot(page, '08_disaster_report_page');

  // 填写表单
  await page.locator('input[placeholder="请输入灾情标题"]').fill('北京朝阳区地震灾情');
  
  // 选择灾情类型
  await page.click('.el-select:visible');
  await page.waitForTimeout(300);
  await page.click('text=地震/主震');
  await page.waitForTimeout(300);

  // 严重程度 - 4星
  const rateItems = await page.locator('.el-rate__item').all();
  if (rateItems.length >= 4) {
    await rateItems[3].click();
  }
  
  // 描述
  await page.locator('textarea[placeholder="请详细描述灾情情况"]').fill('朝阳区发生5.2级地震，多处建筑受损');
  
  // 纬度 - 使用数字输入框
  const numberInputs = await page.locator('.el-input-number input').all();
  log(`数字输入框数量: ${numberInputs.length}`);
  
  // 找到纬度和经度输入框
  for (const input of numberInputs) {
    const placeholder = await input.getAttribute('placeholder');
    if (placeholder === '纬度') {
      await input.click({ clickCount: 3 });
      await input.fill('39.92');
    } else if (placeholder === '经度') {
      await input.click({ clickCount: 3 });
      await input.fill('116.46');
    }
  }
  
  // 地址
  await page.locator('input[placeholder="请输入详细地址"]').fill('北京市朝阳区');
  
  await screenshot(page, '09_disaster_report_filled');

  // 提交
  await page.click('button:has-text("提 交")');
  await page.waitForTimeout(3000);
  await waitForPageLoad(page);
  await screenshot(page, '10_disaster_report_submitted');

  // 创建第二条灾情 - 余震
  log('创建第二条灾情 - 余震');
  await page.click('text=灾情上报');
  await waitForPageLoad(page);
  await page.waitForTimeout(500);
  
  await page.locator('input[placeholder="请输入灾情标题"]').fill('朝阳区余震');
  await page.click('.el-select:visible');
  await page.waitForTimeout(300);
  await page.click('text=余震');
  await page.waitForTimeout(300);
  
  const rateItems2 = await page.locator('.el-rate__item').all();
  if (rateItems2.length >= 3) await rateItems2[2].click();
  
  await page.locator('textarea[placeholder="请详细描述灾情情况"]').fill('朝阳区发生4.0级余震，部分建筑出现裂缝');
  
  for (const input of await page.locator('.el-input-number input').all()) {
    const placeholder = await input.getAttribute('placeholder');
    if (placeholder === '纬度') { await input.click({ clickCount: 3 }); await input.fill('39.93'); }
    else if (placeholder === '经度') { await input.click({ clickCount: 3 }); await input.fill('116.47'); }
  }
  await page.locator('input[placeholder="请输入详细地址"]').fill('北京市朝阳区望京');
  
  await page.click('button:has-text("提 交")');
  await page.waitForTimeout(3000);

  // 创建第三条灾情 - 建筑倒塌
  log('创建第三条灾情 - 建筑倒塌');
  await page.click('text=灾情上报');
  await waitForPageLoad(page);
  await page.waitForTimeout(500);
  
  await page.locator('input[placeholder="请输入灾情标题"]').fill('朝阳区建筑倒塌');
  await page.click('.el-select:visible');
  await page.waitForTimeout(300);
  await page.click('text=建筑倒塌');
  await page.waitForTimeout(300);
  
  const rateItems3 = await page.locator('.el-rate__item').all();
  if (rateItems3.length >= 5) await rateItems3[4].click();
  
  await page.locator('textarea[placeholder="请详细描述灾情情况"]').fill('朝阳区某小区3号楼发生倒塌， estimated 50人被困');
  
  for (const input of await page.locator('.el-input-number input').all()) {
    const placeholder = await input.getAttribute('placeholder');
    if (placeholder === '纬度') { await input.click({ clickCount: 3 }); await input.fill('39.91'); }
    else if (placeholder === '经度') { await input.click({ clickCount: 3 }); await input.fill('116.45'); }
  }
  await page.locator('input[placeholder="请输入详细地址"]').fill('北京市朝阳区大望路');
  
  await page.click('button:has-text("提 交")');
  await page.waitForTimeout(3000);
  await screenshot(page, '11_disaster_reports_created');

  // ============ 4. 灾情列表 ============
  log('=== 4. 灾情列表 ===');
  
  await page.click('text=灾情列表');
  await waitForPageLoad(page);
  await page.waitForTimeout(2000);
  await screenshot(page, '12_disaster_list');

  // 检查列表是否有数据
  const tableRows = await page.locator('.el-table__body tr').count();
  log(`灾情列表行数: ${tableRows}`);
  if (tableRows === 0) logIssue('灾情列表无数据');

  // 测试筛选
  await page.click('.el-select:visible');
  await page.waitForTimeout(300);
  await page.click('text=已上报');
  await page.waitForTimeout(300);
  await page.click('button:has-text("搜索")');
  await page.waitForTimeout(2000);
  await screenshot(page, '13_disaster_list_filtered');

  // 重置筛选
  await page.click('button:has-text("重置")');
  await page.waitForTimeout(2000);

  // 查看详情
  const viewBtn = page.locator('button:has-text("查看")').first();
  if (await viewBtn.isVisible()) {
    await viewBtn.click();
    await page.waitForTimeout(2000);
    await screenshot(page, '14_disaster_detail_dialog');

    // 检查AI分析面板
    const aiPanel = await page.locator('.ai-panel').isVisible().catch(() => false);
    log(`AI分析面板可见: ${aiPanel}`);
    
    // 触发AI分析
    const triggerBtn = page.locator('button:has-text("触发AI分析")');
    if (await triggerBtn.isVisible().catch(() => false)) {
      await triggerBtn.click();
      await page.waitForTimeout(3000);
      await screenshot(page, '15_ai_analysis_result');
    } else {
      log('AI分析已有结果或按钮不可见');
    }

    // 关闭弹窗
    await page.click('.el-dialog__headerbtn');
    await page.waitForTimeout(500);
  }

  // ============ 5. 灾情地图 ============
  log('=== 5. 灾情地图 ===');
  
  await page.click('text=灾情地图');
  await waitForPageLoad(page);
  await page.waitForTimeout(3000);
  await screenshot(page, '16_disaster_map');

  // 检查ECharts渲染
  const mapCanvas = await page.locator('canvas').count();
  log(`地图Canvas数量: ${mapCanvas}`);
  if (mapCanvas === 0) logIssue('灾情地图未渲染Canvas');

  // ============ 6. 资源调度中心 ============
  log('=== 6. 资源调度中心 ===');
  
  await page.click('text=资源调度');
  await waitForPageLoad(page);
  await page.waitForTimeout(2000);
  await screenshot(page, '17_resource_center');

  // 创建资源
  await page.click('button:has-text("新增资源")');
  await page.waitForTimeout(1000);
  await screenshot(page, '18_resource_drawer');

  // 填写资源表单
  await page.locator('.el-drawer:visible input[placeholder="请输入资源名称"]').fill('帐篷');
  
  // 选择类型
  await page.locator('.el-drawer:visible .el-select').first().click();
  await page.waitForTimeout(300);
  await page.click('text=物资');
  await page.waitForTimeout(300);

  // 数量
  const drawerNumberInput = await page.locator('.el-drawer:visible .el-input-number input').first();
  await drawerNumberInput.click({ clickCount: 3 });
  await drawerNumberInput.fill('100');

  // 单位
  await page.locator('.el-drawer:visible input[placeholder="如：个、箱、辆、顶"]').fill('顶');

  // 位置
  await page.locator('.el-drawer:visible input[placeholder="请输入存放位置"]').fill('北京仓库');

  await screenshot(page, '19_resource_form_filled');

  // 保存
  await page.click('.el-drawer:visible button:has-text("保 存")');
  await page.waitForTimeout(3000);
  await screenshot(page, '20_resource_created');

  // ============ 7. 志愿者管理 ============
  log('=== 7. 志愿者管理 ===');
  
  await page.click('text=志愿者管理');
  await waitForPageLoad(page);
  await page.waitForTimeout(2000);
  await screenshot(page, '21_volunteer_manage');

  // ============ 8. 受困者追踪 ============
  log('=== 8. 受困者追踪 ===');
  
  const trappedLink = page.locator('text=受困者追踪');
  if (await trappedLink.isVisible().catch(() => false)) {
    await trappedLink.click();
    await waitForPageLoad(page);
    await page.waitForTimeout(2000);
    await screenshot(page, '22_tracked_persons');
  } else {
    logIssue('侧边栏未找到"受困者追踪"');
    // 尝试直接导航
    await page.goto(`${BASE_URL}/trapped-persons`);
    await waitForPageLoad(page);
    await screenshot(page, '22_tracked_persons');
  }

  // ============ 9. 评估报告 ============
  log('=== 9. 评估报告 ===');
  
  await page.click('text=评估报告');
  await waitForPageLoad(page);
  await page.waitForTimeout(2000);
  await screenshot(page, '23_assessment_report');

  // ============ 10. AI救援助手 ============
  log('=== 10. AI救援助手 ===');
  
  await page.click('text=AI救援助手');
  await waitForPageLoad(page);
  await page.waitForTimeout(2000);
  await screenshot(page, '24_ai_assistant');

  // 点击快捷问题
  const quickBtn = page.locator('button:has-text("哪里最需要救援")');
  if (await quickBtn.isVisible().catch(() => false)) {
    await quickBtn.click();
    await page.waitForTimeout(5000);
    await screenshot(page, '25_ai_reply');
  } else {
    logIssue('未找到快捷问题按钮');
  }

  // ============ 11. 用户管理 ============
  log('=== 11. 用户管理 ===');
  
  await page.click('text=用户管理');
  await waitForPageLoad(page);
  await page.waitForTimeout(2000);
  await screenshot(page, '26_user_manage');

  // ============ 总结 ============
  log('=== E2E测试完成 ===');
  log(`截图数量: 26`);
  log(`发现问题数: ${issues.length}`);
  if (issues.length > 0) {
    log('问题列表:');
    issues.forEach((issue, i) => log(`  ${i + 1}. ${issue}`));
  }

  await browser.close();
}

main().catch(e => {
  console.error('E2E测试失败:', e);
  process.exit(1);
});
