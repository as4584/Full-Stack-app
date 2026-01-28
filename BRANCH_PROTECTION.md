# 🔒 Branch Protection Setup Guide

To prevent pushing to `main` unless CI passes, follow these steps:

## GitHub Repository Settings

1. **Go to your repository**: https://github.com/as4584/Full-Stack-app

2. **Navigate to Settings** → **Branches**

3. **Add Branch Protection Rule**:
   - Branch name pattern: `main`

4. **Enable these protections**:
   
   ✅ **Require a pull request before merging**
   - Require approvals: 0 (or 1 if you want code review)
   - Dismiss stale pull request approvals when new commits are pushed
   
   ✅ **Require status checks to pass before merging**
   - Require branches to be up to date before merging
   - **Required status checks** (add these):
     - `✅ CI Success` (the summary job)
     - `🐍 Backend Lint & Type Check`
     - `⚛️ Frontend Lint & Build`
     - `🔒 Security Scan`
   
   ✅ **Do not allow bypassing the above settings**

5. **Click "Create"** or "Save changes"

## What This Does

After setup, any push directly to `main` will be blocked. You must:

1. Create a feature branch: `git checkout -b feature/my-change`
2. Make your changes and commit
3. Push the branch: `git push origin feature/my-change`
4. Create a Pull Request on GitHub
5. Wait for CI checks to pass
6. Merge the PR (only if all checks pass)

## Quick Commands

```bash
# Create a new feature branch
git checkout -b feature/my-new-feature

# Make changes, then commit
git add .
git commit -m "Add my new feature"

# Push to GitHub
git push origin feature/my-new-feature

# Then go to GitHub and create a Pull Request
```

## CI Workflow Status

| Check | Description | Required |
|-------|-------------|----------|
| Backend Lint | Python syntax & style | ✅ Yes |
| Backend Unit Tests | pytest tests | ⚠️ Optional |
| Frontend Lint & Build | TypeScript & Next.js build | ✅ Yes |
| Security Scan | Check for secrets | ✅ Yes |
| Docker Build | Verify Dockerfile works | ⚠️ Optional |
| CI Success | All required checks passed | ✅ Yes |

## E2E Tests (Separate Workflow)

E2E tests run on a schedule or manual trigger only - they don't block PRs
because they need production secrets that aren't available in CI.

---

*Set up once, protected forever!*
