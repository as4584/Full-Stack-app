# AI Receptionist - Source of Truth

> **⚠️ CRITICAL: READ THIS BEFORE MAKING ANY CHANGES**
> 
> This document is the authoritative reference for the AI Receptionist system.
> Any AI assistant or developer modifying this codebase MUST read and follow this document.
> Breaking changes have occurred multiple times due to ignoring these specifications.

---

## Table of Contents
1. [System Overview](#system-overview)
2. [Critical Architecture (DO NOT CHANGE)](#critical-architecture-do-not-change)
3. [Port Configuration](#port-configuration)
4. [Endpoint Routing](#endpoint-routing)
5. [Twilio Configuration](#twilio-configuration)
6. [OpenAI Realtime API Configuration](#openai-realtime-api-configuration)
7. [Docker & Deployment](#docker--deployment)
8. [Caddy Reverse Proxy](#caddy-reverse-proxy)
9. [Common Failure Modes](#common-failure-modes)
10. [Testing Checklist](#testing-checklist)
11. [Shadow AI & Behavioral Parity](#shadow-ai--behavioral-parity)
12. [Evaluation, Logging, and Drift Control Plan](#evaluation-logging-and-drift-control-plan)
13. [Modular Integrity & Non-Negotiable Constraints](#modular-integrity--non-negotiable-constraints)
14. [Frontend Assets & Branding](#frontend-assets--branding)

---

## System Overview

The AI Receptionist is a voice-enabled AI assistant that answers phone calls via Twilio, 
streams audio to OpenAI's Realtime API, and provides conversational responses.

### Call Flow (CRITICAL - DO NOT MODIFY)
```
1. Caller dials +1 (229) 821-5986
2. Twilio sends POST to https://receptionist.lexmakesit.com/twilio/voice
3. App returns TwiML with <Connect><Stream url="wss://receptionist.lexmakesit.com/twilio/stream"/></Connect>
4. Twilio establishes WebSocket to /twilio/stream
5. App connects to OpenAI Realtime API (wss://api.openai.com/v1/realtime)
6. Bidirectional audio streaming begins
7. AI speaks greeting, then listens and responds
```

---

## Critical Architecture (DO NOT CHANGE)

### Package Structure
```
ai_receptionist/
├── app/
│   ├── main.py              # FastAPI app entry point
│   └── api/
│       └── twilio.py        # /twilio/webhook (legacy, not used for voice)
├── api/
│   └── realtime.py          # /twilio/stream WebSocket handler (CRITICAL)
├── services/
│   └── voice/
│       └── endpoints.py     # /twilio/voice endpoint (CRITICAL)
└── config/

### Authoritative Toggle & Enforcement (CRITICAL)
- **Source of Truth**: The `Business.receptionist_enabled` boolean is the ONLY authority for AI activation.
- **Enforcement Point**: Enforcement happens in `/twilio/voice` (Entry Point).
- **Sequential Check**:
    1. **Global Kill Switch** (`GLOBAL_AI_KILL_SWITCH` env var) - Overrides everything.
    2. **Business Status** (`is_active`) - Account level.
    3. **Receptionist Toggle** (`receptionist_enabled`) - Specific AI toggle.
- **Rule**: The AI stream MUST NOT be initialized if any check fails. Route to offline message or hangup.
    └── settings.py          # Environment configuration
```

### Router Registration Order (CRITICAL)
In `ai_receptionist/app/main.py`, routers MUST be registered in this order:
```python
app.include_router(voice_router, prefix="/twilio")      # /twilio/voice
app.include_router(twilio_router, prefix="/twilio")      # /twilio/webhook
app.include_router(realtime_router, prefix="/twilio")    # /twilio/stream
app.include_router(admin_router)
```

**⚠️ WARNING:** The `voice_router` in `services/voice/endpoints.py` must NOT have a prefix. 
The prefix is applied in `main.py`.

---

## Port Configuration

| Service | Internal Port | External Access |
|---------|---------------|-----------------|
| ai_receptionist_app | 8010 | Via Caddy reverse proxy |
| Caddy | 80, 443 | Public internet |
| PostgreSQL | 5432 | Internal only |
| Redis | 6379 | Internal only |

**⚠️ DO NOT change port 8010.** Caddy, Docker Compose, and Twilio all expect this port.

---

## Endpoint Routing

### Active Endpoints

| Method | Path | Purpose | Handler |
|--------|------|---------|---------|
| POST | `/twilio/voice` | Twilio voice webhook (returns TwiML) | `services/voice/endpoints.py:voice_entry` |
| WebSocket | `/twilio/stream` | Twilio media stream (audio) | `api/realtime.py:websocket_endpoint` |
| POST | `/twilio/webhook` | Legacy webhook (NOT USED FOR VOICE) | `app/api/twilio.py:twilio_webhook` |
| GET | `/health` | Health check | `app/main.py:health` |

### Twilio Phone Number Configuration

**Phone Number:** +1 (229) 821-5986

| Setting | Value |
|---------|-------|
| Voice URL | `https://receptionist.lexmakesit.com/twilio/voice` |
| Voice Method | POST |
| Status Callback | (not configured) |

**⚠️ CRITICAL:** The Voice URL MUST point to `/twilio/voice`, NOT `/twilio/webhook`.
The `/twilio/webhook` endpoint returns 422 for voice calls.

---

## Twilio Configuration

### Required Environment Variables
```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+12298215986
```

### TwiML Response Format
The `/twilio/voice` endpoint MUST return this exact TwiML structure:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Connect>
    <Stream url="wss://receptionist.lexmakesit.com/twilio/stream"/>
  </Connect>
</Response>
```

**⚠️ DO NOT use hardcoded localhost or Docker hostnames in the Stream URL.**
Always use the public hostname: `receptionist.lexmakesit.com`

---

## OpenAI Realtime API Configuration

### Model
```python
OPENAI_MODEL = "gpt-4o-realtime-preview"
```

**⚠️ DO NOT change this model name without testing.** Other models may not support realtime audio.

### Behavioral Consistency (Centralized Config)
To ensure 1:1 parity between live calls and offline testing, any changes to AI behavior MUST be made in:
- `backend/ai_receptionist/services/voice/config.py`

This file centralizes `SYSTEM_INSTRUCTIONS` and `TOOLS` for both the live WebSocket and the Shadow AI Referee.

### Session Configuration
```python
session_update = {
    "type": "session.update",
    "session": {
        "modalities": ["audio", "text"],
        "voice": "shimmer",
        "input_audio_format": "g711_ulaw",
        "output_audio_format": "g711_ulaw",
        "turn_detection": {
            "type": "server_vad",
            "threshold": 0.5,
            "prefix_padding_ms": 300,
            "silence_duration_ms": 500
        },
        "temperature": 0.8,
    }
}
```

### Audio Format
- **Format:** g711_ulaw (8kHz, 8-bit μ-law)
- **Reason:** Twilio uses this format for telephony audio

**⚠️ DO NOT change audio format.** Twilio and OpenAI must use the same format.

### Turn Detection
- **Type:** server_vad (Voice Activity Detection)
- **silence_duration_ms:** 500 (responds after 0.5s of silence)

**⚠️ Setting `turn_detection: null` will break conversations.** The AI won't know when to respond.

---

## Docker & Deployment

### Docker Compose Files
- `docker-compose.yml` - Base configuration
- `docker-compose.hotfix.yml` - Override for mounting local code

### Container Name
```
ai_receptionist_app
```

### Network
```
apps_antigravity_net
```

### Volume Mount (for hotfix deployments)
```yaml
volumes:
  - /home/lex/antigravity_bundle/apps/ai_receptionist_new/ai_receptionist:/app/ai_receptionist
```

### Startup Command
```bash
pip install twilio aiohttp && uvicorn ai_receptionist.app.main:app --host 0.0.0.0 --port 8010 --workers 4
```

### Deployment Commands
```bash
# Restart the app
cd /home/lex/antigravity_bundle/apps
docker compose -f docker-compose.yml -f docker-compose.hotfix.yml restart ai_receptionist_app

# View logs
docker logs --tail 100 ai_receptionist_app

# Copy updated file
docker cp /path/to/file.py ai_receptionist_app:/app/ai_receptionist/path/to/file.py
```

---

## Caddy Reverse Proxy

### Caddyfile Location
```
/home/lex/antigravity_bundle/apps/Caddyfile
```

### Receptionist Configuration
```
receptionist.lexmakesit.com {
    reverse_proxy ai_receptionist_app:8010
}
```

### SSL/TLS
- Caddy automatically manages Let's Encrypt certificates
- Domain: `receptionist.lexmakesit.com`
- Resolves to: `104.236.100.245`

**⚠️ DO NOT add path rewrites or modify the proxy configuration.**

---

## Common Failure Modes

### 1. "Application Error" on Call
**Cause:** Twilio can't reach the webhook or gets an error response.
**Check:**
- Is Voice URL set to `/twilio/voice` (not `/twilio/webhook`)?
- Is the app container running?
- Can Caddy resolve `ai_receptionist_app`?

### 2. AI Doesn't Respond After Greeting
**Cause:** `turn_detection` is set to `null` or disabled.
**Fix:** Enable server_vad turn detection.

### 3. 404 on /twilio/voice
**Cause:** Router not registered or wrong prefix.
**Check:**
- `voice_router` has no prefix in `endpoints.py`
- `voice_router` is included with `prefix="/twilio"` in `main.py`

### 4. 502 Bad Gateway
**Cause:** Caddy can't connect to the app container.
**Check:**
- Container is running: `docker ps | grep ai_receptionist_app`
- Containers on same network: `docker network inspect apps_antigravity_net`

### 5. WebSocket Connection Fails
**Cause:** Caddy not proxying WebSocket correctly or SSL issues.
**Check:**
- Caddy logs: `docker logs antigravity_caddy`
- Test locally: `docker exec ai_receptionist_app python ws_test.py`

---

## Testing Checklist

Before deploying any changes, verify:

- [ ] `curl -X POST https://receptionist.lexmakesit.com/twilio/voice -d "CallSid=test&From=test"` returns TwiML
- [ ] TwiML contains `<Stream url="wss://receptionist.lexmakesit.com/twilio/stream"/>`
- [ ] WebSocket test connects successfully
- [ ] Container logs show "OpenAI Realtime API" connection
- [ ] Make test call - AI speaks greeting
- [ ] Make test call - AI responds to user speech

### Quick Test Commands
```bash
# Test voice endpoint
curl -X POST https://receptionist.lexmakesit.com/twilio/voice \
  -d "CallSid=test&From=test"

# Check container status
ssh droplet "docker ps | grep ai_receptionist"

# View recent logs
ssh droplet "docker logs --tail 50 ai_receptionist_app"

# Test WebSocket from container
ssh droplet "docker exec ai_receptionist_app python /app/ws_test.py wss://receptionist.lexmakesit.com/twilio/stream"
```

---

## Environment Variables Reference

### Required
| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for Realtime API | `sk-...` |
| `TWILIO_ACCOUNT_SID` | Twilio Account SID | `ACxxx` |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token | `xxx` |
| `TWILIO_PHONE_NUMBER` | Twilio phone number | `+12298215986` |

### Optional
| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection | `postgresql://...` |
| `REDIS_URL` | Redis connection | `redis://...` |
| `APP_ENV` | Environment name | `local` |

---

## Shadow AI & Behavioral Parity

### Architecture Principle: "The Silent Referee"
To prevent hallucinations and behavioral drift, every call generates a `ConversationFrame` which is replayed through a Shadow AI.

1. **Zero-Latency Requirement:** Shadow evaluation is an asynchronous background task. It must NEVER block the live WebSocket or increase response time.
2. **Synchronization Principle:** We do not sync audio or raw sessions; we sync **Structured Conversation Frames**.
   - **`ConversationFrame` Schema:** Includes `caller_id`, `timezone`, and a list of `turns`.
   - **`Turn` Metadata:** Each turn includes `intent`, `tool_calls`, and the **`tool_result`** (e.g., "Available", "Busy"). This allows the Shadow AI to see the exact outcome the live AI acted upon.

### The 1:1 Parity Rule
To guarantee behavioral parity, the Shadow AI must be initialized with the exact same:
- **System Instructions**: Formatted with identical business context and dynamic values.
- **Tools**: Reused from `config.py`.
- **Temporal Context**: Both environments must receive the same `Current Date` and `Current Timezone`.

### Benchmarking & The "Golden Standard"
We maintain a `golden_frames.json` (50+ scenarios) that represents ground-truth behavior.
- **Target Accuracy**: 90%+ Match Score.
- **Target Parity**: 100% Tool Call Parity (The Shadow AI makes the same API decisions as Live).

### Real-World Actions (Gating)
Real-world actions (e.g., Google Calendar booking) are simulated in evaluation but strictly enforced in live calls.
- Evaluation logic must explicitly return failure if it attempts a real write action without authorization.

---

## Evaluation, Logging, and Drift Control Plan

### 🎯 System Goal
Continuously improve real-world performance while preventing regressions, detecting drift, and scaling evaluation intelligently as usage grows. This system treats conversational intelligence like software with tests, not "vibes."

### 🧠 Core Concepts
- **Golden Frames**: A canonical conversation scenario with user intent, context, and expected behavior. They act as unit tests for the AI.
- **Conversation Frame**: A structured snapshot of utterances, responses, inferred intent, tools invoked, and outcomes.

### 📌 Phase 1 — Early Coverage (Pre-Scale Robustness)
- **Objective**: Establish a baseline evaluation set beyond minimal demos.
- **Actions**: Maintain 25–50 golden frames (already achieved) covering core scenarios, natural language variations (slang, verbose, fragmented), and conversational nuance (hesitations, interruptions).
- **Success Criteria**: AI handles semantic variation without intent collapse.

### 📌 Phase 2 — Production Growth (Reality-Driven Expansion)
- **Objective**: Move from "imagined" scenarios to "real-world" complexity.
- **Actions**: Log real conversation frames that fail or show ambiguity. human review classifies failures and promotes validated frames into the golden dataset (`golden_frames_v2.json`, etc.).
- **Principle**: Golden frames MUST evolve from production reality.

### 📌 Phase 3 — Continuous Drift Monitoring (AI as Software)
- **Objective**: Detect regressions from prompt edits, model upgrades, or backend changes.
- **Enforcement Rules**: Execute Golden Frames on every prompt/model change. Failures block deployment.
- **Outcome**: quantified improvement and tracking accuracy over time.

### 📊 Logging Schema (Mandatory Fields)
Each logged call MUST capture:
- **Core**: `conversation_frame_id`, `timestamp_start/end`, `latency_ms`.
- **Semantic**: `intent_classification`, `confidence_score`, `state_transition`.
- **Tooling**: `tool_calls[]`, `tool_outcomes[]`, `tool_failures[]`.
- **Signals**: `user_correction_detected`, `handoff_requested`, `user_satisfaction_signal`.

### 🔁 Operational Rulebook (Rolling Evaluation Windows)
| Interval | Purpose |
|----------|---------|
| First 100–200 calls | Launch stability verification |
| Every 500 calls | Golden frame expansion & edge detection |
| Every 1,000–5,000 calls | Drift detection & statistical confidence |
| Continuous | Automated performance monitoring |

### 🧠 System Philosophy (Non-Negotiable)
- AI systems are probabilistic, not deterministic.
- Evaluation requires **distributional thinking**.
- Logging **quality** > logging volume.
- Production reality is the ultimate source of truth.

---

## Modular Integrity & Non-Negotiable Constraints

### ⏳ 1. Temporal Authority (Duration & Timestamps)
The AI module is **NOT** authoritative for time-based metrics.
- **Duration**: Computed ONLY by the backend using `ended_at - answered_at`. The AI must never infer, calculate, or estimate duration from transcript timestamps.
- **Timestamps**: All timestamps MUST be stored as opaque UTC values. Localization happens ONLY at the UI edge.
- **Constraints**: No conversion, no timezone guessing, no approximation.

### 👤 2. Identity & Naming (User-Stated Authority)
User-stated identity is the absolute source of truth.
- **Override Rule**: If a caller identifies themselves (e.g., "My name is Alex"), this value MUST override Caller ID or CRM lookups immediately.
- **Identity Event**: An `identity_update` event must be emitted immediately upon detection.
- **Persistance**: Do not assume identity persists across separate calls unless explicitly verified.

### 🚫 3. Hallucination Guardrails
- If information is missing (e.g., call start time): **Emit no event.**
- Do not approximate or "best guess" system values.
- The AI's role is conversational, not administrative for system state.

## 14. Frontend Assets & Branding

### Wallpaper / Backgrounds
- **Critical Asset**: `waterfall.gif`
- **Location**: `/home/lex/lexmakesit/frontend/portfolio/static/images/waterfall.gif`
- **Usage**: Used as the primary background for:
  - Main Portfolio (`index.html`)
  - Pricing Page (`pricing.html`)
- **Note**: Do not delete or rename this file. CSS references rely on it being exactly at `/static/images/waterfall.gif`.

## Version History

| Date | Change | Author |
|------|--------|--------|
| 2025-12-14 | Fixed Twilio webhook URL from /webhook to /voice | AI Assistant |
| 2025-12-14 | Enabled server_vad turn detection | AI Assistant |
| 2025-12-14 | Created source of truth document | AI Assistant |
| 2026-01-22 | Implemented Shadow AI Testing & 50-Frame Golden Benchmark | Antigravity |
| 2026-01-22 | Consolidated temporal and identity constraints | Antigravity |

---

**⚠️ FINAL WARNING:** This system is working as of 2026-01-22. If you're an AI assistant and the user reports it's broken or hallucinating, use the **Shadow AI Benchmark** (`backend/tests/test_shadow_replay.py`) to verify parity before troubleshooting.
