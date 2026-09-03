import { chromium } from 'playwright';
import fs from 'fs';

const SHOT_DIR = '/Users/zaizai/Downloads/AI地震救援/screenshots/v3.0';
const BASE = 'http://localhost:5173';
fs.mkdirSync(SHOT_DIR, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1600, height: 950 } });
const errors = [];
page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
page.on('pageerror', e => errors.push(String(e)));

// 登录token（演示账号凭据由环境变量注入，不硬编码入库；见 .env.example）
const login = await fetch(`${BASE.replace('5173', '8000')}/api/v1/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: process.env.RESCUEAI_DEMO_USER, password: process.env.RESCUEAI_DEMO_PWD })
}).then(r => r.json());

await page.goto(`${BASE}/login`);
await page.evaluate(token => localStorage.setItem('token', token), login.access_token);

// Dashboard
await page.goto(`${BASE}/command-center`);
await page.waitForTimeout(2500);
await page.screenshot({ path: `${SHOT_DIR}/01-dashboard.png` });

// AI助手
await page.goto(`${BASE}/ai-assistant`);
await page.waitForTimeout(1500);
await page.screenshot({ path: `${SHOT_DIR}/02-ai-assistant.png` });

// 态势地图
await page.goto(`${BASE}/situation-map`);
await page.waitForTimeout(2000);
await page.screenshot({ path: `${SHOT_DIR}/03-situation-map.png` });

// 资源中心
await page.goto(`${BASE}/resource-center`);
await page.waitForTimeout(1500);
await page.screenshot({ path: `${SHOT_DIR}/04-resource-center.png` });

// 人员管理
await page.goto(`${BASE}/personnel/trapped`);
await page.waitForTimeout(1500);
await page.screenshot({ path: `${SHOT_DIR}/05-personnel.png` });

// 志愿者管理
await page.goto(`${BASE}/personnel/volunteers`);
await page.waitForTimeout(1500);
await page.screenshot({ path: `${SHOT_DIR}/06-volunteers.png` });

// 灾情管理(列表)
await page.goto(`${BASE}/disaster-list`);
await page.waitForTimeout(1500);
await page.screenshot({ path: `${SHOT_DIR}/07-disaster-list.png` });

// 灾情上报
await page.goto(`${BASE}/disaster-report`);
await page.waitForTimeout(1200);
await page.screenshot({ path: `${SHOT_DIR}/08-disaster-report.png` });

// 数据分析(评估报告)
await page.goto(`${BASE}/assessment-report`);
await page.waitForTimeout(1500);
await page.screenshot({ path: `${SHOT_DIR}/09-assessment.png` });

// 系统设置(用户管理)
await page.goto(`${BASE}/user-manage`);
await page.waitForTimeout(1500);
await page.screenshot({ path: `${SHOT_DIR}/10-user-manage.png` });

await page.goto(`${BASE}/command-center`);
await page.waitForTimeout(1000);

await browser.close();
console.log('Screenshots saved to', SHOT_DIR);
console.log('Console errors:', errors.length ? errors.slice(0, 5) : 'none');
