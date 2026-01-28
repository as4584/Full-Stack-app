"""
Session manager for voice calls.

Tracks conversation state, language preference, collected data, and turn count per CallSid.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class VoiceSession:
    """State for a single voice call."""

    call_sid: str
    language: str = "en"  # "en" or "es"
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    current_intent: Optional[str] = None
    collected_data: Dict[str, str] = field(default_factory=dict)
    turn_count: int = 0

    def add_turn(self, user_input: str, bot_response: str) -> None:
        """Add a conversation turn."""
        self.turn_count += 1
        self.conversation_history.append({"user": user_input, "bot": bot_response, "turn": self.turn_count})

    def get_last_user_input(self) -> Optional[str]:
        """Get the last thing the user said."""
        if self.conversation_history:
            return self.conversation_history[-1].get("user")
        return None


# Global session store: CallSid -> VoiceSession
_sessions: Dict[str, VoiceSession] = {}


def get_session(call_sid: str) -> VoiceSession:
    """Get or create a session for a call."""
    if call_sid not in _sessions:
        _sessions[call_sid] = VoiceSession(call_sid=call_sid)
    return _sessions[call_sid]


def clear_session(call_sid: str) -> None:
    """Remove a session (call ended)."""
    _sessions.pop(call_sid, None)
