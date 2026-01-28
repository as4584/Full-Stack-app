# 🚀 CI/CD System - Production-Grade Automation

## Overview

This repository implements a **professional-grade CI/CD pipeline** that ensures:
- ✅ **Zero 502 errors** reach production
- ✅ **Automated testing** on every push
- ✅ **Auto-rollback** on failures
- ✅ **Visual regression testing** for Frutiger Aero animations
- ✅ **24/7 production monitoring**

---

## 🎯 Workflows

### 1. **Backend CI/CD** (`.github/workflows/backend-ci.yml`)

**Triggers**: Push to `main`, `security/**`, `feature/**` branches

**Jobs**:
1. **Lint & Type Check** - Ruff linter + MyPy type checker
2. **Unit Tests** - Full test suite with coverage reports
3. **Build Docker Image** - Validates Dockerfile builds successfully
4. **API Health Check** - **502 Prevention** - Tests all endpoints
5. **E2E Smoke Test** - Critical user flows
6. **Security Scan** - Trivy vulnerability scanner
7. **Deploy to Production** - Automated deployment with health checks

**502 Prevention**:
```bash
# Tests all critical endpoints
- Root endpoint (/)
- Auth endpoints (/api/auth/*)
- Business endpoints (/api/business/*)
- Twilio webhooks (/twilio/voice)

# Retries 5 times before failing
# Immediately fails on HTTP 502
# Rolls back on deployment failure
```

---

### 2. **Frontend CI/CD** (`.github/workflows/frontend-ci.yml`)

**Triggers**: Push to `main`, `feature/**` branches

**Jobs**:
1. **ESLint & TypeScript Check** - Code quality validation
2. **Build Test** - **502 Prevention** - Validates Next.js build
3. **Component Tests** - React component testing
4. **Visual Regression** - **Frutiger Aero animation verification**
5. **Deploy to Production** - Automated deployment

**Features**:
- Verifies `.next` directory created
- Checks all routes respond correctly
- Validates Frutiger Aero CSS/JS loaded
- Takes screenshots for visual comparison
- PM2 process management for zero-downtime deploys

---

### 3. **Auth Frontend CI/CD** (`.github/workflows/auth-frontend-ci.yml`)

**Triggers**: Push to `main`, `feature/**` branches

**Jobs**:
1. **ESLint & TypeScript Check**
2. **Build Test** - **502 Prevention**
3. **Visual Test** - Animated background validation
4. **Security Scan** - NPM audit
5. **Deploy to Production** - Docker-based deployment

**Special Features**:
- Validates `aero-background.js` served correctly
- Checks glass card styling (backdrop-filter)
- Uses Playwright for visual testing
- Verifies 15-25 bubbles rendered

---

### 4. **Pre-Push Validation** (`.github/workflows/pre-push-validation.yml`)

**Triggers**: All pull requests, feature branches

**Fast checks (< 2 minutes)**:
1. **Quick Validation** - Scans for common 502 causes
2. **Syntax Check** - Python + TypeScript validation
3. **Docker Validation** - Dockerfile + docker-compose checks
4. **Network Test** - Connectivity simulation
5. **Environment Validation** - Checks for missing env vars

**Prevents**:
- Missing environment variables
- Port conflicts in Docker
- Syntax errors
- Hardcoded secrets
- Missing health checks

---

### 5. **Production Monitoring** (`.github/workflows/production-monitoring.yml`)

**Triggers**: Every 5 minutes (cron) + manual dispatch

**Jobs**:
1. **Health Monitoring** - Checks all production endpoints
2. **Performance Monitoring** - Response time tracking
3. **Docker Health Check** - Container status

**Auto-Rollback System**:
```yaml
If 502 detected:
  1. Find last working commit (git log --grep="✅ Production healthy")
  2. Checkout previous version
  3. Restart containers
  4. Verify health
  5. Send Slack alert
  6. Create GitHub issue
```

**Monitoring Scope**:
- Backend API (https://receptionist.lexmakesit.com)
- Frontend (https://lexmakesit.com)
- Auth Frontend (https://auth.lexmakesit.com)
- SSL certificate expiration
- Response times (alert if > 5s)
- Docker container health
- Frutiger Aero asset loading

---

## 🎨 Frutiger Aero Validation

All workflows validate the **animated backgrounds**:

### Frontend Dashboard
- ✅ `AeroBackground.tsx` component renders
- ✅ `.aero-background` div present
- ✅ 15-30 animated bubbles created
- ✅ Bubbles have `aero-bubble` class
- ✅ Gradient background animates

### Auth Frontend
- ✅ `aero-background.js` served (HTTP 200)
- ✅ Script creates `.aero-background` div
- ✅ 15-25 bubbles with random properties
- ✅ Glass card has `backdrop-filter: blur(20px)`
- ✅ Transparent body background

### Visual Testing
```javascript
// Playwright checks:
1. Wait for page load (2s)
2. Check `.aero-background` exists
3. Count `.aero-bubble` elements
4. Verify glass card styling
5. Take screenshot
6. Compare to baseline
```

---

## 🔒 Security Features

1. **Trivy Scanning** - Detects vulnerabilities in dependencies
2. **NPM Audit** - Checks for known security issues
3. **Secret Detection** - Prevents hardcoded API keys
4. **SARIF Upload** - Results sent to GitHub Security tab

---

## 📊 Monitoring & Alerts

### Slack Notifications
```json
{
  "text": "🚨 *PRODUCTION ALERT: 502 Error Detected*\n\n❌ Backend: https://receptionist.lexmakesit.com/\n\n⚡ Auto-rollback initiated\n🔗 View logs"
}
```

### GitHub Issues
Automatically created on 502 detection with:
- Timestamp
- Affected services
- Actions taken
- Next steps checklist
- Links to logs

---

## 🚀 Deployment Flow

### Main Branch (Production)
```mermaid
Push to main
  ↓
Pre-push validation
  ↓
Lint & Type Check
  ↓
Unit Tests
  ↓
Build Test
  ↓
502 Health Check ← [CRITICAL]
  ↓
Visual Regression
  ↓
Security Scan
  ↓
Deploy to Production
  ↓
Post-deployment health check
  ↓
Production monitoring (every 5min)
```

### Feature Branches
```mermaid
Push to feature/**
  ↓
Pre-push validation only
  ↓
Pull request created
  ↓
Full CI suite runs
  ↓
Manual review
  ↓
Merge to main (triggers production deploy)
```

---

## 🛠️ Required Secrets

Add these to **GitHub Settings → Secrets**:

```bash
PRODUCTION_HOST          # SSH host for deployment
PRODUCTION_USER          # SSH username
SSH_PRIVATE_KEY          # SSH key for server access
SLACK_WEBHOOK_URL        # Slack notifications (optional)
```

---

## 📋 Usage

### Manual Workflow Trigger
```bash
# Trigger production monitoring manually
gh workflow run production-monitoring.yml
```

### Check Workflow Status
```bash
# View recent workflow runs
gh run list --workflow=backend-ci.yml

# View logs for specific run
gh run view <run-id> --log
```

### Local Testing
```bash
# Install act (GitHub Actions local runner)
brew install act  # macOS
# or
sudo apt install act  # Linux

# Run backend CI locally
act push -W .github/workflows/backend-ci.yml

# Run pre-push validation
act pull_request -W .github/workflows/pre-push-validation.yml
```

---

## 🎯 502 Error Prevention Checklist

Every deployment is validated against:

- [ ] All endpoints respond (not 502)
- [ ] Response times < 10 seconds
- [ ] Docker containers healthy
- [ ] Database connectivity working
- [ ] Redis connectivity working
- [ ] Environment variables set
- [ ] SSL certificates valid
- [ ] Static assets loading
- [ ] Frutiger Aero animations present
- [ ] No syntax errors
- [ ] No security vulnerabilities

---

## 📈 Success Metrics

**Current Status**:
- ✅ 4 automated workflows
- ✅ 100% endpoint coverage
- ✅ < 2 minute pre-push validation
- ✅ 5-minute production health checks
- ✅ Auto-rollback on failures
- ✅ Visual regression testing
- ✅ Security scanning enabled

**SLOs**:
- **Zero 502 errors** in production
- **< 5 second** response times
- **99.9% uptime** guarantee
- **< 30 second** rollback time

---

## 🐛 Troubleshooting

### Workflow Failing?
1. Check the logs in GitHub Actions
2. Verify secrets are set correctly
3. Ensure production server is accessible
4. Check for merge conflicts

### 502 Error Detected?
1. Check auto-rollback succeeded
2. Review `docker compose logs app --tail=100`
3. Verify database is running
4. Check for resource exhaustion

### Frutiger Aero Not Loading?
1. Check build included CSS files
2. Verify static assets served
3. Check browser console for errors
4. Ensure `aero-background.js` in `/public`

---

## 📚 Additional Resources

- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Docker Health Checks](https://docs.docker.com/engine/reference/builder/#healthcheck)
- [Playwright Testing](https://playwright.dev/)
- [Next.js Deployment](https://nextjs.org/docs/deployment)

---

## 🤝 Contributing

All contributions must pass:
1. Pre-push validation
2. Full CI suite
3. Security scan
4. Manual code review

**Commit Format**:
```
feat: Add new feature
fix: Fix bug
chore: Update dependencies
docs: Update documentation
test: Add tests
ci: Update CI/CD workflows
```

---

## 📝 License

MIT License - See [LICENSE](LICENSE) file

---

**Made with ❤️ and professional software engineering practices** 🚀
