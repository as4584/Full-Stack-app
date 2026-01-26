const { chromium } = require('playwright');

(async () => {
    try {
        const browser = await chromium.launch({ headless: true });
        const context = await browser.newContext();
        const page = await context.newPage();
        console.log('Navigating to http://localhost:3000...');
        await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
        console.log('Page loaded. Taking screenshot...');
        await page.screenshot({ path: '/home/lex/lexmakesit/screenshot.png' });
        console.log('Screenshot saved to /home/lex/lexmakesit/screenshot.png');
        await browser.close();
    } catch (error) {
        console.error('Error during browser execution:', error);
        process.exit(1);
    }
})();
