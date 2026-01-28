"""
Voice conversation endpoints for Twilio integration.

Handles incoming calls, language selection, and conversation flow.

CRITICAL DESIGN PRINCIPLE:
The /voice endpoint MUST return valid TwiML within ~1-2 seconds.
Twilio will play "system temporarily unavailable" if:
1) Webhook times out (> ~15 seconds)
2) Webhook returns malformed or non-XML TwiML
3) Webhook returns 200 OK with empty body
4) Webhook crashes mid-request (exception after headers sent)
5) Webhook blocks on async work BEFORE returning TwiML

Therefore: NO async work (OpenAI, DB, Redis, HTTP) before TwiML return.
All slow operations are moved to background tasks or the /stream handler.
"""

import logging
import json
import asyncio
import aiohttp
from fastapi import APIRouter, Form, Request, Response, WebSocket, WebSocketDisconnect, BackgroundTasks
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client
from twilio.request_validator import RequestValidator
import math
import time
from datetime import datetime, timezone

from ai_receptionist.services.voice.business_config import BUSINESS_NAME
from ai_receptionist.services.voice.session import get_session, clear_session
from ai_receptionist.services.voice.cost_tracker import get_cost_tracker
from ai_receptionist.services.voice.messages import LANGUAGE_SELECTION_COMBINED, get_message
from ai_receptionist.services.voice.intents import detect_intent, handle_intent
from ai_receptionist.config.settings import Settings, get_settings
from ai_receptionist.core.database import get_db, get_db_session, get_session_local
from sqlalchemy.orm import Session
from fastapi import Depends
from ai_receptionist.models.call import Call

logger = logging.getLogger(__name__)

# Optional call monitor integration
try:
    from call_monitor import monitor
    MONITOR_ENABLED = True
except ImportError:
    MONITOR_ENABLED = False
    monitor = None
    logger.debug("Call monitor not available")


print("DEBUG: Loading ai_receptionist.services.voice.endpoints module", flush=True)
from fastapi import Depends
from ai_receptionist.core.limiter import limiter
router = APIRouter(tags=["voice"])  # prefix moved to main.py


# Emergency TwiML for when the main handler fails - static, pre-computed
_EMERGENCY_TWIML = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Thank you for calling. We are experiencing technical difficulties. Please try again in a moment.</Say>
    <Hangup/>
</Response>"""


def _ms_since(start_time: float) -> int:
    """Return milliseconds elapsed since start_time."""
    return int((time.perf_counter() - start_time) * 1000)


def _background_log_call(
    call_sid: str,
    from_number: str,
    to_number: str,
    business_id: int,
):
    """
    Background task to log the call to database AFTER TwiML has been returned.
    This ensures we don't block the TwiML response.
    """
    try:
        # Create a new session for the background task
        SessionLocal = get_session_local()
        db = SessionLocal()
        try:
            new_call = Call(
                business_id=business_id,
                call_sid=call_sid,
                from_number=from_number,
                to_number=to_number,
                status="in-progress"
            )
            db.add(new_call)
            db.commit()
            logger.info(f"[VOICE-BG] Created call record for {call_sid}")
        except Exception as e:
            logger.error(f"[VOICE-BG] Failed to create call record: {e}")
            db.rollback()
        finally:
            db.close()
    except Exception as e:
        logger.error(f"[VOICE-BG] Background logging error: {e}")


def _background_spam_check(
    call_sid: str,
    from_number: str,
    account_sid: str,
    auth_token: str,
):
    """
    Background task to log spam screening results AFTER TwiML has been returned.
    We can't block calls based on this, but we can log for analytics.
    """
    try:
        client = Client(account_sid, auth_token)
        lookup = client.lookups.v2.phone_numbers(from_number).fetch(
            fields='line_type_intelligence,phone_number_quality_score'
        )
        line_type = lookup.line_type_intelligence.get('type') if lookup.line_type_intelligence else "unknown"
        risk_score = lookup.phone_number_quality_score.get('score') if lookup.phone_number_quality_score else 0
        logger.info(f"[VOICE-BG] Spam Check [{from_number}]: Type={line_type}, Score={risk_score}")
    except Exception as e:
        logger.debug(f"[VOICE-BG] Spam check skipped: {e}")


@router.post("/voice")
@limiter.limit("20/minute")
async def voice_entry(
    request: Request, 
    background_tasks: BackgroundTasks,
    CallSid: str = Form(...), 
    From: str = Form(None),
    To: str = Form(None),
    settings: Settings = Depends(get_settings),
):
    """
    Entry point for incoming calls.
    
    CRITICAL DESIGN (Production-safe):
    - This endpoint MUST return valid TwiML within 1-2 seconds
    - NO async work (OpenAI, external HTTP, Redis) before TwiML return
    - Only allowed await: request.form() for signature validation
    - All slow operations (DB writes, spam checks) run in background tasks
    - Any exception returns emergency TwiML (never crashes)
    
    The business lookup and validation now happens in the /stream WebSocket handler
    where we have time to do proper checks.
    """
    t0 = time.perf_counter()
    
    try:
        return await _voice_entry_inner(request, background_tasks, CallSid, From, To, settings, t0)
    except Exception as e:
        elapsed = _ms_since(t0)
        logger.error(f"[VOICE] CRITICAL EXCEPTION at t={elapsed}ms for {CallSid}: {e}", exc_info=True)
        twiml = _EMERGENCY_TWIML
        logger.info(f"[VOICE] Returning emergency TwiML, len={len(twiml)} bytes, t={_ms_since(t0)}ms")
        return Response(content=twiml, media_type="application/xml", status_code=200)


async def _voice_entry_inner(
    request: Request,
    background_tasks: BackgroundTasks,
    CallSid: str,
    From: str,
    To: str,
    settings: Settings,
    t0: float,
):
    """
    Inner implementation of voice entry.
    
    TIMING BUDGET (must complete in <500ms total):
    - request.form(): ~5-20ms
    - signature validation: ~1-5ms
    - TwiML generation: ~1-5ms
    
    NO ALLOWED:
    - Database queries
    - External HTTP calls (Twilio Lookup, OpenAI)
    - Redis operations
    - WebSocket setup
    """
    logger.info(f"[VOICE] received at t=0ms | CallSid={CallSid}, From={From}, To={To}")
    
    # --- STEP 1: Signature Validation (only allowed await) ---
    sig_start = time.perf_counter()
    
    if settings.enable_twilio_signature:
        token_status = "present" if settings.twilio_auth_token else "MISSING"
        logger.info(f"[VOICE] auth_token={token_status} at t={_ms_since(t0)}ms")
        
        if not settings.twilio_auth_token:
            logger.error(f"[VOICE] CRITICAL: twilio_auth_token is None at t={_ms_since(t0)}ms")
            # Return emergency TwiML - can't validate without token
            twiml = _EMERGENCY_TWIML
            logger.info(f"[VOICE] response sent (no token) at t={_ms_since(t0)}ms, len={len(twiml)}")
            return Response(content=twiml, media_type="application/xml", status_code=200)
        
        try:
            form_data = await request.form()
            params = dict(form_data)
            logger.info(f"[VOICE] form parsed at t={_ms_since(t0)}ms")
            
            validator = RequestValidator(settings.twilio_auth_token)
            
            # Get the URL - Twilio signs with the public URL, so we need to reconstruct it
            # Behind a reverse proxy, request.url may have wrong scheme/host
            original_url = str(request.url)
            
            # Reconstruct the public-facing URL that Twilio used
            # Twilio always uses HTTPS for webhook URLs
            public_url = f"https://{settings.public_host}/twilio/voice"
            
            signature = request.headers.get("X-Twilio-Signature")
            
            logger.info(f"[VOICE] original_url={original_url} at t={_ms_since(t0)}ms")
            logger.info(f"[VOICE] public_url={public_url} at t={_ms_since(t0)}ms")
            logger.info(f"[VOICE] sig_header_present={bool(signature)} at t={_ms_since(t0)}ms")
            
            # Try validating with both URLs for robustness
            is_valid = False
            if signature:
                # First try with the public URL (most likely to match)
                is_valid = validator.validate(public_url, params, signature)
                if not is_valid:
                    # Fall back to original URL in case Twilio used a different path
                    is_valid = validator.validate(original_url, params, signature)
                    if is_valid:
                        logger.info(f"[VOICE] validated with original_url")
                else:
                    logger.info(f"[VOICE] validated with public_url")
            
            logger.info(f"[VOICE] signature validated={is_valid} at t={_ms_since(t0)}ms")
            
            if not signature or not is_valid:
                logger.warning(f"[VOICE] REJECTED (invalid sig) at t={_ms_since(t0)}ms | CallSid={CallSid}")
                return Response(status_code=403)
                
        except Exception as sig_error:
            logger.error(f"[VOICE] sig validation error at t={_ms_since(t0)}ms: {sig_error}")
            # On validation error, still return TwiML (don't crash the call)
    
    sig_elapsed = _ms_since(sig_start)
    logger.info(f"[VOICE] signature phase complete in {sig_elapsed}ms")
    
    # --- STEP 2: Generate TwiML IMMEDIATELY ---
    # NO database queries, NO external HTTP, NO Redis
    # Business validation happens in /stream handler where we have time
    
    twiml_start = time.perf_counter()
    
    # Build TwiML response for Streaming
    public_host = settings.public_host
    stream_url = f"wss://{public_host}/twilio/stream"
    
    resp = VoiceResponse()
    connect = resp.connect()
    stream = connect.stream(url=stream_url)
    
    # Pass all context to stream handler - it will do validation there
    stream.parameter(name="call_sid", value=CallSid)
    stream.parameter(name="from_number", value=From or "")
    stream.parameter(name="to_number", value=To or "")
    stream.parameter(name="start_timestamp", value=str(time.time()))
    
    twiml = str(resp)
    twiml_elapsed = _ms_since(twiml_start)
    
    logger.info(f"[VOICE] twiml generated at t={_ms_since(t0)}ms (took {twiml_elapsed}ms)")
    logger.info(f"[VOICE] stream_url={stream_url}")
    logger.debug(f"[VOICE] twiml content: {twiml[:200]}...")
    
    # --- STEP 3: Schedule Background Tasks (run AFTER response) ---
    # These do NOT block TwiML return
    
    # Log call to database in background
    # We use business_id=1 as default; the stream handler will update this
    background_tasks.add_task(
        _background_log_call,
        call_sid=CallSid,
        from_number=From,
        to_number=To,
        business_id=1,  # Default, stream handler can update
    )
    
    # Spam screening in background (for analytics, not blocking)
    if From and settings.twilio_account_sid and settings.twilio_auth_token:
        background_tasks.add_task(
            _background_spam_check,
            call_sid=CallSid,
            from_number=From,
            account_sid=settings.twilio_account_sid,
            auth_token=settings.twilio_auth_token,
        )
    
    # Optional call monitor
    if MONITOR_ENABLED and monitor:
        background_tasks.add_task(monitor.log_incoming_call, CallSid, From)
    
    # Initialize cost tracking (fast, in-memory)
    tracker = get_cost_tracker(CallSid)
    tracker.log_inbound_call(duration_seconds=0)
    
    # --- STEP 4: Return Response ---
    total_elapsed = _ms_since(t0)
    logger.info(f"[VOICE] response sent at t={total_elapsed}ms | len={len(twiml)} bytes | Content-Type=application/xml")
    
    return Response(content=twiml, media_type="application/xml", status_code=200)


@router.post("/language-selected")
async def language_selected(
    request: Request, 
    CallSid: str = Form(...), 
    Digits: str = Form(None), 
    SpeechResult: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    Handle language selection.
    1 = English, 2 = Spanish, or speech input "English"/"Español"
    """
    session = get_session(CallSid)
    tracker = get_cost_tracker(CallSid)

    # Determine language
    if Digits == "1" or (SpeechResult and "english" in SpeechResult.lower()):
        session.language = "en"
    elif Digits == "2" or (SpeechResult and "español" in SpeechResult.lower()):
        session.language = "es"
    else:
        # Default to English if unclear
        session.language = "en"
    
    # Log language selection to monitor
    if MONITOR_ENABLED and monitor:
        monitor.log_language_selection(CallSid, session.language)

    # Get dynamic business name
    from ai_receptionist.models.business import Business
    business = db.query(Business).first()
    business_name = business.name if business else BUSINESS_NAME

    # Greet caller
    greeting = get_message("GREETING", session.language, business_name=business_name)
    resp = VoiceResponse()

    gather = Gather(
        input="speech",
        action="/twilio/gather",
        method="POST",
        timeout=3,
        language="en-US" if session.language == "en" else "es-ES",
    )
    gather.say(greeting, language="en" if session.language == "en" else "es")
    tracker.log_tts(greeting)
    
    # Log AI greeting to monitor
    if MONITOR_ENABLED and monitor:
        monitor.log_ai_response(CallSid, greeting, "greeting")

    resp.append(gather)

    # If no input, redirect to repeat
    resp.redirect("/twilio/repeat")

    return Response(content=str(resp), media_type="application/xml")


@router.post("/gather")
async def gather_input(request: Request, CallSid: str = Form(...), SpeechResult: str = Form(None)):
    """
    Main conversation loop.
    Receives speech input, detects intent, responds with appropriate message.
    """
    session = get_session(CallSid)
    tracker = get_cost_tracker(CallSid)

    if SpeechResult:
        tracker.log_speech_recognition()
        
        # Log user input to monitor
        if MONITOR_ENABLED and monitor:
            monitor.log_user_input(CallSid, SpeechResult)

    user_input = SpeechResult or ""
    intent = detect_intent(user_input, session.language)
    bot_response, next_action = handle_intent(intent, session.language, user_input)

    # Track conversation
    session.add_turn(user_input, bot_response)
    session.current_intent = intent
    
    # Log AI response to monitor
    if MONITOR_ENABLED and monitor:
        monitor.log_ai_response(CallSid, bot_response, intent)

    # Build TwiML response
    resp = VoiceResponse()

    if next_action == "hangup":
        resp.say(bot_response, language="en" if session.language == "en" else "es")
        tracker.log_tts(bot_response)
        resp.hangup()

        # Log call summary
        summary = tracker.summary()
        logger.info("\n" + "=" * 50)
        logger.info(summary)
        logger.info("=" * 50 + "\n")
        
        # Log call end to monitor
        if MONITOR_ENABLED and monitor:
            monitor.log_call_end(CallSid, "user_goodbye")

        # Clean up session
        clear_session(CallSid)

    else:  # next_action == "gather" or None
        gather = Gather(
            input="speech",
            action="/twilio/gather",
            method="POST",
            timeout=3,
            language="en-US" if session.language == "en" else "es-ES",
        )
        gather.say(bot_response, language="en" if session.language == "en" else "es")
        tracker.log_tts(bot_response)

        resp.append(gather)

        # If no response, ask to repeat
        resp.redirect("/twilio/repeat")

    return Response(content=str(resp), media_type="application/xml")


@router.post("/repeat")
async def repeat_last(request: Request, CallSid: str = Form(...)):
    """
    Handle unclear audio or no input.
    Asks user to repeat with helpful guidance.
    """
    session = get_session(CallSid)
    tracker = get_cost_tracker(CallSid)

    # Progressive help - get more specific each time
    if session.turn_count == 1:
        unclear_msg = get_message("UNCLEAR_RESPONSE", session.language)
    elif session.turn_count <= 3:
        unclear_msg = get_message("HELP_MENU", session.language)
    else:
        unclear_msg = get_message("CLARIFICATION_REQUEST", session.language)
    
    # Log to monitor
    if MONITOR_ENABLED and monitor:
        monitor.log_ai_response(CallSid, unclear_msg, "unclear")

    resp = VoiceResponse()
    gather = Gather(
        input="speech",
        action="/twilio/gather",
        method="POST",
        timeout=3,
        language="en-US" if session.language == "en" else "es-ES",
    )
    gather.say(unclear_msg, language="en" if session.language == "en" else "es")
    tracker.log_tts(unclear_msg)

    resp.append(gather)

    # Only give up after 6 tries (doubled from 3)
    if session.turn_count > 6:
        escalation_msg = get_message("ESCALATION_RESPONSE", session.language)
        resp.say(escalation_msg, language="en" if session.language == "en" else "es")
        tracker.log_tts(escalation_msg)
        
        goodbye = get_message("GOODBYE", session.language, business_name=BUSINESS_NAME)
        resp.say(goodbye, language="en" if session.language == "en" else "es")
        tracker.log_tts(goodbye)
        resp.hangup()

        # Log summary
        summary = tracker.summary()
        print("\n" + "=" * 50)
        print(summary)
        print("=" * 50 + "\n")
        
        # Log call end to monitor
        if MONITOR_ENABLED and monitor:
            monitor.log_call_end(CallSid, "too_many_retries")

        clear_session(CallSid)
    else:
        resp.redirect("/twilio/repeat")

    return Response(content=str(resp), media_type="application/xml")


# ============================================================================
# Realtime OpenAI WebSocket Stream
# ============================================================================

from ai_receptionist.services.voice.config import OPENAI_MODEL, VOICE_MODEL, SYSTEM_INSTRUCTIONS, TOOLS

LOG_EVENT_TYPES = [
    'response.content.done', 'rate_limits.updated', 'response.done',
    'input_audio_buffer.committed', 'input_audio_buffer.speech_stopped',
    'input_audio_buffer.speech_started', 'session.created', 'response.cancelled'
]

async def generate_ai_summary(transcript: str, business_info: str) -> str:
    """Uses GPT-4o-mini to summarize the call transcript."""
    if not transcript or len(transcript) < 20:
        return "Brief call with no significant interaction."
    
    settings = get_settings()
    if not settings.openai_api_key:
        return "Call completed (Summary unavailable)."

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": f"Summarize this phone call for a receptionist dashboard. Focus on user intent and outcomes. Business info: {business_info}"},
                        {"role": "user", "content": transcript}
                    ],
                    "max_tokens": 100
                },
                timeout=10.0
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"Failed to generate AI summary: {e}")
    
    return "Call completed."


def check_guardrails(text: str) -> bool:
    """Basic safety guardrail for prompt injection."""
    denied_patterns = [
        "forget your instructions", "ignore your instructions", 
        "ignore the rules", "new rules", "forget previous"
    ]
    clean_text = text.lower()
    return any(p in clean_text for p in denied_patterns)

@router.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    print("DEBUG: WebSocket connection attempt at /twilio/stream", flush=True)
    await websocket.accept()
    logger.info("Twilio WebSocket connected")
    
    settings = get_settings()
    api_key = settings.openai_api_key
    
    if not api_key:
        logger.critical("OpenAI API Key is missing!")
        await websocket.close(code=1008)
        return

    start_time = None
    business_id_val = None
    call_sid_val = None
    from_number_val = None
    appointment_booked_flag = False

    # TOOLS successfully imported from config

    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "OpenAI-Beta": "realtime=v1",
        }
        url = f"wss://api.openai.com/v1/realtime?model={OPENAI_MODEL}"
        
        try:
            async with session.ws_connect(url, headers=headers) as openai_ws:
                logger.info(f"Connected to OpenAI Realtime API ({OPENAI_MODEL})")
                
                # Default instructions
                instructions = SYSTEM_INSTRUCTIONS
                
                stream_sid = None
                greeting_sent = False
                final_transcript = ""

                # Transcript accumulation (Timestamped Buffer)
                # Each item: {"ts": float, "role": str, "text": str}
                transcript_buffer = []

                async def sync_partial_transcript():
                    """Every 10 seconds, save the transcript so far to prevent loss."""
                    nonlocal transcript_buffer, call_sid_val
                    while True:
                        await asyncio.sleep(10)
                        if transcript_buffer and call_sid_val:
                            try:
                                sorted_transcript = sorted(transcript_buffer, key=lambda x: x["ts"])
                                text_lines = [f"{i['role']}: {i['text']}" for i in sorted_transcript]
                                partial_text = "\n".join(text_lines)
                                
                                # Use a fast update to DB
                                with get_db_session() as partial_db:
                                    # Fix scope issue by importing locally
                                    from ai_receptionist.models.call import Call
                                    partial_call = partial_db.query(Call).filter(Call.call_sid == call_sid_val).first()
                                    if partial_call:
                                        partial_call.transcript = partial_text
                                        # Don't commit yet? No, get_db_session handles it.
                                logger.debug(f"Partial sync for {call_sid_val}")
                            except Exception as e:
                                logger.error(f"Partial sync error: {e}")

                # Start sync background task
                sync_task = asyncio.create_task(sync_partial_transcript())

                async def receive_from_twilio():
                    nonlocal stream_sid, greeting_sent, instructions, start_time, business_id_val, call_sid_val, from_number_val
                    try:
                        async for message in websocket.iter_text():
                            data = json.loads(message)
                            event_type = data.get("event")
                            
                            if event_type == "media":
                                audio_payload = data["media"]["payload"]
                                # Print a dot every 50 packets to show activity in logs
                                if not hasattr(receive_from_twilio, "packet_count"):
                                    receive_from_twilio.packet_count = 0
                                receive_from_twilio.packet_count += 1
                                if receive_from_twilio.packet_count % 50 == 0:
                                    logger.debug(f"Media streaming active... packet {receive_from_twilio.packet_count}")
                                
                                await openai_ws.send_json({
                                    "type": "input_audio_buffer.append",
                                    "audio": audio_payload
                                })
                            elif event_type == "start":
                                start_info = data["start"]
                                stream_sid = start_info["streamSid"]
                                params = start_info.get("customParameters", {})
                                
                                business_id_param = params.get("business_id")
                                call_sid_param = params.get("call_sid")
                                
                                if business_id_param:
                                    business_id_val = int(business_id_param)
                                
                                if call_sid_param:
                                    call_sid_val = call_sid_param
                                
                                from_number_param = params.get("from_number")
                                if from_number_param:
                                    from_number_val = from_number_param
                                
                                to_number_param = params.get("to_number")
                                
                                start_timestamp_str = params.get("start_timestamp")
                                if start_timestamp_str:
                                    try:
                                        from datetime import timezone
                                        start_time = datetime.fromtimestamp(float(start_timestamp_str), tz=timezone.utc).replace(tzinfo=None)
                                    except:
                                        start_time = datetime.now(timezone.utc).replace(tzinfo=None)
                                else:
                                    start_time = datetime.now(timezone.utc).replace(tzinfo=None)
                                
                                # Look up business by to_number (the Twilio number being called)
                                if to_number_param and not business_id_val:
                                    try:
                                        from ai_receptionist.models.business import Business
                                        business = db.query(Business).filter(Business.phone_number == to_number_param).first()
                                        if business:
                                            business_id_val = business.id
                                            logger.info(f"Found business {business.name} (ID: {business.id}) by to_number: {to_number_param}")
                                        else:
                                            logger.warning(f"No business found for to_number: {to_number_param}")
                                    except Exception as e:
                                        logger.error(f"Error looking up business by to_number: {e}")

                                logger.info(f"Stream started: {stream_sid} for Call: {call_sid_val} (Business: {business_id_val})")
                                
                                # Load business context and update session
                                # Note: 'business' may already be loaded from to_number lookup above
                                if business_id_val:
                                    try:
                                        from ai_receptionist.models.business import Business
                                        # Only query if we don't already have the business object
                                        if 'business' not in dir() or business is None or business.id != int(business_id_val):
                                            business = db.query(Business).filter(Business.id == int(business_id_val)).first()
                                        if business:
                                            instructions = f"""You are Aria, an AI Receptionist for {business.name}. Be polite and professional.

LANGUAGE RULES:
- Always start speaking in English.
- Only switch languages if the caller speaks to you in another language first.
- When uncertain, default to English.
                                            
BUSINESS INFO:
- Industry: {business.industry or 'N/A'}
- Description: {business.description or 'N/A'}
- Common Services: {business.common_services or 'N/A'}
- FAQs: {json.dumps(business.faqs) if business.faqs else 'N/A'}

RULES:
- Keep responses brief (1-3 sentences).
- If you don't know something about the business, offer to take a message.
- IMPORTANT: Speak 20% faster than a normal conversational pace (around 1.2x speed) to keep the conversation efficient."""
                                            
                                            logger.info(f"Customized instructions for {business.name}")
                                    except Exception as e:
                                        logger.error(f"Error loading business instructions: {e}")

                                # Send session.update with (potentially) new instructions
                                await openai_ws.send_json({
                                    "type": "session.update",
                                    "session": {
                                        "modalities": ["audio", "text"],
                                        "instructions": instructions,
                                        "voice": VOICE_MODEL,
                                        "input_audio_format": "g711_ulaw",
                                        "output_audio_format": "g711_ulaw",
                                        "input_audio_transcription": {
                                            "model": "whisper-1"
                                        },
                                        "turn_detection": {
                                            "type": "server_vad",
                                            "threshold": 0.5,
                                            "prefix_padding_ms": 300,
                                            "silence_duration_ms": 800
                                        },
                                        "temperature": 0.7,
                                        "tools": TOOLS,
                                        "tool_choice": "auto",
                                    }
                                })

                                if not greeting_sent:
                                    logger.info(f"Triggering initial greeting for business: {business.name if (business_id_val and business) else 'Unknown'}")
                                    greeting_text = f"Hi, thank you for calling {business.name if (business_id_val and business) else 'us'}. This is Aria, how can I help you?"
                                    await openai_ws.send_json({
                                        "type": "response.create",
                                        "response": {
                                            "modalities": ["audio", "text"],
                                            "instructions": f"Say: {greeting_text}. KEEP IT FAST." 
                                        }
                                    })
                                    transcript_buffer.append({
                                        "ts": time.time(),
                                        "role": "Aria",
                                        "text": greeting_text
                                    })
                                    greeting_sent = True
                            elif event_type == "stop":
                                break
                    except WebSocketDisconnect:
                        logger.info("Twilio WebSocket disconnected")
                    except Exception as e:
                        logger.error(f"Error in Twilio receive loop: {e}")

                async def receive_from_openai():
                    nonlocal stream_sid, appointment_booked_flag
                    try:
                        async for msg in openai_ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                response = json.loads(msg.data)
                                event_type = response.get("type")
                                
                                if event_type == "response.audio.delta":
                                    audio_delta = response.get("delta")
                                    if audio_delta and stream_sid:
                                        await websocket.send_json({
                                            "event": "media",
                                            "streamSid": stream_sid,
                                            "media": {"payload": audio_delta}
                                        })
                                elif event_type == "input_audio_buffer.speech_started":
                                    await openai_ws.send_json({"type": "response.cancel"})
                                    if stream_sid:
                                        await websocket.send_json({"event": "clear", "streamSid": stream_sid})
                                    # Track response start for latency
                                    receive_from_openai.response_start = time.time()
                                elif event_type == "conversation.item.input_audio_transcription.completed":
                                    user_text = response.get("transcript", "").strip()
                                    if user_text:
                                        logger.info(f"User: {user_text}")
                                        if check_guardrails(user_text):
                                            logger.warning(f"GUARDRAIL TRIGGERED for {user_text}")
                                            await openai_ws.send_json({"type": "response.cancel"})
                                            await openai_ws.send_json({
                                                "type": "response.create",
                                                "response": {
                                                    "modalities": ["audio", "text"],
                                                    "instructions": "Politely say: 'I apologize, but I must follow my business protocols. How can I help with your appointment?'"
                                                }
                                            })
                                        
                                        transcript_buffer.append({
                                            "ts": time.time(),
                                            "role": "Caller",
                                            "text": user_text
                                        })
                                elif event_type == "response.audio_transcript.done":
                                    ai_text = response.get("transcript", "").strip()
                                    if ai_text:
                                        logger.info(f"Aria: {ai_text}")
                                        latency = 0
                                        if hasattr(receive_from_openai, "response_start"):
                                            latency = (time.time() - receive_from_openai.response_start) * 1000
                                        
                                        transcript_buffer.append({
                                            "ts": time.time(),
                                            "role": "Aria",
                                            "text": ai_text,
                                            "metadata": {"latency_ms": latency}
                                        })
                                elif event_type == "response.function_call_arguments.done":
                                    call_id = response.get("call_id")
                                    name = response.get("name")
                                    args = json.loads(response.get("arguments", "{}"))
                                    
                                    logger.info(f"Tool Call: {name}({args})")
                                    
                                    tool_result = "An error occurred."
                                    if business_id_val:
                                        from ai_receptionist.services.calendar import CalendarService
                                        from datetime import timedelta # REMOVED datetime from local import to avoid shadowing
                                        
                                        try:
                                            with get_db_session() as tool_db:
                                                cal_svc = CalendarService(tool_db)
                                                tenant_id = str(business_id_val)
                                                
                                                if name == "check_availability":
                                                    # Use global datetime
                                                    start = datetime.fromisoformat(args["start_iso"])
                                                    duration_min = int(args.get("duration_minutes", 30))
                                                    end = start + timedelta(minutes=duration_min)
                                                    
                                                    is_avail = await cal_svc.check_availability(tenant_id, start, end)
                                                    tool_result = "Available" if is_avail else "Busy"
                                                    
                                                elif name == "book_appointment":
                                                    start = datetime.fromisoformat(args["start_iso"])
                                                    duration_min = int(args.get("duration_minutes", 30))
                                                    end = start + timedelta(minutes=duration_min)
                                                    
                                                    res = await cal_svc.book_appointment(
                                                        tenant_id=tenant_id,
                                                        start_time=start,
                                                        end_time=end,
                                                        summary=f"Aria Booking: {args['customer_name']}",
                                                        attendee_phone=from_number_val or "Unknown"
                                                    )
                                                    appointment_booked_flag = True
                                                    tool_result = f"Confirmed! Appointment ID: {res['event_id']}"
                                                
                                                elif name == "identify_self":
                                                    caller_name = args.get("name")
                                                    # Emit identity event
                                                    logger.info(f"IDENTITY_UPDATE: call_sid={call_sid_val}, caller_name={caller_name}, source=user_provided")
                                                    
                                                    # Upsert Contact record for identity persistence
                                                    try:
                                                        from ai_receptionist.models.contact import Contact
                                                        contact = tool_db.query(Contact).filter(
                                                            Contact.business_id == int(business_id_val),
                                                            Contact.phone_number == from_number_val
                                                        ).first()
                                                        
                                                        if not contact:
                                                            contact = Contact(
                                                                business_id=int(business_id_val),
                                                                phone_number=from_number_val,
                                                                name=caller_name,
                                                                notes="Auto-identified during call."
                                                            )
                                                            tool_db.add(contact)
                                                        else:
                                                            contact.name = caller_name
                                                            contact.notes = (contact.notes or "") + f"\nUpdated name to {caller_name} during call."
                                                        
                                                        tool_db.commit()
                                                    except Exception as ie:
                                                        logger.error(f"Failed to update contact identity: {ie}")
                                                    
                                                    tool_result = f"Recorded name as {caller_name}."
                                        except Exception as te:
                                            logger.error(f"Tool Execution Error: {te}")
                                            tool_result = f"Error: {str(te)}"
                                    
                                    # Append tool metadata to transcript buffer
                                    transcript_buffer.append({
                                        "ts": time.time(),
                                        "role": "System",
                                        "text": f"Tool Result: {name}",
                                        "metadata": {
                                            "tool_calls": [{"name": name, "arguments": args}],
                                            "tool_result": tool_result
                                        }
                                    })
                                    
                                    await openai_ws.send_json({
                                        "type": "conversation.item.create",
                                        "item": {
                                            "type": "function_call_output",
                                            "call_id": call_id,
                                            "output": tool_result
                                        }
                                    })
                                    await openai_ws.send_json({"type": "response.create"})

                                elif event_type == "error":
                                    logger.error(f"OpenAI Error: {response}")
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                break
                    except Exception as e:
                        logger.error(f"Error in OpenAI receive loop: {e}")

                # Run both loops until one stops
                twilio_task = asyncio.create_task(receive_from_twilio())
                openai_task = asyncio.create_task(receive_from_openai())

                await asyncio.wait(
                    [twilio_task, openai_task],
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Cleanup tasks
                if not twilio_task.done(): twilio_task.cancel()
                if not openai_task.done(): openai_task.cancel()

                # Finalize transcript with sorting
                sorted_transcript = sorted(transcript_buffer, key=lambda x: x["ts"])
                final_transcript = "\n".join([f"{i['role']}: {i['text']}" for i in sorted_transcript])
                
                # Stop sync task
                sync_task.cancel()
        except Exception as e:
            logger.error(f"Failed to connect to OpenAI or runtime error: {e}")
            await websocket.close()
        finally:
            # Update usage stats
            if start_time and business_id_val:
                try:
                    # Strict Temporal Authority: ended_at - answered_at
                    # answered_at is approximated by start_time (UTC)
                    ended_at = datetime.now(timezone.utc).replace(tzinfo=None)
                    duration_seconds = (ended_at - start_time).total_seconds()
                    minutes = math.ceil(duration_seconds / 60)
                    
                    # --- AI SUMMARY GENERATION (Real Intelligence) ---
                    summary = "Call completed."
                    
                    # Re-fetch business for context in finally block
                    biz_context = "AI Receptionist"
                    try:
                        from ai_receptionist.models.business import Business
                        with get_db_session() as final_db:
                            b_obj = final_db.query(Business).filter(Business.id == int(business_id_val)).first()
                            if b_obj:
                                biz_context = f"{b_obj.name} ({b_obj.industry})"
                    except:
                        pass

                    if transcript_buffer:
                        try:
                            summary = await generate_ai_summary(final_transcript, biz_context)
                        except Exception as se:
                            logger.error(f"Summary Generation Error: {se}")
                            summary = "Call completed."

                    logger.info(f"Finalizing Call for Business {business_id_val}: {duration_seconds}s (UTC)")
                    
                    from ai_receptionist.models.business import Business
                    from ai_receptionist.models.call import Call
                    
                    # Update Call Record
                    call_id_to_find = call_sid_val or stream_sid
                    logger.info(f"Searching for call record to update: {call_id_to_find}")
                    
                    call_record = db.query(Call).filter(Call.call_sid == call_id_to_find).first()
                    
                    # Backup lookup by business and recent status
                    if not call_record and business_id_val:
                        logger.info(f"Call record {call_id_to_find} not found. Trying fallback by business_id {business_id_val}")
                        call_record = db.query(Call).filter(
                            Call.business_id == int(business_id_val),
                            Call.status == "in-progress"
                        ).order_by(Call.created_at.desc()).first()

                    if call_record:
                        if not final_transcript and transcript_buffer:
                            sorted_transcript = sorted(transcript_buffer, key=lambda x: x["ts"])
                            final_transcript = "\n".join([f"{i['role']}: {i['text']}" for i in sorted_transcript])
                        
                        logger.info(f"Updating call {call_record.call_sid}: duration={int(duration_seconds)}s")
                        call_record.status = "completed"
                        call_record.duration = max(1, int(duration_seconds))
                        call_record.transcript = final_transcript or "No transcript generated."
                        call_record.summary = summary or "Call completed."
                        
                        # --- STRUCTURED CONVERSATION FRAME (Shadow AI Input) ---
                        # Synchronize only structured data for 1:1 behavioral testing
                        try:
                            frame = {
                                "call_id": call_record.call_sid,
                                "business_id": int(business_id_val),
                                "timezone": "UTC", # Default or fetch from biz
                                "channel": "voice",
                                "turns": [
                                    {
                                        "index": idx,
                                        "timestamp": t.get("ts"),
                                        "role": t.get("role"),
                                        "text": t.get("text"),
                                        "metadata": t.get("metadata", {})
                                    }
                                    for idx, t in enumerate(sorted(transcript_buffer, key=lambda x: x["ts"]))
                                ]
                            }
                            call_record.conversation_frame = json.dumps(frame)
                        except Exception as fe:
                            logger.error(f"Failed to generate conversation frame: {fe}")

                        # Detect intent correctly
                        if appointment_booked_flag:
                            call_record.intent = "Booking"
                            call_record.appointment_booked = 1
                        elif final_transcript and ("schedule" in final_transcript.lower() or "appointment" in final_transcript.lower()):
                            call_record.intent = "Booking Inquiry"
                            call_record.appointment_booked = 0
                        else:
                            call_record.intent = "Inquiry"
                        
                        # Update business minutes
                        biz = db.query(Business).filter(Business.id == int(business_id_val)).first()
                        if biz:
                            biz.minutes_used = (biz.minutes_used or 0) + minutes
                        
                        db.commit()

                        # --- SHADOW AI EVALUATION (DISABLED TO CONSERVE TOKENS) ---
                        # Shadow AI uses gpt-4o-mini to replay every call for quality assurance.
                        # Currently disabled to save OpenAI tokens. Enable via ENABLE_SHADOW_AI=true
                        settings = get_settings()
                        if settings.enable_shadow_ai:
                            try:
                                from ai_receptionist.services.evaluation.shadow_eval import process_call_shadow
                                asyncio.create_task(process_call_shadow(call_record.id))
                                logger.info(f"Shadow AI evaluation queued for call {call_record.id}")
                            except Exception as shadow_err:
                                logger.error(f"Failed to queue shadow evaluation: {shadow_err}")
                        else:
                            logger.debug(f"Shadow AI disabled - skipping evaluation for call {call_record.id}")

                    else:
                        logger.warning(f"CRITICAL: Could not find call record to update for {call_id_to_find}")
                        db.rollback()
                except Exception as e:
                    logger.error(f"Failed to update usage stats/transcript: {e}")
                    db.rollback()


@router.post("/recording-status")
async def recording_status(
    CallSid: str = Form(...),
    RecordingUrl: str = Form(None),
    db: Session = Depends(get_db)
):
    """Callback from Twilio when a recording is ready."""
    if RecordingUrl:
        logger.info(f"Recording ready for {CallSid}: {RecordingUrl}")
        try:
            from ai_receptionist.models.call import Call
            call = db.query(Call).filter(Call.call_sid == CallSid).first()
            if call:
                call.recording_url = RecordingUrl
                db.commit()
        except Exception as e:
            logger.error(f"Failed to save recording URL: {e}")
            db.rollback()
    
    return Response(content="OK", media_type="text/plain")


# =============================================================================
# EMERGENCY FALLBACK ENDPOINT
# =============================================================================
# This endpoint is called by Twilio when the primary /twilio/voice fails.
# It MUST:
#   - Always return valid TwiML
#   - Never crash
#   - Never touch database
#   - Never call external APIs
#   - Work even if the rest of the app is down
# =============================================================================

# Static TwiML - defined at module load time for maximum reliability
_FALLBACK_TWIML = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">We're sorry, our system is temporarily unavailable. Please try your call again in a few minutes. Thank you for your patience.</Say>
    <Hangup/>
</Response>"""


@router.post("/fallback")
async def twilio_fallback():
    """
    Emergency fallback endpoint for Twilio Voice.
    
    This endpoint is called by Twilio when the primary webhook fails.
    It returns static TwiML to gracefully handle the call without
    depending on any external services, database, or authentication.
    
    Returns:
        Static TwiML XML response that apologizes and hangs up cleanly.
    """
    return Response(
        content=_FALLBACK_TWIML,
        media_type="application/xml",
        status_code=200
    )

