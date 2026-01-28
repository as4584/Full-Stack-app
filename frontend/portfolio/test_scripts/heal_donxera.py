import asyncio
from playwright.async_api import async_playwright
import os
import time

MAIN_PY_PATH = r"c:\Users\AlexS\Downloads\antigravity_bundle\testing\portfolio\main.py"
search_url = "http://localhost:8010"
replace_url = "http://don-era.lexmakesit.com"

async def heal_file():
    print(f"Healing main.py by replacing {search_url} with {replace_url}")
    with open(MAIN_PY_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    
    new_content = content.replace(search_url, replace_url)
    
    with open(MAIN_PY_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("File updated.")

async def run():
    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("Navigating to portfolio (http://localhost:8001)...")
        try:
            # Retry connection a few times in case server is just starting
            max_retries = 5
            for i in range(max_retries):
                try:
                    await page.goto("http://localhost:8001", timeout=5000)
                    break
                except Exception as e:
                    print(f"Attempt {i+1} failed: {e}")
                    if i == max_retries - 1:
                        raise
                    await asyncio.sleep(2)
        except Exception as e:
            print(f"Error connecting to server: {e}")
            await browser.close()
            return

        # Find Donxera
        print("Looking for 'DonXera Website Demo'...")
        donxera_card = page.locator(".glass-card", has_text="DonXera Website Demo")
        if await donxera_card.count() == 0:
            print("DonXera card not found!")
            content = await page.content()
            print("Page content snippet:", content[:500])
            await browser.close()
            return

        print("Found DonXera card.")
        
        # Get the link
        link = donxera_card.locator("a.aero-btn")
        href = await link.get_attribute("href")
        print(f"Current href: {href}")

        if href == search_url:
            print("Link is pointing to localhost:8010 (Broken/Deprecated). Initiating self-healing...")
            await heal_file()
            print("Waiting for server reload (5s)...")
            await asyncio.sleep(5) 
            print("Reloading page...")
            await page.reload()
            await page.wait_for_load_state("networkidle")
            
            # Re-locate
            donxera_card = page.locator(".glass-card", has_text="DonXera Website Demo")
            link = donxera_card.locator("a.aero-btn")
            href = await link.get_attribute("href")
            print(f"New href: {href}")
            
        if href == replace_url:
             print("Link is correct. Clicking...")
             await link.click()
             
             # Wait for navigation
             await page.wait_for_load_state("domcontentloaded")
             title = await page.title()
             print(f"Navigated to: {page.url}")
             print(f"Page Title: {title}")
             
             if "DonXEra" in title or "don-era" in page.url:
                 print("SUCCESS: DonXera demo is working!")
             else:
                 print(f"WARNING: Title ('{title}') didn't match expected 'DonXEra'")
        else:
             print(f"Link is pointing to unexpected URL: {href}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
