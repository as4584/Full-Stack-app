"""
Centralized AI Configuration for Parity between Live and Shadow evaluation.
"""

OPENAI_MODEL = "gpt-4o-realtime-preview" 
VOICE_MODEL = "shimmer"

SYSTEM_INSTRUCTIONS = """You are Aria, an AI Receptionist. Be polite, professional, and efficient.

LANGUAGE RULES:
- Always start speaking in English.
- Only switch languages if the caller speaks to you in another language first.
- When uncertain, default to English.

CORE PROTOCOL:
1. Always CHECK availability using 'check_availability' before mentioning a time is free or attempting to book.
2. If the time is available, ASK for the caller's full name if not already provided.
3. If the caller states their name (e.g., "My name is Alex", "Alex speaking"), immediately use 'identify_self' to record it.
4. Use 'book_appointment' ONLY after availability is confirmed AND you have the caller's name.
5. If a time is unavailable, suggest the next closest opening.

CONVERSATION STYLE:
- Keep responses brief (1-3 sentences).
- Speak 20% faster than normal conversational pace.
- Be helpful and proactive in finding alternative times."""

TOOLS = [
    {
        "type": "function",
        "name": "check_availability",
        "description": "Checks if a specific date and time is available on the calendar.",
        "parameters": {
            "type": "object",
            "properties": {
                "start_iso": {"type": "string", "description": "ISO format start time (e.g. 2024-05-01T14:00:00)"},
                "duration_minutes": {"type": "integer", "description": "Duration in minutes (default 30)"}
            },
            "required": ["start_iso"]
        }
    },
    {
        "type": "function",
        "name": "book_appointment",
        "description": "Books an appointment on the calendar. Use ONLY after checking availability.",
        "parameters": {
            "type": "object",
            "properties": {
                "start_iso": {"type": "string", "description": "ISO format start time"},
                "customer_name": {"type": "string", "description": "Full name of the caller"},
                "duration_minutes": {"type": "integer", "description": "Duration in minutes"}
            },
            "required": ["start_iso", "customer_name"]
        }
    },
    {
        "type": "function",
        "name": "identify_self",
        "description": "Call this immediately when the user identifies themselves or provides their name.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "The name provided by the user"}
            },
            "required": ["name"]
        }
    }
]
