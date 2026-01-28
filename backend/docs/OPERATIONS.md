# Operations Manual - AI Receptionist

## Service Overview
- **URL**: https://receptionist.lexmakesit.com
- **Internal DNS**: `ai.internal`
- **Port**: 8002 (Internal Only)
- **Database**: Postgres (Port 5432 Internal)
- **Vector DB**: Qdrant (Port 6333 Internal)

## Common Tasks

### Restart Service
```bash
cd /srv/ai_receptionist
docker compose -f docker-compose.prod.yml -p ai_receptionist-green restart app
```

### Database Access
**Postgres**:
```bash
docker exec -it ai_receptionist-green-postgres-1 psql -U ai -d ai_receptionist
```

**Qdrant**:
Access via API: `curl http://localhost:6333/collections`

### View Logs
**Via CLI**:
```bash
docker logs -f ai_receptionist-green-app-1
```

**Via Grafana**:
Query: `{container="ai_receptionist-green-app-1"}`

## Environment Variables
Located at: `/srv/env/ai_receptionist/.env`
**Permissions**: `600` (root:root)

To update:
1.  Edit file: `sudo nano /srv/env/ai_receptionist/.env`
2.  Restart service.
