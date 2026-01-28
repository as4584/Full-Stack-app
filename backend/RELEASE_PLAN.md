# Release Plan - AI Receptionist

## Pre-Deployment Checklist
- [ ] **Tests**: Ensure all unit tests pass locally (`pytest`).
- [ ] **Security**: Run `pip-audit` and `safety check` locally.
- [ ] **Migrations**: Verify new Alembic migrations are generated (`alembic revision --autogenerate`).
- [ ] **Secrets**: Verify any new environment variables are added to GitHub Secrets (`AI_ENV`).

## Deployment Architecture
- **Strategy**: Blue/Green Deployment.
- **Orchestration**: GitHub Actions -> SSH -> Docker Compose.
- **Traffic Switching**: Caddy (Global) -> `ai.internal:8002` (Load Balanced).
- **Readiness Gate**: New container must pass 3 consecutive health checks at `/health`.

## Rollback Steps
**Automatic**: The CI/CD pipeline will automatically stop the new container if readiness checks fail.

**Manual Rollback**:
1.  SSH into the server.
2.  Identify the running "Green" container.
3.  Identify the stopped "Blue" container.
4.  Start the old container:
    ```bash
    cd /srv/ai_receptionist
    docker compose -f docker-compose.prod.yml -p ai_receptionist-blue up -d
    ```
5.  Stop the new container:
    ```bash
    docker compose -p ai_receptionist-green down
    ```
6.  **Database Rollback** (If migrations ran):
    ```bash
    docker exec ai_receptionist-blue-app-1 alembic downgrade -1
    ```

## Validation
- **Health Check**: `curl https://receptionist.lexmakesit.com/health`
- **Logs**: Check Grafana or `docker logs ai_receptionist-green-app-1`.
