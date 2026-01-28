# AI Receptionist (FastAPI + Poetry)

A production-ready scaffold for an AI Receptionist service built with FastAPI, following SOLID principles and clean layering. Includes Twilio webhook stub, dependency inversion for telephony, and test scaffolding.

## Features
- FastAPI app with health endpoint and `/twilio/webhook` POST stub
- SOLID services: Telephony interface + Twilio implementation via dependency inversion
- Structured packages: app, core, services, models, db, workers
- Poetry for dependency management (`pyproject.toml` included)
- Pytest configured with a sample test
- Environment variables via `.env` using Pydantic Settings

## Getting Started

1) Install Poetry (if needed): https://python-poetry.org/docs/#installation

2) Install dependencies:
```bash
cd ai_receptionist
poetry install
```

3) Create a `.env` from the example and set required values:
```bash
cp .env.example .env
# Edit .env with your secrets (Twilio credentials, etc.)
```

4) Run the API locally:
```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

5) Health check:
```bash
curl http://localhost:8080/health
```

## Testing
```bash
poetry run pytest
```

## Project Layout
```
ai_receptionist/
  app/          # API layer (FastAPI routers, entrypoints)
  core/         # Settings, DI container
  services/     # Domain services (telephony, ai, billing)
  models/       # Pydantic DTOs
  db/           # Repositories (ports/adapters)
  workers/      # Background/async tasks
  tests/        # Unit/integration tests
  pyproject.toml
  README.md
```

## SOLID and Dependency Inversion
- `services/telephony/telephony.py` defines `TelephonyService` (abstract interface)
- `services/telephony/twilio_service.py` implements the interface
- `core/di.py` wires dependencies so API depends on the interface, not the implementation

## Environment Variables
- Managed via `core/settings.py` using Pydantic Settings
- Put secrets in `.env` (not committed); examples in `.env.example`
- Example variables:
```
APP_ENV=local
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+15551234567
```

## Senior Notes
- Secrets: never commit `.env` or secrets. Use environment variables in CI/CD or a secrets manager (AWS Secrets Manager, GCP Secret Manager, HashiCorp Vault).
- CI: In CI, run `poetry install`, then `ruff` and `black` in check mode, and `pytest`:
  ```bash
  poetry install --no-root
  poetry run ruff check .
  poetry run black --check .
  poetry run pytest
  ```
- Linting/Type-checking: Ruff for linting, Black for formatting, Mypy optional for type checks.
- Observability: Add structured logging, request IDs, and metrics early. Consider middleware for tracing.
- Scalability: Keep services small with single responsibility; split routers by domain; use background workers for long-running tasks.

## Twilio Webhook Development
- Expose your local server with `ngrok` when testing with Twilio.
- Configure your Twilio phone number webhook to `POST https://<your-ngrok>/twilio/webhook`.

---
This scaffold is intentionally minimal but provides strong foundations to extend into a production-grade system.

## Human fallback SRE runbook (on-call + SLA)

When the AI cannot confidently complete a task, the system emits an `escalate` event. A background worker persists this to a `human_fallback` store and notifies a Slack channel for on-call humans.

- Source of truth: `human_fallback` table (or repository) contains tenant_id, caller, reason, created_at, and raw context.
- Notification: `#human-fallback` Slack channel receives a message with tenant, caller, reason, and entry_id.
- On-call rotation: Assign an on-call engineer or support agent with Slack push notifications enabled. Use a shared runbook and escalation policy (PagerDuty/Slack).
- SLA guidance:
  - Critical/Live-call: Acknowledge within 2 minutes, engage caller in < 5 minutes.
  - Standard: Acknowledge within 15 minutes, follow-up within 1 hour.
- Procedure:
  1) Open the latest Slack notification, copy `entry_id`.
  2) Retrieve full context from `human_fallback` by `entry_id`.
  3) Contact the caller (or join live handoff) and resolve.
  4) Record resolution notes and mark the entry closed.
- Post-incident: Tag recurring reasons (e.g., “payment”, “ambiguous time”), feed back to model/rules to reduce future escalations.

## Infrastructure as Code (IaC) and local dev

- Use Terraform to provision cloud infra: Postgres (OLTP), Redis (queues/cache), and a vector DB (e.g., Pinecone, Qdrant, or OpenSearch KNN). Keep state in a remote backend (S3/GCS) and apply via CI with approvals.
- For local development, a minimal Docker Compose file is provided at `docker-compose.dev.yml` with Postgres, Redis, and Qdrant:
  ```bash
  docker compose -f docker-compose.dev.yml up -d
  ```
  Configure your `.env` to point to these local services.

## Feature flags per-tenant

- Model flag configuration per `tenant_id` (e.g., allow_ai_booking, enable_rag, require_human_review) in a `feature_flags` table or config store.
- Evaluate flags at request time via a cached read (e.g., Redis) to keep latency low; default to safest behavior on cache miss.
- Rollouts: enable flags for a small subset of tenants first; use observability signals to decide broader rollout.

## Database migrations strategy

- Use Alembic (or Prisma/Flyway) for versioned migrations. Target backward-compatible changes first.
- Zero-downtime pattern:
  1) Add new columns/tables in a non-breaking way.
  2) Deploy app that writes to both old and new (dual-write) if needed.
  3) Backfill data with a one-off job or migration script.
  4) Switch reads to the new schema; monitor.
  5) Remove old columns/paths after a grace period.
- Maintain per-tenant migrations if multi-tenant isolation requires it (schema-per-tenant). Otherwise use a global shared schema with a `tenant_id` column and partial indexes.

## Admin CLI (tools/adminctl.py)

Small Click-based tool for tenant plan and feature flag management. Requires a private key at `~/.adminctl.env`:

```
ADMIN_PRIVATE_KEY=your-very-secret
```

Optionally set the API base URL for admin endpoints:

```
export ADMIN_API_URL=http://localhost:8080
```

Examples:

```
# Set plan to core for tenant t1
python tools/adminctl.py set-plan --tenant t1 --plan core --admin-user lex

# Enable RAG for tenant t1
python tools/adminctl.py set-flag --tenant t1 --flag allow_rag --enable true --admin-user lex

# Show flags for tenant t1
python tools/adminctl.py show-flags --tenant t1
```

The CLI signs a short-lived JWT (HS256) using ADMIN_PRIVATE_KEY and sends it as a Bearer token to /admin endpoints.
