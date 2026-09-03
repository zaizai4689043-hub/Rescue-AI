// 台风模式删除后：顶栏与整体视觉确认
import { chromium } from 'playwright';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const file = 'file://' + path.resolve(__dirname, '../GOAI复赛/rescueai-dashboard.html');
const shots = path.resolve(__dirname, '../screenshots');

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
await page.goto(file);
await page.waitForTimeout(3000);
await page.locator('#header').screenshot({ path: path.join(shots, 'final_09_no_typhoon_header.png') });
await page.screenshot({ path: path.join(shots, 'final_09_no_typhoon_full.png') });
const btns = await page.locator('.mode-btn').allInnerTexts();
console.log('顶栏按钮：', JSON.stringify(btns));
await browser.close();
