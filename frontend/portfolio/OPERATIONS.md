# Operations Manual - Portfolio

## Service Overview
- **URL**: https://lexmakesit.com
- **Internal DNS**: `portfolio.internal`
- **Port**: 8001 (Internal Only)
- **Framework**: FastAPI

## Common Tasks

### Restart Service
```bash
cd /srv/portfolio
# Identify current color
docker ps | grep portfolio
# Restart specific color
docker compose -p portfolio-green restart web
```

### View Logs
**Via CLI**:
```bash
docker logs -f portfolio-green-web-1
```

**Via Grafana**:
1.  Go to `monitor.lexmakesit.com`.
2.  Explore -> Loki.
3.  Query: `{container="portfolio-green-web-1"}`.

### Debugging Connection Issues
1.  Check if container is healthy:
    ```bash
    curl http://localhost:8001/api/health
    ```
2.  Check Caddy logs:
    ```bash
    tail -f /var/log/caddy/portfolio.log
    ```

## Environment Variables
Located at: `/srv/env/portfolio/.env`
**Permissions**: `600` (root:root)

To update:
1.  Edit file: `sudo nano /srv/env/portfolio/.env`
2.  Restart service.
