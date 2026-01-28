#!/usr/bin/env node
/**
 * BROWSER E2E TEST - Dashboard Render Verification
 * Tests actual browser rendering with Playwright
 */

const { chromium } = require('playwright');

const PRODUCTION_URL = 'https://dashboard.lexmakesit.com';
const TIMEOUT_MS = 10000;

async function testDashboardBrowser() {
    console.log('='.repeat(60));
    console.log('🌐 BROWSER E2E TEST');
    console.log('='.repeat(60));
    console.log();
    console.log(`Testing: ${PRODUCTION_URL}`);
    console.log(`Timeout: ${TIMEOUT_MS}ms`);
    console.log();

    let browser;
    let allPassed = true;

    try {
        // Launch browser
        console.log('[1/6] Launching browser...');
        browser = await chromium.launch({
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });
        const context = await browser.newContext({
            ignoreHTTPSErrors: false,
            viewport: { width: 1920, height: 1080 }
        });
        const page = await context.newPage();
        console.log('✅ PASS: Browser launched');

        // Collect console messages
        const consoleMessages = [];
        const consoleErrors = [];
        page.on('console', msg => {
            consoleMessages.push({ type: msg.type(), text: msg.text() });
            if (msg.type() === 'error') {
                consoleErrors.push(msg.text());
            }
        });

        // Collect page errors
        const pageErrors = [];
        page.on('pageerror', err => {
            pageErrors.push(err.message);
        });

        // Test 2: Navigate to page
        console.log('\n[2/6] Navigating to dashboard...');
        const response = await page.goto(PRODUCTION_URL, {
            waitUntil: 'domcontentloaded',
            timeout: TIMEOUT_MS
        });
        
        if (!response || !response.ok()) {
            console.log(`❌ FAIL: HTTP ${response?.status() || 'unknown'}`);
            allPassed = false;
        } else {
            console.log(`✅ PASS: HTTP ${response.status()}`);
        }

        // Test 3: Wait for body to have content
        console.log('\n[3/6] Waiting for page to render...');
        await page.waitForSelector('body', { timeout: 5000 });
        
        // Wait a bit more for React to hydrate
        await page.waitForTimeout(2000);
        
        const bodyText = await page.evaluate(() => document.body.innerText);
        
        if (bodyText.length < 50) {
            console.log(`❌ FAIL: Page appears blank (${bodyText.length} chars)`);
            console.log(`Body text: "${bodyText.substring(0, 100)}..."`);
            allPassed = false;
        } else {
            console.log(`✅ PASS: Page has ${bodyText.length} chars of text`);
        }

        // Test 4: Check for emergency failsafe
        console.log('\n[4/6] Checking for emergency failsafe...');
        const hasFailsafe = bodyText.includes('Dashboard Temporarily Unavailable');
        if (hasFailsafe) {
            console.log('❌ FAIL: Emergency failsafe was triggered - React failed to hydrate');
            allPassed = false;
        } else {
            console.log('✅ PASS: No failsafe triggered');
        }

        // Test 5: Check for UI elements
        console.log('\n[5/6] Checking for UI elements...');
        const hasLoginForm = bodyText.toLowerCase().includes('sign in') || 
                            bodyText.toLowerCase().includes('email') ||
                            bodyText.toLowerCase().includes('password');
        
        const hasDashboard = bodyText.toLowerCase().includes('dashboard') ||
                           bodyText.toLowerCase().includes('receptionist');
        
        if (!hasLoginForm && !hasDashboard) {
            console.log('❌ FAIL: No recognizable UI elements found');
            console.log(`First 200 chars: "${bodyText.substring(0, 200)}..."`);
            allPassed = false;
        } else {
            console.log('✅ PASS: UI elements present');
            if (hasLoginForm) console.log('   ✓ Login form detected');
            if (hasDashboard) console.log('   ✓ Dashboard elements detected');
        }

        // Test 6: Check for console errors
        console.log('\n[6/6] Checking for console errors...');
        
        // Filter out noise
        const realErrors = consoleErrors.filter(err => {
            const lower = err.toLowerCase();
            return !lower.includes('favicon') && 
                   !lower.includes('chrome-extension') &&
                   !lower.includes('warning');
        });
        
        if (realErrors.length > 0) {
            console.log(`⚠️  WARN: ${realErrors.length} console error(s):`);
            realErrors.forEach((err, i) => {
                console.log(`   ${i + 1}. ${err.substring(0, 100)}${err.length > 100 ? '...' : ''}`);
            });
            // Not failing for console errors, just warning
        } else {
            console.log('✅ PASS: No console errors');
        }

        if (pageErrors.length > 0) {
            console.log(`⚠️  WARN: ${pageErrors.length} page error(s):`);
            pageErrors.forEach((err, i) => {
                console.log(`   ${i + 1}. ${err.substring(0, 100)}${err.length > 100 ? '...' : ''}`);
            });
        }

        // Take screenshot
        await page.screenshot({ path: '/tmp/dashboard-test.png', fullPage: true });
        console.log('\n📸 Screenshot saved: /tmp/dashboard-test.png');

    } catch (error) {
        console.log(`\n❌ FATAL ERROR: ${error.message}`);
        allPassed = false;
    } finally {
        if (browser) {
            await browser.close();
        }
    }

    // Final result
    console.log();
    console.log('='.repeat(60));
    if (allPassed) {
        console.log('✅ ALL BROWSER TESTS PASSED');
        console.log('='.repeat(60));
        console.log();
        console.log('Dashboard is rendering correctly in browser:');
        console.log('  - Page loads: ✅');
        console.log('  - Content visible: ✅');
        console.log('  - No white screen: ✅');
        console.log('  - No failsafe: ✅');
        console.log('  - UI elements: ✅');
        process.exit(0);
    } else {
        console.log('❌ BROWSER TESTS FAILED');
        console.log('='.repeat(60));
        console.log();
        console.log('🚨 The dashboard has rendering issues in browser');
        console.log('Check the screenshot: /tmp/dashboard-test.png');
        process.exit(1);
    }
}

// Run test
testDashboardBrowser().catch(err => {
    console.error('Unhandled error:', err);
    process.exit(1);
});
