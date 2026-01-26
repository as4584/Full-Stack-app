#!/usr/bin/env python3
"""
PHASE 1: Asset Availability Check
Verifies wallpaper.gif assets are accessible and valid.
"""

import asyncio
import aiohttp
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import mimetypes

@dataclass
class AssetCheck:
    url: str
    page_context: str
    status_code: int = 0
    content_type: str = ""
    content_length: int = 0
    success: bool = False
    error_message: str = ""

class WallpaperAssetChecker:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.target_urls = [
            {
                "page": "https://lexmakesit.com",
                "wallpapers": [
                    "https://lexmakesit.com/static/images/waterfall.gif",
                    "https://lexmakesit.com/static/images/waterfall.png"
                ]
            }
        ]
        self.min_file_size = 1024  # 1KB minimum
        self.timeout = 10  # seconds
        
    def log_step(self, message: str):
        print(f"🔄 {message}")
        
    def log_success(self, message: str):
        print(f"✅ {message}")
        
    def log_error(self, message: str):
        print(f"❌ {message}")
        
    def log_warning(self, message: str):
        print(f"⚠️  {message}")

    async def check_asset(self, url: str, page_context: str) -> AssetCheck:
        """Check a single wallpaper asset."""
        self.log_step(f"Checking {url}...")
        
        check = AssetCheck(url=url, page_context=page_context)
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url) as response:
                    check.status_code = response.status
                    check.content_type = response.headers.get('content-type', '').lower()
                    check.content_length = int(response.headers.get('content-length', 0))
                    
                    # Check status code
                    if response.status != 200:
                        check.error_message = f"HTTP {response.status}: {response.reason}"
                        return check
                    
                    # Check content type (allow both GIF and PNG)
                    valid_types = ['image/gif', 'image/png']
                    if not any(mime_type in check.content_type for mime_type in valid_types):
                        check.error_message = f"Wrong MIME type: {check.content_type} (expected image/gif or image/png)"
                        return check
                    
                    # Check file size
                    if check.content_length < self.min_file_size:
                        check.error_message = f"File too small: {check.content_length} bytes (minimum {self.min_file_size})"
                        return check
                    
                    # Verify it's actually a GIF or PNG by reading magic bytes
                    content_sample = await response.content.read(8)
                    if check.content_type.startswith('image/gif'):
                        if not (content_sample.startswith(b'GIF87a') or content_sample.startswith(b'GIF89a')):
                            check.error_message = "Invalid GIF file format (missing GIF header)"
                            return check
                    elif check.content_type.startswith('image/png'):
                        if not content_sample.startswith(b'\x89PNG\r\n\x1a\n'):
                            check.error_message = "Invalid PNG file format (missing PNG header)"
                            return check
                    
                    check.success = True
                    self.log_success(f"Asset valid: {url} ({check.content_length} bytes)")
                    return check
                    
        except asyncio.TimeoutError:
            check.error_message = f"Request timeout after {self.timeout} seconds"
        except aiohttp.ClientError as e:
            check.error_message = f"Network error: {str(e)}"
        except Exception as e:
            check.error_message = f"Unexpected error: {str(e)}"
            
        return check

    async def discover_wallpaper_urls(self, page_url: str) -> List[str]:
        """Discover wallpaper URLs by inspecting the page source."""
        self.log_step(f"Discovering wallpaper URLs on {page_url}...")
        
        discovered_urls = []
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(page_url) as response:
                    if response.status != 200:
                        self.log_warning(f"Could not fetch page {page_url}: HTTP {response.status}")
                        return []
                    
                    content = await response.text()
                    
                    # Look for wallpaper.gif references in various formats
                    import re
                    
                    # CSS background-image patterns
                    css_patterns = [
                        r'background-image:\s*url\(["\']?([^)]*waterfall\.(gif|png)[^)]*)["\']?\)',
                        r'background:\s*[^;]*url\(["\']?([^)]*waterfall\.(gif|png)[^)]*)["\']?\)',
                        r'--wallpaper-primary:\s*url\(["\']?([^)]*)["\']?\)',
                        r'--wallpaper-fallback:\s*url\(["\']?([^)]*)["\']?\)',
                    ]
                    
                    # HTML src patterns
                    html_patterns = [
                        r'src=["\']([^"\']*waterfall\.(gif|png)[^"\']*)["\']',
                        r'<img[^>]*src=["\']([^"\']*waterfall\.(gif|png)[^"\']*)["\'][^>]*>',
                    ]
                    
                    all_patterns = css_patterns + html_patterns
                    
                    for pattern in all_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        for match in matches:
                            # Convert relative URLs to absolute
                            if match.startswith('/'):
                                full_url = f"{page_url.rstrip('/')}{match}"
                            elif match.startswith('http'):
                                full_url = match
                            else:
                                full_url = f"{page_url.rstrip('/')}/{match}"
                            
                            if full_url not in discovered_urls:
                                discovered_urls.append(full_url)
                                self.log_step(f"Found wallpaper reference: {full_url}")
                    
        except Exception as e:
            self.log_warning(f"Error discovering URLs from {page_url}: {e}")
        
        return discovered_urls

    async def run_asset_availability_check(self) -> bool:
        """Run all asset availability checks."""
        print("🖼️  Starting Phase 1: Asset Availability Check\n")
        
        all_checks = []
        
        # Check predefined URLs and discover new ones
        for target in self.target_urls:
            page_url = target["page"]
            predefined_wallpapers = target["wallpapers"]
            
            # Discover additional wallpaper URLs from the page
            discovered_wallpapers = await self.discover_wallpaper_urls(page_url)
            
            # Combine predefined and discovered URLs
            all_wallpapers = list(set(predefined_wallpapers + discovered_wallpapers))
            
            if not all_wallpapers:
                self.log_warning(f"No wallpaper URLs found for {page_url}")
                continue
            
            # Check each wallpaper URL
            for wallpaper_url in all_wallpapers:
                check = await self.check_asset(wallpaper_url, page_url)
                all_checks.append(check)
        
        # Analyze results
        successful_checks = [c for c in all_checks if c.success]
        failed_checks = [c for c in all_checks if not c.success]
        
        print(f"\n📊 Phase 1 Summary:")
        print(f"✅ Successful: {len(successful_checks)}/{len(all_checks)}")
        print(f"❌ Failed: {len(failed_checks)}/{len(all_checks)}")
        
        if successful_checks:
            print(f"\n🎉 Working wallpaper assets:")
            for check in successful_checks:
                print(f"  • {check.url} ({check.content_length} bytes)")
        
        if failed_checks:
            print(f"\n🚨 Failed wallpaper assets:")
            for check in failed_checks:
                print(f"  • {check.url}: {check.error_message}")
        
        # Success if at least one wallpaper works for each page
        page_coverage = {}
        for check in successful_checks:
            if check.page_context not in page_coverage:
                page_coverage[check.page_context] = []
            page_coverage[check.page_context].append(check.url)
        
        all_pages_covered = True
        for target in self.target_urls:
            page_url = target["page"]
            if page_url not in page_coverage:
                self.log_error(f"No working wallpaper found for {page_url}")
                all_pages_covered = False
            else:
                self.log_success(f"Page {page_url} has {len(page_coverage[page_url])} working wallpaper(s)")
        
        return all_pages_covered and len(successful_checks) > 0

def main():
    if len(sys.argv) != 2:
        print("Usage: python phase1_asset_availability.py <project_root>")
        sys.exit(1)
    
    project_root = sys.argv[1]
    checker = WallpaperAssetChecker(project_root)
    
    success = asyncio.run(checker.run_asset_availability_check())
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()