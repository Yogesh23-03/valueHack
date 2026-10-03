const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

async function run() {
  const browser = await chromium.launch({ headless: true });
  const routes = ['', 'dashboard', 'fire-drill', 'pricing', 'vendor-check', 'bill-scan', 'report', 'about'];
  const baseDir = path.join(__dirname, 'public', 'screenshots');
  if (!fs.existsSync(baseDir)) fs.mkdirSync(baseDir, { recursive: true });

  const viewports = [
    { name: 'desktop', width: 1440, height: 900 },
    { name: 'mobile', width: 390, height: 844 }
  ];

  for (const vp of viewports) {
    for (const theme of ['dark', 'light']) {
      const context = await browser.newContext({
        viewport: { width: vp.width, height: vp.height },
        colorScheme: theme
      });
      const page = await context.newPage();

      for (const r of routes) {
        const url = `http://localhost:3004/${r}`;
        try {
          await page.goto(url, { waitUntil: 'networkidle', timeout: 10000 });
          await page.evaluate((t) => {
            document.documentElement.classList.remove('dark', 'light');
            document.documentElement.classList.add(t);
          }, theme);
          await page.waitForTimeout(500);

          const fileName = `${r || 'home'}_${vp.name}_${theme}.png`;
          const filePath = path.join(baseDir, fileName);
          await page.screenshot({ path: filePath, fullPage: false });
          console.log(`Saved screenshot: ${fileName}`);
        } catch (e) {
          console.error(`Error taking screenshot for ${url}:`, e.message);
        }
      }
      await context.close();
    }
  }

  await browser.close();
  console.log('All screenshots captured successfully!');
}

run();
