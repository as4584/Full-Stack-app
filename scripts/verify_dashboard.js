const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// Configuration
const BASE_URL = 'https://dashboard.lexmakesit.com';
const USER_EMAIL = 'thegamermasterninja@gmail.com';
const USER_PASSWORD = 'password123';
const SCREENSHOT_DIR = '/home/lex/lexmakesit/artifacts/browser_test';

// Ensure artifact directory exists
if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

async function runTests() {
    console.log('🚀 Starting Comprehensive Dashboard Test...');
    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    });
    const context = await browser.newContext({
        viewport: { width: 1280, height: 800 },
        ignoreHTTPSErrors: true
    });
    const page = await context.newPage();

    // Helper for screenshots
    async function takeScreenshot(name) {
        const filename = `${name}.png`;
        const filepath = path.join(SCREENSHOT_DIR, filename);
        await page.screenshot({ path: filepath, fullPage: true });
        console.log(`📸 Screenshot saved: ${filename}`);
    }

    try {
        // 1. Login
        console.log('🔑 Logging in...');
        await page.goto(`${BASE_URL}/login`);
        await page.fill('input[type="email"]', USER_EMAIL);
        await page.fill('input[type="password"]', USER_PASSWORD);
        await page.click('button[type="submit"]'); // Adjust selector if needed

        // Wait for navigation and verify redirect
        await page.waitForTimeout(3000);
        const url = page.url();
        console.log(`📍 Current URL: ${url}`);
        await takeScreenshot('01_after_login');

        if (url.includes('/login')) {
            throw new Error('Login failed - stuck on login page');
        }

        if (url.includes('/onboarding')) {
            console.log('🚧 User redirected to Onboarding - Verifying Pricing...');
            const pageContent = await page.content();
            if (pageContent.includes('$75') && pageContent.includes('250 Minutes')) {
                console.log('✅ Onboarding Pricing Verified: $75 / 250 mins');
            } else {
                console.error('❌ Onboarding Pricing Mismatch!');
            }
            await takeScreenshot('01b_onboarding_pricing');

            // Try to bypass onboarding to test dashboard if possible, or stop here
            console.log('⚠️ Cannot test Dashboard buttons because user is locked in Onboarding payment wall.');
            // We will TRY to navigate to /app anyway to see if it lets us
            await page.goto(`${BASE_URL}/app`);
            await page.waitForTimeout(2000);
            await takeScreenshot('01c_forced_dashboard_nav');
            if (page.url().includes('/onboarding')) {
                throw new Error('User is correctly locked in onboarding. Cannot test Dashboard functions until payment is simulated or bypassed.');
            }
        }

        // 2. Dashboard Home
        console.log('🏠 Testing Dashboard Home...');
        // Check key elements
        await takeScreenshot('02_dashboard_home');

        // Check Minutes
        // NOTE: We need to identify the selector for minutes. 
        // Assuming it's some text on the page logic we have in page.tsx

        // 3. Logs Page
        console.log('📋 Testing Logs Page...');
        await page.goto(`${BASE_URL}/app/receptionists`);
        await page.waitForTimeout(2000);
        await takeScreenshot('03_logs_page');

        // Check if calls exist
        const calls = await page.$$('.logItem'); // Assuming class name from css modules logic (might need tweaking)
        // Actually CSS modules hash classes, so we might need to look for text or partial selectors.
        // However, the text "Call History" should be there.
        const h1Text = await page.textContent('h1');
        if (!h1Text.includes('Call History')) console.error('❌ Logs Page Title Missing');
        else console.log('✅ Logs Page Loaded');

        // 4. Click a Call (if any)
        const callLinks = await page.$$('div[onClick]'); // Rough guess, often divs with onClick in React
        // Better strategy: Click the first element that looks like a logs row
        // We can search for text like "Unknown" or a phone number regex

        // 5. Test Settings / Calendar
        console.log('⚙️ Testing Settings...');
        await page.goto(`${BASE_URL}/app/settings`);
        await takeScreenshot('04_settings_page');

        console.log('✅ Test Run Complete.');

    } catch (error) {
        console.error('❌ Test Failed:', error);
        await takeScreenshot('error_state');
    } finally {
        await browser.close();
    }
}

runTests();
