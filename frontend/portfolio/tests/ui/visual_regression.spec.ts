import { test, expect } from '@playwright/test';

test.describe('Frutiger Aero UI Tests', () => {

    test('Homepage loads with correct title', async ({ page }) => {
        await page.goto('/');
        await expect(page).toHaveTitle(/Lex Santiago/);
    });

    test('Hero section has waterfall background', async ({ page }) => {
        await page.goto('/');
        const hero = page.locator('.hero');
        await expect(hero).toBeVisible();
        // Check if body has the background (since it's fixed on body)
        const body = page.locator('body');
        await expect(body).toHaveCSS('background-image', /waterfall\.png/);
    });

    test('Visual Regression - Homepage Desktop', async ({ page }) => {
        await page.goto('/');
        await expect(page).toHaveScreenshot('homepage-desktop.png', { fullPage: true });
    });

    test('Mobile Layout Check', async ({ page, isMobile }) => {
        await page.goto('/');
        if (isMobile) {
            const nav = page.locator('.navbar');
            await expect(nav).toBeVisible();
            // Ensure no horizontal scroll
            const scrollWidth = await page.evaluate(() => document.body.scrollWidth);
            const viewportWidth = await page.evaluate(() => window.innerWidth);
            expect(scrollWidth).toBeLessThanOrEqual(viewportWidth);
        }
    });

    test('Contrast Check (Heuristic)', async ({ page }) => {
        await page.goto('/');
        const headings = page.locator('h1, h2, h3');
        const count = await headings.count();
        for (let i = 0; i < count; ++i) {
            const color = await headings.nth(i).evaluate(el => getComputedStyle(el).color);
            // Simple check to ensure text isn't transparent or matching background too closely
            // Real contrast check requires more complex logic, this is a placeholder for the agent
            expect(color).not.toBe('rgba(0, 0, 0, 0)');
        }
    });

});
