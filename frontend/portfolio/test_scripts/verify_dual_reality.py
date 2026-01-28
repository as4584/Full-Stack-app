import asyncio
from playwright.async_api import async_playwright
import time
import sys

URL = "http://localhost:8001"

async def test_reality():
    async with async_playwright() as p:
        print("LAUNCHING BROWSER...")
        browser = await p.chromium.launch(headless=True)
        
        # --- TEST 1: DESKTOP REALITY ---
        print("\n--- TEST 1: DESKTOP REALITY (1920x1080) ---")
        page_desktop = await browser.new_page(viewport={"width": 1920, "height": 1080})
        
        try:
            await page_desktop.goto(URL, timeout=10000)
            await page_desktop.wait_for_load_state("networkidle")
        except Exception as e:
            print(f"FAILED to load {URL}: {e}")
            await browser.close()
            return

        # Check Body Class
        body_class = await page_desktop.eval_on_selector("body", "el => el.className")
        print(f"Body Class: {body_class}")
        
        if "desktop-reality" in body_class:
            print("✅ PASS: 'desktop-reality' class present.")
        else:
            print("❌ FAIL: 'desktop-reality' class missing!")

        # Check Canvas/Bubbles existence (via logic presence)
        # In current impl, bubbles are div elements in #bubble-container
        bubble_container = await page_desktop.query_selector("#bubble-container")
        if bubble_container:
            display = await bubble_container.evaluate("el => getComputedStyle(el).display")
            print(f"Bubble Container Display: {display}")
            if display != "none":
                print("✅ PASS: Bubble container visible.")
            else:
                print("❌ FAIL: Bubble container hidden on desktop!")
        else:
            print("❌ FAIL: Bubble container not found in DOM!")

        
        # --- TEST 2: MOBILE REALITY ---
        print("\n--- TEST 2: MOBILE REALITY (375x812) ---")
        page_mobile = await browser.new_page(viewport={"width": 375, "height": 812})
        await page_mobile.goto(URL)
        await page_mobile.wait_for_load_state("networkidle")
        
        # Check Body Class
        body_class_mobile = await page_mobile.eval_on_selector("body", "el => el.className")
        print(f"Body Class: {body_class_mobile}")
        
        if "mobile-reality" in body_class_mobile:
            print("✅ PASS: 'mobile-reality' class present.")
        else:
            print("❌ FAIL: 'mobile-reality' class missing!")

        # Check Bubble Container hidden
        bubble_container_mob = await page_mobile.query_selector("#bubble-container")
        if bubble_container_mob:
            # It might exist in DOM but be hidden by CSS
            display_mob = await bubble_container_mob.evaluate("el => getComputedStyle(el).display")
            print(f"Bubble Container Display: {display_mob}")
            if display_mob == "none":
                 print("✅ PASS: Bubble container hidden on mobile.")
            else:
                 print("⚠️ WARN: Bubble container might be visible (check CSS priority).")
        else:
             print("✅ PASS: Bubble container not present (good).")

        # Check Waterfall Background
        bg_image = await page_mobile.eval_on_selector("body", "el => getComputedStyle(el).backgroundImage")
        print(f"Background Image: {bg_image}")
        if "waterfall.gif" in bg_image:
             print("✅ PASS: Waterfall GIF active.")
        else:
             print("❌ FAIL: Waterfall GIF missing on mobile!")

        # --- TEST 3: DONXERA LINK ---
        print("\n--- TEST 3: LINK REGRESSION CHECK ---")
        # Reuse desktop page
        donxera_link = await page_desktop.get_attribute("a[href*='don-era.lexmakesit.com']", "href")
        if donxera_link == "http://don-era.lexmakesit.com":
             print("✅ PASS: DonXera link is correct.")
        else:
             print(f"❌ FAIL: DonXera link incorrect: {donxera_link}")


        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_reality())
