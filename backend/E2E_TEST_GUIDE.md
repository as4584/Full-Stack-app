# E2E Test Suite Guide

## Overview

Comprehensive end-to-end testing suite for the AI Receptionist SaaS platform. Tests verify critical functionality end-to-end including settings persistence, calendar integration, and phone routing.

## Test Suite

### 1. Settings Persistence (`test_settings_e2e.py`)
Verifies settings can be saved and retrieved correctly for all users.

**Tests:**
- JWT authentication
- Fetch current business settings
- Update settings with test data
- Verify changes persisted to database

### 2. Calendar Integration (`test_calendar_e2e.py`)
Tests Google Calendar OAuth integration flow.

**Tests:**
- OAuth availability check
- Calendar connection state
- Proper error handling when OAuth not configured
- State consistency validation

### 3. Twilio Phone Integration (`test_twilio_e2e.py`)
Validates phone number assignment and receptionist routing.

**Tests:**
- Phone number validation (E.164 format)
- Receptionist enabled state
- State consistency (phone required for receptionist)
- Business info completeness for receptionist

## Running Tests

### Basic Usage

```bash
cd /home/lex/lexmakesit/backend

# Run individual tests
python3 test_settings_e2e.py --url https://receptionist.lexmakesit.com
python3 test_calendar_e2e.py --url https://receptionist.lexmakesit.com
python3 test_twilio_e2e.py --url https://receptionist.lexmakesit.com

# Run all tests (production verification)
./run_all_e2e_tests.sh https://receptionist.lexmakesit.com
```

### Smoke Test Mode (FAST)

Smoke tests provide fast verification by skipping deep field validation. Ideal for:
- Post-deployment verification
- PR quick checks
- Continuous monitoring

```bash
# Environment variable (recommended)
SMOKE_TEST=true python3 test_settings_e2e.py --url https://receptionist.lexmakesit.com
SMOKE_TEST=true python3 test_calendar_e2e.py --url https://receptionist.lexmakesit.com
SMOKE_TEST=true python3 test_twilio_e2e.py --url https://receptionist.lexmakesit.com

# CLI flag (alternative)
python3 test_settings_e2e.py --smoke --url https://receptionist.lexmakesit.com
python3 test_calendar_e2e.py --smoke --url https://receptionist.lexmakesit.com
python3 test_twilio_e2e.py --smoke --url https://receptionist.lexmakesit.com

# All tests in smoke mode
cd /home/lex/lexmakesit
./scripts/deploy_verify.sh https://receptionist.lexmakesit.com
```

**Smoke Mode Differences:**
- ✅ Authentication still verified
- ✅ API responses still checked
- ✅ Critical fields still validated
- ⏭️ Deep field comparisons skipped
- ⏭️ Consistency checks simplified
- ⚡ Completes in <10 seconds (vs ~30 seconds full mode)

### When to Use Each Mode

**Full E2E Tests (Default):**
- Before production releases
- After major backend changes
- When debugging persistence issues
- Weekly scheduled verification

**Smoke Tests:**
- After every deployment (automated)
- On every PR (GitHub Actions)
- Continuous health monitoring
- Quick sanity checks

## Exit Codes

All tests follow consistent exit code discipline for CI/CD:

### Settings Test (`test_settings_e2e.py`)
- `0` - All tests passed ✅
- `1` - Authentication failed
- `2` - Fetch settings failed
- `3` - Update settings failed
- `4` - Persistence verification failed
- `5` - Invalid response data

### Calendar Test (`test_calendar_e2e.py`)
- `0` - All tests passed ✅
- `1` - Authentication failed
- `2` - Fetch calendar state failed
- `3` - OAuth availability check failed
- `4` - Calendar state inconsistent
- `5` - Unexpected error

### Twilio Test (`test_twilio_e2e.py`)
- `0` - All tests passed ✅
- `1` - Authentication failed
- `2` - Fetch phone state failed
- `3` - Phone number invalid
- `4` - Receptionist state inconsistent
- `5` - Unexpected error

## Test Configuration

All tests use consistent production credentials:
- **Email**: `thegamermasterninja@gmail.com`
- **Password**: `Alexander1221`
- **API Base URL**: `https://receptionist.lexmakesit.com` (configurable)

### Settings Test Data
- Business Name: "Lex Makes It"
- Industry: "Software Development, Website Development"
- Services: "Software Development, Website Development"
- Hours: "Monday-Friday, 12:00 PM - 10:00 PM"
- Description: "We provide software development and website development services. For more information, visit lexmakesit.com."

## Understanding Test Output

### Success Example

```
╔════════════════════════════════════════════════════════════════════╗
║                  ✅ ALL TESTS PASSED                                ║
╚════════════════════════════════════════════════════════════════════╝
```

### Failure Example

```
❌ FAIL | Update Settings: Failed to update settings (HTTP 500)
Details: {
  "detail": "Cannot import SessionLocal from database module"
}
```

## Troubleshooting

### Test fails at PHASE 1 (Authentication)
- Check credentials are correct
- Verify user exists in database
- Confirm JWT secret (ADMIN_PRIVATE_KEY) is configured

### Test fails at PHASE 2 (Fetch Settings)
- Check user has associated business record
- Verify `/api/business/me` endpoint is working
- Confirm auth middleware resolves user correctly

### Test fails at PHASE 3 (Update Settings)
- Check backend logs for exceptions
- Verify database is writable
- Confirm no required fields are missing

### Test fails at PHASE 4 (Persistence)
- Database commit may have failed
- Check for transaction rollbacks
- Verify no field validation errors

## CI/CD Integration

### GitHub Actions (Automated)

The E2E test suite runs automatically on every push and pull request via `.github/workflows/e2e-tests.yml`:

**On Push to main/master:**
- Runs full E2E tests (all 3 test suites)
- Blocks merge if any test returns non-zero exit code
- Reports results in GitHub UI

**On Pull Request:**
- Runs smoke tests (fast verification in <30 seconds)
- Provides quick feedback before merge
- Fails loudly with error annotations

**Workflow Configuration:**
```yaml
name: E2E Tests
on:
  pull_request:
    branches: [ main, master ]
  push:
    branches: [ main, master ]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Run Settings E2E Test
        run: python3 test_settings_e2e.py --url "$API_URL"
      
      - name: Run Calendar E2E Test
        run: python3 test_calendar_e2e.py --url "$API_URL"
      
      - name: Run Twilio E2E Test
        run: python3 test_twilio_e2e.py --url "$API_URL"
      
      - name: Run Smoke Tests (PR only)
        if: github.event_name == 'pull_request'
        env:
          SMOKE_TEST: "true"
        run: |
          python3 test_settings_e2e.py --url "$API_URL" &
          python3 test_calendar_e2e.py --url "$API_URL" &
          python3 test_twilio_e2e.py --url "$API_URL" &
          wait
```

### Post-Deploy Verification (Automated)

Add to your deployment script to run smoke tests automatically after deploy:

```bash
#!/bin/bash
# deploy.sh

# 1. Deploy code
docker compose -f docker-compose.prod.yml up -d --build

# 2. Wait for services to start
echo "Waiting for services to stabilize..."
sleep 30

# 3. Run post-deploy verification
./scripts/deploy_verify.sh || {
    echo "❌ Post-deploy verification FAILED"
    echo "Consider rolling back deployment"
    exit 1
}

echo "✅ Deployment verified and healthy"
```

**What `deploy_verify.sh` does:**
- Runs all 3 smoke tests sequentially
- Reports individual test results
- Returns exit code 0 only if ALL tests pass
- Provides clear error messages if any test fails
- Logs output to `/tmp/*_smoke.log` for debugging

### Manual Deployment Checklist

```bash
# 1. Deploy code
./deploy_production.sh

# 2. Wait for services to start
sleep 30

# 3. Run verification script
./scripts/deploy_verify.sh https://receptionist.lexmakesit.com

# 4. Check exit code
if [ $? -eq 0 ]; then
    echo "✅ Deployment verified"
else
    echo "❌ Verification failed - check logs"
fi
```

### Continuous Monitoring (Optional)

Run smoke tests on a schedule to detect issues proactively:

```bash
# Add to crontab for hourly health checks
0 * * * * cd /opt/ai-receptionist && SMOKE_TEST=true ./scripts/deploy_verify.sh
```

## Safety Features

- ✅ **Idempotent** - Can be run multiple times safely
- ✅ **No data corruption** - Only updates test user's data
- ✅ **No secret logging** - JWT tokens masked in logs
- ✅ **Clear diagnostics** - Fails loudly with actionable errors
- ✅ **Production-safe** - Uses real auth, no bypasses

## Architecture

The test exercises the complete stack:
```
Test Script (Python)
    ↓
HTTPS Request
    ↓
Caddy Reverse Proxy
    ↓
FastAPI Backend
    ↓
JWT Auth Middleware
    ↓
Business Endpoints
    ↓
PostgreSQL Database
```

## What Was Fixed

### Bug: ImportError in auditor.py

**Symptom:** Settings save returned HTTP 500 with ImportError

**Root Cause:** `auditor.py` tried to import `SessionLocal` directly, but the database module refactored to use `get_session_local()` factory function

**Fix:** Updated import in `auditor.py`:
```python
# Before (broken)
from ai_receptionist.core.database import SessionLocal
db = SessionLocal()

# After (fixed)
from ai_receptionist.core.database import get_session_local
SessionLocal = get_session_local()
db = SessionLocal()
```

**Impact:** All users can now save settings. Description/FAQ updates trigger background audit without blocking save.

## Maintenance

### Updating Test Data

Edit `TEST_SETTINGS` in `test_settings_e2e.py`:

```python
TEST_SETTINGS = {
    "name": "Your Business Name",
    "industry": "Your Industry",
    # ... etc
}
```

### Adding Test User

```bash
# Generate password hash
python3 -c "import bcrypt; print(bcrypt.hashpw(b'password', bcrypt.gensalt()).decode())"

# Insert user
ssh Innovation "cd /opt/ai-receptionist && docker compose -f docker-compose.prod.yml exec -T postgres psql -U ai_receptionist_user -d ai_receptionist -c \"INSERT INTO users (email, password_hash, full_name, is_active, is_verified, created_at) VALUES ('email@example.com', '<hash>', 'Full Name', true, true, NOW());\""
```

## Related Files

- `test_settings_e2e.py` - Main test script
- `ai_receptionist/app/main.py` - Settings endpoints (`/api/business/me`)
- `ai_receptionist/services/voice/auditor.py` - Background audit system
- `ai_receptionist/core/database.py` - Database session management
- `frontend/lib/api.ts` - Frontend API client

## Contact

For issues or questions about this test:
1. Check backend logs: `docker compose logs app`
2. Review this documentation
3. Run test with `--verbose` flag
4. Contact platform maintainer
