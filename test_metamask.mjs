import { chromium } from 'playwright';

const EXTENSION_PATH = '/tmp/metamask-ext';
const LIVE_URL = 'https://adebisi1111.github.io/agent-coordination/';

const browser = await chromium.launchPersistentContext('/tmp/mm-browser', {
  headless: true,
  args: [
    `--disable-extensions-except=${EXTENSION_PATH}`,
    `--load-extension=${EXTENSION_PATH}`,
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-dev-shm-usage',
  ],
});

const page = browser.pages()[0] || await browser.newPage();

console.log('=== Opening live site ===');
await page.goto(LIVE_URL, { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(3000);

const title = await page.locator('h1').textContent();
console.log('Page title:', title);

// Try clicking connect
const connectBtn = await page.locator('#connectBtn');
console.log('Connect button found:', await connectBtn.count());

if (await connectBtn.count()) {
  await connectBtn.click();
  console.log('Clicked connect');
  await page.waitForTimeout(5000);
  
  // Check pages for MetaMask popup
  const pages = browser.pages();
  console.log('Open pages:', pages.length);
  for (const p of pages) {
    console.log('  page:', p.url().slice(0, 80));
  }
}

// Check wallet status
const walletStatus = await page.locator('#walletStatus').textContent();
console.log('Wallet status:', walletStatus);

await page.screenshot({ path: 'shot_metamask.png', fullPage: true });
console.log('Screenshot saved');

await browser.close();
