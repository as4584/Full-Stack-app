# Lex Santiago Portfolio

Professional API Consulting Portfolio Website built with FastAPI.

## Quick Start (Local Development)

1.  **Clone & Setup**:
    ```bash
    git clone <repo>
    cd portfolio
    python -m venv .venv
    source .venv/bin/activate  # or .venv\Scripts\activate on Windows
    pip install -r requirements.txt
    ```

2.  **Run Locally**:
    ```bash
    uvicorn main:app --reload --port 8001
    ```
    Access at: http://localhost:8001

3.  **Run via Docker**:
    ```bash
    docker compose up -d
    ```

## Deployment

This repository uses **Blue/Green Deployment** via GitHub Actions.
- **Trigger**: Push to `main`.
- **CI/CD**: `.github/workflows/deploy.yml`.

### Secrets
Secrets are managed in GitHub Actions and injected into `/srv/env/portfolio/.env` on the server.

## Documentation
- [RELEASE PLAN](RELEASE_PLAN.md) - Deployment & Rollback steps.
- [OPERATIONS](OPERATIONS.md) - Debugging & Maintenance.
- [SECURITY](SECURITY.md) - Security policies.
