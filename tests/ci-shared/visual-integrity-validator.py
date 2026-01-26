#!/usr/bin/env python3
"""
SHARED VISUAL INTEGRITY VALIDATOR
Common visual regression and asset validation logic.
Used by wallpaper CI and other visual testing pipelines.
"""

import asyncio
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass
class VisualAsset:
    name: str
    url: str
    asset_type: str  # 'image', 'video', 'css', 'font'
    critical: bool  # If true, failure blocks deployment
    min_size_bytes: int
    max_size_bytes: int
    expected_mime_types: List[str]

@dataclass
class VisualCheck:
    asset: VisualAsset
    passed: bool = False
    file_size: int = 0
    content_type: str = ""
    response_time_ms: int = 0
    content_hash: str = ""
    error_message: str = ""

class SharedVisualIntegrityValidator:
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or 'visual-assets-config.json'
        self.assets = self._load_assets()
        
    def _load_assets(self) -> List[VisualAsset]:
        """Load visual assets configuration."""
        # Default critical visual assets for LexMakesIt platform
        return [
            VisualAsset(
                name="homepage_waterfall_gif",
                url="https://lexmakesit.com/static/images/waterfall.gif",
                asset_type="image",
                critical=True,
                min_size_bytes=1024,
                max_size_bytes=10485760,  # 10MB
                expected_mime_types=["image/gif"]
            ),
            VisualAsset(
                name="homepage_waterfall_fallback",
                url="https://lexmakesit.com/static/images/waterfall.png",
                asset_type="image", 
                critical=True,
                min_size_bytes=1024,
                max_size_bytes=5242880,  # 5MB
                expected_mime_types=["image/png"]
            ),
            VisualAsset(
                name="og_logo",
                url="https://lexmakesit.com/static/images/og-logo.png",
                asset_type="image",
                critical=False,
                min_size_bytes=500,
                max_size_bytes=1048576,  # 1MB
                expected_mime_types=["image/png", "image/jpeg"]
            )
        ]
    
    def log_step(self, message: str):
        print(f"🔄 {message}")
        
    def log_success(self, message: str):
        print(f"✅ {message}")
        
    def log_error(self, message: str):
        print(f"❌ {message}")
        
    def log_warning(self, message: str):
        print(f"⚠️  {message}")

    async def validate_asset(self, asset: VisualAsset) -> VisualCheck:
        """Validate a single visual asset."""
        self.log_step(f"Validating {asset.name}: {asset.url}")
        
        check = VisualCheck(asset=asset)
        
        try:
            import aiohttp
            import time
            
            start_time = time.time()
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                async with session.get(asset.url) as response:
                    check.response_time_ms = int((time.time() - start_time) * 1000)
                    
                    if response.status != 200:
                        check.error_message = f"HTTP {response.status}: {response.reason}"
                        return check
                    
                    # Get content info
                    check.content_type = response.headers.get('content-type', '').lower()
                    content = await response.read()
                    check.file_size = len(content)
                    check.content_hash = hashlib.sha256(content).hexdigest()[:16]
                    
                    # Validate MIME type
                    if not any(mime in check.content_type for mime in asset.expected_mime_types):
                        check.error_message = f"Wrong MIME type: {check.content_type}, expected one of {asset.expected_mime_types}"
                        return check
                    
                    # Validate file size
                    if check.file_size < asset.min_size_bytes:
                        check.error_message = f"File too small: {check.file_size} bytes (min {asset.min_size_bytes})"
                        return check
                        
                    if check.file_size > asset.max_size_bytes:
                        check.error_message = f"File too large: {check.file_size} bytes (max {asset.max_size_bytes})"
                        return check
                    
                    # Validate file format integrity
                    if asset.asset_type == "image":
                        format_valid = self._validate_image_format(content, check.content_type)
                        if not format_valid:
                            check.error_message = "Invalid or corrupted image file format"
                            return check
                    
                    check.passed = True
                    self.log_success(f"{asset.name}: OK ({check.file_size} bytes, {check.response_time_ms}ms)")
                    
        except Exception as e:
            check.error_message = f"Validation error: {str(e)}"
            
        return check
    
    def _validate_image_format(self, content: bytes, content_type: str) -> bool:
        """Validate image file format integrity."""
        try:
            if 'image/gif' in content_type:
                return content.startswith(b'GIF87a') or content.startswith(b'GIF89a')
            elif 'image/png' in content_type:
                return content.startswith(b'\x89PNG\r\n\x1a\n')
            elif 'image/jpeg' in content_type or 'image/jpg' in content_type:
                return content.startswith(b'\xff\xd8\xff')
            else:
                return True  # Unknown format, assume valid
        except:
            return False

    async def validate_all_assets(self) -> Dict[str, Any]:
        """Validate all visual assets."""
        print("🎨 Starting Shared Visual Integrity Validation\n")
        
        checks = []
        for asset in self.assets:
            check = await self.validate_asset(asset)
            checks.append(check)
        
        # Analyze results
        critical_checks = [c for c in checks if c.asset.critical]
        critical_passed = [c for c in critical_checks if c.passed]
        optional_checks = [c for c in checks if not c.asset.critical]
        optional_passed = [c for c in optional_checks if c.passed]
        
        summary = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "critical_passed": len(critical_passed),
            "critical_total": len(critical_checks),
            "optional_passed": len(optional_passed),
            "optional_total": len(optional_checks),
            "overall_passed": len(critical_passed) == len(critical_checks),
            "checks": [{
                "name": c.asset.name,
                "url": c.asset.url,
                "critical": c.asset.critical,
                "passed": c.passed,
                "file_size": c.file_size,
                "response_time_ms": c.response_time_ms,
                "content_hash": c.content_hash,
                "error_message": c.error_message
            } for c in checks]
        }
        
        print(f"\n📊 Visual Integrity Summary:")
        print(f"✅ Critical assets: {summary['critical_passed']}/{summary['critical_total']}")
        print(f"📌 Optional assets: {summary['optional_passed']}/{summary['optional_total']}")
        
        if summary["overall_passed"]:
            self.log_success("All critical visual assets validated successfully")
        else:
            self.log_error("Some critical visual assets failed validation")
            print("\n🚨 Failed Critical Assets:")
            for check in critical_checks:
                if not check.passed:
                    print(f"  • {check.asset.name}: {check.error_message}")
        
        # Show optional failures as warnings
        failed_optional = [c for c in optional_checks if not c.passed]
        if failed_optional:
            print("\n⚠️  Failed Optional Assets:")
            for check in failed_optional:
                print(f"  • {check.asset.name}: {check.error_message}")
                
        return summary

def main():
    validator = SharedVisualIntegrityValidator()
    summary = asyncio.run(validator.validate_all_assets())
    
    sys.exit(0 if summary["overall_passed"] else 1)

if __name__ == "__main__":
    main()