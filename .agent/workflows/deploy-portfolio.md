---
description: Rebuild and deploy the portfolio web container with latest changes
---

# Portfolio Deployment Workflow

// turbo-all

## Pre-Deployment Checks
1. Run local tests to verify changes work
   ```bash
   cd frontend/portfolio && python -m pytest tests/ -v
   ```

2. Lint check for any syntax errors
   ```bash
   cd frontend/portfolio && python -m py_compile main.py
   ```

## Deployment Steps

3. Copy updated templates to server
   ```bash
   scp frontend/portfolio/templates/ai-receptionist.html droplet:~/antigravity_bundle/apps/portfolio/templates/
   ```

4. Copy updated static files (if changed)
   ```bash
   scp -r frontend/portfolio/static/css droplet:~/antigravity_bundle/apps/portfolio/static/
   ```

5. SSH into droplet and rebuild container
   ```bash
   ssh droplet "cd ~/antigravity_bundle/apps/portfolio && docker stop portfolio_web || true && docker rm portfolio_web || true && docker build -t portfolio_web:latest . && docker run -d --name portfolio_web --network apps_antigravity_net -e PRODUCTION=true --env-file ~/antigravity_bundle/apps/.env -p 8001:8000 portfolio_web:latest"
   ```

6. Verify health check
   ```bash
   ssh droplet "curl -s http://localhost:8001/api/health"
   ```

7. Reload Caddy to clear any cache
   ```bash
   ssh droplet "docker exec antigravity_caddy caddy reload --config /etc/caddy/Caddyfile"
   ```

## Post-Deployment Verification

8. Check live site via curl
   ```bash
   curl -s https://lexmakesit.com/api/health
   ```

## Rollback (if needed)
If deployment fails:
```bash
ssh droplet "docker stop portfolio_web && docker rm portfolio_web && docker run -d --name portfolio_web --network apps_antigravity_net -e PRODUCTION=true --env-file ~/antigravity_bundle/apps/.env -p 8001:8000 portfolio_web:previous"
```
