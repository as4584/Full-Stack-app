# AI Receptionist

> ## ⚠️ CRITICAL: READ BEFORE MAKING CHANGES
> 
> **Before modifying this codebase, you MUST read:**
> 
> 📖 **[AI_RECEPTIONIST_SOURCE_OF_TRUTH.md](AI_RECEPTIONIST_SOURCE_OF_TRUTH.md)**
> 
> This document contains the authoritative configuration for ports, webhooks, 
> Caddy, Docker, Twilio, and OpenAI settings. Ignoring this document has 
> repeatedly caused system failures.

Intelligent Voice Receptionist powered by OpenAI Realtime API, Twilio, and Qdrant.

## Quick Start (Local Development)

1.  **Clone & Setup**:
    ```bash
    git clone <repo>
    cd ai_receptionist
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Start Dependencies**:
    ```bash
    docker compose -f docker-compose.dev.yml up -d
    ```

3.  **Run App**:
    ```bash
    uvicorn main:app --reload --port 8002
    ```

## Deployment

This repository uses **Blue/Green Deployment** via GitHub Actions.
- **Trigger**: Push to `main`.
- **CI/CD**: `.github/workflows/deploy.yml`.

### Secrets
Secrets are managed in GitHub Actions and injected into `/srv/env/ai_receptionist/.env` on the server.

## Documentation
- **[AI_RECEPTIONIST_SOURCE_OF_TRUTH.md](AI_RECEPTIONIST_SOURCE_OF_TRUTH.md)** - ⚠️ CRITICAL: System configuration reference
- [RELEASE PLAN](RELEASE_PLAN.md) - Deployment & Rollback steps.
- [OPERATIONS](OPERATIONS.md) - Debugging & Maintenance.
- [SECURITY](SECURITY.md) - Security policies.
