# CI/CD Architecture — The Nervous System

## 1. Monorepo Structure
The repository contains multiple distinct services, each with its own lifecycle but shared governance.

*   **`portfolio/`**: FastAPI backend + Jinja2 frontend.
*   **`inventory_manager/`**: Flask backend + React/Jinja2 frontend.
*   **`ai_receptionist/`**: Python/FastAPI AI agent service.
*   **`lexmakesit-infra/`**: Infrastructure as Code (IaC) and monitoring.

## 2. Workflow Strategy
We use a **Path-Filtered Trigger** strategy to optimize resource usage.

*   **Global Guardian**: Runs on ALL pushes. Checks repo health, linting, and security policies.
*   **Service Pipelines**: Trigger only when files in their specific directory change.
    *   `deploy-portfolio.yml`: Triggers on `portfolio/**`
    *   `deploy-inventory.yml`: Triggers on `inventory_manager/**`

## 3. The Deployment Chain
1.  **Test**: Unit tests (`pytest`) + Static Analysis (`ruff`, `mypy`).
2.  **Audit**: Security scanning (`pip-audit`, `safety`).
3.  **Build**: Docker image creation (`docker build`).
4.  **Push**: Upload to GHCR (`ghcr.io`).
5.  **Deploy**: SSH into DigitalOcean -> `docker compose pull` -> `docker compose up`.

## 4. Security Architecture
*   **Secrets Management**: All sensitive data via GitHub Secrets (`*_ENV`, `SSH_KEY`).
*   **Vulnerability Management**:
    *   High/Critical CVEs block deployment.
    *   Low/Medium CVEs may be ignored *if and only if* a `deployment.md` justification exists.
*   **Network**: Services sit behind Caddy (Reverse Proxy) with automatic HTTPS.

## 5. Self-Healing Architecture
*   **Guardian Agent**: Monitors every run.
*   **PR Bot**: If a run fails, it attempts to generate a fix PR automatically.
*   **Epistemic Logs**: Every failure is recorded in `CI_HEALTH.md`.
