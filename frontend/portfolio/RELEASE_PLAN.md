# Release Plan - Portfolio

## Pre-Deployment Checklist
- [ ] **Tests**: Ensure all unit tests pass locally (`pytest`).
- [ ] **Security**: Run `pip-audit` and `safety check` locally.
- [ ] **Secrets**: Verify any new environment variables are added to GitHub Secrets (`PORTFOLIO_ENV`).
- [ ] **Resources**: Check server RAM usage (`htop`) to ensure capacity for Blue/Green overlap.

## Deployment Architecture
- **Strategy**: Blue/Green Deployment.
- **Orchestration**: GitHub Actions -> SSH -> Docker Compose.
- **Traffic Switching**: Caddy (Global) -> `portfolio.internal:8001` (Load Balanced).
- **Readiness Gate**: New container must pass 3 consecutive health checks at `/api/health`.

## Rollback Steps
**Automatic**: The CI/CD pipeline will automatically stop the new container if readiness checks fail.

**Manual Rollback**:
1.  SSH into the server.
2.  Identify the running "Green" container (the bad one).
3.  Identify the stopped "Blue" container (the good one).
4.  Start the old container:
    ```bash
    cd /srv/portfolio
    docker compose -p portfolio-blue up -d
    ```
5.  Stop the new container:
    ```bash
    docker compose -p portfolio-green down
    ```
6.  Verify Caddy is routing traffic correctly:
    ```bash
    curl -I https://lexmakesit.com
    ```

## Validation
- **Health Check**: `curl https://lexmakesit.com/api/health`
- **Logs**: Check Grafana or `docker logs portfolio-green-web-1`.
