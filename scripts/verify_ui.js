const { chromium } = require('playwright');

(async () => {
    try {
        const browser = await chromium.launch({ headless: true });
        const context = await browser.newContext();
        const page = await context.newPage();
        const url = 'https://lexmakesit.com/projects/ai-receptionist';
        console.log(`Navigating to ${url}...`);
        await page.goto(url, { waitUntil: 'networkidle' });

        // Scroll to the bottom of the trust section
        await page.evaluate(() => {
            window.scrollTo(0, document.body.scrollHeight);
        });

        console.log('Page loaded. Taking screenshot...');
        await page.screenshot({ path: '/home/lex/lexmakesit/verification_screenshot_2.png', fullPage: true });
        console.log('Screenshot saved to /home/lex/lexmakesit/verification_screenshot_2.png');
        await browser.close();
    } catch (error) {
        console.error('Error during browser execution:', error);
        process.exit(1);
    }
})();
