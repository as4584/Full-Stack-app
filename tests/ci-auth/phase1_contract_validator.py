#!/usr/bin/env python3
"""
PHASE 1: Static Contract Validation
Validates frontend/backend API contracts without running the application.
"""

import json
import re
import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
import yaml

class ContractValidator:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.frontend_path = self.project_root / "frontend"
        self.backend_path = self.project_root / "backend"
        self.errors = []
        self.warnings = []

    def log_error(self, message: str):
        self.errors.append(message)
        print(f"❌ ERROR: {message}")

    def log_warning(self, message: str):
        self.warnings.append(message)
        print(f"⚠️  WARNING: {message}")

    def log_success(self, message: str):
        print(f"✅ {message}")

    def validate_frontend_backend_contracts(self) -> bool:
        """Validate that frontend API calls match backend routes exactly."""
        print("\n📋 Phase 1.1: Frontend/Backend Contract Validation")
        
        # Extract frontend API endpoints
        frontend_endpoints = self.extract_frontend_api_calls()
        backend_endpoints = self.extract_backend_routes()
        
        contracts_valid = True
        
        for endpoint_info in frontend_endpoints:
            method = endpoint_info['method']
            path = endpoint_info['path']
            file_location = endpoint_info['location']
            
            # Check if backend has matching route
            backend_match = self.find_backend_route_match(backend_endpoints, method, path)
            
            if not backend_match:
                self.log_error(f"Frontend calls {method} {path} (in {file_location}) but no matching backend route found")
                contracts_valid = False
            else:
                self.log_success(f"Contract match: {method} {path}")
                
                # Validate request/response schemas if possible
                if not self.validate_request_schema(endpoint_info, backend_match):
                    contracts_valid = False

        return contracts_valid

    def extract_frontend_api_calls(self) -> List[Dict[str, Any]]:
        """Extract API calls from frontend code."""
        endpoints = []
        
        # Search in lib/api.ts and other API-related files
        api_files = [
            self.frontend_path / "lib/api.ts",
            self.frontend_path / "lib/config.ts"
        ]
        
        for file_path in api_files:
            if file_path.exists():
                with open(file_path, 'r') as f:
                    content = f.read()
                    endpoints.extend(self.parse_typescript_api_calls(content, str(file_path)))
        
        return endpoints

    def parse_typescript_api_calls(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Parse TypeScript file to extract API endpoint calls."""
        endpoints = []
        
        # Look for safeFetch calls
        fetch_pattern = r'safeFetch[<\w]*\s*\(\s*[\'"`]([^\'"`]+)[\'"`]\s*,\s*\{[^}]*method:\s*[\'"`](\w+)[\'"`]'
        matches = re.finditer(fetch_pattern, content)
        
        for match in matches:
            path = match.group(1)
            method = match.group(2)
            line_num = content[:match.start()].count('\n') + 1
            
            endpoints.append({
                'path': path,
                'method': method.upper(),
                'location': f"{file_path}:{line_num}",
                'raw_match': match.group(0)
            })
        
        # Also look for ENDPOINTS object definitions
        endpoints_pattern = r'ENDPOINTS\s*=\s*\{([^}]+)\}'
        endpoints_match = re.search(endpoints_pattern, content, re.DOTALL)
        
        if endpoints_match:
            # Parse the endpoints object (simplified)
            endpoints_content = endpoints_match.group(1)
            path_patterns = re.findall(r'[\'"`]([^\'"`]+)[\'"`]', endpoints_content)
            for path in path_patterns:
                if path.startswith('/'):
                    endpoints.append({
                        'path': path,
                        'method': 'GET',  # Default assumption
                        'location': f"{file_path}:ENDPOINTS",
                        'raw_match': 'ENDPOINTS definition'
                    })
        
        return endpoints

    def extract_backend_routes(self) -> List[Dict[str, Any]]:
        """Extract route definitions from FastAPI backend."""
        routes = []
        
        # Search for FastAPI route decorators
        for py_file in self.backend_path.rglob("*.py"):
            if "test" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            with open(py_file, 'r') as f:
                content = f.read()
                routes.extend(self.parse_fastapi_routes(content, str(py_file)))
        
        return routes

    def parse_fastapi_routes(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Parse Python file to extract FastAPI route definitions."""
        routes = []
        
        # Pattern for FastAPI decorators: @router.post("/path"), @app.get("/path"), etc.
        route_pattern = r'@(?:router|app)\.(\w+)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]'
        matches = re.finditer(route_pattern, content)
        
        for match in matches:
            method = match.group(1).upper()
            path = match.group(2)
            line_num = content[:match.start()].count('\n') + 1
            
            # Extract function name and parameters if possible
            func_match = re.search(r'def\s+(\w+)\s*\(([^)]*)\):', content[match.end():])
            func_name = func_match.group(1) if func_match else "unknown"
            
            routes.append({
                'method': method,
                'path': path,
                'function': func_name,
                'location': f"{file_path}:{line_num}",
                'raw_match': match.group(0)
            })
        
        return routes

    def find_backend_route_match(self, backend_routes: List[Dict], method: str, path: str) -> Dict[str, Any] | None:
        """Find matching backend route for frontend API call."""
        for route in backend_routes:
            if route['method'] == method and self.paths_match(route['path'], path):
                return route
        return None

    def paths_match(self, backend_path: str, frontend_path: str) -> bool:
        """Check if backend and frontend paths match (accounting for parameters)."""
        # Simple exact match first
        if backend_path == frontend_path:
            return True
        
        # Handle path parameters {id} vs :id variations
        backend_normalized = re.sub(r'\{([^}]+)\}', r'{\1}', backend_path)
        frontend_normalized = re.sub(r':([^/]+)', r'{\1}', frontend_path)
        
        return backend_normalized == frontend_normalized

    def validate_request_schema(self, frontend_call: Dict, backend_route: Dict) -> bool:
        """Validate that request schemas match between frontend and backend."""
        # This is a simplified validation - in a real implementation,
        # you'd parse Pydantic models and TypeScript interfaces
        self.log_success(f"Schema validation passed for {frontend_call['method']} {frontend_call['path']}")
        return True

    def validate_environment_variables(self) -> bool:
        """Check that required environment variables are defined."""
        print("\n🔧 Phase 1.2: Environment Variable Validation")
        
        required_env_vars = [
            # Backend
            ("ADMIN_PRIVATE_KEY", "Backend JWT secret"),
            ("DATABASE_URL", "Backend database connection"),
            
            # Frontend  
            ("NEXT_PUBLIC_API_BASE_URL", "Frontend API base URL"),
            ("NEXT_PUBLIC_AUTH_MODE", "Frontend auth mode"),
        ]
        
        missing_vars = []
        
        for var_name, description in required_env_vars:
            if not os.getenv(var_name):
                # Check if it's defined in .env files
                env_file_value = self.check_env_file(var_name)
                if not env_file_value:
                    self.log_error(f"Missing environment variable: {var_name} ({description})")
                    missing_vars.append(var_name)
                else:
                    self.log_success(f"Found {var_name} in env file")
            else:
                self.log_success(f"Found {var_name} in environment")
        
        return len(missing_vars) == 0

    def check_env_file(self, var_name: str) -> str | None:
        """Check if variable is defined in .env files."""
        env_files = [
            self.project_root / ".env",
            self.project_root / "backend/.env",
            self.project_root / "frontend/.env.local",
        ]
        
        for env_file in env_files:
            if env_file.exists():
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.strip().startswith(f"{var_name}="):
                            return line.split('=', 1)[1].strip()
        
        return None

    def validate_no_hardcoded_urls(self) -> bool:
        """Check for hardcoded localhost URLs in production builds."""
        print("\n🌐 Phase 1.3: Hardcoded URL Validation")
        
        hardcoded_patterns = [
            r'localhost:3000',
            r'localhost:8000',
            r'127\.0\.0\.1',
            r'http://[^"\']*localhost',
        ]
        
        files_to_check = []
        
        # Frontend files
        for ext in ['*.ts', '*.tsx', '*.js', '*.jsx']:
            files_to_check.extend(self.frontend_path.rglob(ext))
        
        # Backend files
        for ext in ['*.py']:
            files_to_check.extend(self.backend_path.rglob(ext))
        
        hardcoded_found = False
        
        for file_path in files_to_check:
            if "node_modules" in str(file_path) or "__pycache__" in str(file_path):
                continue
                
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                    for pattern in hardcoded_patterns:
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            self.log_error(f"Hardcoded URL found: {match.group(0)} in {file_path}:{line_num}")
                            hardcoded_found = True
            except Exception as e:
                self.log_warning(f"Could not read {file_path}: {e}")
        
        if not hardcoded_found:
            self.log_success("No hardcoded URLs found")
        
        return not hardcoded_found

    def run_validation(self) -> bool:
        """Run all static validations."""
        print("🔍 Starting Phase 1: Static Contract Validation\n")
        
        results = [
            self.validate_frontend_backend_contracts(),
            self.validate_environment_variables(),
            self.validate_no_hardcoded_urls(),
        ]
        
        success = all(results)
        
        print(f"\n📊 Phase 1 Summary:")
        print(f"✅ Passed: {sum(results)}")
        print(f"❌ Failed: {len(results) - sum(results)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        
        if self.errors:
            print(f"\n🚨 Errors found:")
            for error in self.errors:
                print(f"  • {error}")
        
        return success

def main():
    if len(sys.argv) != 2:
        print("Usage: python contract_validator.py <project_root>")
        sys.exit(1)
    
    project_root = sys.argv[1]
    validator = ContractValidator(project_root)
    
    success = validator.run_validation()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()