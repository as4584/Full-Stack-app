"""
AI Receptionist - Intelligent phone receptionist system.

This package provides automated phone reception capabilities
using Twilio voice services and conversational AI.
"""

__version__ = "0.2.0"
__author__ = "AI Receptionist Team"

from ai_receptionist.config import get_settings, Settings
from ai_receptionist.agent import ConversationBot, ToolCall

__all__ = [
    "get_settings",
    "Settings",
    "ConversationBot",
    "ToolCall",
    "__version__"
]
