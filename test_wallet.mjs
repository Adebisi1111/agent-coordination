import { chromium } from 'playwright';

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
const errs = [];
page.on('pageerror', (e) => errs.push('PAGEERROR ' + e.message));
page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });

await page.goto('http://127.0.0.1:8099/index.html', { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(3000);

// Check connect button exists
const connectBtn = await page.locator('#connectBtn').count();
console.log('connect button:', connectBtn);

// Check wallet status
const walletStatus = await page.locator('#walletStatus').textContent();
console.log('wallet status:', walletStatus);

// Try clicking connect (should fail without MetaMask, but should show error handling)
await page.click('#connectBtn');
await page.waitForTimeout(1000);

const walletStatusAfter = await page.locator('#walletStatus').textContent();
console.log('wallet status after click:', walletStatusAfter);

console.log('errors:', errs.length ? errs.slice(0, 5) : 'none');

await browser.close();
