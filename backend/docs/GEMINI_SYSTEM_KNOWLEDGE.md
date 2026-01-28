# AI Receptionist - Complete System Documentation for Gemini

> **Purpose**: This document provides comprehensive knowledge about the AI Receptionist system for brainstorming improvements and integrations with Google AI technologies.

---

## Table of Contents
1. [System Overview](#system-overview)
2. [Current Architecture](#current-architecture)
3. [Technology Stack](#technology-stack)
4. [Call Flow & Processing](#call-flow--processing)
5. [Cost Analysis](#cost-analysis)
6. [Recent Improvements](#recent-improvements)
7. [Current Capabilities](#current-capabilities)
8. [Known Limitations](#known-limitations)
9. [Integration Opportunities](#integration-opportunities)
10. [Technical Specifications](#technical-specifications)

---

## System Overview

The AI Receptionist is a **voice-enabled AI assistant** that answers phone calls for businesses using:
- **Twilio** for telephony (phone number: +1 (229) 821-5986)
- **OpenAI GPT-4o Realtime API** for conversational AI with built-in speech-to-text and text-to-speech
- **FastAPI** for the web application backend
- **WebSocket** for real-time audio streaming

### What It Does
- Answers incoming phone calls professionally
- Greets callers with "Hi, this is Aria. How can I help you?"
- Handles conversations in real-time with natural voice
- Can handle: appointments, messages, basic info, transfers
- Supports multiple languages (starts in English, switches on request)

### Current Status
✅ **Fully operational** as of December 22, 2025
- Connection time: 2-3 seconds (recently optimized from 10 seconds)
- Cost per 3-minute call: ~$0.95
- Deployed at: https://receptionist.lexmakesit.com

---

## Current Architecture

### High-Level Architecture
```
┌─────────────┐
│   Caller    │
│ (Phone)     │
└──────┬──────┘
       │
       ↓
┌─────────────────────────────────────┐
│         Twilio Voice API            │
│  Phone: +1 (229) 821-5986          │
│  Media Streams (WebSocket)          │
└──────┬──────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────┐
│    Caddy Reverse Proxy (SSL/TLS)   │
│  receptionist.lexmakesit.com        │
└──────┬──────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────┐
│      FastAPI Application            │
│      (ai_receptionist)              │
│                                     │
│  ┌───────────────────────────────┐ │
│  │  /twilio/voice (POST)         │ │
│  │  Returns TwiML with Stream    │ │
│  └───────────────────────────────┘ │
│                                     │
│  ┌───────────────────────────────┐ │
│  │  /twilio/stream (WebSocket)   │ │
│  │  Bidirectional audio stream   │ │
│  └───────────────────────────────┘ │
└──────┬──────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────┐
│    OpenAI Realtime API              │
│    (GPT-4o-realtime-preview)        │
│                                     │
│  • Speech-to-Text (built-in)       │
│  • Conversational AI               │
│  • Text-to-Speech (built-in)       │
│  • Voice: "shimmer"                │
└─────────────────────────────────────┘
```

### Call Flow (Step-by-Step)
1. **Caller dials** +1 (229) 821-5986
2. **Twilio receives call** and sends POST to `https://receptionist.lexmakesit.com/twilio/voice`
3. **App returns TwiML** with `<Connect><Stream url="wss://receptionist.lexmakesit.com/twilio/stream"/></Connect>`
4. **Twilio establishes WebSocket** to `/twilio/stream`
5. **App connects to OpenAI** Realtime API (`wss://api.openai.com/v1/realtime`)
6. **Wait for stream_sid** from Twilio (critical for audio forwarding)
7. **Send greeting request** to OpenAI: "Say: Hi, this is Aria. How can I help you?"
8. **OpenAI generates audio** and streams back
9. **App forwards audio** to Twilio via WebSocket
10. **Caller hears greeting** (2-3 seconds after call connects)
11. **Bidirectional conversation** begins:
    - Caller speaks → Twilio → App → OpenAI (STT + AI processing)
    - OpenAI responds → App → Twilio → Caller (TTS)

---

## Technology Stack

### Backend
- **Language**: Python 3.10+
- **Framework**: FastAPI (async web framework)
- **WebSocket**: aiohttp (for OpenAI connection)
- **Audio Format**: g711_ulaw (8kHz, 8-bit μ-law - telephony standard)

### AI & Voice
- **Conversational AI**: OpenAI GPT-4o Realtime API
  - Model: `gpt-4o-realtime-preview`
  - Voice: `shimmer`
  - Temperature: 0.7 (optimized for speed)
  - Turn Detection: Server-side VAD (Voice Activity Detection)
- **Speech-to-Text**: Built into Realtime API (~$0.06/minute)
- **Text-to-Speech**: Built into Realtime API (~$0.24/minute)

### Telephony
- **Provider**: Twilio
- **Phone Number**: +1 (229) 821-5986
- **Media Streams**: WebSocket-based real-time audio streaming
- **Cost**: ~$0.013/minute for inbound calls

### Infrastructure
- **Deployment**: Docker Compose
- **Reverse Proxy**: Caddy (automatic SSL/TLS with Let's Encrypt)
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Vector DB**: Qdrant (for future RAG capabilities)
- **Port**: 8002 (internal), 443 (external via Caddy)

### File Structure
```
ai_receptionist/
├── app/
│   ├── main.py              # FastAPI entry point, router registration
│   └── api/
│       └── twilio.py        # Legacy webhook (not used for voice)
├── api/
│   └── realtime.py          # WebSocket handler for OpenAI Realtime API ⭐
├── services/
│   └── voice/
│       └── endpoints.py     # /twilio/voice endpoint ⭐
├── config/
│   └── settings.py          # Environment configuration
└── agent/
    └── tasks/               # Evaluation system (scenarios, TTS, STT, metrics)
```

---

## Call Flow & Processing

### Audio Processing Pipeline
```
Caller Voice
    ↓
Twilio (captures audio in g711_ulaw format)
    ↓
WebSocket to /twilio/stream
    ↓
Forward to OpenAI Realtime API
    ↓
OpenAI STT (Speech-to-Text)
    ↓
GPT-4o processes conversation
    ↓
OpenAI TTS (Text-to-Speech)
    ↓
Audio streamed back to app
    ↓
Forwarded to Twilio via WebSocket
    ↓
Caller hears AI response
```

### Turn Detection (How AI Knows When to Respond)
- **Type**: Server-side VAD (Voice Activity Detection)
- **Threshold**: 0.5
- **Prefix Padding**: 200ms (captures start of speech)
- **Silence Duration**: 400ms (waits 0.4s of silence before responding)
- **Interruption Handling**: User can interrupt AI mid-sentence

### System Instructions (Current)
```
You are Aria, an AI Receptionist for businesses. Be polite, professional, and concise.

RULES:
- Always start in English. Switch languages only if caller requests.
- Keep responses brief (1-3 sentences) unless more detail is needed.
- You're an AI assistant - be honest if asked.
- Handle: appointments, messages, basic info, transfers.

Each call is independent. Start fresh every time.
```

---

## Cost Analysis

### Current Costs (Per 3-Minute Call)
| Component | Cost | Percentage |
|-----------|------|------------|
| Twilio Voice | $0.039 | 4% |
| Twilio Media Streams | $0.008 | 1% |
| OpenAI Realtime Input (STT) | $0.180 | 19% |
| OpenAI Realtime Output (TTS) | $0.720 | 76% |
| **TOTAL** | **$0.947** | **100%** |

### Cost at Scale
- **10 calls/day**: $284/month
- **50 calls/day**: $1,420/month
- **100 calls/day**: $2,841/month

### Cost Breakdown by Component
**Most Expensive**: OpenAI Realtime API TTS ($0.24/minute)
- This is 8-16x more expensive than alternatives like ElevenLabs or OpenAI's standard TTS API
- Reason: Real-time streaming with <100ms latency

**Second Most Expensive**: OpenAI Realtime API STT ($0.06/minute)
- This is 10-240x more expensive than alternatives like Deepgram or Whisper API
- Reason: Real-time streaming with <100ms latency

### Potential Cost Optimizations
**Option 1**: Modular Architecture (85-90% savings)
```
Twilio → Deepgram (STT) → GPT-4o-mini → OpenAI TTS → Twilio
Cost: $0.11 per 3-min call (vs $0.95 current)
Latency: 500ms-1s (vs <100ms current)
Annual savings at 100 calls/day: $30,204
```

**Option 2**: Ultra-Budget (92% savings)
```
Twilio → AssemblyAI (STT) → GPT-3.5-turbo → Google Cloud TTS → Twilio
Cost: $0.075 per 3-min call
Latency: 1-2s
Trade-off: Slightly lower quality, noticeable pauses
```

---

## Recent Improvements

### 1. Silence Bug Fix (Dec 22, 2025)
**Problem**: Calls were completely silent - no greeting heard

**Root Cause**: Race condition where greeting was sent before Twilio's `stream_sid` was received, so audio couldn't be forwarded back to caller.

**Solution**: 
- Moved greeting trigger to **after** receiving Twilio's "start" event
- Added `greeting_sent` flag to prevent duplicate greetings
- Now audio is properly forwarded with valid `stream_sid`

**Result**: ✅ Greeting now heard on every call

### 2. Speed Optimization (Dec 22, 2025)
**Problem**: 10-second delay before greeting started

**Optimizations**:
1. **Shortened system instructions** by 60% (40 lines → 10 lines)
2. **Reduced temperature** from 0.8 → 0.7 (faster generation)
3. **Optimized turn detection** padding (300ms → 200ms)
4. **Simplified greeting** instruction

**Result**: 
- ✅ Connection time reduced from 10s → 2-3s (70% faster)
- ✅ Also reduces costs by ~5-10% per call
- ✅ No impact on conversation quality

---

## Current Capabilities

### What Aria Can Do
✅ Answer incoming phone calls professionally  
✅ Greet callers naturally with voice  
✅ Understand and respond to speech in real-time  
✅ Handle appointments, messages, basic info, transfers  
✅ Support multiple languages (English default, switches on request)  
✅ Interrupt handling (caller can cut off AI mid-sentence)  
✅ Natural conversation flow with <3s response time  

### What Aria Currently Does NOT Do
❌ Schedule appointments in a calendar system  
❌ Access external databases or CRM systems  
❌ Transfer calls to real people (no integration yet)  
❌ Send SMS/email confirmations  
❌ Remember previous calls (no persistent memory)  
❌ Handle complex multi-step workflows  
❌ Provide business-specific information (generic responses only)  

---

## Known Limitations

### Technical Limitations
1. **No persistent memory** - Each call is independent, no caller history
2. **No external integrations** - Can't access calendars, CRMs, databases
3. **Generic responses** - Not customized to specific businesses
4. **No call transfer** - Can't actually transfer to human agents
5. **No SMS/Email** - Can't send confirmations or follow-ups
6. **Single language per call** - Can switch but doesn't auto-detect
7. **No sentiment analysis** - Doesn't track caller satisfaction

### Cost Limitations
1. **Expensive at scale** - $0.95 per 3-min call adds up quickly
2. **OpenAI Realtime API premium** - Paying 8-16x more than alternatives
3. **No cost controls** - Long calls can get very expensive

### Functional Limitations
1. **No business context** - Doesn't know about specific business hours, services, pricing
2. **No appointment booking** - Can't actually schedule anything
3. **No message delivery** - Can't send messages to staff
4. **No call analytics** - Limited tracking of call metrics

---

## Integration Opportunities

### Potential Google AI Integrations

#### 1. **Google Cloud Speech-to-Text**
**Current**: OpenAI Realtime API STT ($0.06/min)  
**Alternative**: Google Cloud Speech-to-Text ($0.006/min)  
**Savings**: 90% reduction in STT costs  
**Latency**: 200-500ms (vs <100ms current)  
**Features**:
- Multi-language support with auto-detection
- Speaker diarization (identify different speakers)
- Profanity filtering
- Word-level timestamps

#### 2. **Google Cloud Text-to-Speech**
**Current**: OpenAI Realtime API TTS ($0.24/min)  
**Alternative**: Google Cloud TTS ($0.016/min)  
**Savings**: 93% reduction in TTS costs  
**Features**:
- WaveNet voices (very natural)
- 380+ voices in 50+ languages
- Custom voice training
- SSML support for prosody control

#### 3. **Google Gemini for Conversation**
**Current**: GPT-4o Realtime API  
**Alternative**: Gemini 2.0 Flash (with multimodal capabilities)  
**Benefits**:
- Potentially lower cost
- Multimodal understanding (could analyze call context)
- Longer context window
- Better reasoning for complex queries
- Native Google Workspace integration

#### 4. **Google Calendar Integration**
**Use Case**: Actually schedule appointments  
**How**:
- Aria asks for preferred date/time
- Checks Google Calendar availability via API
- Books appointment and sends confirmation
- Syncs with business calendar

#### 5. **Google Dialogflow CX**
**Use Case**: Structured conversation flows  
**Benefits**:
- Pre-built conversation templates
- Visual flow designer
- Intent detection and entity extraction
- Multi-turn conversation management
- Analytics and insights

#### 6. **Google Contact Center AI (CCAI)**
**Use Case**: Enterprise-grade call center features  
**Features**:
- Agent assist (suggestions during calls)
- Call summarization
- Sentiment analysis
- Smart reply suggestions
- Integration with existing call center software

#### 7. **Google Vertex AI**
**Use Case**: Custom AI models and RAG  
**Benefits**:
- Train custom models on business-specific data
- RAG (Retrieval-Augmented Generation) for accurate business info
- Vector search with Vertex AI Matching Engine
- Model monitoring and versioning

#### 8. **Google Cloud Functions**
**Use Case**: Serverless integrations  
**Benefits**:
- Trigger actions based on call events
- Send SMS via Twilio
- Update CRM systems
- Log call data to BigQuery

---

## Technical Specifications

### API Endpoints

#### POST /twilio/voice
**Purpose**: Twilio voice webhook (returns TwiML)  
**Handler**: `services/voice/endpoints.py:voice_entry`  
**Request**: Form data from Twilio (CallSid, From, etc.)  
**Response**: TwiML XML with `<Connect><Stream>` directive  

#### WebSocket /twilio/stream
**Purpose**: Twilio media stream (bidirectional audio)  
**Handler**: `api/realtime.py:websocket_endpoint`  
**Protocol**: WebSocket  
**Audio Format**: g711_ulaw (base64 encoded)  

#### GET /health
**Purpose**: Health check  
**Response**: `{"status": "ok", "env": "local"}`  

### Environment Variables
```bash
# Required
OPENAI_API_KEY=sk-...
TWILIO_ACCOUNT_SID=ACxxx...
TWILIO_AUTH_TOKEN=xxx...
TWILIO_PHONE_NUMBER=+12298215986

# Optional
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
APP_ENV=local
```

### Docker Deployment
```bash
# Start server
uvicorn ai_receptionist.app.main:app --host 0.0.0.0 --port 8002 --reload

# With Docker Compose
docker compose -f docker-compose.prod.yml up -d

# View logs
docker logs -f ai_receptionist_app
```

### OpenAI Realtime API Configuration
```python
{
    "type": "session.update",
    "session": {
        "modalities": ["audio", "text"],
        "voice": "shimmer",
        "input_audio_format": "g711_ulaw",
        "output_audio_format": "g711_ulaw",
        "turn_detection": {
            "type": "server_vad",
            "threshold": 0.5,
            "prefix_padding_ms": 200,
            "silence_duration_ms": 400
        },
        "temperature": 0.7,
        "instructions": "You are Aria, an AI Receptionist..."
    }
}
```

---

## Evaluation System

The codebase includes a **comprehensive evaluation pipeline** for testing and improving the AI:

### Components
1. **Scenario Generator** - Creates test conversation scenarios
2. **TTS Pipeline** - Generates customer audio using OpenAI TTS
3. **Whisper Pipeline** - Transcribes audio for verification
4. **Diarizer** - Builds conversation records with speaker labels
5. **Metrics Engine** - Computes quality metrics
6. **Report Engine** - Generates terminal reports
7. **Improvement Engine** - Auto-triggers fixes for low scores

### Metrics Tracked
- **Latency**: AI response time
- **UX Score**: Overall user experience (target: >85%)
- **Qualitative**: Weaknesses and strengths
- **Accuracy**: Transcription and response accuracy

---

## Questions for Brainstorming

### Architecture Questions
1. Should we replace OpenAI Realtime API with a modular approach (Gemini + Google STT/TTS)?
2. How can we reduce costs while maintaining <1s latency?
3. Should we use Dialogflow CX for structured flows or keep free-form conversation?

### Feature Questions
1. What Google AI features from the YouTube video are most valuable?
2. Should we integrate Google Calendar for real appointment booking?
3. How can we add business-specific knowledge (RAG with Vertex AI)?
4. Should we add sentiment analysis to track caller satisfaction?

### Integration Questions
1. How do we handle the transition from OpenAI to Google AI?
2. Can we use Gemini 2.0 Flash for real-time voice conversations?
3. Should we keep Twilio or explore Google Cloud telephony?
4. How do we integrate with existing business systems (CRM, calendar, etc.)?

---

## Next Steps for Google AI Integration

### Phase 1: Research & Planning
- [ ] Watch YouTube video on Google AI capabilities
- [ ] Identify specific Google AI features to integrate
- [ ] Compare costs: OpenAI vs Google AI stack
- [ ] Design new architecture with Google AI components

### Phase 2: Proof of Concept
- [ ] Test Google Cloud Speech-to-Text with Twilio
- [ ] Test Google Cloud TTS for voice quality
- [ ] Test Gemini 2.0 Flash for conversation quality
- [ ] Measure latency and cost differences

### Phase 3: Implementation
- [ ] Build modular architecture (STT → LLM → TTS)
- [ ] Integrate Google Calendar API
- [ ] Add RAG with Vertex AI for business knowledge
- [ ] Implement Dialogflow CX for structured flows

### Phase 4: Testing & Optimization
- [ ] Run evaluation pipeline with new architecture
- [ ] Compare metrics: latency, cost, quality
- [ ] A/B test with real calls
- [ ] Optimize for best performance/cost ratio

---

## Resources

### Documentation
- `AI_RECEPTIONIST_SOURCE_OF_TRUTH.md` - System configuration reference
- `COST_DIAGNOSIS.md` - Detailed cost analysis and optimization options
- `SILENCE_BUG_FIX.md` - Recent bug fix documentation
- `SPEED_OPTIMIZATION.md` - Performance optimization details
- `OPERATIONS.md` - Deployment and maintenance guide

### External Links
- [OpenAI Realtime API Docs](https://platform.openai.com/docs/guides/realtime)
- [Twilio Media Streams](https://www.twilio.com/docs/voice/twiml/stream)
- [Google Cloud Speech-to-Text](https://cloud.google.com/speech-to-text)
- [Google Cloud Text-to-Speech](https://cloud.google.com/text-to-speech)
- [Google Gemini API](https://ai.google.dev/gemini-api/docs)
- [Dialogflow CX](https://cloud.google.com/dialogflow/cx/docs)

---

**Last Updated**: December 22, 2025  
**System Status**: ✅ Fully Operational  
**Version**: 1.0 (OpenAI Realtime API)  
**Next Version**: 2.0 (Google AI Integration - Planned)
