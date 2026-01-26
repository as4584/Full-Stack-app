const { chromium } = require('playwright');
const fs = require('fs');

const BASE_URL = 'https://dashboard.lexmakesit.com';
const USER_EMAIL = 'thegamermasterninja@gmail.com';
const USER_PASSWORD = 'ChangeMe123!';

async function runVisualInspection() {
    console.log('👁️  Initializing Visual Inspection...');

    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    });

    const context = await browser.newContext({
        viewport: { width: 1280, height: 800 },
        ignoreHTTPSErrors: true
    });

    const page = await context.newPage();

    // Helper to print what we see
    async function see(label, selector, property = 'innerText') {
        try {
            await page.waitForSelector(selector, { timeout: 2000 });
            const element = await page.$(selector);
            let value;
            if (property === 'checked') {
                value = await element.isChecked() ? 'CHECKED' : 'UNCHECKED';
            } else if (property === 'count') {
                const elements = await page.$$(selector);
                value = elements.length;
            } else {
                value = await element.innerText();
                value = value.replace(/\n/g, ' ').trim();
            }
            console.log(`   [${label}]: "${value}"`);
            return value;
        } catch (e) {
            console.log(`   [${label}]: ❌ NOT FOUND or ERROR`);
            return null;
        }
    }

    try {
        // 1. Login
        console.log('\n--- 🔑 Login Step ---');
        await page.goto(`${BASE_URL}/login`);
        await page.fill('input[type="email"]', USER_EMAIL);
        await page.fill('input[type="password"]', USER_PASSWORD);
        await page.click('button[type="submit"]');
        await page.waitForLoadState('networkidle');

        const url = page.url();
        console.log(`   Converted URL: ${url}`);

        if (url.includes('/login')) throw new Error('Login Failed');

        // 2. Dashboard Overview
        console.log('\n--- 🏠 Dashboard Home ---');

        // VERIFY QUIET ZONES
        const cardStyle = await page.evaluate(() => {
            const card = document.querySelector('.aiStatusCard') || document.querySelector('[class*="aiStatusCard"]');
            return window.getComputedStyle(card).backgroundImage;
        });
        console.log(`   [Quiet Zone Gradient]: ${cardStyle}`);
        if (!cardStyle.includes('linear-gradient')) throw new Error('Quiet Zone Gradient NOT found!');

        // Check Status Card
        await see('AI Status Title', 'h2:has-text("AI Receptionist Status")');
        await see('Business Name', '.statusInfo h3'); // Using class names we saw in css
        await see('Status Text', '.statusInfo .statusText'); // "Active" or "Inactive"
        await see('Toggle Switch', 'input[type="checkbox"]', 'checked');

        // Check Queue
        await see('Active Calls Count', '.queueOrb span');
        await see('Active Calls Detail', '.queueSubtext');

        // Check Logs
        console.log('\n--- 📋 Logs Section ---');
        const logCount = await see('Log Rows Visible', '.logItem', 'count');

        if (logCount > 0) {
            // Inspect first log
            console.log('   > Inspecting First Log Entry:');
            await see('   Number', '.logItem:first-child .logName');
            await see('   Summary', '.logItem:first-child .logSummary');
            await see('   Duration', '.logItem:first-child .logDuration');
            await see('   Date', '.logItem:first-child .chip:last-child'); // Approx selector

            // 3. Drill down into Call Detail
            console.log('\n--- 🔍 Call Detail Page ---');
            console.log('   > Clicking first log item...');
            await page.click('.logItem:first-child');
            await page.waitForTimeout(2000);

            console.log(`   Navigated to: ${page.url()}`);
            await see('Caller Header', 'h1');
            await see('Appointment Tag', '.chip');

            // Check Transcript
            console.log('   > Checking Transcript...');
            const transcriptLines = await see('Transcript Lines', '.transcriptText p', 'count');
            console.log(`   [Transcript]: Found ${transcriptLines} lines of conversation.`);

            if (transcriptLines > 0) {
                const firstLine = await page.innerText('.transcriptText p:first-child');
                console.log(`   [Sample Line]: "${firstLine.replace(/\n/g, ' ')}"`);
            } else {
                await see('Empty State', '.transcriptContent p');
            }

            // Check Block Button
            console.log('   > Checking Actions...');
            const blockBtnText = await see('Block Button', 'button:has-text("Block")');
            if (!blockBtnText) await see('Block Button', 'button:has-text("Blocked")');

            // Test Back Button
            console.log('   > Testing Back Navigation...');
            await page.click('button:has-text("Back to Dashboard")');
            await page.waitForLoadState('networkidle');
            console.log(`   Returned to: ${page.url()}`);
        } else {
            console.log('   (No logs to inspect)');
        }

        // 4. Settings
        console.log('\n--- ⚙️ Settings Page ---');
        await page.goto(`${BASE_URL}/app/settings`);
        await see('Settings Header', 'h1');
        await see('Description Input Value', 'textarea', 'value'); // Might need input value logic

    } catch (error) {
        console.error('❌ FATAL ERROR:', error);
    } finally {
        await browser.close();
        console.log('\n✨ Inspection Complete.');
    }
}

runVisualInspection();
