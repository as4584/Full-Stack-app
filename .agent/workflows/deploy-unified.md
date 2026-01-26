---
description: Sync and deploy all local changes to AI Receptionist Backend and Dashboard
---

# AI Receptionist Deployment Workflow

This workflow automates the process of pushing your local code fixes (Backend, Database, and Dashboard) to the live servers and restarting the necessary services.

// turbo-all

## 1. Deploy All Changes
Run the unified deployment script. This now uses **Zero-Downtime Rolling Deployments** (starts new, waits for health, removes old):
```bash
./scripts/deploy_all.sh
```

## 2. Setup Twilio Failover (Optional/One-time)
Ensure Twilio has a fallback URL if the primary server is unreachable:
```bash
# This sets the failover voice URL to receptionist.lexmakesit.com/fallback-voice
python3 backend/scripts/setup_twilio_fallback.py
```

## 3. Verify Deployment
Check health and test calls:
- [Backend Health](https://receptionist.lexmakesit.com/health)
- [Onboarding Flow](https://dashboard.lexmakesit.com/app/onboarding)

### High Availability Features
- **Rolling Update**: The backend swaps containers only after the new one is healthy.
- **Failover TwiML**: If the backend is 502/503 (e.g. during a database migration), Caddy returns a "Hold and Retry" message that prevents the "Application Error".
