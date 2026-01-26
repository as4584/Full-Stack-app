#!/usr/bin/env python3
"""
PHASE 2: Runtime Auth Smoke Test
Spins up services and tests end-to-end authentication flow.
"""

import asyncio
import aiohttp
import json
import time
import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
import docker
from dataclasses import dataclass

@dataclass
class TestResult:
    passed: bool
    message: str
    details: Optional[Dict] = None

class AuthSmokeTest:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.compose_file = self.project_root / "tests/ci-auth/docker-compose.ci.yml"
        self.docker_client = docker.from_env()
        self.project_name = "ci-auth-test"
        self.test_user = {
            "email": "test@example.com", 
            "password": "TestPassword123!"
        }
        
    def log_step(self, message: str):
        print(f"🔄 {message}")
        
    def log_success(self, message: str):
        print(f"✅ {message}")
        
    def log_error(self, message: str):
        print(f"❌ {message}")
        
    def log_warning(self, message: str):
        print(f"⚠️  {message}")

    async def setup_test_environment(self) -> bool:
        """Start all services using docker-compose."""
        self.log_step("Starting test services...")
        
        try:
            # Stop any existing containers
            subprocess.run([
                "docker-compose", "-f", str(self.compose_file), 
                "-p", self.project_name, "down", "-v"
            ], capture_output=True)
            
            # Start services
            result = subprocess.run([
                "docker-compose", "-f", str(self.compose_file),
                "-p", self.project_name, "up", "-d", "--build"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                self.log_error(f"Failed to start services: {result.stderr}")
                return False
            
            # Wait for services to be healthy
            self.log_step("Waiting for services to be ready...")
            if not await self.wait_for_services():
                return False
                
            # Create test user
            if not await self.create_test_user():
                return False
                
            self.log_success("Test environment ready")
            return True
            
        except Exception as e:
            self.log_error(f"Setup failed: {e}")
            return False

    async def wait_for_services(self, timeout: int = 120) -> bool:
        """Wait for all services to be healthy."""
        services = [
            ("Backend", "http://localhost:8080/health"),
            ("Frontend", "http://localhost:3080/"),
        ]
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            all_ready = True
            
            for service_name, url in services:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=5) as response:
                            if response.status != 200:
                                all_ready = False
                                break
                except:
                    all_ready = False
                    break
            
            if all_ready:
                self.log_success("All services are healthy")
                return True
                
            await asyncio.sleep(5)
            self.log_step(f"Waiting for services... ({int(time.time() - start_time)}s elapsed)")
        
        self.log_error("Services failed to start within timeout")
        return False

    async def create_test_user(self) -> bool:
        """Create a test user for authentication tests."""
        self.log_step("Creating test user...")
        
        try:
            signup_data = {
                "email": self.test_user["email"],
                "password": self.test_user["password"],
                "full_name": "Test User",
                "business_name": "Test Business"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:8080/api/auth/signup",
                    json=signup_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status in [200, 201]:
                        self.log_success("Test user created")
                        return True
                    elif response.status == 400:
                        # User might already exist - that's ok
                        response_text = await response.text()
                        if "already exists" in response_text:
                            self.log_success("Test user already exists")
                            return True
                    
                    self.log_error(f"Failed to create test user: {response.status} - {await response.text()}")
                    return False
                    
        except Exception as e:
            self.log_error(f"Error creating test user: {e}")
            return False

    async def test_login_endpoint(self) -> TestResult:
        """Test POST /api/auth/login endpoint."""
        self.log_step("Testing login endpoint...")
        
        try:
            login_data = {
                "email": self.test_user["email"],
                "password": self.test_user["password"]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:8080/api/auth/login",
                    json=login_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    response_data = await response.json()
                    response_headers = dict(response.headers)
                    
                    # Check status code
                    if response.status != 200:
                        return TestResult(
                            passed=False,
                            message=f"Login failed with status {response.status}",
                            details={
                                "status": response.status,
                                "response": response_data,
                                "headers": response_headers
                            }
                        )
                    
                    # Check for required fields
                    required_fields = ["access_token", "token_type", "user"]
                    for field in required_fields:
                        if field not in response_data:
                            return TestResult(
                                passed=False,
                                message=f"Missing required field: {field}",
                                details={"response": response_data}
                            )
                    
                    # Check for auth cookie
                    set_cookie = response.headers.get("set-cookie", "")
                    if "lex_token=" not in set_cookie:
                        return TestResult(
                            passed=False,
                            message="No auth cookie set",
                            details={"set_cookie": set_cookie}
                        )
                    
                    self.log_success("Login endpoint test passed")
                    return TestResult(
                        passed=True,
                        message="Login successful",
                        details={
                            "token": response_data["access_token"][:50] + "...",  # Truncated
                            "user_id": response_data["user"]["id"],
                            "cookie_set": "lex_token" in set_cookie
                        }
                    )
                    
        except Exception as e:
            return TestResult(
                passed=False,
                message=f"Login test error: {e}",
                details={"exception": str(e)}
            )

    async def test_token_validation(self, token: str) -> TestResult:
        """Test that token is valid by hitting /me endpoint."""
        self.log_step("Testing token validation...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "http://localhost:8080/api/auth/me",
                    headers={"Authorization": f"Bearer {token}"},
                ) as response:
                    
                    if response.status != 200:
                        return TestResult(
                            passed=False,
                            message=f"Token validation failed with status {response.status}",
                            details={
                                "status": response.status,
                                "response": await response.text()
                            }
                        )
                    
                    user_data = await response.json()
                    
                    # Check required user fields
                    required_fields = ["user_id", "email"]
                    for field in required_fields:
                        if field not in user_data:
                            return TestResult(
                                passed=False,
                                message=f"Missing user field: {field}",
                                details={"response": user_data}
                            )
                    
                    self.log_success("Token validation test passed")
                    return TestResult(
                        passed=True,
                        message="Token is valid",
                        details={"user": user_data}
                    )
                    
        except Exception as e:
            return TestResult(
                passed=False,
                message=f"Token validation error: {e}",
                details={"exception": str(e)}
            )

    async def test_cookie_authentication(self) -> TestResult:
        """Test cookie-based authentication."""
        self.log_step("Testing cookie authentication...")
        
        try:
            # First login to get cookie
            login_data = {
                "email": self.test_user["email"],
                "password": self.test_user["password"]
            }
            
            async with aiohttp.ClientSession() as session:
                # Login
                async with session.post(
                    "http://localhost:8080/api/auth/login",
                    json=login_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    if response.status != 200:
                        return TestResult(
                            passed=False,
                            message="Could not login for cookie test"
                        )
                    
                    # Extract cookie
                    set_cookie = response.headers.get("set-cookie", "")
                    if "lex_token=" not in set_cookie:
                        return TestResult(
                            passed=False,
                            message="No cookie set during login"
                        )
                
                # Test using cookie for /me endpoint
                cookie_value = None
                for cookie_part in set_cookie.split(";"):
                    if cookie_part.strip().startswith("lex_token="):
                        cookie_value = cookie_part.strip()
                        break
                
                if not cookie_value:
                    return TestResult(
                        passed=False,
                        message="Could not extract cookie value"
                    )
                
                async with session.get(
                    "http://localhost:8080/api/auth/me",
                    headers={"Cookie": cookie_value}
                ) as response:
                    
                    if response.status != 200:
                        return TestResult(
                            passed=False,
                            message=f"Cookie auth failed with status {response.status}",
                            details={
                                "status": response.status,
                                "response": await response.text()
                            }
                        )
                    
                    self.log_success("Cookie authentication test passed")
                    return TestResult(
                        passed=True,
                        message="Cookie authentication works"
                    )
                    
        except Exception as e:
            return TestResult(
                passed=False,
                message=f"Cookie auth error: {e}",
                details={"exception": str(e)}
            )

    async def test_request_reaches_backend(self) -> TestResult:
        """Verify that requests are reaching the backend by checking logs."""
        self.log_step("Checking if requests reach backend...")
        
        try:
            # Get backend container logs
            result = subprocess.run([
                "docker", "logs", f"{self.project_name}_auth-test-backend_1"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                # Try alternative container naming
                result = subprocess.run([
                    "docker", "logs", f"{self.project_name}-auth-test-backend-1"
                ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logs = result.stdout
                if "/api/auth/login" in logs or "POST" in logs:
                    self.log_success("Requests are reaching backend")
                    return TestResult(
                        passed=True,
                        message="Backend receives requests",
                        details={"log_sample": logs[-500:]}  # Last 500 chars
                    )
                else:
                    return TestResult(
                        passed=False,
                        message="No evidence of requests in backend logs",
                        details={"logs": logs[-500:]}
                    )
            else:
                return TestResult(
                    passed=False,
                    message="Could not retrieve backend logs"
                )
                
        except Exception as e:
            return TestResult(
                passed=False,
                message=f"Error checking backend logs: {e}"
            )

    async def cleanup(self):
        """Clean up test environment."""
        self.log_step("Cleaning up test environment...")
        try:
            subprocess.run([
                "docker-compose", "-f", str(self.compose_file),
                "-p", self.project_name, "down", "-v"
            ], capture_output=True)
            self.log_success("Cleanup complete")
        except Exception as e:
            self.log_warning(f"Cleanup warning: {e}")

    async def run_smoke_tests(self) -> bool:
        """Run all smoke tests."""
        print("🧪 Starting Phase 2: Runtime Auth Smoke Tests\n")
        
        try:
            # Setup
            if not await self.setup_test_environment():
                return False
            
            # Run tests
            tests = [
                ("Login Endpoint", self.test_login_endpoint),
                ("Request Routing", self.test_request_reaches_backend),
                ("Cookie Authentication", self.test_cookie_authentication),
            ]
            
            results = []
            token = None
            
            for test_name, test_func in tests:
                print(f"\n🔍 Running {test_name} test...")
                
                if test_name == "Token Validation" and not token:
                    # Skip token validation if we don't have a token
                    continue
                    
                if test_name == "Token Validation":
                    result = await test_func(token)
                else:
                    result = await test_func()
                
                results.append((test_name, result))
                
                if result.passed:
                    self.log_success(f"{test_name}: {result.message}")
                    
                    # Extract token for validation test
                    if test_name == "Login Endpoint" and result.details:
                        # Get full token from a fresh login
                        login_data = {"email": self.test_user["email"], "password": self.test_user["password"]}
                        async with aiohttp.ClientSession() as session:
                            async with session.post("http://localhost:8080/api/auth/login", json=login_data) as resp:
                                if resp.status == 200:
                                    data = await resp.json()
                                    token = data.get("access_token")
                else:
                    self.log_error(f"{test_name}: {result.message}")
                    if result.details:
                        print(f"   Details: {json.dumps(result.details, indent=2)}")
            
            # Run token validation test if we have a token
            if token:
                print(f"\n🔍 Running Token Validation test...")
                result = await self.test_token_validation(token)
                results.append(("Token Validation", result))
                
                if result.passed:
                    self.log_success(f"Token Validation: {result.message}")
                else:
                    self.log_error(f"Token Validation: {result.message}")
            
            # Summary
            passed_tests = sum(1 for _, result in results if result.passed)
            total_tests = len(results)
            
            print(f"\n📊 Phase 2 Summary:")
            print(f"✅ Passed: {passed_tests}/{total_tests}")
            print(f"❌ Failed: {total_tests - passed_tests}/{total_tests}")
            
            success = passed_tests == total_tests
            
            return success
            
        except Exception as e:
            self.log_error(f"Smoke test failed: {e}")
            return False
        finally:
            await self.cleanup()

def main():
    if len(sys.argv) != 2:
        print("Usage: python runtime_smoke_test.py <project_root>")
        sys.exit(1)
    
    project_root = sys.argv[1]
    tester = AuthSmokeTest(project_root)
    
    success = asyncio.run(tester.run_smoke_tests())
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()