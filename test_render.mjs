import { chromium } from 'playwright';

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 390, height: 844 } });

await page.goto('http://127.0.0.1:8099/index.html', { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(2000);

const title = await page.locator('h1').textContent();
const nav = await page.locator('.nav a').count();
const statCount = await page.locator('.stat').count();
const sectionCount = await page.locator('.section').count();

console.log('title      :', title);
console.log('nav tabs   :', nav);
console.log('stats      :', statCount);
console.log('sections   :', sectionCount);

// Tab navigation
await page.click('.nav a[data-tab="agents"]');
await page.waitForTimeout(300);
console.log('agents tab :', await page.locator('#tab-agents').isVisible());

await page.click('.nav a[data-tab="post"]');
await page.waitForTimeout(300);
console.log('post tab   :', await page.locator('#tab-post').isVisible());
console.log('post btn   :', await page.locator('#postBtn').count());

await page.click('.nav a[data-tab="register"]');
await page.waitForTimeout(300);
console.log('reg tab    :', await page.locator('#tab-register').isVisible());
console.log('reg btn    :', await page.locator('#regBtn').count());

await page.screenshot({ path: 'shot_final.png', fullPage: true });
await browser.close();
