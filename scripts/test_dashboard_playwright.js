#!/usr/bin/env node
/**
 * PLAYWRIGHT E2E TEST - Dashboard White Screen Detection
 * 
 * This test MUST FAIL if the dashboard shows a white screen.
 * Used as a deployment gate to prevent white screen bugs.
 * 
 * Tests:
 * 1. Page loads without errors
 * 2. Visible text content exists (not blank)
 * 3. No React hydration errors
 * 4. Key UI elements are present
 */

const { chromium } = require('playwright');

const PRODUCTION_URL = 'https://dashboard.lexmakesit.com';
const TIMEOUT_MS = 15000;

async function testDashboardRendering() {
    console.log('='.repeat(70));
    console.log('🎭 PLAYWRIGHT E2E TEST - White Screen Detection');
    console.log('='.repeat(70));
    console.log();
    console.log(`Target: ${PRODUCTION_URL}`);
    console.log(`Timeout: ${TIMEOUT_MS}ms`);
    console.log();

    let browser;
    let allPassed = true;
    const errors = [];

    try {
        // Test 1: Launch browser
        console.log('[1/6] 🚀 Launching headless browser...');
        browser = await chromium.launch({
            headless: true,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-web-security'
            ]
        });
        
        const context = await browser.newContext({
            viewport: { width: 1920, height: 1080 },
            userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        });
        
        const page = await context.newPage();
        console.log('   ✅ Browser launched');

        // Collect console messages and errors
        const consoleErrors = [];
        const hydrationErrors = [];
        
        page.on('console', msg => {
            if (msg.type() === 'error') {
                const text = msg.text();
                consoleErrors.push(text);
                
                // Detect React hydration errors
                if (text.includes('Hydration') || 
                    text.includes('hydration') ||
                    text.includes('Minified React error #418') ||
                    text.includes('Minified React error #423')) {
                    hydrationErrors.push(text);
                }
            }
        });

        page.on('pageerror', err => {
            consoleErrors.push(err.message);
        });

        // Test 2: Navigate to dashboard
        console.log('\n[2/6] 🌐 Navigating to dashboard...');
        const response = await page.goto(PRODUCTION_URL, {
            waitUntil: 'domcontentloaded',
            timeout: TIMEOUT_MS
        });
        
        const status = response?.status();
        if (!response || (status !== 200 && status !== 307)) {
            errors.push(`HTTP ${status || 'unknown'} - Expected 200 or 307`);
            allPassed = false;
            console.log(`   ❌ HTTP ${status}`);
        } else {
            console.log(`   ✅ HTTP ${status}`);
        }

        // Test 3: Wait for content to render
        console.log('\n[3/6] ⏳ Waiting for content to render...');
        try {
            await page.waitForSelector('body', { timeout: 5000 });
            
            // Wait for React to hydrate (give it time)
            await page.waitForTimeout(3000);
            
            console.log('   ✅ Page rendered');
        } catch (e) {
            errors.push(`Timeout waiting for body: ${e.message}`);
            allPassed = false;
            console.log('   ❌ Page render timeout');
        }

        // Test 4: Check for visible text content (CRITICAL - must fail if blank)
        console.log('\n[4/6] 📝 Checking for visible text...');
        const bodyText = await page.evaluate(() => {
            const body = document.body;
            const innerText = body.innerText || '';
            const textContent = body.textContent || '';
            
            // Also check if body has any visible elements
            const visibleElements = Array.from(body.querySelectorAll('*')).filter(el => {
                const style = window.getComputedStyle(el);
                return style.display !== 'none' && 
                       style.visibility !== 'hidden' && 
                       style.opacity !== '0';
            });
            
            return {
                innerText,
                textContent,
                visibleElementCount: visibleElements.length,
                bodyHasContent: body.children.length > 0
            };
        });

        const visibleText = bodyText.innerText.trim();
        const textLength = visibleText.length;

        // STRICT CHECK - fail if page appears blank
        if (textLength < 50 || !bodyText.bodyHasContent) {
            errors.push(`CRITICAL: Page appears blank (${textLength} chars, ${bodyText.visibleElementCount} visible elements)`);
            allPassed = false;
            console.log(`   ❌ BLANK PAGE DETECTED`);
            console.log(`      - Text length: ${textLength} chars`);
            console.log(`      - Visible elements: ${bodyText.visibleElementCount}`);
            console.log(`      - Body has children: ${bodyText.bodyHasContent}`);
            console.log(`      - First 100 chars: "${visibleText.substring(0, 100)}"`);
        } else {
            console.log(`   ✅ ${textLength} characters visible`);
            console.log(`      - ${bodyText.visibleElementCount} visible elements`);
        }

        // Test 5: Check for expected UI elements
        console.log('\n[5/6] 🔍 Checking for UI elements...');
        const hasLoginElements = visibleText.toLowerCase().includes('sign in') ||
                                visibleText.toLowerCase().includes('email') ||
                                visibleText.toLowerCase().includes('password') ||
                                visibleText.toLowerCase().includes('welcome back');
        
        const hasDashboardElements = visibleText.toLowerCase().includes('dashboard') ||
                                    visibleText.toLowerCase().includes('receptionist') ||
                                    visibleText.toLowerCase().includes('lexmakesit');

        if (!hasLoginElements && !hasDashboardElements) {
            errors.push('No recognizable UI elements found');
            allPassed = false;
            console.log('   ❌ No login or dashboard UI found');
        } else {
            console.log('   ✅ UI elements detected');
            if (hasLoginElements) console.log('      - Login form detected');
            if (hasDashboardElements) console.log('      - Dashboard elements detected');
        }

        // Test 6: Check for hydration errors
        console.log('\n[6/6] 🔬 Checking for hydration errors...');
        
        if (hydrationErrors.length > 0) {
            errors.push(`${hydrationErrors.length} React hydration error(s) detected`);
            allPassed = false;
            console.log(`   ❌ ${hydrationErrors.length} hydration error(s):`);
            hydrationErrors.slice(0, 3).forEach((err, i) => {
                console.log(`      ${i + 1}. ${err.substring(0, 80)}...`);
            });
        } else {
            console.log('   ✅ No hydration errors');
        }

        // Log other console errors (warnings only)
        if (consoleErrors.length > 0 && hydrationErrors.length === 0) {
            const nonHydrationErrors = consoleErrors.filter(err => 
                !err.includes('favicon') && 
                !err.includes('chrome-extension')
            );
            
            if (nonHydrationErrors.length > 0) {
                console.log(`\n   ⚠️  ${nonHydrationErrors.length} other console error(s):`);
                nonHydrationErrors.slice(0, 3).forEach((err, i) => {
                    console.log(`      ${i + 1}. ${err.substring(0, 80)}...`);
                });
            }
        }

        // Take screenshot for debugging
        const screenshotPath = '/tmp/dashboard-playwright.png';
        await page.screenshot({ path: screenshotPath, fullPage: true });
        console.log(`\n📸 Screenshot saved: ${screenshotPath}`);

    } catch (error) {
        errors.push(`Fatal error: ${error.message}`);
        allPassed = false;
        console.log(`\n❌ FATAL ERROR: ${error.message}`);
    } finally {
        if (browser) {
            await browser.close();
        }
    }

    // Final verdict
    console.log();
    console.log('='.repeat(70));
    
    if (allPassed) {
        console.log('✅ ALL TESTS PASSED - Dashboard renders correctly');
        console.log('='.repeat(70));
        console.log();
        console.log('Dashboard Status:');
        console.log('  ✅ Page loads');
        console.log('  ✅ Content visible');
        console.log('  ✅ No white screen');
        console.log('  ✅ No hydration errors');
        console.log('  ✅ UI elements present');
        console.log();
        process.exit(0);
    } else {
        console.log('❌ TESTS FAILED - White screen or rendering issues detected');
        console.log('='.repeat(70));
        console.log();
        console.log('🚨 DEPLOYMENT BLOCKED 🚨');
        console.log();
        console.log('Errors detected:');
        errors.forEach((err, i) => {
            console.log(`  ${i + 1}. ${err}`);
        });
        console.log();
        console.log('Action required:');
        console.log('  - Check screenshot: /tmp/dashboard-playwright.png');
        console.log('  - Review browser console for errors');
        console.log('  - Verify hydration mismatches are fixed');
        console.log('  - Ensure AuthGate is working correctly');
        console.log();
        process.exit(1);
    }
}

// Run test
testDashboardRendering().catch(err => {
    console.error('\n💥 Unhandled error:', err);
    process.exit(1);
});
