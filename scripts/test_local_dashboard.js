
const { chromium } = require('playwright');

(async () => {
    console.log('Starting browser test for local dashboard...');
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext();
    const page = await context.newPage();

    try {
        console.log('Navigating to http://localhost:3000...');
        await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });

        // Check for "Configure Phone Number" button if no number
        const configBtn = await page.$('button:has-text("Configure Phone Number")');
        if (configBtn) {
            console.log('Configure Phone Number button found. Opening modal...');
            await configBtn.click();

            const zipInput = await page.$('input[placeholder*="Zip Code"]');
            if (zipInput) {
                console.log('Searching for zip 89089...');
                await zipInput.fill('89089');
                await page.keyboard.press('Enter');
                await page.waitForTimeout(2000);

                const results = await page.$$('div:has-text("(890)")');
                console.log(`Found ${results.length} mock results for 89089.`);
            }
        } else {
            console.log('Dashboard loaded. Checking phone number...');
            const phoneText = await page.innerText('body');
            if (phoneText.includes('+15550001234')) {
                console.log('Found correct business phone number from DB: +15550001234');
            } else {
                console.log('Business phone number not found as expected.');
            }
        }

        // Check Google Cal button
        const googleBtn = await page.$('button:has-text("Connect Google Cal")');
        if (googleBtn) {
            console.log('Connect Google Cal button found. Clicking...');
            await googleBtn.click();
            await page.waitForTimeout(2000);
            console.log('URL after click:', page.url());
            if (page.url().includes('accounts.google.com')) {
                console.log('Redirected to Google OAuth correctly!');
            } else {
                console.log('Redirect failed or went elsewhere:', page.url());
            }
        }

    } catch (err) {
        console.error('Test failed:', err);
    } finally {
        await browser.close();
        console.log('Browser closed.');
    }
})();
