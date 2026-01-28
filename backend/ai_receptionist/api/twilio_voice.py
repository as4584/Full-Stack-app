"""
Twilio Voice webhook endpoint for AI Receptionist.

Handles incoming voice calls, processes speech with ConversationBot,
and returns TwiML responses for Twilio to speak back to the caller.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Form, Request, Response, Depends
from fastapi.responses import Response as FastAPIResponse

from ai_receptionist import ConversationBot, get_settings
from ai_receptionist.config import Settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/twilio", tags=["twilio-voice"])


@router.post("/voice")
async def handle_voice_call(
    request: Request,
    CallSid: str = Form(...),
    From: str = Form(...),
    To: Optional[str] = Form(None),
    SpeechResult: Optional[str] = Form(None),
    Confidence: Optional[float] = Form(None),
    settings: Settings = Depends(get_settings)
) -> FastAPIResponse:
    """
    Twilio Voice webhook endpoint.
    
    Receives incoming voice calls, processes caller speech with ConversationBot,
    and returns TwiML XML for Twilio to speak the AI response.
    
    Args:
        request: FastAPI request object
        CallSid: Twilio call identifier
        From: Caller's phone number
        To: Dialed phone number
        SpeechResult: Transcribed speech from caller (optional)
        Confidence: Speech recognition confidence (optional)
        settings: Application settings
        
    Returns:
        TwiML XML response with <Say> and <Gather> for continuing conversation
    """
    
    logger.info(
        f"Incoming call - CallSid: {CallSid}, From: {From}, "
        f"Speech: {SpeechResult or 'None'}, Confidence: {Confidence}"
    )
    
    # Initialize conversation bot
    bot = ConversationBot()
    
    # Handle first call (no speech yet)
    if not SpeechResult:
        greeting = "Hello! Thank you for calling. How can I help you today?"
        logger.info(f"New call - sending greeting: {greeting}")
        twiml = _create_twiml_response(greeting)
        return _twiml_response(twiml)
    
    # Process caller's speech
    try:
        logger.info(f"Processing speech from {From}: '{SpeechResult}'")
        ai_response = bot.handle_user_message(SpeechResult)
        logger.info(f"AI response: {ai_response}")
        
        twiml = _create_twiml_response(ai_response)
        return _twiml_response(twiml)
        
    except Exception as e:
        logger.error(f"Error processing call {CallSid}: {e}", exc_info=True)
        error_message = "I apologize, but I'm having technical difficulties. Please try again later."
        twiml = _create_twiml_response(error_message, continue_listening=False)
        return _twiml_response(twiml)


def _create_twiml_response(message: str, continue_listening: bool = True) -> str:
    """
    Create TwiML XML response with <Say> and optional <Gather> for speech input.
    
    Args:
        message: Text for Twilio to speak
        continue_listening: Whether to continue listening for more speech
        
    Returns:
        TwiML XML string
    """
    if continue_listening:
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather input="speech" timeout="5" speechTimeout="auto" action="/twilio/voice" method="POST">
        <Say voice="Polly.Joanna">{message}</Say>
    </Gather>
    <Say voice="Polly.Joanna">I didn't catch that. Please call back if you need assistance.</Say>
</Response>"""
    else:
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">{message}</Say>
    <Hangup/>
</Response>"""
    
    return twiml


def _twiml_response(twiml_content: str) -> FastAPIResponse:
    """
    Create FastAPI Response with proper TwiML content type.
    
    Args:
        twiml_content: TwiML XML string
        
    Returns:
        FastAPI Response with application/xml content type
    """
    return FastAPIResponse(
        content=twiml_content,
        media_type="application/xml",
        status_code=200
    )


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
async def twilio_fallback() -> Response:
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
