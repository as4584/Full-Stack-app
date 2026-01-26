#!/usr/bin/env python3
"""
PHASE 2: Rendering Validation (Headless Browser)
Uses Playwright to verify wallpapers render and animate on pages.
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json
import base64
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

@dataclass
class RenderCheck:
    page_url: str
    wallpaper_found: bool = False
    background_applied: bool = False
    animation_detected: bool = False
    error_message: str = ""
    screenshot_path: str = ""
    css_selector: str = ""
    wallpaper_url: str = ""

class WallpaperRenderingValidator:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.target_pages = [
            "https://lexmakesit.com"
        ]
        self.screenshots_dir = self.project_root / "tests/ci-wallpaper/snapshots"
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        
    def log_step(self, message: str):
        print(f"🔄 {message}")
        
    def log_success(self, message: str):
        print(f"✅ {message}")
        
    def log_error(self, message: str):
        print(f"❌ {message}")
        
    def log_warning(self, message: str):
        print(f"⚠️  {message}")

    async def check_page_rendering(self, page: Page, page_url: str) -> RenderCheck:
        """Check wallpaper rendering on a single page."""
        self.log_step(f"Checking wallpaper rendering on {page_url}...")
        
        check = RenderCheck(page_url=page_url)
        
        try:
            # Navigate to page
            await page.goto(page_url, wait_until="networkidle", timeout=30000)
            
            # Wait for page to load
            await page.wait_for_timeout(2000)
            
            # Look for wallpaper elements using various selectors
            wallpaper_selectors = [
                "[style*='waterfall']",
                "[style*='background-image']",
                "body.homepage",
                "body",
                ".wallpaper",
                "[class*='wallpaper']",
                "[id*='wallpaper']"
            ]
            
            wallpaper_element = None
            
            for selector in wallpaper_selectors:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    # Check if element has background-image style
                    bg_image = await page.evaluate(
                        "element => getComputedStyle(element).backgroundImage",
                        element
                    )
                    
                    if bg_image and ("waterfall" in bg_image or "wallpaper" in bg_image):
                        wallpaper_element = element
                        check.css_selector = selector
                        check.wallpaper_found = True
                        check.background_applied = True
                        
                        # Extract wallpaper URL
                        import re
                        url_match = re.search(r'url\(["\']?([^)]*)["\']?\)', bg_image)
                        if url_match:
                            check.wallpaper_url = url_match.group(1)
                        
                        break
                
                if wallpaper_element:
                    break
            
            if not check.wallpaper_found:
                # Try to find waterfall/wallpaper references in page source
                content = await page.content()
                if "waterfall" in content or "wallpaper" in content:
                    check.error_message = "Waterfall/wallpaper referenced in source but not applied to any visible element"
                else:
                    check.error_message = "No waterfall/wallpaper references found in page"
                return check
            
            self.log_success(f"Found wallpaper element: {check.css_selector}")
            
            # Check if wallpaper is actually visible
            is_visible = await wallpaper_element.is_visible()
            if not is_visible:
                check.error_message = "Wallpaper element exists but is not visible"
                return check
            
            # Test animation by taking screenshots at different times
            await self.detect_animation(page, wallpaper_element, check)
            
            # Take screenshot for visual verification
            screenshot_filename = f"wallpaper_{page_url.replace('/', '_').replace(':', '_')}.png"
            screenshot_path = self.screenshots_dir / screenshot_filename
            await page.screenshot(path=str(screenshot_path), full_page=True)
            check.screenshot_path = str(screenshot_path)
            
            self.log_success(f"Screenshot saved: {screenshot_path}")
            
        except Exception as e:
            check.error_message = f"Browser error: {str(e)}"
            
        return check

    async def detect_animation(self, page: Page, element, check: RenderCheck):
        """Detect if wallpaper GIF is animating."""
        self.log_step("Detecting animation...")
        
        try:
            # Method 1: Check if element has animated GIF
            bg_image_url = await page.evaluate("""
                element => {
                    const style = getComputedStyle(element);
                    const bgImage = style.backgroundImage;
                    const match = bgImage.match(/url\(["\']?([^)"\']*)["\'']?\)/);
                    return match ? match[1] : null;
                }
            """, element)
            
            if bg_image_url and bg_image_url.endswith('.gif'):
                # GIF file detected - assume it's animated
                # (More sophisticated checks could inspect GIF frames)
                check.animation_detected = True
                self.log_success("GIF wallpaper detected - assuming animated")
                return
            
            # Method 2: Pixel difference detection over time
            # Take screenshot of wallpaper element at two different times
            bbox = await element.bounding_box()
            if not bbox:
                self.log_warning("Could not get wallpaper element bounds for animation detection")
                return
            
            # First screenshot
            screenshot1 = await page.screenshot(
                clip={
                    "x": bbox["x"],
                    "y": bbox["y"], 
                    "width": min(bbox["width"], 200),
                    "height": min(bbox["height"], 200)
                }
            )
            
            # Wait and take second screenshot
            await page.wait_for_timeout(1000)
            
            screenshot2 = await page.screenshot(
                clip={
                    "x": bbox["x"],
                    "y": bbox["y"],
                    "width": min(bbox["width"], 200), 
                    "height": min(bbox["height"], 200)
                }
            )
            
            # Compare screenshots
            if screenshot1 != screenshot2:
                check.animation_detected = True
                self.log_success("Animation detected via pixel difference")
            else:
                self.log_warning("No animation detected - wallpaper may be static")
                
        except Exception as e:
            self.log_warning(f"Could not detect animation: {e}")

    async def run_rendering_validation(self) -> bool:
        """Run rendering validation on all target pages."""
        print("🎭 Starting Phase 2: Rendering Validation\n")
        
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            
            results = []
            
            try:
                for page_url in self.target_pages:
                    page = await context.new_page()
                    try:
                        result = await self.check_page_rendering(page, page_url)
                        results.append(result)
                    finally:
                        await page.close()
                        
            finally:
                await browser.close()
        
        # Analyze results
        successful_checks = [r for r in results if r.wallpaper_found and r.background_applied]
        failed_checks = [r for r in results if not (r.wallpaper_found and r.background_applied)]
        animated_checks = [r for r in results if r.animation_detected]
        
        print(f"\n📊 Phase 2 Summary:")
        print(f"🖼️  Wallpapers found: {len([r for r in results if r.wallpaper_found])}/{len(results)}")
        print(f"🎨 Backgrounds applied: {len([r for r in results if r.background_applied])}/{len(results)}")
        print(f"🎬 Animations detected: {len(animated_checks)}/{len(results)}")
        
        if successful_checks:
            print(f"\n✅ Successful renders:")
            for result in successful_checks:
                anim_status = "🎬 Animated" if result.animation_detected else "🖼️  Static"
                print(f"  • {result.page_url}: {anim_status}")
                if result.wallpaper_url:
                    print(f"    URL: {result.wallpaper_url}")
                if result.screenshot_path:
                    print(f"    Screenshot: {result.screenshot_path}")
        
        if failed_checks:
            print(f"\n❌ Failed renders:")
            for result in failed_checks:
                print(f"  • {result.page_url}: {result.error_message}")
        
        # Success if all pages have working wallpapers
        all_success = len(failed_checks) == 0
        
        if all_success:
            self.log_success("All wallpapers rendering correctly!")
        else:
            self.log_error("Some wallpapers failed to render properly")
        
        return all_success

def main():
    if len(sys.argv) != 2:
        print("Usage: python phase2_rendering_validation.py <project_root>")
        sys.exit(1)
    
    project_root = sys.argv[1]
    validator = WallpaperRenderingValidator(project_root)
    
    success = asyncio.run(validator.run_rendering_validation())
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()