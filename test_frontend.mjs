// Verify Agent Coordination System renders and works end-to-end
import { chromium } from 'playwright';

const BASE = 'http://127.0.0.1:8099';
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 390, height: 844 } });

const errs = [];
page.on('pageerror', (e) => errs.push('PAGEERROR ' + e.message));
page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });

await page.goto(`${BASE}/index.html`, { waitUntil: 'domcontentloaded' });

// Wait for the page to fully load
await page.waitForTimeout(2000);

// Check core UI elements exist
const title = await page.locator('h1').textContent();
const badges = await page.locator('.badge').count();
const nav = await page.locator('.nav a').count();
const statCount = await page.locator('.stat').count();
const sectionCount = await page.locator('.section').count();

console.log('title      :', title);
console.log('badges     :', badges);
console.log('nav tabs   :', nav);
console.log('stats      :', statCount);
console.log('sections   :', sectionCount);

// Check tabs work
await page.click('.nav a:nth-child(2)');  // Agents tab
await page.waitForTimeout(300);
const agentsVisible = await page.locator('#tab-agents').isVisible();

await page.click('.nav a:nth-child(3)');  // Post Task tab
await page.waitForTimeout(300);
const postFormVisible = await page.locator('#tab-post').isVisible();
const postBtn = await page.locator('#postBtn').count();

await page.click('.nav a:nth-child(4)');  // Register tab
await page.waitForTimeout(300);
const regFormVisible = await page.locator('#tab-register').isVisible();
const regBtn = await page.locator('#regBtn').count();

console.log('agents tab visible :', agentsVisible);
console.log('post tab visible   :', postFormVisible);
console.log('post button        :', postBtn);
console.log('register tab visible:', regFormVisible);
console.log('register button    :', regBtn);

// Verify contract address in client
const contractHtml = await page.content();
const hasContract = contractHtml.includes('0x07DCEc4A77AB245a7F66144eDDa6A6D9C05789eD');
console.log('contract in page   :', hasContract);

// Check if gl-client.js is loaded
const hasClient = await page.locator('script[src*="gl-client"]').count();
console.log('client script      :', hasClient);

console.log('console errors     :', errs.length ? errs.slice(0, 5) : 'none');

await page.screenshot({ path: 'shot_agent_coordination.png', fullPage: true });
await browser.close();
