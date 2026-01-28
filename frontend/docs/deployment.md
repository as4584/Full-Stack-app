# 🚀 Deployment Guardian — Ultra-Secure Pipeline Contract  
This document defines the complete ruleset, architecture knowledge, and safety
guarantees required before ANY code may be committed, pushed, merged, or deployed.

Copilot MUST follow this contract at all times.

---

# 🔰 1. Purpose of This Contract
This document exists to ensure:

- Zero broken pushes  
- Zero red CI pipelines  
- Zero deployments of untested code  
- Zero production outages  
- Zero accidental changes to infrastructure  

Copilot is responsible for enforcing all rules here.

If any requirement fails → pushing and deployment are FORBIDDEN.

---

# 🧠 2. Full Architecture Knowledge Base

## 2.1 System Overview
The project uses:
- Python backend (FastAPI/Flask)
- Static frontend (`static/` + `templates/`)
- Docker & Docker Compose
- Caddy reverse proxy on the production server
- GitHub Actions for CI/CD
- Antigravity for local agent-based development

## 2.2 Deployment Flow
1. Developer writes code locally (vibe coding allowed)
2. Tests, linting, builds run locally
3. Fixes applied automatically by Copilot or Antigravity
4. Commit → GitHub push
5. GitHub Actions runs:
   - Install dependencies
   - Linting (ruff, black)
   - Tests (pytest)
   - Docker build
   - Healthchecks
6. If all CI checks are green → deployment proceeds
7. Caddy reloads new container image

Copilot must understand this pipeline deeply.

---

# 🚦 3. Push Protection Rules (MANDATORY)

Copilot MUST block all commit/push attempts unless ALL of the following pass:

## ✔ 3.1 Tests
```
./run_tests.sh
```
- 100% green  
- No failures  
- No warnings upgraded to errors

## ✔ 3.2 Linting
```
ruff check .
black --check .
```

## ✔ 3.3 Type Checking (if enabled)
```
mypy .
```

## ✔ 3.4 Docker Build
```
docker compose build
```
- No failing layers  
- No missing dependencies  
- No missing static files  
- Build size not exploding unexpectedly

## ✔ 3.5 Docker Health
```
docker compose up --exit-code-from portfolio-web-1
```
- Must reach “healthy”  
- No exceptions on startup  
- No template errors  
- No missing variables

## ✔ 3.6 No Uncommitted Migrations (if applicable)

## ✔ 3.7 Production-Parity Local Run
Copilot must mentally simulate:
- File structure correctness  
- Import path correctness  
- Template rendering  
- Static asset loading  

If anything is suspicious → STOP.

---

# 🛡️ 4. Security Enforcement

Copilot must NEVER allow:

- API keys in commits  
- Secrets in code  
- `.env` included in repo  
- Plaintext credentials  
- Debug logs exposing data  
- Insecure HTTP → must use HTTPS

Before any push:
- Scan staged files for secrets  
- Block pushes if secrets appear  
- Suggest using GitHub Secrets instead

---

# 🧱 5. Branch Protection Logic

Copilot must assume:
- `main` is protected
- Direct pushes forbidden
- Only CI-validated PR merges allowed

For every change:
- PR must be small, readable, clean
- PR must contain a clear description
- No unrelated file changes
- No formatting churn

---

# 🔍 6. Required Local Commands (Copilot Must Know)

## Test Suite
```
./run_tests.sh
```

## Lint
```
ruff check .
black --check .
```

## Type Check
```
mypy .
```

## Build
```
docker compose build
```

## Local Run
```
docker compose up
```

Copilot should automatically suggest these commands during coding sessions.

---

# 📦 7. Deployment Playbook — What Copilot Must Do

## If something fails locally:
- Explain the failure  
- Show the broken file/line  
- Suggest a minimal fix  
- Apply a minimal diff patch  
- Re-run `./run_tests.sh` mentally  
- Repeat until fully green  

## If something fails in CI:
- Read CI logs  
- Identify root cause  
- Reproduce locally  
- Fix the issue  
- Open a clean PR  

Copilot must NEVER ignore CI errors.

---

# 🔄 8. Automated Debugging Loop (Copilot Behavior Contract)

When running tests:
1. Run test suite  
2. Capture stack trace  
3. Identify failing file + function  
4. Explain root cause  
5. Apply minimal patch  
6. Re-run tests (mentally or through Antigravity)  
7. Repeat until green  

Copilot must do this **automatically**.

---

# 🧩 9. Code Generation Guidelines

Copilot must:
- Generate minimal diffs  
- Avoid unnecessary rewrites  
- Preserve architecture  
- Follow `.copilot.md` rules  
- Maintain Frutiger Aero frontend requirements  
- Keep backend logic unchanged unless tests require it  
- Avoid introducing technical debt  
- Maintain perfect formatting  

---

# 🚫 10. Forbidden Behaviors

Copilot MUST NOT:
- Push code with failing tests  
- Disable linting/tests to bypass errors  
- Rewrite entire files without request  
- Modify deployment infrastructure without approval  
- Remove tests or silence warnings  
- Push directly to production branches  
- Deploy unreviewed code  

If a user tries to force any of these:
Copilot must ask,  
**“Tests are not fully green. Do you want me to help fix them first?”**

---

# 🟩 11. Final Deployment Rule
**If ANY requirement is not green → deployment must NOT proceed.**

Everything must be:
- green  
- clean  
- tested  
- validated  
- reproducible  
- safe  

Copilot must protect the project at all costs.