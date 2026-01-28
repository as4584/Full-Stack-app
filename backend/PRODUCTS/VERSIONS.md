# Product Versions (V1–V4)

- V1 — Starter: Essential call handling to get you live fast.
  - Features:
    - Health-checked API and Twilio webhook
    - Basic intent routing with human fallback queue
    - Tenant config (plan + flags) read-only
  - Pitch: “Launch an AI receptionist in days, not months.” Price: $99–$199/mo
  - Acceptance tests:
    - Health endpoint returns status=ok
    - Incoming webhook enqueues call event
    - Escalation produces human-fallback entry and Slack notification

- V2 — Core: Solid routing and bookings for SMBs.
  - Features:
    - Booking flows with conflict checks and reschedule
    - Per-tenant feature flags (enable_rag, allow_ai_booking)
    - Observability: request/tenant IDs in logs
  - Pitch: “Fewer missed calls, more booked revenue.” Price: $249–$499/mo
  - Acceptance tests:
    - Booking flow completes with valid time
    - Reschedule updates existing appointment
    - Logs include request_id and tenant_id

- V3 — Pro: RAG answers and integrations.
  - Features:
    - RAG knowledge answers (vector DB)
    - Payment capture handoff + billing dashboard
    - SSO and role-based admin console
  - Pitch: “Turn calls into conversions with AI answers.” Price: $599–$1,499/mo
  - Acceptance tests:
    - RAG returns relevant snippets in prompt
    - Minutes billed correctly at month end
    - Admin can toggle feature flags per tenant

- V4 — Enterprise: Scale, security, and SLAs.
  - Features:
    - Multi-region HA, priority queues, rate limits
    - Audit logs, PII redaction, data retention controls
    - SSO/SAML, DLP policies, 99.9% support SLA
  - Pitch: “Enterprise-grade reliability and compliance.” Price: $2,500–$10,000+/mo
  - Acceptance tests:
    - Rate limiting caps tenant spikes
    - Audit logs capture admin actions
    - Failover path preserves inbound calls
