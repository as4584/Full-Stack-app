#!/usr/bin/env python3
"""
SHARED AUTH CONTRACT VALIDATOR
Reusable authentication contract validation logic.
Used by both frontend and backend CI pipelines.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import aiohttp

@dataclass
class AuthContract:
    name: str
    endpoint: str
    method: str
    expected_status: int
    headers: Dict[str, str]
    payload: Optional[Dict[str, Any]]
    description: str

class SharedAuthContractValidator:
    def __init__(self, base_url: str, config_path: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.config_path = config_path or 'ci-standards.json'
        self.contracts = self._load_contracts()
        
    def _load_contracts(self) -> List[AuthContract]:
        """Load authentication contracts from configuration."""
        # Standard auth contracts that all systems must implement
        return [
            AuthContract(
                name="login_endpoint_exists",
                endpoint="/api/login",
                method="POST",
                expected_status=422,  # Validation error for missing credentials
                headers={"Content-Type": "application/json"},
                payload={},
                description="Login endpoint accepts POST requests"
            ),
            AuthContract(
                name="protected_route_guards",
                endpoint="/api/user/profile",
                method="GET", 
                expected_status=401,  # Unauthorized without token
                headers={},
                payload=None,
                description="Protected routes require authentication"
            ),
            AuthContract(
                name="invalid_token_rejection",
                endpoint="/api/user/profile",
                method="GET",
                expected_status=401,  # Unauthorized with invalid token
                headers={"Authorization": "Bearer invalid_token_12345"},
                payload=None,
                description="Invalid tokens are properly rejected"
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

    async def validate_contract(self, contract: AuthContract) -> Dict[str, Any]:
        """Validate a single authentication contract."""
        self.log_step(f"Testing {contract.name}: {contract.description}")
        
        result = {
            "name": contract.name,
            "passed": False,
            "actual_status": None,
            "expected_status": contract.expected_status,
            "error_message": "",
            "response_time_ms": 0
        }
        
        url = f"{self.base_url}{contract.endpoint}"
        
        try:
            import time
            start_time = time.time()
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.request(
                    method=contract.method,
                    url=url,
                    headers=contract.headers,
                    json=contract.payload
                ) as response:
                    result["actual_status"] = response.status
                    result["response_time_ms"] = int((time.time() - start_time) * 1000)
                    
                    if response.status == contract.expected_status:
                        result["passed"] = True
                        self.log_success(f"{contract.name}: HTTP {response.status} (expected {contract.expected_status})")
                    else:
                        result["error_message"] = f"Got HTTP {response.status}, expected {contract.expected_status}"
                        self.log_error(f"{contract.name}: {result['error_message']}")
                        
        except asyncio.TimeoutError:
            result["error_message"] = "Request timeout"
            self.log_error(f"{contract.name}: Request timeout")
        except Exception as e:
            result["error_message"] = f"Network error: {str(e)}"
            self.log_error(f"{contract.name}: Network error: {str(e)}")
            
        return result

    async def validate_all_contracts(self) -> Dict[str, Any]:
        """Validate all authentication contracts."""
        print("🔐 Starting Shared Auth Contract Validation\n")
        
        results = []
        for contract in self.contracts:
            result = await self.validate_contract(contract)
            results.append(result)
        
        # Analyze results
        passed_count = sum(1 for r in results if r["passed"])
        total_count = len(results)
        
        summary = {
            "passed": passed_count,
            "total": total_count,
            "success_rate": passed_count / total_count if total_count > 0 else 0,
            "results": results,
            "overall_passed": passed_count == total_count
        }
        
        print(f"\n📊 Auth Contract Summary:")
        print(f"✅ Passed: {passed_count}/{total_count}")
        print(f"📌 Success Rate: {summary['success_rate']:.1%}")
        
        if summary["overall_passed"]:
            self.log_success("All authentication contracts validated successfully")
        else:
            self.log_error("Some authentication contracts failed validation")
            
        return summary

def main():
    if len(sys.argv) != 2:
        print("Usage: python auth-contract-validator.py <base_url>")
        print("Example: python auth-contract-validator.py http://localhost:8010")
        sys.exit(1)
    
    base_url = sys.argv[1]
    validator = SharedAuthContractValidator(base_url)
    
    summary = asyncio.run(validator.validate_all_contracts())
    sys.exit(0 if summary["overall_passed"] else 1)

if __name__ == "__main__":
    main()