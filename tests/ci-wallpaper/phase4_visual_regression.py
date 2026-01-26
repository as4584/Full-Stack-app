#!/usr/bin/env python3
"""
PHASE 4: Visual Regression Protection
Captures screenshots and detects wallpaper changes.
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import json
import hashlib
from datetime import datetime, timezone
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from PIL import Image, ImageChops
import io

@dataclass
class VisualSnapshot:
    timestamp: str
    page_url: str
    screenshot_path: str
    wallpaper_hash: str
    animation_frame_hashes: List[str]
    wallpaper_bounds: Dict[str, float]
    checksum: str
    error_message: str = ""

class WallpaperVisualRegression:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.snapshots_dir = self.project_root / "tests/ci-wallpaper/snapshots"
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        self.baseline_file = self.snapshots_dir / "visual_baseline.json"
        
        self.target_pages = [
            "https://lexmakesit.com"
        ]
        
    def log_step(self, message: str):
        print(f"🔄 {message}")
        
    def log_success(self, message: str):
        print(f"✅ {message}")
        
    def log_error(self, message: str):
        print(f"❌ {message}")
        
    def log_warning(self, message: str):
        print(f"⚠️  {message}")

    def calculate_image_hash(self, image_data: bytes) -> str:
        """Calculate perceptual hash of image data."""
        try:
            # Simple content hash for now
            return hashlib.sha256(image_data).hexdigest()[:16]
        except Exception as e:
            self.log_warning(f"Could not hash image: {e}")
            return "error"

    async def capture_wallpaper_region(self, page: Page, page_url: str) -> VisualSnapshot:
        """Capture wallpaper region and create visual snapshot."""
        self.log_step(f"Capturing wallpaper visual for {page_url}...")
        
        snapshot = VisualSnapshot(
            timestamp=datetime.now(timezone.utc).isoformat(),
            page_url=page_url,
            screenshot_path="",
            wallpaper_hash="",
            animation_frame_hashes=[],
            wallpaper_bounds={},
            checksum=""
        )
        
        try:
            # Navigate to page
            await page.goto(page_url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)  # Wait for animations to start
            
            # Find wallpaper element
            wallpaper_element = None
            wallpaper_selectors = [
                "[style*='waterfall']",
                "[style*='background-image']",
                "body.homepage",
                "body",
                ".wallpaper",
                "[class*='wallpaper']"
            ]
            
            for selector in wallpaper_selectors:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    bg_image = await page.evaluate(
                        "element => getComputedStyle(element).backgroundImage",
                        element
                    )
                    if bg_image and ("waterfall" in bg_image or "wallpaper" in bg_image):
                        wallpaper_element = element
                        break
                if wallpaper_element:
                    break
            
            if not wallpaper_element:
                snapshot.error_message = "No wallpaper element found"
                return snapshot
            
            # Get element bounds
            bounds = await wallpaper_element.bounding_box()
            if not bounds:
                snapshot.error_message = "Could not get wallpaper element bounds"
                return snapshot
            
            snapshot.wallpaper_bounds = {
                "x": bounds["x"],
                "y": bounds["y"],
                "width": bounds["width"],
                "height": bounds["height"]
            }
            
            # Take full page screenshot first
            page_clean = page_url.replace('/', '_').replace(':', '_').replace('?', '_')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_filename = f"wallpaper_visual_{page_clean}_{timestamp}.png"
            screenshot_path = self.snapshots_dir / screenshot_filename
            
            await page.screenshot(path=str(screenshot_path), full_page=True)
            snapshot.screenshot_path = str(screenshot_path)
            
            # Capture wallpaper region specifically
            wallpaper_region_data = await page.screenshot(
                clip={
                    "x": bounds["x"],
                    "y": bounds["y"],
                    "width": min(bounds["width"], 800),  # Limit size for performance
                    "height": min(bounds["height"], 600)
                }
            )
            
            snapshot.wallpaper_hash = self.calculate_image_hash(wallpaper_region_data)
            
            # Capture multiple animation frames
            frame_hashes = []
            for i in range(3):  # Capture 3 frames
                await page.wait_for_timeout(500)  # Wait between frames
                frame_data = await page.screenshot(
                    clip={
                        "x": bounds["x"],
                        "y": bounds["y"],
                        "width": min(bounds["width"], 800),
                        "height": min(bounds["height"], 600)
                    }
                )
                frame_hash = self.calculate_image_hash(frame_data)
                frame_hashes.append(frame_hash)
            
            snapshot.animation_frame_hashes = frame_hashes
            
            # Calculate overall checksum
            snapshot_data = {
                "wallpaper_hash": snapshot.wallpaper_hash,
                "bounds": snapshot.wallpaper_bounds,
                "frame_hashes": snapshot.animation_frame_hashes
            }
            snapshot.checksum = hashlib.sha256(
                json.dumps(snapshot_data, sort_keys=True).encode()
            ).hexdigest()[:16]
            
            self.log_success(f"Visual snapshot captured: {screenshot_filename}")
            
        except Exception as e:
            snapshot.error_message = f"Capture error: {str(e)}"
            
        return snapshot

    async def capture_current_visuals(self) -> List[VisualSnapshot]:
        """Capture current visual state of all target pages."""
        self.log_step("Capturing current wallpaper visuals...")
        
        snapshots = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            
            try:
                for page_url in self.target_pages:
                    page = await context.new_page()
                    try:
                        snapshot = await self.capture_wallpaper_region(page, page_url)
                        snapshots.append(snapshot)
                    except Exception as e:
                        error_snapshot = VisualSnapshot(
                            timestamp=datetime.now(timezone.utc).isoformat(),
                            page_url=page_url,
                            screenshot_path="",
                            wallpaper_hash="",
                            animation_frame_hashes=[],
                            wallpaper_bounds={},
                            checksum="",
                            error_message=f"Page capture failed: {str(e)}"
                        )
                        snapshots.append(error_snapshot)
                    finally:
                        await page.close()
                        
            finally:
                await browser.close()
        
        return snapshots

    def save_baseline(self, snapshots: List[VisualSnapshot]):
        """Save visual snapshots as baseline."""
        self.log_step("Saving visual baseline...")
        
        baseline_data = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "snapshots": [asdict(snapshot) for snapshot in snapshots]
        }
        
        with open(self.baseline_file, 'w') as f:
            json.dump(baseline_data, f, indent=2)
        
        self.log_success(f"Visual baseline saved with {len(snapshots)} snapshots")

    def load_baseline(self) -> Optional[List[VisualSnapshot]]:
        """Load baseline visual snapshots."""
        if not self.baseline_file.exists():
            return None
        
        try:
            with open(self.baseline_file, 'r') as f:
                data = json.load(f)
            
            snapshots = []
            for snapshot_data in data.get("snapshots", []):
                snapshots.append(VisualSnapshot(**snapshot_data))
            
            return snapshots
            
        except Exception as e:
            self.log_error(f"Failed to load baseline: {e}")
            return None

    def compare_visuals(self, current: List[VisualSnapshot], baseline: List[VisualSnapshot]) -> Dict[str, Any]:
        """Compare current visuals with baseline."""
        self.log_step("Comparing visuals with baseline...")
        
        # Index by page URL
        current_by_url = {s.page_url: s for s in current}
        baseline_by_url = {s.page_url: s for s in baseline}
        
        comparison = {
            "identical": [],
            "changed": [],
            "new_pages": [],
            "missing_pages": [],
            "errors": []
        }
        
        # Compare each page
        for page_url, current_snapshot in current_by_url.items():
            if current_snapshot.error_message:
                comparison["errors"].append({
                    "page": page_url,
                    "error": current_snapshot.error_message
                })
                continue
                
            if page_url not in baseline_by_url:
                comparison["new_pages"].append(page_url)
                continue
            
            baseline_snapshot = baseline_by_url[page_url]
            
            # Compare checksums for exact match
            if current_snapshot.checksum == baseline_snapshot.checksum:
                comparison["identical"].append(page_url)
            else:
                # Detailed comparison
                changes = []
                
                if current_snapshot.wallpaper_hash != baseline_snapshot.wallpaper_hash:
                    changes.append("Wallpaper content changed")
                
                if current_snapshot.wallpaper_bounds != baseline_snapshot.wallpaper_bounds:
                    changes.append("Wallpaper position/size changed")
                
                # Check animation frames
                current_frames = set(current_snapshot.animation_frame_hashes)
                baseline_frames = set(baseline_snapshot.animation_frame_hashes)
                
                if current_frames != baseline_frames:
                    if len(current_frames.intersection(baseline_frames)) == 0:
                        changes.append("Animation completely different")
                    else:
                        changes.append("Animation frames changed")
                
                comparison["changed"].append({
                    "page": page_url,
                    "changes": changes,
                    "current": asdict(current_snapshot),
                    "baseline": asdict(baseline_snapshot)
                })
        
        # Check for missing pages
        for page_url in baseline_by_url.keys():
            if page_url not in current_by_url:
                comparison["missing_pages"].append(page_url)
        
        return comparison

    def save_comparison_report(self, comparison: Dict[str, Any]):
        """Save comparison report."""
        report_file = self.snapshots_dir / f"visual_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w') as f:
            json.dump(comparison, f, indent=2)
        
        self.log_step(f"Comparison report saved: {report_file}")

    async def run_visual_regression_check(self, create_baseline: bool = False) -> bool:
        """Run visual regression check."""
        print("📸 Starting Phase 4: Visual Regression Protection\n")
        
        # Capture current state
        current_snapshots = await self.capture_current_visuals()
        
        successful_captures = [s for s in current_snapshots if not s.error_message]
        failed_captures = [s for s in current_snapshots if s.error_message]
        
        print(f"📊 Capture Results:")
        print(f"✅ Successful: {len(successful_captures)}/{len(current_snapshots)}")
        print(f"❌ Failed: {len(failed_captures)}/{len(current_snapshots)}")
        
        if failed_captures:
            print(f"\n❌ Capture failures:")
            for snapshot in failed_captures:
                print(f"  • {snapshot.page_url}: {snapshot.error_message}")
        
        # If creating baseline, save and exit
        if create_baseline:
            if successful_captures:
                self.save_baseline(successful_captures)
                self.log_success("Visual baseline created successfully")
                return True
            else:
                self.log_error("Cannot create baseline - no successful captures")
                return False
        
        # Load baseline for comparison
        baseline_snapshots = self.load_baseline()
        
        if not baseline_snapshots:
            self.log_warning("No baseline found. Creating initial baseline...")
            self.save_baseline(successful_captures)
            return True
        
        # Compare with baseline
        comparison = self.compare_visuals(successful_captures, baseline_snapshots)
        
        # Save comparison report
        self.save_comparison_report(comparison)
        
        # Report results
        print(f"\n📊 Visual Comparison Results:")
        print(f"✅ Identical: {len(comparison['identical'])}")
        print(f"🔄 Changed: {len(comparison['changed'])}")
        print(f"🆕 New pages: {len(comparison['new_pages'])}")
        print(f"❓ Missing pages: {len(comparison['missing_pages'])}")
        print(f"❌ Errors: {len(comparison['errors'])}")
        
        if comparison["identical"]:
            print(f"\n✅ Pages with identical wallpapers:")
            for page in comparison["identical"]:
                print(f"  • {page}")
        
        if comparison["changed"]:
            print(f"\n🚨 Pages with wallpaper changes:")
            for change in comparison["changed"]:
                print(f"  • {change['page']}: {', '.join(change['changes'])}")
        
        if comparison["new_pages"]:
            print(f"\n🆕 New pages detected:")
            for page in comparison["new_pages"]:
                print(f"  • {page}")
        
        if comparison["missing_pages"]:
            print(f"\n❓ Missing pages (were in baseline):")
            for page in comparison["missing_pages"]:
                print(f"  • {page}")
        
        # Determine success
        has_regressions = (
            len(comparison["changed"]) > 0 or 
            len(comparison["missing_pages"]) > 0 or
            len(comparison["errors"]) > 0
        )
        
        if not has_regressions:
            self.log_success("No visual regressions detected!")
        else:
            self.log_error("Visual regressions detected - wallpaper display has changed")
        
        return not has_regressions

def main():
    if len(sys.argv) < 2:
        print("Usage: python phase4_visual_regression.py <project_root> [--create-baseline]")
        sys.exit(1)
    
    project_root = sys.argv[1]
    create_baseline = "--create-baseline" in sys.argv
    
    checker = WallpaperVisualRegression(project_root)
    success = asyncio.run(checker.run_visual_regression_check(create_baseline))
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()