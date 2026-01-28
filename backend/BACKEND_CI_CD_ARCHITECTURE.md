# Backend CI/CD Architecture Guide

## 🏗️ Multi-Repo Architecture

This document explains how CI/CD works for the **backend repository** in a multi-repo architecture.

### Repository Structure

```
Organization/
├── backend/                    ← THIS REPO (FastAPI backend)
│   ├── .github/workflows/      ← Backend CI configuration
│   ├── test_*.py               ← Backend E2E tests
│   └── backend_post_deploy_verify.sh
│
└── frontend/                   ← SEPARATE REPO (React/Next.js frontend)
    ├── .github/workflows/      ← Frontend CI (separate)
    └── ...
```

**Key Principles:**
- ✅ Backend repo is **self-contained** and independently deployable
- ✅ Backend CI validates **API correctness** without frontend dependencies
- ✅ Backend is the **source of truth** for API contracts
- ✅ Frontend repo has its own CI pipeline
- ⚠️ **Do NOT assume** frontend is deployed when backend is deployed

---

## 🎯 Backend CI Responsibilities

### What Backend CI DOES Validate

✅ **API Correctness**
- Settings persistence (`POST/PUT /api/business/me`)
- Calendar integration (`GET /oauth/google/start`, `/oauth/google/callback`)
- Twilio phone routing (`GET /api/business/me` phone fields)

✅ **Authentication**
- JWT token generation (`POST /api/auth/login`)
- Token validation (all protected endpoints)
- User/business resolution

✅ **Database Operations**
- Write operations persist correctly
- Read operations return consistent data
- Transactions commit properly

✅ **Error Handling**
- Structured JSON errors (not generic 500s)
- Proper HTTP status codes
- Graceful degradation when integrations unavailable

### What Backend CI Does NOT Validate

❌ Frontend build/bundle
❌ Frontend routing
❌ UI/UX behavior
❌ Browser compatibility
❌ Frontend-backend integration (that's a separate integration test)

---

## 🔄 Backend CI Pipeline

### Workflow File

Located at: `backend/.github/workflows/backend-e2e-tests.yml`

### Triggers

```yaml
on:
  pull_request:
    branches: [ main, master ]
  push:
    branches: [ main, master ]
  workflow_dispatch:
```

### Pipeline Steps

1. **Checkout Backend Code**
   - Pulls backend repo only
   - No frontend code needed

2. **Set Up Python 3.11**
   - Backend runtime environment
   - Install pip dependencies

3. **Install Backend Dependencies**
   ```bash
   pip install requests bcrypt
   ```
   - Minimal dependencies for API testing
   - No frontend build tools

4. **Run Full E2E Tests** (on push to main)
   - `test_settings_e2e.py` - Settings persistence API
   - `test_calendar_e2e.py` - Calendar OAuth API
   - `test_twilio_e2e.py` - Twilio phone API
   - ~30 seconds total

5. **Run Smoke Tests** (on pull requests)
   - Same tests with `SMOKE_TEST=true`
   - Run in parallel for speed
   - <10 seconds total

6. **Generate Test Summary**
   - Report results in GitHub UI
   - Fail pipeline on ANY non-zero exit

### Exit Code Discipline

```bash
# Every test MUST exit with these codes:
0 = API works correctly
1 = Authentication failed
2 = Fetch API failed
3 = Update/Integration API failed
4 = Persistence/State validation failed
5 = Unexpected error

# CI pipeline behavior:
if [ $EXIT_CODE -ne 0 ]; then
    echo "::error::API test failed - BLOCKING MERGE"
    exit $EXIT_CODE
fi
```

**CRITICAL**: Non-zero exit **ALWAYS blocks merge**. No exceptions.

---

## 🧪 Backend E2E Tests

### Design Philosophy

Backend E2E tests are **API-level integration tests** that:
- Make direct HTTP requests to backend endpoints
- Use real JWT authentication
- Verify database persistence
- Validate error responses
- **Do NOT require frontend code**

### Test Suite

#### 1. `test_settings_e2e.py`

**Purpose**: Verify settings persistence API

**Test Flow**:
```python
1. POST /api/auth/login → Get JWT token
2. GET /api/business/me → Fetch current settings
3. PUT /api/business/me → Update settings
4. GET /api/business/me → Verify persistence
```

**Exit Codes**:
- 0 = All API operations successful
- 1 = Auth API failed (JWT not returned)
- 2 = Fetch API failed (GET returned error)
- 3 = Update API failed (PUT returned error)
- 4 = Persistence failed (data not saved to database)
- 5 = Invalid response format

#### 2. `test_calendar_e2e.py`

**Purpose**: Verify calendar integration API

**Test Flow**:
```python
1. POST /api/auth/login → Get JWT token
2. GET /api/business/me → Fetch calendar state
3. GET /oauth/google/start → Check OAuth availability
   - If OAuth configured: Returns HTTP 302 redirect
   - If NOT configured: Returns HTTP 200 JSON error
4. Validate calendar state consistency
```

**Exit Codes**:
- 0 = Calendar API behaves correctly
- 1 = Auth API failed
- 2 = Fetch API failed
- 3 = OAuth endpoint returned unexpected response
- 4 = Calendar state inconsistent
- 5 = Unexpected error

**IMPORTANT**: Calendar API must NEVER return generic "Failed to fetch" errors. When OAuth is not configured:
```json
{
  "available": false,
  "error": "Google Calendar integration is not configured on this server",
  "detail": "Contact your administrator to enable Google Calendar integration"
}
```

#### 3. `test_twilio_e2e.py`

**Purpose**: Verify Twilio phone integration API

**Test Flow**:
```python
1. POST /api/auth/login → Get JWT token
2. GET /api/business/me → Fetch phone state
3. Validate phone number format (E.164)
4. Validate receptionist_enabled state
5. Check consistency (phone required if receptionist enabled)
```

**Exit Codes**:
- 0 = Twilio API working correctly
- 1 = Auth API failed
- 2 = Fetch API failed
- 3 = Phone number invalid
- 4 = Receptionist state inconsistent
- 5 = Unexpected error

---

## ⚡ Smoke Test Mode

### Purpose

Smoke tests provide **fast API verification** for:
- Post-deployment verification (<10s)
- PR quick checks
- Continuous health monitoring

### How It Works

**Enable via environment variable**:
```bash
SMOKE_TEST=true python3 test_settings_e2e.py --url https://api.example.com
```

**Or via CLI flag**:
```bash
python3 test_settings_e2e.py --smoke --url https://api.example.com
```

### What's Different in Smoke Mode?

**FULL MODE** (default):
- Validates all API response fields
- Checks field-by-field consistency
- Validates related state consistency
- Comprehensive diagnostics
- ~30 seconds for all 3 tests

**SMOKE MODE**:
- Validates API returns 200 OK
- Checks critical fields only
- Skips deep consistency checks
- Fast path validation
- ~8 seconds for all 3 tests

**What's STILL validated in smoke mode**:
- ✅ Authentication works
- ✅ API endpoints return 200
- ✅ Critical fields exist and correct type
- ✅ Database reads/writes function

**What's skipped in smoke mode**:
- ⏭️ Field-by-field value comparison
- ⏭️ Related field consistency checks
- ⏭️ Additional metadata validation

### When to Use Each Mode

| Scenario | Mode | Why |
|----------|------|-----|
| PR validation | Smoke | Fast feedback |
| Push to main | Full | Thorough validation |
| Post-deploy verification | Smoke | Quick health check |
| Weekly scheduled test | Full | Catch subtle regressions |
| Debugging API issues | Full | Comprehensive diagnostics |

---

## 🚀 Post-Deploy Verification

### Purpose

After deploying backend to production, verify API health before marking deployment as successful.

### Script

Located at: `backend/backend_post_deploy_verify.sh`

### How It Works

```bash
#!/bin/bash
# In your backend deployment script:

# 1. Deploy backend code
docker compose -f docker-compose.prod.yml up -d --build

# 2. Wait for backend to start
sleep 30

# 3. Verify backend API health
./backend_post_deploy_verify.sh https://api.production.com || {
    echo "❌ BACKEND API VERIFICATION FAILED"
    echo "Backend is NOT healthy - consider rollback"
    exit 1
}

echo "✅ Backend API verified and healthy"
```

### What It Does

1. **Checks Prerequisites**
   - Python 3 installed
   - `requests` module available
   - Test scripts exist

2. **Runs API Smoke Tests**
   - Settings API (`test_settings_e2e.py`)
   - Calendar API (`test_calendar_e2e.py`)
   - Twilio API (`test_twilio_e2e.py`)

3. **Reports Results**
   - Individual API status
   - Overall health assessment
   - Detailed logs at `/tmp/backend_*_smoke.log`

4. **Returns Exit Code**
   - 0 = All APIs healthy
   - 1-4 = Specific API failure
   - 5 = Script error

### Exit Code Handling

```bash
EXIT_CODE=$?

case $EXIT_CODE in
    0)
        echo "✅ Backend healthy"
        ;;
    1)
        echo "❌ Settings API broken"
        rollback_backend
        ;;
    2)
        echo "❌ Calendar API broken"
        rollback_backend
        ;;
    3)
        echo "❌ Twilio API broken"
        rollback_backend
        ;;
    4)
        echo "❌ Multiple APIs broken - CRITICAL"
        rollback_backend
        alert_team
        ;;
esac
```

---

## 🛡️ Backend API Error Handling Requirements

### Calendar Integration (CRITICAL)

❌ **BAD** (what we fixed):
```
User clicks "Connect Calendar"
→ Frontend makes request
→ Backend raises unhandled exception
→ User sees "Failed to fetch"
```

✅ **GOOD** (current implementation):
```
User clicks "Connect Calendar"
→ Frontend makes request
→ Backend returns structured JSON:
   {
     "available": false,
     "error": "Google Calendar integration is not configured",
     "detail": "Contact your administrator"
   }
→ User sees clear message
```

### Backend API Contract

**When OAuth IS configured**:
```http
GET /oauth/google/start?business_id=123

HTTP/1.1 302 Found
Location: https://accounts.google.com/o/oauth2/v2/auth?...
```

**When OAuth NOT configured**:
```http
GET /oauth/google/start?business_id=123

HTTP/1.1 200 OK
Content-Type: application/json

{
  "available": false,
  "error": "Google Calendar integration is not configured on this server",
  "detail": "Contact your administrator to enable Google Calendar integration"
}
```

### General Error Response Format

All backend errors MUST return structured JSON:

```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "detail": "Additional context (optional)",
  "action": "suggested_action (optional)"
}
```

**HTTP Status Codes**:
- `400` - Client error (invalid request)
- `401` - Authentication required
- `403` - Forbidden (valid auth, insufficient permissions)
- `404` - Resource not found
- `503` - Service unavailable (integration down)
- **Never use `500` for expected error conditions**

---

## 📊 CI/CD Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│  BACKEND REPOSITORY (This Repo)                                 │
└─────────────────────────────────────────────────────────────────┘

Developer creates PR
       │
       ▼
┌──────────────────┐
│ GitHub Actions   │
│ (Backend CI)     │
└──────────────────┘
       │
       ├─> Run Settings E2E Test (API)
       ├─> Run Calendar E2E Test (API)
       ├─> Run Twilio E2E Test (API)
       └─> Run Smoke Tests (parallel)
       │
       ▼
   Tests pass? ─────> NO ──> ❌ Block merge
       │                        │
      YES                       │
       │                        ▼
       ▼                   Fix API issue
   Merge to main           Rerun CI
       │
       ▼
   Deploy backend to production
       │
       ├─> docker compose up -d --build
       ├─> Wait 30 seconds
       │
       ▼
   Run post-deploy verification
       │
       └─> ./backend_post_deploy_verify.sh
       │
       ▼
   Tests pass? ────> NO ──> ❌ Rollback backend
       │                        │
      YES                       │
       │                        ▼
       ▼                   Alert team
   ✅ Backend healthy       Fix ASAP


┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND REPOSITORY (Separate Repo)                            │
└─────────────────────────────────────────────────────────────────┘

Developer creates PR
       │
       ▼
   Frontend CI (separate workflow)
       │
       ├─> Lint/TypeScript checks
       ├─> Build frontend
       ├─> Frontend unit tests
       └─> (optional) Frontend E2E tests
       │
       ▼
   Tests pass? ──> Merge to main ──> Deploy frontend

Note: Frontend deployment is INDEPENDENT of backend deployment
```

---

## 🔧 Adding New Backend E2E Tests

### Step 1: Create Test Script

Create `backend/test_<feature>_e2e.py`:

```python
#!/usr/bin/env python3
"""
<Feature> E2E Test for Backend API
"""
import os
import sys
import requests

SMOKE_TEST_MODE = os.getenv('SMOKE_TEST', '').lower() in ('true', '1', 'yes')

class FeatureE2ETest:
    def __init__(self, base_url: str, smoke_mode: bool = False):
        self.base_url = base_url.rstrip('/')
        self.smoke_mode = smoke_mode
        self.jwt_token = None
    
    def test_auth(self):
        """Test authentication API"""
        # ... make API request ...
        # Exit with code 1 if fails
    
    def test_feature_api(self):
        """Test feature-specific API endpoint"""
        # ... make API request ...
        # Exit with code 2-4 based on failure type
    
    def run_full_test(self):
        """Run all tests"""
        self.test_auth()
        self.test_feature_api()
        return 0  # Success

# Exit codes: 0=pass, 1-5=fail
```

### Step 2: Add to CI Workflow

Edit `backend/.github/workflows/backend-e2e-tests.yml`:

```yaml
- name: Run Feature E2E Test
  env:
    API_URL: ${{ secrets.PROD_API_URL }}
  run: |
    python3 test_feature_e2e.py --url "$API_URL"
    EXIT_CODE=$?
    if [ $EXIT_CODE -ne 0 ]; then
      echo "::error::Feature API test failed"
      exit $EXIT_CODE
    fi
```

### Step 3: Add to Post-Deploy Script

Edit `backend/backend_post_deploy_verify.sh`:

```bash
run_api_smoke_test "Feature" "test_feature_e2e.py" "exit_feature"
```

### Step 4: Test Locally

```bash
# Full test
python3 test_feature_e2e.py --url https://api.staging.com

# Smoke test
SMOKE_TEST=true python3 test_feature_e2e.py --url https://api.staging.com
```

---

## 🐛 Troubleshooting

### CI Fails with "Tests not found"

**Symptom**: GitHub Actions can't find test scripts

**Cause**: Tests are in wrong directory or not committed

**Fix**:
```bash
cd backend/
ls -la test_*.py  # Verify tests exist
git add test_*.py
git commit -m "Add E2E tests"
git push
```

### API Tests Fail Locally but Pass in CI

**Symptom**: Tests pass in GitHub Actions but fail on your machine

**Possible Causes**:
1. Using wrong API URL
2. Local backend not running
3. Database state different

**Fix**:
```bash
# Ensure you're testing the right environment
python3 test_settings_e2e.py --url https://api.staging.com

# Not localhost (unless backend is running locally)
```

### Calendar API Returns "Failed to fetch"

**Symptom**: Frontend shows "Failed to fetch" for calendar

**Root Cause**: Backend returning unstructured error

**Fix**:
1. Check backend logs for exception stack trace
2. Ensure OAuth endpoint returns structured JSON when unavailable
3. Verify `GOOGLE_CLIENT_ID` is set (or handle gracefully if not)
4. Run `test_calendar_e2e.py` to verify API behavior

### Post-Deploy Verification Always Fails

**Symptom**: `backend_post_deploy_verify.sh` exits non-zero

**Possible Causes**:
1. Backend not fully started (increase sleep time)
2. Environment variables not set
3. Test credentials invalid

**Debug**:
```bash
# Check backend logs
docker compose logs backend --tail=50

# Run tests manually with verbose output
SMOKE_TEST=true python3 test_settings_e2e.py --url https://api.production.com

# Check test logs
cat /tmp/backend_Settings_smoke.log
```

---

## 📚 Best Practices

### 1. Backend is Source of Truth

✅ **DO**: Validate API contracts in backend CI
✅ **DO**: Ensure backend is independently deployable
✅ **DO**: Return structured errors from all endpoints

❌ **DON'T**: Assume frontend is deployed when backend is deployed
❌ **DON'T**: Rely on frontend for API validation
❌ **DON'T**: Return generic 500 errors for expected conditions

### 2. Exit Code Discipline

✅ **DO**: Use specific exit codes (0=pass, 1-5=fail types)
✅ **DO**: Block merge on ANY non-zero exit
✅ **DO**: Provide clear error messages

❌ **DON'T**: Allow silent failures
❌ **DON'T**: Ignore exit codes
❌ **DON'T**: Continue on error

### 3. Integration Optional

✅ **DO**: Make integrations (calendar, Twilio) optional
✅ **DO**: Return clear errors when integration unavailable
✅ **DO**: Allow core functionality without integrations

❌ **DON'T**: Require all integrations to be configured
❌ **DON'T**: Block settings save if calendar unavailable
❌ **DON'T**: Return 500 errors for missing integration config

### 4. Test Maintenance

✅ **DO**: Run tests locally before pushing
✅ **DO**: Update tests when API changes
✅ **DO**: Keep tests fast (smoke mode for quick checks)

❌ **DON'T**: Skip testing "small" API changes
❌ **DON'T**: Disable tests that fail
❌ **DON'T**: Hardcode test data that will become stale

---

## 📖 Related Documentation

- **E2E Test Guide**: `backend/E2E_TEST_GUIDE.md` - How to run tests
- **Calendar Fix Report**: `backend/CALENDAR_FIX_REPORT.md` - Root cause analysis
- **Settings Bug Fix**: `backend/SETTINGS_BUG_FIX_REPORT.md` - Previous fix

---

## 🆘 Support

For questions about backend CI/CD:
1. Check this guide first
2. Review test output logs
3. Check backend logs (`docker compose logs backend`)
4. Verify API contracts with manual curl/Postman
5. Run tests locally to reproduce issue

**Remember**: Backend CI validates **API correctness only**. Frontend behavior is validated in frontend repo's CI.
