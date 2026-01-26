# 🔐 Authentication Reliability CI System

A comprehensive CI test suite that ensures authentication (login/signup/session) never silently breaks across frontend, backend, and proxy layers.

## 🎯 Purpose

This system prevents authentication regressions by running automated tests on every:
- Pull Request
- Merge to main  
- Deployment

## 🏗️ Architecture

The test suite consists of 4 phases:

### Phase 1: Static Contract Validation ✅
**No Docker required** - Validates code contracts without running services
- ✅ Frontend API calls match backend routes exactly
- ✅ HTTP methods and request schemas match
- ✅ Environment variables are defined
- ✅ No hardcoded localhost URLs in production builds

### Phase 2: Runtime Auth Smoke Test 🧪  
**Docker required** - End-to-end authentication testing
- ✅ Spins up backend, frontend, and proxy via Docker Compose
- ✅ POST /api/auth/login with test user
- ✅ Verifies 200 status, token returned, token valid
- ✅ Confirms requests reach backend (log evidence)
- ✅ Tests cookie-based authentication

### Phase 3: CORS & Transport Check 🌐
**Tests cross-origin and transport layer**
- ✅ OPTIONS preflight requests work
- ✅ Valid origins allowed, invalid origins blocked  
- ✅ credentials=include works correctly
- ✅ HTTPS/HTTP consistency
- ✅ Proxy routing functions

### Phase 4: Regression Snapshot 📸
**Baseline comparison system**
- ✅ Captures request/response payloads
- ✅ Compares against golden snapshots
- ✅ Alerts on breaking changes
- ✅ Generates diff reports

## 🚀 Quick Start

### Run All Tests
```bash
cd tests/ci-auth
./run_auth_tests.sh
```

### Run Individual Phases
```bash
./run_auth_tests.sh phase1          # Static validation only
./run_auth_tests.sh phase2          # Runtime smoke test only  
./run_auth_tests.sh phase3          # CORS/transport only
./run_auth_tests.sh phase4          # Regression snapshot only
```

### Create New Baseline
```bash
./run_auth_tests.sh phase4 --create-baseline
```

### Get Help
```bash
./run_auth_tests.sh --help
```

## 📋 Prerequisites

### Local Development
- Python 3.8+
- Docker & Docker Compose
- curl (for manual testing)

### CI Environment
- Ubuntu runner
- Python dependencies auto-installed
- Docker images pre-built

## 🔧 Configuration

### Environment Variables
Required for testing:
```bash
# Backend
DATABASE_URL=sqlite:///app/test_auth.db
ADMIN_PRIVATE_KEY=your-jwt-secret

# Frontend  
NEXT_PUBLIC_API_BASE_URL=http://backend:8000
NEXT_PUBLIC_AUTH_MODE=cookie
```

### Test User
The system creates/uses this test account:
```json
{
  "email": "test@example.com",
  "password": "TestPassword123!",
  "business_name": "Test Business"
}
```

## 📊 CI Integration

### GitHub Actions Workflow
Located at: `.github/workflows/auth-ci.yml`

**Triggers:**
- Pull requests to main/develop
- Pushes to main branch
- Manual workflow dispatch

**Matrix Strategy:**
Runs all 4 phases in parallel for faster feedback

**Artifacts:**
- Test result snapshots
- Comparison reports  
- Debug logs

### Success Criteria
✅ **PASS**: All phases pass - safe to merge/deploy
❌ **FAIL**: Any phase fails - blocks merge/deployment

## 🔍 Troubleshooting

### Phase 1 Failures
- **Contract mismatch**: Frontend API call doesn't match backend route
- **Missing env vars**: Required environment variables not defined
- **Hardcoded URLs**: localhost URLs found in code

### Phase 2 Failures  
- **Services won't start**: Docker/compose issues
- **Login fails**: Authentication logic broken
- **Network error**: "failed to fetch" - transport layer issues

### Phase 3 Failures
- **CORS blocked**: Origin not allowed or preflight issues
- **Credentials issues**: Cookie auth not working cross-origin
- **Proxy routing**: Requests not reaching backend

### Phase 4 Failures
- **Breaking changes**: Auth behavior differs from baseline
- **Missing tests**: Previously tested endpoints no longer tested
- **Schema changes**: Request/response format changes

## 📁 File Structure

```
tests/ci-auth/
├── run_auth_tests.sh              # Main test runner
├── phase1_contract_validator.py   # Static validation
├── phase2_runtime_smoke_test.py   # E2E auth testing
├── phase3_cors_transport_test.py  # CORS/transport testing
├── phase4_regression_snapshot.py  # Regression detection
├── docker-compose.ci.yml          # Test environment
├── caddy/Caddyfile.ci             # Proxy config
├── snapshots/                     # Baseline data
│   ├── auth_baseline.json         # Golden snapshots
│   └── comparison_report_*.json   # Diff reports
└── quick_test.py                  # Quick validation
```

## 🎯 Success Examples

### All Tests Pass
```
🔐 AI Receptionist Auth CI Test Suite
========================================

🔍 PHASE 1: Static Contract Validation
✅ Contract match: POST /api/auth/login
✅ Found ADMIN_PRIVATE_KEY in environment
✅ No hardcoded URLs found
✅ Phase 1: PASSED

🧪 PHASE 2: Runtime Auth Smoke Tests  
✅ All services are healthy
✅ Test user created
✅ Login endpoint: Login successful
✅ Cookie authentication works
✅ Phase 2: PASSED

🌐 PHASE 3: CORS & Transport Check
✅ CORS preflight works correctly
✅ Origin validation works correctly
✅ Credentials handling works correctly
✅ Phase 3: PASSED

📸 PHASE 4: Regression Snapshot Test
✅ Captured 2 snapshots
✅ No regressions detected  
✅ Phase 4: PASSED

📊 FINAL SUMMARY
================
✅ phase1: PASSED
✅ phase2: PASSED  
✅ phase3: PASSED
✅ phase4: PASSED

🎉 ALL TESTS PASSED - Authentication reliability verified!
```

## 🚨 Failure Examples

### Contract Mismatch (Phase 1)
```
❌ ERROR: Frontend calls POST /api/auth/signin but no matching backend route found
❌ ERROR: Missing environment variable: ADMIN_PRIVATE_KEY
❌ Phase 1: FAILED
```

### Runtime Failure (Phase 2)
```
❌ Login Endpoint: Login failed with status 500
   Details: {
     "status": 500,
     "response": "Internal Server Error"
   }
❌ Phase 2: FAILED
```

### Regression Detected (Phase 4)
```
🚨 Breaking changes detected:
  • login_endpoint: 3 differences
    - changed: response.user.business_id
    - removed: response.token_type
    - added: response.expires_in
❌ Phase 4: FAILED - Regression detected
```

## 🔄 Maintenance

### Update Baseline
When auth behavior legitimately changes:
```bash
./run_auth_tests.sh phase4 --create-baseline
git add tests/ci-auth/snapshots/auth_baseline.json
git commit -m "Update auth regression baseline"
```

### Add New Tests
1. Extend relevant phase script
2. Update test matrix in GitHub Actions
3. Update documentation

### Debug Issues
```bash
# Verbose output
./run_auth_tests.sh --verbose

# Keep containers running
./run_auth_tests.sh --skip-cleanup

# Manual inspection
cd tests/ci-auth
docker-compose -f docker-compose.ci.yml up
```

## 🎯 Goals Achieved

✅ **Never Silent Breaks**: Comprehensive testing catches auth issues
✅ **Multi-Layer Validation**: Static, runtime, transport, and regression testing  
✅ **Fast Feedback**: Parallel execution and clear error messages
✅ **CI Integration**: Blocks bad merges and deployments
✅ **Maintainable**: Clear documentation and modular design