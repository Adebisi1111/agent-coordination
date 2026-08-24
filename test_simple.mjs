import { chromium } from 'playwright';

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
const errs = [];
page.on('pageerror', (e) => errs.push('PAGEERROR ' + e.message));
page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });

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
await page.click('.nav a:nth-child(2)');
await page.waitForTimeout(300);
console.log('agents tab :', await page.locator('#tab-agents').isVisible());

await page.click('.nav a:nth-child(3)');
await page.waitForTimeout(300);
console.log('post tab   :', await page.locator('#tab-post').isVisible());
console.log('post btn   :', await page.locator('#postBtn').count());

await page.click('.nav a:nth-child(4)');
await page.waitForTimeout(300);
console.log('reg tab    :', await page.locator('#tab-register').isVisible());
console.log('reg btn    :', await page.locator('#regBtn').count());

// Contract address
const html = await page.content();
console.log('has contract:', html.includes('0x07DCEc4A77AB245a7F66144eDDa6A6D9C05789eD'));
console.log('errors      :', errs.length ? errs.slice(0, 5) : 'none');

await page.screenshot({ path: 'shot_test.png', fullPage: true });
await browser.close();
