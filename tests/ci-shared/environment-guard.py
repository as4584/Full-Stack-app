#!/usr/bin/env python3
"""
SHARED ENVIRONMENT GUARD
Validates deployment environment safety and readiness.
Used by all CI pipelines before deployment.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class EnvironmentCheck:
    name: str
    description: str
    check_type: str  # 'env_var', 'file_exists', 'command', 'port', 'url'
    target: str
    required: bool
    passed: bool = False
    error_message: str = ""

class SharedEnvironmentGuard:
    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.checks = self._define_checks()
        
    def _define_checks(self) -> List[EnvironmentCheck]:
        """Define environment safety checks based on environment type."""
        common_checks = [
            EnvironmentCheck(
                name="python_version",
                description="Python version compatibility",
                check_type="command",
                target="python3 --version",
                required=True
            ),
            EnvironmentCheck(
                name="git_clean_workspace",
                description="Git workspace is clean",
                check_type="command",
                target="git status --porcelain",
                required=True
            ),
            EnvironmentCheck(
                name="dependencies_installed",
                description="Required dependencies available",
                check_type="command",
                target="python3 -c 'import aiohttp, playwright'",
                required=True
            )
        ]
        
        if self.environment == "production":
            common_checks.extend([
                EnvironmentCheck(
                    name="ssl_certificates",
                    description="SSL certificates valid",
                    check_type="env_var",
                    target="SSL_CERT_PATH",
                    required=True
                ),
                EnvironmentCheck(
                    name="database_connection",
                    description="Database connection available",
                    check_type="env_var",
                    target="DATABASE_URL",
                    required=True
                ),
                EnvironmentCheck(
                    name="jwt_secret",
                    description="JWT secret configured",
                    check_type="env_var",
                    target="JWT_SECRET",
                    required=True
                )
            ])
        
        return common_checks
    
    def log_step(self, message: str):
        print(f"🔄 {message}")
        
    def log_success(self, message: str):
        print(f"✅ {message}")
        
    def log_error(self, message: str):
        print(f"❌ {message}")
        
    def log_warning(self, message: str):
        print(f"⚠️  {message}")

    def check_env_var(self, check: EnvironmentCheck) -> bool:
        """Check if required environment variable exists."""
        value = os.getenv(check.target)
        if not value:
            check.error_message = f"Environment variable {check.target} not set"
            return False
        
        if len(value.strip()) == 0:
            check.error_message = f"Environment variable {check.target} is empty"
            return False
            
        return True

    def check_file_exists(self, check: EnvironmentCheck) -> bool:
        """Check if required file exists."""
        if not Path(check.target).exists():
            check.error_message = f"Required file {check.target} not found"
            return False
        return True

    def check_command(self, check: EnvironmentCheck) -> bool:
        """Execute command and check result."""
        try:
            result = subprocess.run(
                check.target,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Special handling for git status (should be empty)
            if "git status" in check.target:
                if result.returncode == 0 and len(result.stdout.strip()) == 0:
                    return True
                else:
                    check.error_message = "Git workspace has uncommitted changes"
                    return False
            
            # General command success
            if result.returncode != 0:
                check.error_message = f"Command failed: {result.stderr.strip()}"
                return False
                
            return True
            
        except subprocess.TimeoutExpired:
            check.error_message = "Command timeout"
            return False
        except Exception as e:
            check.error_message = f"Command error: {str(e)}"
            return False

    def run_check(self, check: EnvironmentCheck) -> bool:
        """Run a single environment check."""
        self.log_step(f"Checking {check.name}: {check.description}")
        
        if check.check_type == "env_var":
            check.passed = self.check_env_var(check)
        elif check.check_type == "file_exists":
            check.passed = self.check_file_exists(check)
        elif check.check_type == "command":
            check.passed = self.check_command(check)
        else:
            check.error_message = f"Unknown check type: {check.check_type}"
            check.passed = False
        
        if check.passed:
            self.log_success(f"{check.name}: OK")
        else:
            if check.required:
                self.log_error(f"{check.name}: {check.error_message}")
            else:
                self.log_warning(f"{check.name}: {check.error_message} (optional)")
        
        return check.passed

    def run_all_checks(self) -> Dict[str, Any]:
        """Run all environment safety checks."""
        print(f"🛡️  Starting Environment Guard ({self.environment})\n")
        
        results = []
        for check in self.checks:
            self.run_check(check)
            results.append({
                "name": check.name,
                "description": check.description,
                "required": check.required,
                "passed": check.passed,
                "error_message": check.error_message
            })
        
        # Analyze results
        required_checks = [c for c in self.checks if c.required]
        required_passed = [c for c in required_checks if c.passed]
        optional_checks = [c for c in self.checks if not c.required]
        optional_passed = [c for c in optional_checks if c.passed]
        
        summary = {
            "environment": self.environment,
            "required_passed": len(required_passed),
            "required_total": len(required_checks),
            "optional_passed": len(optional_passed),
            "optional_total": len(optional_checks),
            "overall_passed": len(required_passed) == len(required_checks),
            "results": results
        }
        
        print(f"\n📊 Environment Guard Summary:")
        print(f"✅ Required checks: {summary['required_passed']}/{summary['required_total']}")
        print(f"📌 Optional checks: {summary['optional_passed']}/{summary['optional_total']}")
        
        if summary["overall_passed"]:
            self.log_success(f"Environment {self.environment} is ready for deployment")
        else:
            self.log_error(f"Environment {self.environment} is NOT ready for deployment")
            print("\n🚨 Failed Required Checks:")
            for check in required_checks:
                if not check.passed:
                    print(f"  • {check.name}: {check.error_message}")
                    
        return summary

def main():
    environment = os.getenv("CI_ENVIRONMENT", "development")
    if len(sys.argv) > 1:
        environment = sys.argv[1]
    
    guard = SharedEnvironmentGuard(environment)
    summary = guard.run_all_checks()
    
    sys.exit(0 if summary["overall_passed"] else 1)

if __name__ == "__main__":
    main()