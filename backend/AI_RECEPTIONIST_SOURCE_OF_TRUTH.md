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

## Version History

| Date | Change | Author |
|------|--------|--------|
| 2025-12-14 | Fixed Twilio webhook URL from /webhook to /voice | AI Assistant |
| 2025-12-14 | Enabled server_vad turn detection | AI Assistant |
| 2025-12-14 | Created source of truth document | AI Assistant |

---

**⚠️ FINAL WARNING:** This system is working as of 2025-12-14. If you're an AI assistant and the user reports it's broken, assume YOUR previous actions broke it and use this document to restore it.
