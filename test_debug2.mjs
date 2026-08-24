import { chromium } from 'playwright';

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
const allMsgs = [];
page.on('pageerror', (e) => allMsgs.push('PAGEERROR ' + e.message));
page.on('console', (m) => allMsgs.push(`CONSOLE ${m.type()}: ${m.text()}`));
page.on('requestfailed', (r) => allMsgs.push(`REQFAIL ${r.url()} ${r.failure()?.errorText}`));
page.on('response', (r) => { if (r.status() >= 400) allMsgs.push(`HTTP ${r.status()} ${r.url()}`); });

await page.goto('http://127.0.0.1:8099/index.html', { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(3000);

console.log('=== ALL MESSAGES ===');
allMsgs.forEach(m => console.log(m));

// Check if module executed
const moduleExecuted = await page.evaluate(() => {
  return typeof window.loadTasks === 'function';
});
console.log('loadTasks on window:', moduleExecuted);

await browser.close();
