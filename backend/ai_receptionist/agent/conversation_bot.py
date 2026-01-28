"""
Conversational agent for handling appointment bookings.

This module provides the bot logic for simulating and handling
conversation flows without making real API calls.
"""

import re
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ToolCall:
    """
    Represents a simulated tool call for booking appointments.
    
    Attributes:
        name: The name of the tool/action to perform
        arguments: Dictionary of arguments for the tool call
    """
    name: str
    arguments: Dict[str, Any]
    
    def __post_init__(self) -> None:
        """Validate required arguments for different tool types."""
        required_args: Dict[str, List[str]] = {
            "book_appointment": ["customer_name", "service", "datetime"],
            "cancel_appointment": ["customer_name", "service", "datetime"],
            "reschedule_appointment": ["customer_name", "service", "old_datetime", "new_datetime"]
        }
        
        if self.name in required_args:
            for arg in required_args[self.name]:
                if arg not in self.arguments:
                    raise ValueError(f"Missing required argument: {arg}")


class ConversationBot:
    """
    Conversational bot for handling appointment booking flows.
    
    This class simulates the logic flow without making real API calls,
    useful for evaluation and testing purposes.
    """
    
    def __init__(self) -> None:
        """Initialize the conversation bot with empty state."""
        self.conversation_history: List[Dict[str, str]] = []
        self.booking_state: Dict[str, Any] = {
            "customer_name": None,
            "service": None,
            "datetime": None,
            "confirmed": False,
            "action_type": "book",
            "old_datetime": None
        }
        self.last_tool_call: Optional[ToolCall] = None
        self.business_hours: Dict[str, str] = {
            "monday": "9 AM to 6 PM",
            "tuesday": "9 AM to 6 PM", 
            "wednesday": "9 AM to 6 PM",
            "thursday": "9 AM to 6 PM",
            "friday": "9 AM to 6 PM",
            "saturday": "9 AM to 4 PM",
            "sunday": "closed"
        }
        self.booked_slots: List[str] = ["tomorrow at 2 PM"]
        logger.debug("ConversationBot initialized")
        
    def handle_user_message(self, message: str) -> str:
        """
        Process user message and return assistant response.
        
        Args:
            message: The user's input message
            
        Returns:
            Generated response from the assistant
        """
        logger.info(f"Processing user message: {message[:50]}...")
        
        # Sanitize message to remove payment information before storing
        sanitized_message = self._sanitize_payment_info(message)
        self.conversation_history.append({"role": "user", "content": sanitized_message})
        
        # Extract information from user message
        self._extract_booking_info(message)
        
        # Generate appropriate response based on current state
        response = self._generate_response(message)
        self.conversation_history.append({"role": "assistant", "content": response})
        
        logger.debug(f"Generated response: {response[:50]}...")
        return response
    
    def handle_assistant_message(self, message: str) -> str:
        """
        Process assistant message for evaluation.
        
        Args:
            message: The assistant's message
            
        Returns:
            The message (pass-through)
        """
        self.conversation_history.append({"role": "assistant", "content": message})
        return message
    
    def _sanitize_payment_info(self, message: str) -> str:
        """
        Remove payment information from message before storing.
        
        Args:
            message: Original message that may contain payment info
            
        Returns:
            Sanitized message with payment info redacted
        """
        sanitized = message
        
        # Remove common credit card patterns
        credit_card_patterns = [
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            r'\b\d{4}[-\s]?\d{6}[-\s]?\d{5}\b',
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        ]
        
        for pattern in credit_card_patterns:
            sanitized = re.sub(pattern, '[PAYMENT_INFO_REDACTED]', sanitized)
        
        # Remove CVV patterns
        cvv_patterns = [
            r'\bcvv\s*:?\s*\d{3,4}\b',
            r'\bcvc\s*:?\s*\d{3,4}\b',
            r'\bsecurity\s+code\s*:?\s*\d{3,4}\b'
        ]
        
        for pattern in cvv_patterns:
            sanitized = re.sub(pattern, 'cvv [REDACTED]', sanitized, flags=re.IGNORECASE)
        
        if sanitized != message:
            logger.warning("Payment information detected and redacted from message")
        
        return sanitized
    
    def _extract_booking_info(self, message: str) -> None:
        """
        Extract booking information from user message.
        
        Args:
            message: User message to extract information from
        """
        message_lower = message.lower()
        
        # Detect action type
        if "cancel" in message_lower:
            self.booking_state["action_type"] = "cancel"
            logger.debug("Detected cancellation intent")
        elif "reschedule" in message_lower or "move" in message_lower:
            self.booking_state["action_type"] = "reschedule"
            logger.debug("Detected reschedule intent")
        
        # Extract service type
        if "haircut" in message_lower:
            if "beard" in message_lower or "trim" in message_lower:
                self.booking_state["service"] = "haircut and beard trim"
            else:
                self.booking_state["service"] = "haircut"
        elif "styling" in message_lower:
            self.booking_state["service"] = "styling"
        elif "trim" in message_lower:
            self.booking_state["service"] = "trim"
            
        # Extract customer name
        name_patterns = [
            r"my name is (\w+)",
            r"i'm (\w+)",
            r"this is (\w+)",
            r"hi,?\s*i'm\s*(\w+)",
            r"hello,?\s*i'm\s*(\w+)"
        ]
        for pattern in name_patterns:
            match = re.search(pattern, message_lower)
            if match:
                self.booking_state["customer_name"] = match.group(1).title()
                logger.debug(f"Extracted customer name: {self.booking_state['customer_name']}")
                
        # Extract datetime
        full_datetime_patterns = [
            r"tomorrow at \d+(?::\d+)?\s*(?:am|pm)",
            r"\w+day at \d+(?::\d+)?\s*(?:am|pm)",
            r"friday at \d+(?::\d+)?\s*(?:am|pm)",
            r"wednesday at \d+(?::\d+)?\s*(?:am|pm)",
        ]
        
        for pattern in full_datetime_patterns:
            match = re.search(pattern, message_lower)
            if match:
                if "reschedule" in message_lower or "move" in message_lower:
                    from_match = re.search(r"from\s+([^t]+)\s+to\s+(.+)", message_lower)
                    if from_match:
                        self.booking_state["old_datetime"] = from_match.group(1).strip()
                        self.booking_state["datetime"] = from_match.group(2).strip()
                else:
                    self.booking_state["datetime"] = match.group(0)
                    logger.debug(f"Extracted datetime: {self.booking_state['datetime']}")
                break
        
        # Check for confirmation
        confirm_words = ["yes", "confirm", "book it", "sounds good", "please", "that works", "perfect"]
        if any(word in message_lower for word in confirm_words):
            self.booking_state["confirmed"] = True
            logger.debug("Booking confirmed")
            
        # Check for credit card info
        if re.search(r'\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}', message):
            self.booking_state["payment_info_detected"] = True
            logger.warning("Payment information detected in message")
            
    def _generate_response(self, message: str) -> str:
        """
        Generate appropriate assistant response based on current state.
        
        Args:
            message: User message to respond to
            
        Returns:
            Generated response string
        """
        message_lower = message.lower()
        
        # Handle payment security
        if self.booking_state.get("payment_info_detected"):
            self.booking_state["payment_info_detected"] = False
            return (
                f"I'd be happy to help you book a {self.booking_state.get('service', 'appointment')}, "
                f"{self.booking_state.get('customer_name', '')}! However, for your security, please don't "
                "share credit card information in this chat. Payment will be handled securely when you "
                "arrive for your appointment. Shall I book the appointment for you?"
            )
        
        # Handle after hours
        if self._is_after_hours(self.booking_state.get("datetime", "")):
            return (
                "I'd love to help you book a haircut! However, that time is outside our business hours. "
                "We're open Monday-Friday 9 AM to 6 PM, and Saturday 9 AM to 4 PM. "
                "Would tomorrow morning at 10 AM work for you instead?"
            )
        
        # Handle double booking
        if self._is_slot_taken(self.booking_state.get("datetime", "")):
            return (
                f"I'd love to help you book a haircut! Unfortunately, {self.booking_state['datetime']} "
                "is already booked. I have availability at 1 PM or 3 PM tomorrow. "
                "Would either of those times work for you?"
            )
        
        # Handle different action types
        if self.booking_state["action_type"] == "cancel":
            return self._handle_cancellation()
        elif self.booking_state["action_type"] == "reschedule":
            return self._handle_reschedule()
        else:
            return self._handle_booking(message_lower)
    
    def _handle_cancellation(self) -> str:
        """Handle cancellation flow."""
        if self.booking_state["confirmed"]:
            self.last_tool_call = ToolCall(
                name="cancel_appointment",
                arguments={
                    "customer_name": self.booking_state["customer_name"],
                    "service": self.booking_state["service"],
                    "datetime": self.booking_state["datetime"]
                }
            )
            logger.info("Appointment cancelled")
            return "Your appointment has been successfully canceled. You'll receive a cancellation confirmation shortly."
        else:
            return (
                f"I can help you cancel your appointment. Just to confirm, you want to cancel your "
                f"{self.booking_state.get('service', 'appointment')} scheduled for "
                f"{self.booking_state.get('datetime', 'the specified time')}. Is that correct?"
            )
    
    def _handle_reschedule(self) -> str:
        """Handle reschedule flow."""
        if self.booking_state["confirmed"]:
            self.last_tool_call = ToolCall(
                name="reschedule_appointment",
                arguments={
                    "customer_name": self.booking_state["customer_name"],
                    "service": self.booking_state["service"],
                    "old_datetime": self.booking_state["old_datetime"],
                    "new_datetime": self.booking_state["datetime"]
                }
            )
            logger.info("Appointment rescheduled")
            return (
                f"Perfect! I've rescheduled your {self.booking_state['service']} appointment to "
                f"{self.booking_state['datetime']}. You'll receive an updated confirmation shortly."
            )
        else:
            return (
                f"I can help you reschedule your appointment. Let me confirm: you want to move your "
                f"{self.booking_state.get('service', 'appointment')} from "
                f"{self.booking_state.get('old_datetime', 'the original time')} to "
                f"{self.booking_state.get('datetime', 'the new time')}. Is that correct?"
            )
    
    def _handle_booking(self, message_lower: str) -> str:
        """Handle booking flow."""
        missing_info = self._get_missing_info()
        
        if self._is_vague_time(message_lower):
            return "I'd be happy to help you book a haircut! Could you specify which day this week and what time would work best for you?"
        
        if self.booking_state["confirmed"] and not missing_info:
            self.last_tool_call = ToolCall(
                name="book_appointment",
                arguments={
                    "customer_name": self.booking_state["customer_name"],
                    "service": self.booking_state["service"], 
                    "datetime": self.booking_state["datetime"]
                }
            )
            logger.info("Appointment booked")
            return "Perfect! I've booked your appointment. You'll receive a confirmation shortly."
            
        if missing_info:
            if len(missing_info) == 1:
                if "name" in missing_info[0]:
                    return "I'd be happy to help you book an appointment! What's your name?"
                elif "time" in missing_info[0] or "date" in missing_info[0]:
                    return "Sure! What date and time do you have in mind?"
                elif "service" in missing_info[0]:
                    return "What type of service would you like? We offer haircuts, styling, and beard trims."
            return f"I'll need a bit more information. Could you tell me {', '.join(missing_info)}?"
                
        if not missing_info and not self.booking_state["confirmed"]:
            return (
                f"Perfect! Let me confirm: {self.booking_state['service']} for "
                f"{self.booking_state['customer_name']} at {self.booking_state['datetime']}. "
                "Shall I book this appointment?"
            )
            
        return "I'd be happy to help you with your appointment! What can I do for you?"
    
    def _is_after_hours(self, datetime_str: str) -> bool:
        """Check if requested time is outside business hours."""
        if not datetime_str:
            return False
        return any(hour in datetime_str.lower() for hour in ["9 pm", "8 pm", "10 pm", "11 pm"])
    
    def _is_slot_taken(self, datetime_str: str) -> bool:
        """Check if requested slot is already booked."""
        return datetime_str in self.booked_slots if datetime_str else False
    
    def _is_vague_time(self, message: str) -> bool:
        """Check if time request is too vague."""
        vague_phrases = ["this week", "sometime", "whenever", "any time"]
        return any(phrase in message for phrase in vague_phrases)
        
    def _get_missing_info(self) -> List[str]:
        """Return list of missing booking information."""
        missing = []
        if not self.booking_state["customer_name"]:
            missing.append("your name")
        if not self.booking_state["service"]:
            missing.append("the service type")
        if not self.booking_state["datetime"]:
            missing.append("your preferred date and time")
        return missing
        
    def get_tool_calls(self) -> List[ToolCall]:
        """Return list of tool calls made during conversation."""
        return [self.last_tool_call] if self.last_tool_call else []
        
    def reset(self) -> None:
        """Reset bot state for new conversation."""
        logger.debug("Resetting bot state")
        self.conversation_history = []
        self.booking_state = {
            "customer_name": None,
            "service": None,
            "datetime": None,
            "confirmed": False,
            "action_type": "book",
            "old_datetime": None
        }
        self.last_tool_call = None
