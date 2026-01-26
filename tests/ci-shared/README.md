# 🔧 Shared CI Standards & Components

**Purpose:** Centralized CI/CD standards and reusable components for the LexMakesIt platform.

## 🎯 Architecture

### Separation of Concerns
- **Frontend CI:** Remains in own pipeline (Next.js, React, TypeScript)
- **Backend CI:** Remains in own pipeline (FastAPI, Python, SQLite)
- **Shared Standards:** Common validation logic and configurations

### Components

#### 1. `ci-standards.json`
**Central configuration** for all CI pipelines:
- Environment specifications (Python, Node versions)
- Quality gates and timeouts
- Artifact retention policies
- Notification rules

#### 2. `auth-contract-validator.py`
**Reusable authentication testing** for both frontend and backend:
- Login endpoint validation
- Protected route guards
- Token validation contracts
- Cross-system auth compatibility

#### 3. `environment-guard.py`
**Deployment readiness validation:**
- Python version compatibility
- Git workspace cleanliness
- Required dependencies
- Environment-specific secrets (prod only)

#### 4. `visual-integrity-validator.py`
**Asset and visual validation:**
- Critical asset availability (waterfall.gif, logos)
- File format integrity
- Size and performance validation
- Content hash verification

#### 5. `ci-utils.py`
**Common utilities:**
- Standardized logging with emoji indicators
- Report generation
- GitHub Actions integration
- Configuration management

## 🚀 Usage

### In Frontend CI (Next.js)
```yaml
- name: 🔐 Auth Contract Validation
  run: python3 tests/ci-shared/auth-contract-validator.py http://localhost:3000

- name: 🎨 Visual Assets Check
  run: python3 tests/ci-shared/visual-integrity-validator.py
```

### In Backend CI (FastAPI)
```yaml
- name: 🔐 Auth Contract Validation  
  run: python3 tests/ci-shared/auth-contract-validator.py http://localhost:8010

- name: 🛡️ Environment Guard
  run: python3 tests/ci-shared/environment-guard.py production
```

### In Wallpaper CI (Specialized)
```yaml
- name: 🎨 Visual Integrity Base Check
  run: python3 tests/ci-shared/visual-integrity-validator.py
  
- name: 🖼️ Wallpaper Specific Tests
  run: ./tests/ci-wallpaper/run_wallpaper_tests.sh all
```

## 📋 Standards Enforcement

### Quality Gates
1. **Auth Contracts** - All auth endpoints must pass validation
2. **Visual Integrity** - Critical assets must be available and valid
3. **Environment Guards** - Deployment environment must be ready

### Failure Handling
- **Critical failures** block deployment
- **Optional checks** generate warnings
- **Retry logic** for network-dependent checks

## 🔧 Integration Points

### Existing Workflows
- **Frontend:** `.github/workflows/frontend-ci.yml` (to be created/updated)
- **Backend:** `.github/workflows/backend-ci.yml` (to be created/updated) 
- **Auth CI:** `.github/workflows/auth-ci.yml` (references shared auth validator)
- **Wallpaper CI:** `.github/workflows/wallpaper-ci.yml` (uses shared visual validator)

### Configuration Override
Each pipeline can override shared standards:
```python
# Custom timeouts
validator = SharedAuthContractValidator(base_url, timeout=60)

# Environment-specific checks
guard = SharedEnvironmentGuard("production")
```

## 📊 Reporting

### GitHub Actions Integration
- Standardized step summaries
- Artifact collection
- PR comments with results
- Matrix strategy support

### Report Formats
- JSON reports for programmatic processing
- Markdown summaries for human consumption
- GitHub Actions annotations for inline feedback

## 🔄 Versioning

**Current Version:** 1.0.0

### Backward Compatibility
- Existing pipelines continue to work
- Gradual migration to shared standards
- Optional adoption of new features

### Update Process
1. Update `ci-standards.json` version
2. Test changes in development environment
3. Deploy to staging pipelines
4. Roll out to production workflows

## 🛠️ Maintenance

### Adding New Standards
1. Update relevant shared component
2. Increment version in `ci-standards.json`
3. Update this README
4. Test with existing pipelines

### Pipeline Migration
1. Reference shared component in workflow
2. Remove duplicate validation logic
3. Test pipeline passes/fails correctly
4. Update pipeline documentation

---

**Key Principle:** Share standards and logic, not execution pipelines. Each system maintains its own deployment autonomy while ensuring consistent quality gates.