
import logging
import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import aiohttp
from ai_receptionist.config.settings import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["realtime"])

# OpenAI Realtime API Configuration
OPENAI_MODEL = "gpt-4o-realtime-preview" 
VOICE = "shimmer"

# Optimized system instructions for faster connection
SYSTEM_INSTRUCTIONS = """You are Aria, an AI Receptionist for businesses. Be polite, professional, and concise.

RULES:
- Always start in English. Switch languages only if caller requests.
- Keep responses brief (1-3 sentences) unless more detail is needed.
- You're an AI assistant - be honest if asked.
- Handle: appointments, messages, basic info, transfers.

Each call is independent. Start fresh every time."""

LOG_EVENT_TYPES = [
    'response.content.done',
    'rate_limits.updated',
    'response.done',
    'input_audio_buffer.committed',
    'input_audio_buffer.speech_stopped',
    'input_audio_buffer.speech_started',
    'session.created',
    'response.cancelled'
]

@router.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    print("DEBUG: WebSocket connection attempt at /twilio/stream", flush=True)
    await websocket.accept()
    logger.info("Twilio WebSocket connected")
    
    settings = get_settings()
    api_key = settings.openai_api_key
    
    logger.info(f"Connecting to OpenAI Realtime API. Key present: {bool(api_key)}")
    
    if not api_key:
        logger.critical("OpenAI API Key is missing! Cannot connect to Realtime API.")
        await websocket.close(code=1008)
        return

    # Use aiohttp for OpenAI connection
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "OpenAI-Beta": "realtime=v1",
        }
        url = f"wss://api.openai.com/v1/realtime?model={OPENAI_MODEL}"
        logger.info(f"OpenAI WSS URL: {url}")
        
        try:
            async with session.ws_connect(url, headers=headers) as openai_ws:
                logger.info(f"Connected to OpenAI Realtime API ({OPENAI_MODEL})")
                
                # Phase 1.2: Force Audio Output First
                # Enable server-side VAD for automatic turn detection
                session_update = {
                    "type": "session.update",
                    "session": {
                        "modalities": ["audio", "text"],
                        "instructions": SYSTEM_INSTRUCTIONS,
                        "voice": VOICE,
                        "input_audio_format": "g711_ulaw",
                        "output_audio_format": "g711_ulaw",
                        "turn_detection": {
                            "type": "server_vad",
                            "threshold": 0.5,
                            "prefix_padding_ms": 200,
                            "silence_duration_ms": 400
                        },
                        "temperature": 0.7,
                    }
                }
                logger.info("Sending session.update...")
                await openai_ws.send_json(session_update)
                
                stream_sid = None
                greeting_sent = False

                async def receive_from_twilio():
                    nonlocal stream_sid, greeting_sent
                    try:
                        async for message in websocket.iter_text():
                            data = json.loads(message)
                            event_type = data.get("event")
                            
                            if event_type == "media":
                                # Forward audio to OpenAI
                                # Only forward if we have established connection? 
                                # Realtime API accepts buffer append anytime.
                                audio_payload = data["media"]["payload"]
                                await openai_ws.send_json({
                                    "type": "input_audio_buffer.append",
                                    "audio": audio_payload
                                })
                            elif event_type == "start":
                                stream_sid = data["start"]["streamSid"]
                                logger.info(f"Stream started: {stream_sid}")
                                
                                # NOW send the greeting after we have stream_sid
                                if not greeting_sent:
                                    logger.info("Triggering initial greeting (after stream start)...")
                                    await openai_ws.send_json({
                                        "type": "response.create",
                                        "response": {
                                            "modalities": ["audio", "text"],
                                            "instructions": "Say: Hi, this is Aria. How can I help you?" 
                                        }
                                    })
                                    greeting_sent = True
                            elif event_type == "stop":
                                logger.info("Stream stopped from Twilio side")
                                # Close OpenAI connection?
                                # await openai_ws.close()
                                break
                    except WebSocketDisconnect:
                        logger.info("Twilio WebSocket disconnected")
                    except Exception as e:
                        logger.error(f"Error in Twilio receive loop: {e}")

                async def receive_from_openai():
                    nonlocal stream_sid
                    try:
                        async for msg in openai_ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                response = json.loads(msg.data)
                                event_type = response.get("type")
                                
                                if event_type == "response.audio.delta":
                                    # Forward audio to Twilio
                                    audio_delta = response.get("delta")
                                    if audio_delta and stream_sid:
                                        await websocket.send_json({
                                            "event": "media",
                                            "streamSid": stream_sid,
                                            "media": {
                                                "payload": audio_delta
                                            }
                                        })
                                        
                                elif event_type == "input_audio_buffer.speech_started":
                                    # INTERRUPTION HANDLING: User started speaking
                                    # Cancel any ongoing AI response immediately
                                    logger.info("User interrupted - cancelling AI response")
                                    await openai_ws.send_json({
                                        "type": "response.cancel"
                                    })
                                    # Clear Twilio's audio buffer to stop playback
                                    if stream_sid:
                                        await websocket.send_json({
                                            "event": "clear",
                                            "streamSid": stream_sid
                                        })
                                        
                                elif event_type == "response.cancelled":
                                    logger.info("AI response cancelled due to interruption")
                                    
                                elif event_type == "response.audio.done":
                                    logger.debug("AI finished speaking")
                                    
                                elif event_type == "error":
                                    logger.error(f"OpenAI Error: {response}")
                                    
                                elif event_type in LOG_EVENT_TYPES:
                                    logger.debug(f"OpenAI Event: {event_type}")
                                    
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                logger.error("OpenAI WebSocket connection closed with error")
                                break
                    except Exception as e:
                        logger.error(f"Error in OpenAI receive loop: {e}")

                # Run both loops
                await asyncio.gather(receive_from_twilio(), receive_from_openai())

        except Exception as e:
            logger.error(f"Failed to connect to OpenAI or runtime error: {e}")
            # Try to inform Twilio? 
            # Usually if WS closes, Twilio call ends or proceeds to next TwiML
            await websocket.close()
