#!/usr/bin/env python3
"""
SHARED CI UTILITIES
Common utility functions for all CI pipelines.
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

class CILogger:
    """Standardized CI logging with emoji indicators."""
    
    @staticmethod
    def step(message: str):
        print(f"🔄 {message}")
        
    @staticmethod
    def success(message: str):
        print(f"✅ {message}")
        
    @staticmethod
    def error(message: str):
        print(f"❌ {message}")
        
    @staticmethod
    def warning(message: str):
        print(f"⚠️  {message}")
        
    @staticmethod
    def info(message: str):
        print(f"ℹ️  {message}")
        
    @staticmethod
    def header(message: str):
        print(f"\n📊 {message}")
        print("=" * (len(message) + 4))

class CIReporter:
    """Generate standardized CI reports."""
    
    def __init__(self, test_name: str, output_dir: Optional[str] = None):
        self.test_name = test_name
        self.output_dir = Path(output_dir) if output_dir else Path.cwd() / "ci-reports"
        self.output_dir.mkdir(exist_ok=True)
        self.start_time = time.time()
        
    def generate_report(self, results: Dict[str, Any], success: bool) -> str:
        """Generate a standardized CI test report."""
        end_time = time.time()
        duration = end_time - self.start_time
        
        report = {
            "test_name": self.test_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": round(duration, 2),
            "success": success,
            "results": results,
            "environment": {
                "python_version": sys.version.split()[0],
                "platform": sys.platform,
                "ci_environment": os.getenv("CI", "false") == "true",
                "github_actions": os.getenv("GITHUB_ACTIONS", "false") == "true"
            }
        }
        
        # Save report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.output_dir / f"{self.test_name}_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        return str(report_file)

class CIConfig:
    """Load and validate CI configuration."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "ci-standards.json"
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load CI configuration from file."""
        config_path = Path(__file__).parent / self.config_file
        
        if not config_path.exists():
            # Return default configuration
            return {
                "version": "1.0.0",
                "environments": {
                    "development": {
                        "python_version": "3.11",
                        "timeout_seconds": 30
                    }
                }
            }
            
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            CILogger.warning(f"Failed to load config {config_path}: {e}")
            return {}
    
    def get_environment_config(self, env: str = "development") -> Dict[str, Any]:
        """Get configuration for specific environment."""
        return self.config.get("environments", {}).get(env, {})
    
    def get_timeout(self, env: str = "development") -> int:
        """Get timeout for environment."""
        return self.get_environment_config(env).get("timeout_seconds", 30)
    
    def get_python_version(self, env: str = "development") -> str:
        """Get required Python version."""
        return self.get_environment_config(env).get("python_version", "3.11")

def create_github_summary(title: str, results: Dict[str, Any], success: bool) -> str:
    """Create GitHub Actions step summary."""
    status_emoji = "✅" if success else "❌"
    status_text = "PASSED" if success else "FAILED"
    
    summary = f"## {status_emoji} {title}: {status_text}\n\n"
    
    # Add key metrics if available
    if "passed" in results and "total" in results:
        passed = results["passed"]
        total = results["total"]
        percentage = (passed / total * 100) if total > 0 else 0
        
        summary += f"**Results:** {passed}/{total} ({percentage:.1f}%)\n\n"
    
    # Add details table if results available
    if "results" in results and isinstance(results["results"], list):
        summary += "| Check | Status | Details |\n"
        summary += "|-------|--------|---------|\n"
        
        for result in results["results"][:10]:  # Limit to first 10 results
            name = result.get("name", "Unknown")
            status = "✅ Pass" if result.get("passed", False) else "❌ Fail"
            error = result.get("error_message", "")
            details = error if error else "OK"
            
            summary += f"| {name} | {status} | {details} |\n"
            
        if len(results["results"]) > 10:
            summary += f"| ... | ... | {len(results['results']) - 10} more results |\n"
    
    summary += f"\n**Timestamp:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
    
    return summary

def load_shared_standards() -> Dict[str, Any]:
    """Load shared CI standards configuration."""
    config = CIConfig()
    return config.config

def validate_environment_readiness(environment: str = "development") -> bool:
    """Quick environment readiness check."""
    config = CIConfig()
    env_config = config.get_environment_config(environment)
    
    if not env_config:
        CILogger.error(f"No configuration found for environment: {environment}")
        return False
        
    # Check Python version
    required_version = config.get_python_version(environment)
    current_version = sys.version.split()[0]
    
    if not current_version.startswith(required_version):
        CILogger.error(f"Python version mismatch: got {current_version}, need {required_version}")
        return False
        
    CILogger.success(f"Environment {environment} is ready")
    return True