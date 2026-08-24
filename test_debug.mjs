import { chromium } from 'playwright';

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
const errs = [];
page.on('pageerror', (e) => errs.push('PAGEERROR ' + e.message));
page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });

await page.goto('http://127.0.0.1:8099/index.html', { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(3000);

// Debug: check if showTab is defined
const hasShowTab = await page.evaluate(() => typeof window.showTab);
console.log('showTab on window:', hasShowTab);

// Debug: manually call showTab
await page.evaluate(() => {
  if (window.showTab) window.showTab('agents');
});
await page.waitForTimeout(500);
console.log('agents tab after manual call:', await page.locator('#tab-agents').isVisible());

// Debug: check all tab divs
const tabStates = await page.evaluate(() => {
  const tabs = ['tasks', 'agents', 'post', 'register'];
  const result = {};
  tabs.forEach(t => {
    const el = document.getElementById('tab-' + t);
    result[t] = el ? el.style.display : 'not found';
  });
  return result;
});
console.log('tab display states:', tabStates);

console.log('errors:', errs.length ? errs.slice(0, 5) : 'none');

await browser.close();
