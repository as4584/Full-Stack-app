import json
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import openai

logger = logging.getLogger(__name__)

class Turn(BaseModel):
    role: str
    text: str
    index: int
    timestamp: float
    metadata: Dict[str, Any] = {}

class ConversationFrame(BaseModel):
    call_id: str
    business_id: int
    timezone: str
    channel: str = "voice"
    turns: List[Turn]

class ShadowResult(BaseModel):
    call_id: str
    match_score: float # 0.0 to 1.0
    intent_match: bool
    tool_match: bool
    discrepancies: List[str]
    shadow_decisions: List[Dict[str, Any]]

async def run_shadow_eval(frame: Dict[str, Any], business_info: Dict[str, Any]):
    """
    Silent Referee: Replays a real conversation frame through a shadow AI.
    It compares live decisions (tool calls, intents) against its own thinking.
    """
    from ai_receptionist.config.settings import get_settings
    settings = get_settings()
    
    # Initialize Shadow AI (No access to live users/calendar)
    client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    
    # Parse frame
    cv_frame = ConversationFrame(**frame)
    turns = sorted(cv_frame.turns, key=lambda x: x.index)
    
    shadow_decisions = []
    
    intent_match = True
    tool_match = True
    discrepancies = []
    matches = 0
    total_assistant_turns = 0
    
    from ai_receptionist.services.voice.config import TOOLS, SYSTEM_INSTRUCTIONS

    # Shadow AI instructions (1:1 with live)
    # Replicate the prompt formatting from endpoints.py
    biz_context = f"Business Name: {business_info.get('name')}\n" \
                  f"Description: {business_info.get('description')}\n" \
                  f"FAQs: {json.dumps(business_info.get('faqs'))}"
    
    instructions = SYSTEM_INSTRUCTIONS.replace("{business_info}", biz_context)
    # Add date and timezone context for 1:1 parity
    instructions += f"\n\nCurrent Date: {datetime.now().strftime('%A, %Y-%m-%d')}"
    instructions += f"\nCurrent Timezone: {cv_frame.timezone}"
    
    # Initialize history with system instructions
    live_history = [{"role": "system", "content": instructions}]

    # Simulation Loop
    for i, turn in enumerate(turns):
        if turn.role == "Caller":
            live_history.append({"role": "user", "content": turn.text})
        elif turn.role == "Aria":
            total_assistant_turns += 1
            
            # Predict what the shadow AI would do at this exact moment
            try:
                # Use centralized tool definitions (parity)
                functions = []
                for t in TOOLS:
                    functions.append({
                        "name": t["name"],
                        "parameters": t["parameters"]
                    })

                # GET DECISION FROM SHADOW AI
                shadow_resp = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=live_history,
                    functions=functions,
                    function_call="auto",
                    temperature=0
                )

                shadow_message = shadow_resp.choices[0].message
                shadow_tool_call = shadow_message.function_call.name if (hasattr(shadow_message, 'function_call') and shadow_message.function_call) else None
                shadow_arguments = json.loads(shadow_message.function_call.arguments) if shadow_tool_call else {}
                
                # Compare with Live Decision recorded in frame
                live_tool_call = None
                if turn.metadata and turn.metadata.get("tool_calls"):
                     live_tool_call = turn.metadata.get("tool_calls")[0].get("name")
                
                # Special cases for null comparisons
                if shadow_tool_call == live_tool_call:
                    matches += 1
                else:
                    # If this is the greeting (turn index 0 or similar), and both are None, it's a match
                    if not shadow_tool_call and not live_tool_call:
                        matches += 1
                    else:
                        tool_match = False
                        discrepancies.append(f"Turn {turn.index}: Shadow wanted '{shadow_tool_call}', Live used '{live_tool_call}'")
                
                shadow_decisions.append({
                    "turn_index": turn.index,
                    "shadow_text": shadow_message.content,
                    "shadow_tool": shadow_tool_call,
                    "shadow_arguments": shadow_arguments,
                    "live_tool": live_tool_call
                })
                
                # Append live turn text and any tool results to history for next iteration
                live_history.append({"role": "assistant", "content": turn.text})
                if turn.metadata and turn.metadata.get("tool_calls"):
                    # Mock the tool result for the shadow assistant
                    tool_result = turn.metadata.get("tool_result", "Success")
                    live_history.append({
                        "role": "function",
                        "name": turn.metadata.get("tool_calls")[0].get("name"),
                        "content": str(tool_result)
                    })
                
            except Exception as e:
                logger.error(f"Shadow eval error at turn {turn.index}: {e}")
                discrepancies.append(f"Turn {turn.index}: Shadow AI error: {str(e)}")

    match_score = matches / total_assistant_turns if total_assistant_turns > 0 else 1.0
    
    return ShadowResult(
        call_id=cv_frame.call_id,
        match_score=match_score,
        intent_match=intent_match,
        tool_match=tool_match,
        discrepancies=discrepancies,
        shadow_decisions=shadow_decisions
    )

async def process_call_shadow(call_id: int):
    # Same as before
    from ai_receptionist.core.database import SessionLocal
    from ai_receptionist.models.call import Call
    from ai_receptionist.models.business import Business
    
    db = SessionLocal()
    try:
        call = db.query(Call).filter(Call.id == call_id).first()
        if not call or not call.conversation_frame:
            return
            
        biz = db.query(Business).filter(Business.id == call.business_id).first()
        biz_info = {
            "name": biz.name,
            "description": biz.description,
            "faqs": biz.faqs
        }
        
        frame_data = json.loads(call.conversation_frame)
        result = await run_shadow_eval(frame_data, biz_info)
        
        call.shadow_result = result.json()
        db.commit()
    except Exception as e:
        logger.error(f"Shadow background task failed: {e}")
        db.rollback()
    finally:
        db.close()
