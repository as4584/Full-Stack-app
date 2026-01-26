#!/usr/bin/env python3
"""
PHASE 3: CORS & Transport Check
Tests CORS preflight, origin validation, and transport layer.
"""

import asyncio
import aiohttp
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class CorsTestResult:
    passed: bool
    message: str
    details: Optional[Dict] = None

class CorsTransportTester:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.backend_url = "http://localhost:8080"
        self.frontend_url = "http://localhost:3080"
        self.proxy_url = "http://localhost:8881"
        
        # Test origins
        self.test_origins = [
            self.frontend_url,
            "http://localhost:3000",  # Dev frontend
            "https://dashboard.lexmakesit.com",  # Production
        ]
        
        self.invalid_origins = [
            "http://malicious.example.com",
            "https://evil.com",
            "http://localhost:9999",
        ]

    def log_step(self, message: str):
        print(f"🔄 {message}")
        
    def log_success(self, message: str):
        print(f"✅ {message}")
        
    def log_error(self, message: str):
        print(f"❌ {message}")

    async def test_options_preflight(self) -> CorsTestResult:
        """Test CORS preflight OPTIONS request."""
        self.log_step("Testing OPTIONS preflight...")
        
        try:
            headers = {
                "Origin": self.frontend_url,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type, Authorization",
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.options(
                    f"{self.backend_url}/api/auth/login",
                    headers=headers
                ) as response:
                    
                    response_headers = dict(response.headers)
                    
                    # Check status code
                    if response.status not in [200, 204]:
                        return CorsTestResult(
                            passed=False,
                            message=f"OPTIONS request failed with status {response.status}",
                            details={"status": response.status, "headers": response_headers}
                        )
                    
                    # Check CORS headers
                    required_headers = [
                        "Access-Control-Allow-Origin",
                        "Access-Control-Allow-Methods",
                        "Access-Control-Allow-Headers",
                    ]
                    
                    missing_headers = []
                    for header in required_headers:
                        if header.lower() not in [h.lower() for h in response_headers.keys()]:
                            missing_headers.append(header)
                    
                    if missing_headers:
                        return CorsTestResult(
                            passed=False,
                            message=f"Missing CORS headers: {missing_headers}",
                            details={"response_headers": response_headers}
                        )
                    
                    # Check if credentials are allowed
                    credentials_allowed = response_headers.get("Access-Control-Allow-Credentials", "").lower() == "true"
                    if not credentials_allowed:
                        return CorsTestResult(
                            passed=False,
                            message="Access-Control-Allow-Credentials not set to true",
                            details={"credentials_header": response_headers.get("Access-Control-Allow-Credentials")}
                        )
                    
                    self.log_success("OPTIONS preflight test passed")
                    return CorsTestResult(
                        passed=True,
                        message="CORS preflight works correctly",
                        details={"cors_headers": {k: v for k, v in response_headers.items() if "access-control" in k.lower()}}
                    )
                    
        except Exception as e:
            return CorsTestResult(
                passed=False,
                message=f"OPTIONS preflight error: {e}",
                details={"exception": str(e)}
            )

    async def test_origin_validation(self) -> CorsTestResult:
        """Test that valid origins are allowed and invalid ones are rejected."""
        self.log_step("Testing origin validation...")
        
        results = {"valid": [], "invalid": []}
        
        try:
            # Test valid origins
            for origin in self.test_origins:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            f"{self.backend_url}/api/auth/login",
                            json={"email": "test@example.com", "password": "invalid"},
                            headers={
                                "Origin": origin,
                                "Content-Type": "application/json"
                            }
                        ) as response:
                            
                            cors_origin = response.headers.get("Access-Control-Allow-Origin")
                            if cors_origin and (cors_origin == origin or cors_origin == "*"):
                                results["valid"].append({"origin": origin, "allowed": True})
                            else:
                                results["valid"].append({"origin": origin, "allowed": False, "cors_origin": cors_origin})
                                
                except Exception as e:
                    results["valid"].append({"origin": origin, "error": str(e)})
            
            # Test invalid origins
            for origin in self.invalid_origins:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            f"{self.backend_url}/api/auth/login",
                            json={"email": "test@example.com", "password": "invalid"},
                            headers={
                                "Origin": origin,
                                "Content-Type": "application/json"
                            }
                        ) as response:
                            
                            cors_origin = response.headers.get("Access-Control-Allow-Origin")
                            if cors_origin == origin:
                                results["invalid"].append({"origin": origin, "incorrectly_allowed": True})
                            else:
                                results["invalid"].append({"origin": origin, "correctly_blocked": True})
                                
                except Exception as e:
                    results["invalid"].append({"origin": origin, "error": str(e)})
            
            # Analyze results
            valid_passed = all(r.get("allowed", False) for r in results["valid"])
            invalid_passed = all(r.get("correctly_blocked", False) for r in results["invalid"])
            
            if valid_passed and invalid_passed:
                self.log_success("Origin validation test passed")
                return CorsTestResult(
                    passed=True,
                    message="Origin validation works correctly",
                    details=results
                )
            else:
                return CorsTestResult(
                    passed=False,
                    message="Origin validation failed",
                    details=results
                )
                
        except Exception as e:
            return CorsTestResult(
                passed=False,
                message=f"Origin validation error: {e}",
                details={"exception": str(e), "partial_results": results}
            )

    async def test_credentials_handling(self) -> CorsTestResult:
        """Test that credentials=include works correctly."""
        self.log_step("Testing credentials handling...")
        
        try:
            login_data = {"email": "test@example.com", "password": "TestPassword123!"}
            
            # First, try to login and get a cookie
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.backend_url}/api/auth/login",
                    json=login_data,
                    headers={
                        "Origin": self.frontend_url,
                        "Content-Type": "application/json"
                    }
                ) as response:
                    
                    if response.status != 200:
                        # Login failed, but that's ok - we're testing credentials handling
                        pass
                    
                    # Check if server allows credentials
                    allows_credentials = response.headers.get("Access-Control-Allow-Credentials", "").lower() == "true"
                    if not allows_credentials:
                        return CorsTestResult(
                            passed=False,
                            message="Server does not allow credentials",
                            details={"credentials_header": response.headers.get("Access-Control-Allow-Credentials")}
                        )
                    
                    # Check if cookies can be set cross-origin
                    set_cookie = response.headers.get("Set-Cookie", "")
                    if set_cookie and "SameSite" in set_cookie:
                        # Analyze SameSite policy
                        if "SameSite=None" in set_cookie or "SameSite=Lax" in set_cookie:
                            cookie_policy_ok = True
                        else:
                            cookie_policy_ok = False
                    else:
                        cookie_policy_ok = True  # No SameSite restriction
                    
                    if not cookie_policy_ok:
                        return CorsTestResult(
                            passed=False,
                            message="Cookie SameSite policy may prevent cross-origin auth",
                            details={"set_cookie": set_cookie}
                        )
                    
                    self.log_success("Credentials handling test passed")
                    return CorsTestResult(
                        passed=True,
                        message="Credentials handling works correctly",
                        details={
                            "allows_credentials": allows_credentials,
                            "cookie_policy": "Compatible with cross-origin",
                            "set_cookie_sample": set_cookie[:100] + "..." if len(set_cookie) > 100 else set_cookie
                        }
                    )
                    
        except Exception as e:
            return CorsTestResult(
                passed=False,
                message=f"Credentials handling error: {e}",
                details={"exception": str(e)}
            )

    async def test_https_http_consistency(self) -> CorsTestResult:
        """Test HTTPS/HTTP protocol consistency."""
        self.log_step("Testing HTTP/HTTPS consistency...")
        
        try:
            # This is a simplified test - in a real scenario you'd test both protocols
            # For now, we'll just verify the protocol handling is consistent
            
            protocols_tested = []
            
            # Test HTTP
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.backend_url}/health") as response:
                        protocols_tested.append({
                            "protocol": "HTTP",
                            "status": response.status,
                            "accessible": response.status == 200
                        })
            except Exception as e:
                protocols_tested.append({
                    "protocol": "HTTP",
                    "error": str(e),
                    "accessible": False
                })
            
            # For HTTPS test, we'd need proper certificates in CI
            # For now, we'll assume HTTP is the target for CI testing
            
            http_accessible = any(p.get("accessible") for p in protocols_tested if p.get("protocol") == "HTTP")
            
            if http_accessible:
                self.log_success("Protocol consistency test passed")
                return CorsTestResult(
                    passed=True,
                    message="HTTP protocol accessible for testing",
                    details={"protocols": protocols_tested}
                )
            else:
                return CorsTestResult(
                    passed=False,
                    message="No accessible protocols found",
                    details={"protocols": protocols_tested}
                )
                
        except Exception as e:
            return CorsTestResult(
                passed=False,
                message=f"Protocol consistency error: {e}",
                details={"exception": str(e)}
            )

    async def test_proxy_routing(self) -> CorsTestResult:
        """Test that proxy correctly routes auth requests."""
        self.log_step("Testing proxy routing...")
        
        try:
            # Test direct backend access
            backend_direct = None
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.backend_url}/health") as response:
                        backend_direct = {"status": response.status, "accessible": True}
            except Exception:
                backend_direct = {"accessible": False}
            
            # Test proxy access  
            proxy_access = None
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.proxy_url}/api/health") as response:
                        proxy_access = {"status": response.status, "accessible": True}
            except Exception as e:
                proxy_access = {"accessible": False, "error": str(e)}
            
            # Test auth endpoint through proxy
            auth_through_proxy = None
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.proxy_url}/api/auth/login",
                        json={"email": "test@example.com", "password": "invalid"},
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        auth_through_proxy = {
                            "status": response.status,
                            "accessible": True,
                            "reaches_backend": response.status in [401, 422, 200]  # Any backend response
                        }
            except Exception as e:
                auth_through_proxy = {"accessible": False, "error": str(e)}
            
            results = {
                "backend_direct": backend_direct,
                "proxy_access": proxy_access, 
                "auth_through_proxy": auth_through_proxy
            }
            
            # Determine if routing works
            routing_works = (
                backend_direct and backend_direct.get("accessible") and
                auth_through_proxy and auth_through_proxy.get("reaches_backend")
            )
            
            if routing_works:
                self.log_success("Proxy routing test passed")
                return CorsTestResult(
                    passed=True,
                    message="Proxy correctly routes auth requests",
                    details=results
                )
            else:
                return CorsTestResult(
                    passed=False,
                    message="Proxy routing issues detected",
                    details=results
                )
                
        except Exception as e:
            return CorsTestResult(
                passed=False,
                message=f"Proxy routing error: {e}",
                details={"exception": str(e)}
            )

    async def run_cors_transport_tests(self) -> bool:
        """Run all CORS and transport tests."""
        print("🌐 Starting Phase 3: CORS & Transport Check\n")
        
        tests = [
            ("OPTIONS Preflight", self.test_options_preflight),
            ("Origin Validation", self.test_origin_validation), 
            ("Credentials Handling", self.test_credentials_handling),
            ("Protocol Consistency", self.test_https_http_consistency),
            ("Proxy Routing", self.test_proxy_routing),
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"\n🔍 Running {test_name} test...")
            
            try:
                result = await test_func()
                results.append((test_name, result))
                
                if result.passed:
                    self.log_success(f"{test_name}: {result.message}")
                else:
                    self.log_error(f"{test_name}: {result.message}")
                    if result.details:
                        print(f"   Details: {json.dumps(result.details, indent=2)}")
                        
            except Exception as e:
                self.log_error(f"{test_name}: Unexpected error: {e}")
                results.append((test_name, CorsTestResult(passed=False, message=str(e))))
        
        # Summary
        passed_tests = sum(1 for _, result in results if result.passed)
        total_tests = len(results)
        
        print(f"\n📊 Phase 3 Summary:")
        print(f"✅ Passed: {passed_tests}/{total_tests}")
        print(f"❌ Failed: {total_tests - passed_tests}/{total_tests}")
        
        success = passed_tests == total_tests
        
        if not success:
            print(f"\n🚨 Failed tests:")
            for test_name, result in results:
                if not result.passed:
                    print(f"  • {test_name}: {result.message}")
        
        return success

def main():
    if len(sys.argv) != 2:
        print("Usage: python cors_transport_test.py <project_root>")
        sys.exit(1)
    
    project_root = sys.argv[1]
    tester = CorsTransportTester(project_root)
    
    success = asyncio.run(tester.run_cors_transport_tests())
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()