#!/usr/bin/env python3
"""
PHASE 3: Cache & CDN Safety Check
Verifies cache headers and CDN behavior for wallpaper assets.
"""

import asyncio
import aiohttp
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import time

@dataclass
class CacheCheck:
    url: str
    status_code: int = 0
    cache_control: str = ""
    etag: str = ""
    last_modified: str = ""
    expires: str = ""
    content_hash: str = ""
    response_time: float = 0.0
    cdn_headers: Dict[str, str] = None
    cache_safe: bool = False
    error_message: str = ""

class WallpaperCacheSafetyChecker:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.wallpaper_urls = [
            "https://lexmakesit.com/static/images/waterfall.gif",
            "https://lexmakesit.com/static/images/waterfall.png"
        ]
        self.timeout = 15
        
    def log_step(self, message: str):
        print(f"🔄 {message}")
        
    def log_success(self, message: str):
        print(f"✅ {message}")
        
    def log_error(self, message: str):
        print(f"❌ {message}")
        
    def log_warning(self, message: str):
        print(f"⚠️  {message}")

    async def check_cache_headers(self, url: str) -> CacheCheck:
        """Check cache-related headers for a wallpaper asset."""
        self.log_step(f"Checking cache headers for {url}...")
        
        check = CacheCheck(url=url, cdn_headers={})
        
        try:
            start_time = time.time()
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url) as response:
                    check.response_time = time.time() - start_time
                    check.status_code = response.status
                    
                    if response.status != 200:
                        check.error_message = f"Asset unavailable: HTTP {response.status}"
                        return check
                    
                    # Extract cache-related headers
                    headers = response.headers
                    check.cache_control = headers.get('cache-control', '')
                    check.etag = headers.get('etag', '')
                    check.last_modified = headers.get('last-modified', '')
                    check.expires = headers.get('expires', '')
                    
                    # Check for CDN headers (common CDN providers)
                    cdn_header_patterns = [
                        'cf-',      # Cloudflare
                        'x-amz-',   # Amazon CloudFront
                        'x-azure-', # Azure CDN
                        'x-cache',  # Generic cache header
                        'x-served-by', # Fastly
                        'server',   # Server info
                        'via'       # Proxy/CDN via header
                    ]
                    
                    for header_name, header_value in headers.items():
                        for pattern in cdn_header_patterns:
                            if header_name.lower().startswith(pattern):
                                check.cdn_headers[header_name] = header_value
                    
                    # Calculate content hash for consistency checking
                    content = await response.read()
                    check.content_hash = hashlib.sha256(content).hexdigest()[:16]
                    
                    # Validate cache configuration
                    check.cache_safe = self.validate_cache_config(check)
                    
        except asyncio.TimeoutError:
            check.error_message = f"Request timeout after {self.timeout} seconds"
        except aiohttp.ClientError as e:
            check.error_message = f"Network error: {str(e)}"
        except Exception as e:
            check.error_message = f"Unexpected error: {str(e)}"
            
        return check

    def validate_cache_config(self, check: CacheCheck) -> bool:
        """Validate that cache configuration is safe for wallpaper assets."""
        issues = []
        
        # Check Cache-Control header
        if not check.cache_control:
            issues.append("Missing Cache-Control header")
        else:
            cache_control_lower = check.cache_control.lower()
            
            # Check for reasonable max-age
            import re
            max_age_match = re.search(r'max-age=(\d+)', cache_control_lower)
            if max_age_match:
                max_age = int(max_age_match.group(1))
                if max_age < 300:  # Less than 5 minutes
                    issues.append(f"Cache max-age too short: {max_age} seconds")
                elif max_age > 31536000:  # More than 1 year
                    issues.append(f"Cache max-age very long: {max_age} seconds")
            else:
                if 'no-cache' in cache_control_lower or 'no-store' in cache_control_lower:
                    issues.append("Asset set to no-cache/no-store - may cause performance issues")
        
        # Check for ETags or Last-Modified for cache validation
        if not check.etag and not check.last_modified:
            issues.append("Missing ETag and Last-Modified headers for cache validation")
        
        # Log issues
        for issue in issues:
            self.log_warning(f"{check.url}: {issue}")
        
        return len(issues) == 0

    async def test_cache_consistency(self, url: str) -> Tuple[bool, str]:
        """Test that cached responses are consistent."""
        self.log_step(f"Testing cache consistency for {url}...")
        
        try:
            # Make multiple requests to test consistency
            hashes = []
            response_times = []
            
            for i in range(3):
                async with aiohttp.ClientSession() as session:
                    start_time = time.time()
                    async with session.get(url) as response:
                        response_time = time.time() - start_time
                        response_times.append(response_time)
                        
                        if response.status == 200:
                            content = await response.read()
                            content_hash = hashlib.sha256(content).hexdigest()
                            hashes.append(content_hash)
                        else:
                            return False, f"HTTP {response.status} on request {i+1}"
                
                # Small delay between requests
                if i < 2:
                    await asyncio.sleep(0.5)
            
            # Check consistency
            if len(set(hashes)) != 1:
                return False, "Content hash mismatch between requests - unstable caching"
            
            # Check if caching is working (second request should be faster)
            if len(response_times) >= 2 and response_times[1] > response_times[0] * 2:
                self.log_warning(f"Second request not significantly faster - caching may not be working")
            
            return True, "Cache consistency verified"
            
        except Exception as e:
            return False, f"Cache consistency test error: {str(e)}"

    async def check_stale_references(self) -> List[str]:
        """Check for stale or broken wallpaper references."""
        self.log_step("Checking for stale references...")
        
        stale_issues = []
        
        # This would ideally integrate with deployment information
        # For now, we'll do basic checks
        
        try:
            # Check if old wallpaper URLs return 404 (good - means cleanup happened)
            old_patterns = [
                "https://lexmakesit.com/old-wallpaper.gif",
                "https://lexmakesit.com/wallpaper-v1.gif", 
                "https://lexmakesit.com/backup-wallpaper.gif"
            ]
            
            for old_url in old_patterns:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(old_url) as response:
                            if response.status == 200:
                                stale_issues.append(f"Old wallpaper still accessible: {old_url}")
                except:
                    pass  # 404 is expected and good
                    
        except Exception as e:
            self.log_warning(f"Error checking stale references: {e}")
        
        return stale_issues

    async def run_cache_safety_check(self) -> bool:
        """Run all cache safety checks."""
        print("🗄️  Starting Phase 3: Cache & CDN Safety Check\n")
        
        # Check cache headers for all wallpaper URLs
        cache_checks = []
        for url in self.wallpaper_urls:
            try:
                check = await self.check_cache_headers(url)
                cache_checks.append(check)
            except Exception as e:
                self.log_error(f"Failed to check {url}: {e}")
        
        # Test cache consistency for accessible URLs
        consistency_results = []
        accessible_urls = [c.url for c in cache_checks if c.status_code == 200]
        
        for url in accessible_urls[:2]:  # Limit to first 2 to avoid overloading
            success, message = await self.test_cache_consistency(url)
            consistency_results.append((url, success, message))
        
        # Check for stale references
        stale_issues = await self.check_stale_references()
        
        # Analyze results
        successful_cache_checks = [c for c in cache_checks if c.status_code == 200 and c.cache_safe]
        accessible_checks = [c for c in cache_checks if c.status_code == 200]
        failed_checks = [c for c in cache_checks if c.status_code != 200]
        unsafe_cache_checks = [c for c in accessible_checks if not c.cache_safe]
        
        print(f"\n📊 Phase 3 Summary:")
        print(f"🌐 Accessible URLs: {len(accessible_checks)}/{len(self.wallpaper_urls)}")
        print(f"✅ Safe cache config: {len(successful_cache_checks)}/{len(accessible_checks)}")
        print(f"🔄 Consistency tests: {len([r for r in consistency_results if r[1]])}/{len(consistency_results)}")
        
        if successful_cache_checks:
            print(f"\n✅ URLs with safe caching:")
            for check in successful_cache_checks:
                print(f"  • {check.url}")
                if check.cache_control:
                    print(f"    Cache-Control: {check.cache_control}")
                if check.cdn_headers:
                    cdn_info = ", ".join([f"{k}: {v}" for k, v in list(check.cdn_headers.items())[:2]])
                    print(f"    CDN: {cdn_info}")
        
        if unsafe_cache_checks:
            print(f"\n⚠️  URLs with cache issues:")
            for check in unsafe_cache_checks:
                print(f"  • {check.url}: Cache configuration needs attention")
        
        if failed_checks:
            print(f"\n❌ Inaccessible URLs:")
            for check in failed_checks:
                print(f"  • {check.url}: {check.error_message}")
        
        if consistency_results:
            print(f"\n🔄 Cache consistency results:")
            for url, success, message in consistency_results:
                status = "✅" if success else "❌"
                print(f"  {status} {url}: {message}")
        
        if stale_issues:
            print(f"\n🗑️  Stale reference issues:")
            for issue in stale_issues:
                print(f"  • {issue}")
        
        # Overall success criteria
        success = (
            len(accessible_checks) > 0 and  # At least one URL accessible
            len(failed_checks) == 0 and     # No completely broken URLs
            len([r for r in consistency_results if not r[1]]) == 0  # No consistency failures
        )
        
        if success:
            self.log_success("Cache safety checks passed!")
        else:
            self.log_error("Cache safety issues detected")
        
        return success

def main():
    if len(sys.argv) != 2:
        print("Usage: python phase3_cache_safety.py <project_root>")
        sys.exit(1)
    
    project_root = sys.argv[1]
    checker = WallpaperCacheSafetyChecker(project_root)
    
    success = asyncio.run(checker.run_cache_safety_check())
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()