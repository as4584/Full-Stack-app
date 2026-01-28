
import { test, expect } from '@playwright/test';

test('Phone Purchase UI Flow', async ({ page }) => {
    // 1. Go to Dashboard
    await page.goto('http://localhost:3000/app');

    // 2. Open Modal
    const configButton = page.getByText(/Configure Phone Number|\+ Add Number/);
    await configButton.click();
    await expect(page.locator('text=Get New Number')).toBeVisible();

    // 3. Search for Magic Number
    await page.getByPlaceholder('Area Code (e.g. 415)').fill('000');
    await page.getByRole('button', { name: 'Search' }).click();

    // 4. Verify & Buy
    const testNumber = page.locator('text=Test Number (+1 000-000-0000)');
    await expect(testNumber).toBeVisible();

    await testNumber.locator('..').getByRole('button', { name: 'Buy' }).click();

    // 5. Verify Success
    await expect(page.locator('text=Phone number purchased successfully')).toBeVisible();
    await expect(page.locator('text=Phone: +10000000000')).toBeVisible();
});
