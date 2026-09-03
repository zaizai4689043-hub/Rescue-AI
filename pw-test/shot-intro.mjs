import { chromium } from 'playwright';

const url = 'http://localhost:8765/RescueAI%E4%BA%A7%E5%93%81%E4%BB%8B%E7%BB%8D.html';
const outDir = '/Users/zaizai/Downloads/AI地震救援/screenshots/intro';
import { mkdirSync } from 'fs';
mkdirSync(outDir, { recursive: true });

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2 });
const page = await ctx.newPage();

await page.goto(url, { waitUntil: 'networkidle' });
await page.waitForTimeout(1500);

// 1. Hero
await page.screenshot({ path: `${outDir}/01_hero.png` });

// 2. Problem
await page.locator('#problem').scrollIntoViewIfNeeded();
await page.waitForTimeout(1200);
await page.screenshot({ path: `${outDir}/02_problem.png` });

// 3. Positioning
await page.locator('#position').scrollIntoViewIfNeeded();
await page.waitForTimeout(800);
await page.screenshot({ path: `${outDir}/03_position.png` });

// 4. Architecture
await page.locator('#arch').scrollIntoViewIfNeeded();
await page.waitForTimeout(800);
await page.screenshot({ path: `${outDir}/04_arch.png` });

// 5. Agents
await page.locator('#agents').scrollIntoViewIfNeeded();
await page.waitForTimeout(800);
await page.screenshot({ path: `${outDir}/05_agents.png` });

// 6. Verify loop
await page.locator('#verify').scrollIntoViewIfNeeded();
await page.waitForTimeout(800);
await page.screenshot({ path: `${outDir}/06_verify.png` });

// 7. Sources
await page.locator('#sources').scrollIntoViewIfNeeded();
await page.waitForTimeout(800);
await page.screenshot({ path: `${outDir}/07_sources.png` });

// 8. Data
await page.locator('#data').scrollIntoViewIfNeeded();
await page.waitForTimeout(800);
await page.screenshot({ path: `${outDir}/08_data.png` });

// 9. Cases
await page.locator('#cases').scrollIntoViewIfNeeded();
await page.waitForTimeout(800);
await page.screenshot({ path: `${outDir}/09_cases.png` });

// 10. Tech
await page.locator('#tech').scrollIntoViewIfNeeded();
await page.waitForTimeout(800);
await page.screenshot({ path: `${outDir}/10_tech.png` });

// 11. Responsibility
await page.locator('#resp').scrollIntoViewIfNeeded();
await page.waitForTimeout(800);
await page.screenshot({ path: `${outDir}/11_resp.png` });

// 12. CTA + Footer
await page.locator('#cta').scrollIntoViewIfNeeded();
await page.waitForTimeout(800);
await page.screenshot({ path: `${outDir}/12_cta.png` });

// 13. Full page
await page.screenshot({ path: `${outDir}/00_fullpage.png`, fullPage: true });

console.log('✅ All screenshots saved to', outDir);
await browser.close();
