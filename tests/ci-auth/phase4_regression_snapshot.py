#!/usr/bin/env python3
"""
PHASE 4: Regression Snapshot System
Captures and compares auth request/response payloads to detect breaking changes.
"""

import json
import hashlib
import os
import sys
import asyncio
import aiohttp
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

@dataclass
class AuthSnapshot:
    timestamp: str
    test_name: str
    request: Dict[str, Any]
    response: Dict[str, Any]
    headers: Dict[str, str]
    status_code: int
    checksum: str

class SnapshotManager:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.snapshots_dir = self.project_root / "tests/ci-auth/snapshots"
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        self.baseline_file = self.snapshots_dir / "auth_baseline.json"
        self.backend_url = "http://localhost:8080"

    def log_step(self, message: str):
        print(f"🔄 {message}")
        
    def log_success(self, message: str):
        print(f"✅ {message}")
        
    def log_error(self, message: str):
        print(f"❌ {message}")
        
    def log_warning(self, message: str):
        print(f"⚠️  {message}")

    def calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate checksum of normalized data."""
        # Normalize data by removing timestamps and other volatile fields
        normalized = self.normalize_data(data)
        data_str = json.dumps(normalized, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def normalize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove volatile fields for stable comparison."""
        if isinstance(data, dict):
            normalized = {}
            for key, value in data.items():
                # Skip volatile fields
                if key.lower() in ['timestamp', 'exp', 'iat', 'date', 'x-request-id']:
                    continue
                
                # Truncate long tokens for comparison
                if key in ['access_token', 'token'] and isinstance(value, str) and len(value) > 50:
                    normalized[key] = f"{value[:20]}...{value[-20:]}"
                else:
                    normalized[key] = self.normalize_data(value)
            return normalized
        elif isinstance(data, list):
            return [self.normalize_data(item) for item in data]
        else:
            return data

    async def capture_login_snapshot(self) -> AuthSnapshot:
        """Capture current login request/response."""
        self.log_step("Capturing login snapshot...")
        
        test_user = {
            "email": "test@example.com",
            "password": "TestPassword123!"
        }
        
        request_data = {
            "method": "POST",
            "url": "/api/auth/login",
            "body": test_user,
            "headers": {"Content-Type": "application/json"}
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.backend_url}/api/auth/login",
                    json=test_user,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    response_data = await response.text()
                    response_headers = dict(response.headers)
                    
                    # Try to parse JSON response
                    try:
                        response_json = json.loads(response_data)
                    except:
                        response_json = {"raw_response": response_data}
                    
                    snapshot_data = {
                        "request": request_data,
                        "response": response_json,
                        "status_code": response.status,
                        "headers": response_headers
                    }
                    
                    snapshot = AuthSnapshot(
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        test_name="login_endpoint",
                        request=request_data,
                        response=response_json,
                        headers=response_headers,
                        status_code=response.status,
                        checksum=self.calculate_checksum(snapshot_data)
                    )
                    
                    return snapshot
                    
        except Exception as e:
            # Return error snapshot
            error_data = {
                "request": request_data,
                "response": {"error": str(e)},
                "status_code": 0,
                "headers": {}
            }
            
            return AuthSnapshot(
                timestamp=datetime.now(timezone.utc).isoformat(),
                test_name="login_endpoint",
                request=request_data,
                response={"error": str(e)},
                headers={},
                status_code=0,
                checksum=self.calculate_checksum(error_data)
            )

    async def capture_token_validation_snapshot(self, token: str) -> AuthSnapshot:
        """Capture token validation request/response."""
        self.log_step("Capturing token validation snapshot...")
        
        request_data = {
            "method": "GET",
            "url": "/api/auth/me",
            "headers": {"Authorization": f"Bearer {token}"}
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.backend_url}/api/auth/me",
                    headers={"Authorization": f"Bearer {token}"}
                ) as response:
                    
                    response_data = await response.text()
                    response_headers = dict(response.headers)
                    
                    try:
                        response_json = json.loads(response_data)
                    except:
                        response_json = {"raw_response": response_data}
                    
                    snapshot_data = {
                        "request": request_data,
                        "response": response_json,
                        "status_code": response.status,
                        "headers": response_headers
                    }
                    
                    return AuthSnapshot(
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        test_name="token_validation",
                        request=request_data,
                        response=response_json,
                        headers=response_headers,
                        status_code=response.status,
                        checksum=self.calculate_checksum(snapshot_data)
                    )
                    
        except Exception as e:
            error_data = {
                "request": request_data,
                "response": {"error": str(e)},
                "status_code": 0,
                "headers": {}
            }
            
            return AuthSnapshot(
                timestamp=datetime.now(timezone.utc).isoformat(),
                test_name="token_validation",
                request=request_data,
                response={"error": str(e)},
                headers={},
                status_code=0,
                checksum=self.calculate_checksum(error_data)
            )

    def save_baseline(self, snapshots: List[AuthSnapshot]):
        """Save snapshots as baseline."""
        self.log_step("Saving baseline snapshots...")
        
        baseline_data = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "snapshots": [asdict(snapshot) for snapshot in snapshots]
        }
        
        with open(self.baseline_file, 'w') as f:
            json.dump(baseline_data, f, indent=2)
        
        self.log_success(f"Baseline saved with {len(snapshots)} snapshots")

    def load_baseline(self) -> Optional[List[AuthSnapshot]]:
        """Load baseline snapshots."""
        if not self.baseline_file.exists():
            return None
        
        try:
            with open(self.baseline_file, 'r') as f:
                data = json.load(f)
            
            snapshots = []
            for snapshot_data in data.get("snapshots", []):
                snapshots.append(AuthSnapshot(**snapshot_data))
            
            return snapshots
            
        except Exception as e:
            self.log_error(f"Failed to load baseline: {e}")
            return None

    def compare_snapshots(self, current: List[AuthSnapshot], baseline: List[AuthSnapshot]) -> Dict[str, Any]:
        """Compare current snapshots with baseline."""
        self.log_step("Comparing snapshots with baseline...")
        
        # Index snapshots by test name
        current_by_name = {s.test_name: s for s in current}
        baseline_by_name = {s.test_name: s for s in baseline}
        
        comparison_results = {
            "identical": [],
            "changed": [],
            "new_tests": [],
            "missing_tests": [],
            "summary": {}
        }
        
        # Check all current tests
        for test_name, current_snapshot in current_by_name.items():
            if test_name not in baseline_by_name:
                comparison_results["new_tests"].append({
                    "test": test_name,
                    "current": asdict(current_snapshot)
                })
            else:
                baseline_snapshot = baseline_by_name[test_name]
                
                if current_snapshot.checksum == baseline_snapshot.checksum:
                    comparison_results["identical"].append(test_name)
                else:
                    # Find specific differences
                    differences = self.find_differences(
                        asdict(current_snapshot), 
                        asdict(baseline_snapshot)
                    )
                    
                    comparison_results["changed"].append({
                        "test": test_name,
                        "current": asdict(current_snapshot),
                        "baseline": asdict(baseline_snapshot),
                        "differences": differences
                    })
        
        # Check for missing tests
        for test_name in baseline_by_name.keys():
            if test_name not in current_by_name:
                comparison_results["missing_tests"].append(test_name)
        
        # Create summary
        comparison_results["summary"] = {
            "total_tests": len(current_by_name),
            "identical": len(comparison_results["identical"]),
            "changed": len(comparison_results["changed"]),
            "new": len(comparison_results["new_tests"]),
            "missing": len(comparison_results["missing_tests"]),
            "regression_detected": len(comparison_results["changed"]) > 0 or len(comparison_results["missing_tests"]) > 0
        }
        
        return comparison_results

    def find_differences(self, current: Dict, baseline: Dict, path: str = "") -> List[Dict]:
        """Find specific differences between two dictionaries."""
        differences = []
        
        # Skip timestamp fields
        excluded_keys = {'timestamp', 'checksum'}
        
        for key in set(current.keys()) | set(baseline.keys()):
            if key in excluded_keys:
                continue
                
            key_path = f"{path}.{key}" if path else key
            
            if key not in current:
                differences.append({
                    "type": "removed",
                    "path": key_path,
                    "baseline_value": baseline[key]
                })
            elif key not in baseline:
                differences.append({
                    "type": "added", 
                    "path": key_path,
                    "current_value": current[key]
                })
            elif current[key] != baseline[key]:
                if isinstance(current[key], dict) and isinstance(baseline[key], dict):
                    differences.extend(self.find_differences(current[key], baseline[key], key_path))
                else:
                    differences.append({
                        "type": "changed",
                        "path": key_path,
                        "current_value": current[key],
                        "baseline_value": baseline[key]
                    })
        
        return differences

    def save_comparison_report(self, comparison: Dict[str, Any]):
        """Save comparison report to file."""
        report_file = self.snapshots_dir / f"comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w') as f:
            json.dump(comparison, f, indent=2)
        
        self.log_step(f"Comparison report saved to {report_file}")

    async def run_regression_test(self, create_baseline: bool = False) -> bool:
        """Run regression snapshot test."""
        print("📸 Starting Phase 4: Regression Snapshot Test\n")
        
        try:
            # Capture current snapshots
            self.log_step("Capturing current auth snapshots...")
            
            current_snapshots = []
            
            # Login snapshot
            login_snapshot = await self.capture_login_snapshot()
            current_snapshots.append(login_snapshot)
            
            # Token validation snapshot (if login succeeds)
            if login_snapshot.status_code == 200 and 'access_token' in login_snapshot.response:
                token = login_snapshot.response['access_token']
                validation_snapshot = await self.capture_token_validation_snapshot(token)
                current_snapshots.append(validation_snapshot)
            
            self.log_success(f"Captured {len(current_snapshots)} snapshots")
            
            # If creating baseline, save and exit
            if create_baseline:
                self.save_baseline(current_snapshots)
                return True
            
            # Load baseline for comparison
            baseline_snapshots = self.load_baseline()
            
            if not baseline_snapshots:
                self.log_warning("No baseline found. Creating initial baseline...")
                self.save_baseline(current_snapshots)
                return True
            
            # Compare with baseline
            comparison = self.compare_snapshots(current_snapshots, baseline_snapshots)
            
            # Save comparison report
            self.save_comparison_report(comparison)
            
            # Print results
            summary = comparison["summary"]
            print(f"\n📊 Phase 4 Summary:")
            print(f"📋 Total tests: {summary['total_tests']}")
            print(f"✅ Identical: {summary['identical']}")
            print(f"🔄 Changed: {summary['changed']}")
            print(f"🆕 New tests: {summary['new']}")
            print(f"❌ Missing tests: {summary['missing']}")
            
            # Report changes
            if comparison["changed"]:
                print(f"\n🚨 Breaking changes detected:")
                for change in comparison["changed"]:
                    print(f"  • {change['test']}: {len(change['differences'])} differences")
                    for diff in change['differences'][:3]:  # Show first 3 differences
                        print(f"    - {diff['type']}: {diff['path']}")
                    if len(change['differences']) > 3:
                        print(f"    - ... and {len(change['differences']) - 3} more")
            
            if comparison["missing_tests"]:
                print(f"\n❌ Missing tests:")
                for test_name in comparison["missing_tests"]:
                    print(f"  • {test_name}")
            
            if comparison["new_tests"]:
                print(f"\n🆕 New tests:")
                for new_test in comparison["new_tests"]:
                    print(f"  • {new_test['test']}")
            
            # Determine success
            success = not summary["regression_detected"]
            
            if success:
                self.log_success("No regressions detected")
            else:
                self.log_error("Regression detected - auth behavior has changed")
            
            return success
            
        except Exception as e:
            self.log_error(f"Regression test failed: {e}")
            return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python regression_snapshot.py <project_root> [--create-baseline]")
        sys.exit(1)
    
    project_root = sys.argv[1]
    create_baseline = "--create-baseline" in sys.argv
    
    manager = SnapshotManager(project_root)
    success = asyncio.run(manager.run_regression_test(create_baseline))
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()