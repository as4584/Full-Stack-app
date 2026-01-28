"""
🧠 Copilot context:
This file acts as an eval system for the AI haircut concierge bot.
- It tests conversation flows offline (no API calls).
- Each fixture under docs/samples/*.json represents a scenario.
- We simulate assistant responses and tool calls.
- Each new feature must include:
  1. a fixture file (sample dialogue)
  2. a pytest function to validate logic and order of actions
  3. assertions for confirmation → booking → readback

Copilot, when I ask for new tests, generate both:
- a JSON fixture (docs/samples/)
- a pytest test function following the same structure.
"""

import json
import pytest
from typing import Dict, List, Any
from ai_receptionist.agent import ConversationBot

def load_fixture(fixture_name: str) -> Dict[str, Any]:
    """Load a JSON fixture from docs/samples/"""
    fixture_path = f"docs/samples/{fixture_name}.json"
    with open(fixture_path, 'r') as f:
        return json.load(f)

def validate_booking_flow(bot: ConversationBot, dialogue: List[Dict], validation_rules: Dict) -> None:
    """
    Core evaluation function that validates the booking flow follows proper patterns:
    1. Confirmation occurs before tool call
    2. Tool arguments contain name, service, datetime  
    3. Assistant output contains confirmation phrase
    """
    bot.reset()  # Start fresh
    tool_calls = []
    confirmation_given = False
    last_response = ""
    
    for i, turn in enumerate(dialogue):
        if turn["role"] == "user":
            response = bot.handle_user_message(turn["content"])
            last_response = response
            
            # Check if this is a confirmation from user
            if any(word in turn["content"].lower() for word in ["yes", "confirm", "book it", "please book", "that works", "sounds good", "that's right"]):
                confirmation_given = True
                
        elif turn["role"] == "assistant":
            # For assistant turns in fixtures, we check if they expect a tool call
            if "expected_tool_call" in turn:
                # Verify that a tool call was made during the last user interaction
                current_tool_calls = bot.get_tool_calls()
                if current_tool_calls and len(current_tool_calls) > len(tool_calls):
                    tool_calls = current_tool_calls
                    
                    # Validate: confirmation should happen before booking (for booking actions)
                    latest_tool_call = current_tool_calls[-1]
                    if validation_rules.get("confirmation_before_booking", False) and latest_tool_call.name == "book_appointment":
                        assert confirmation_given, "Tool call made without user confirmation"
                    elif validation_rules.get("confirmation_before_canceling", False) and latest_tool_call.name == "cancel_appointment":
                        assert confirmation_given, "Cancellation made without user confirmation"
                    elif validation_rules.get("confirmation_before_rescheduling", False) and latest_tool_call.name == "reschedule_appointment":
                        assert confirmation_given, "Rescheduling made without user confirmation"
                    
                    # Validate: tool call has required arguments
                    required_args = validation_rules.get("tool_call_has_required_args", [])
                    for arg in required_args:
                        assert arg in latest_tool_call.arguments, f"Missing required argument: {arg}"
                        assert latest_tool_call.arguments[arg] is not None, f"Argument {arg} is None"
                    
                    # Validate: success message contains expected phrases
                    success_phrases = validation_rules.get("success_message_contains", [])
                    for phrase in success_phrases:
                        assert phrase.lower() in last_response.lower(), f"Success message missing phrase: {phrase}"

@pytest.fixture
def sample_dialogue():
    """Legacy fixture for backward compatibility"""
    return [
        {"role": "user", "content": "I'd like to book a haircut."},
        {"role": "assistant", "content": "Sure! What date and time do you have in mind?"}
    ]

def test_legacy_haircut_booking_flow(sample_dialogue):
    """Legacy test for backward compatibility"""
    bot = ConversationBot()
    dialogue = sample_dialogue

    for turn in dialogue:
        if turn["role"] == "user":
            response = bot.handle_user_message(turn["content"])
        else:
            response = bot.handle_assistant_message(turn["content"])

    # This test needs updating - the original assertion was incorrect
    # The bot should ask for clarification, not immediately confirm booking
    assert "date and time" in response.lower() or "when" in response.lower()

def test_incomplete_booking_missing_datetime_flow():
    """
    Eval test for scenario where user asks for haircut but doesn't specify time or date.
    The assistant should clarify missing info before calling booking tool.
    """
    fixture = load_fixture("incomplete_booking_missing_datetime")
    bot = ConversationBot()
    
    # Validate the entire flow
    validate_booking_flow(bot, fixture["dialogue"], fixture["validation_rules"])
    
    # Additional specific assertions
    tool_calls = bot.get_tool_calls()
    assert len(tool_calls) == 1, "Expected exactly one tool call"
    
    tool_call = tool_calls[0]
    assert tool_call.name == "book_appointment"
    assert tool_call.arguments["customer_name"] == "John"
    assert tool_call.arguments["service"] == "haircut"
    assert "tomorrow" in tool_call.arguments["datetime"].lower()

def test_complete_booking_with_all_details_flow():
    """
    Eval test for scenario where user provides all information upfront.
    Should still confirm before booking.
    """
    fixture = load_fixture("complete_booking_flow")
    bot = ConversationBot()
    
    # Validate the entire flow
    validate_booking_flow(bot, fixture["dialogue"], fixture["validation_rules"])
    
    # Additional specific assertions
    tool_calls = bot.get_tool_calls()
    assert len(tool_calls) == 1, "Expected exactly one tool call"
    
    tool_call = tool_calls[0]
    assert tool_call.name == "book_appointment"
    assert tool_call.arguments["customer_name"] == "Sarah"
    assert tool_call.arguments["service"] == "haircut"

def test_no_premature_booking_without_confirmation():
    """
    Eval test to ensure bot never makes booking tool calls without confirmation.
    """
    bot = ConversationBot()
    
    # User provides partial info but doesn't confirm
    bot.handle_user_message("I'm John and I want a haircut tomorrow at 2pm")
    
    # Bot should not have made any tool calls yet
    tool_calls = bot.get_tool_calls()
    assert len(tool_calls) == 0, "Bot made premature booking without confirmation"
    
    # Bot should ask for confirmation
    # (This would be tested by checking the actual response in a real implementation)

def test_missing_customer_name_flow():
    """
    Eval test for scenario where user provides service and time but no name.
    The assistant should ask for the missing name before proceeding.
    """
    fixture = load_fixture("missing_name_flow")
    bot = ConversationBot()
    
    # Validate the entire flow
    validate_booking_flow(bot, fixture["dialogue"], fixture["validation_rules"])
    
    # Additional specific assertions
    tool_calls = bot.get_tool_calls()
    assert len(tool_calls) == 1, "Expected exactly one tool call"
    
    tool_call = tool_calls[0]
    assert tool_call.name == "book_appointment"
    assert tool_call.arguments["customer_name"] == "Alex"
    assert tool_call.arguments["service"] == "haircut"
    assert "tomorrow" in tool_call.arguments["datetime"].lower()

def test_missing_information_edge_cases():
    """
    Eval test to ensure bot properly handles missing information scenarios.
    """
    bot = ConversationBot()
    
    # Test missing name
    response = bot.handle_user_message("I want a haircut tomorrow at 2pm")
    assert "name" in response.lower(), "Bot should ask for missing name"
    
    bot.reset()
    
    # Test missing datetime
    response = bot.handle_user_message("Hi, I'm Alice and I want a haircut")
    assert any(word in response.lower() for word in ["date", "time", "when"]), "Bot should ask for missing datetime"
    
    bot.reset()
    
    # Test missing service
    response = bot.handle_user_message("I'm Bob and I want an appointment tomorrow at 3pm")
    # Note: The current bot assumes haircut by default, but in a more sophisticated version
    # it might ask for service type clarification

def test_ambiguous_datetime_request_flow():
    """
    Eval test for scenario where user requests haircut with vague time reference.
    The assistant must clarify before proceeding with booking.
    """
    fixture = load_fixture("ambiguous_datetime_request")
    bot = ConversationBot()
    
    # Validate the entire flow
    validate_booking_flow(bot, fixture["dialogue"], fixture["validation_rules"])
    
    # Additional specific assertions
    tool_calls = bot.get_tool_calls()
    assert len(tool_calls) == 1, "Expected exactly one tool call"
    
    tool_call = tool_calls[0]
    assert tool_call.name == "book_appointment"
    assert tool_call.arguments["customer_name"] == "Mike"
    assert tool_call.arguments["service"] == "haircut"
    assert "wednesday" in tool_call.arguments["datetime"].lower()

def test_after_hours_request_flow():
    """
    Eval test for scenario where user requests appointment outside business hours.
    Assistant must offer alternatives within business hours.
    """
    fixture = load_fixture("after_hours_request")
    bot = ConversationBot()
    
    # Validate the entire flow
    validate_booking_flow(bot, fixture["dialogue"], fixture["validation_rules"])
    
    # Additional specific assertions
    tool_calls = bot.get_tool_calls()
    assert len(tool_calls) == 1, "Expected exactly one tool call"
    
    tool_call = tool_calls[0]
    assert tool_call.name == "book_appointment"
    assert tool_call.arguments["customer_name"] == "Lisa"
    assert tool_call.arguments["service"] == "haircut"
    assert "10 am" in tool_call.arguments["datetime"].lower()

def test_missing_service_type_flow():
    """
    Eval test for scenario where user requests appointment without specifying service.
    Assistant must ask for service type clarification.
    """
    fixture = load_fixture("missing_service_type")
    bot = ConversationBot()
    
    # Validate the entire flow
    validate_booking_flow(bot, fixture["dialogue"], fixture["validation_rules"])
    
    # Additional specific assertions
    tool_calls = bot.get_tool_calls()
    assert len(tool_calls) == 1, "Expected exactly one tool call"
    
    tool_call = tool_calls[0]
    assert tool_call.name == "book_appointment"
    assert tool_call.arguments["customer_name"] == "David"
    assert "haircut and beard trim" in tool_call.arguments["service"]

def test_double_booking_conflict_flow():
    """
    Eval test for scenario where user attempts to book an already taken slot.
    Assistant must detect conflict and offer alternatives.
    """
    fixture = load_fixture("double_booking_conflict")
    bot = ConversationBot()
    
    # Validate the entire flow
    validate_booking_flow(bot, fixture["dialogue"], fixture["validation_rules"])
    
    # Additional specific assertions
    tool_calls = bot.get_tool_calls()
    assert len(tool_calls) == 1, "Expected exactly one tool call"
    
    tool_call = tool_calls[0]
    assert tool_call.name == "book_appointment"
    assert tool_call.arguments["customer_name"] == "Emma"
    assert tool_call.arguments["service"] == "haircut"
    assert "3 pm" in tool_call.arguments["datetime"].lower()

def test_cancel_appointment_flow():
    """
    Eval test for appointment cancellation flow.
    Assistant must confirm before making cancellation tool call.
    """
    fixture = load_fixture("cancel_appointment_flow")
    bot = ConversationBot()
    
    # Validate the entire flow
    validate_booking_flow(bot, fixture["dialogue"], fixture["validation_rules"])
    
    # Additional specific assertions
    tool_calls = bot.get_tool_calls()
    assert len(tool_calls) == 1, "Expected exactly one tool call"
    
    tool_call = tool_calls[0]
    assert tool_call.name == "cancel_appointment"
    assert tool_call.arguments["customer_name"] == "Tom"
    assert tool_call.arguments["service"] == "haircut"
    assert "tomorrow at 11 am" in tool_call.arguments["datetime"].lower()

def test_reschedule_appointment_flow():
    """
    Eval test for appointment rescheduling flow.
    Assistant must confirm new time and ensure no duplicate booking.
    """
    fixture = load_fixture("reschedule_appointment_flow")
    bot = ConversationBot()
    
    # Validate the entire flow
    validate_booking_flow(bot, fixture["dialogue"], fixture["validation_rules"])
    
    # Additional specific assertions
    tool_calls = bot.get_tool_calls()
    assert len(tool_calls) == 1, "Expected exactly one tool call"
    
    tool_call = tool_calls[0]
    assert tool_call.name == "reschedule_appointment"
    assert tool_call.arguments["customer_name"] == "Rachel"
    assert tool_call.arguments["service"] == "haircut"
    assert "tomorrow at 10 am" in tool_call.arguments["old_datetime"].lower()
    assert "friday at 2 pm" in tool_call.arguments["new_datetime"].lower()

def test_payment_security_rejection_flow():
    """
    Eval test for payment security scenario.
    Assistant must reject payment info and guide to secure payment process.
    """
    fixture = load_fixture("payment_security_rejection")
    bot = ConversationBot()
    
    # Validate the entire flow
    validate_booking_flow(bot, fixture["dialogue"], fixture["validation_rules"])
    
    # Additional specific assertions
    tool_calls = bot.get_tool_calls()
    assert len(tool_calls) == 1, "Expected exactly one tool call"
    
    tool_call = tool_calls[0]
    assert tool_call.name == "book_appointment"
    assert tool_call.arguments["customer_name"] == "Chris"
    assert tool_call.arguments["service"] == "haircut"
    assert "tomorrow at 1 pm" in tool_call.arguments["datetime"].lower()

# ===== NEW EVAL TESTS FOR 7 SCENARIOS =====

def test_haircut_ambiguous_time_flow():
    """
    Eval test for scenario where user requests haircut with ambiguous time reference.
    Assistant must clarify specific datetime before booking.
    """
    fixture = load_fixture("haircut_ambiguous_time")
    bot = ConversationBot()
    
    # Validate the entire flow
    validate_booking_flow(bot, fixture["dialogue"], fixture["validation_rules"])
    
    # Additional specific assertions
    tool_calls = bot.get_tool_calls()
    assert len(tool_calls) == 1, "Expected exactly one tool call"
    
    tool_call = tool_calls[0]
    assert tool_call.name == "book_appointment"
    assert tool_call.arguments["customer_name"] == "Mike"
    assert tool_call.arguments["service"] == "haircut"
    assert "wednesday" in tool_call.arguments["datetime"].lower()
    assert "3 pm" in tool_call.arguments["datetime"].lower()

def test_haircut_after_hours_flow():
    """
    Eval test for scenario where user requests appointment outside business hours.
    Assistant must decline professionally and offer alternatives within business hours.
    """
    fixture = load_fixture("haircut_after_hours")
    bot = ConversationBot()
    
    # Validate the entire flow
    validate_booking_flow(bot, fixture["dialogue"], fixture["validation_rules"])
    
    # Additional specific assertions
    tool_calls = bot.get_tool_calls()
    assert len(tool_calls) == 1, "Expected exactly one tool call"
    
    tool_call = tool_calls[0]
    assert tool_call.name == "book_appointment"
    assert tool_call.arguments["customer_name"] == "Sarah"
    assert tool_call.arguments["service"] == "haircut"
    assert "4 pm" in tool_call.arguments["datetime"].lower()

def test_haircut_missing_service_flow():
    """
    Eval test for scenario where user requests appointment without specifying service type.
    Assistant must ask for service clarification before proceeding.
    """
    fixture = load_fixture("haircut_missing_service")
    bot = ConversationBot()
    
    # Validate the entire flow
    validate_booking_flow(bot, fixture["dialogue"], fixture["validation_rules"])
    
    # Additional specific assertions
    tool_calls = bot.get_tool_calls()
    assert len(tool_calls) == 1, "Expected exactly one tool call"
    
    tool_call = tool_calls[0]
    assert tool_call.name == "book_appointment"
    assert tool_call.arguments["customer_name"] == "Alex"
    assert tool_call.arguments["service"] == "haircut"
    assert "2 pm" in tool_call.arguments["datetime"].lower()

def test_haircut_conflict_propose_alt_flow():
    """
    Eval test for scenario where user attempts to book an already taken slot.
    Assistant must detect conflict and propose exactly 2 alternatives, then book user's choice.
    """
    fixture = load_fixture("haircut_conflict_propose_alt")
    bot = ConversationBot()
    
    # Validate the entire flow
    validate_booking_flow(bot, fixture["dialogue"], fixture["validation_rules"])
    
    # Additional specific assertions
    tool_calls = bot.get_tool_calls()
    assert len(tool_calls) == 1, "Expected exactly one tool call"
    
    tool_call = tool_calls[0]
    assert tool_call.name == "book_appointment"
    assert tool_call.arguments["customer_name"] == "Emma"
    assert tool_call.arguments["service"] == "haircut"
    assert "3 pm" in tool_call.arguments["datetime"].lower()

def test_haircut_cancel_flow():
    """
    Eval test for appointment cancellation flow.
    Assistant must confirm cancellation details before making cancel tool call.
    """
    fixture = load_fixture("haircut_cancel_flow")
    bot = ConversationBot()
    
    # Validate the entire flow
    validate_booking_flow(bot, fixture["dialogue"], fixture["validation_rules"])
    
    # Additional specific assertions
    tool_calls = bot.get_tool_calls()
    assert len(tool_calls) == 1, "Expected exactly one tool call"
    
    tool_call = tool_calls[0]
    assert tool_call.name == "cancel_appointment"
    assert tool_call.arguments["customer_name"] == "John"
    assert tool_call.arguments["service"] == "haircut"
    assert "3 pm" in tool_call.arguments["datetime"].lower()

def test_haircut_reschedule_flow():
    """
    Eval test for appointment rescheduling flow.
    Assistant must confirm both old and new times before making reschedule tool call.
    """
    fixture = load_fixture("haircut_reschedule_flow")
    bot = ConversationBot()
    
    # Validate the entire flow
    validate_booking_flow(bot, fixture["dialogue"], fixture["validation_rules"])
    
    # Additional specific assertions
    tool_calls = bot.get_tool_calls()
    assert len(tool_calls) == 1, "Expected exactly one tool call"
    
    tool_call = tool_calls[0]
    assert tool_call.name == "reschedule_appointment"
    assert tool_call.arguments["customer_name"] == "Lisa"
    assert tool_call.arguments["service"] == "haircut"
    assert "2 pm" in tool_call.arguments["old_datetime"].lower()
    assert "4 pm" in tool_call.arguments["new_datetime"].lower()

def test_haircut_payment_refusal_flow():
    """
    Eval test for payment security scenario.
    Assistant must refuse payment info, provide security warning, and never echo PAN numbers.
    """
    fixture = load_fixture("haircut_payment_refusal")
    bot = ConversationBot()
    
    # Validate the entire flow  
    validate_booking_flow(bot, fixture["dialogue"], fixture["validation_rules"])
    
    # Additional specific assertions
    tool_calls = bot.get_tool_calls()
    assert len(tool_calls) == 1, "Expected exactly one tool call"
    
    tool_call = tool_calls[0]
    assert tool_call.name == "book_appointment"
    assert tool_call.arguments["customer_name"] == "Tom"
    assert tool_call.arguments["service"] == "haircut"
    assert "3 pm" in tool_call.arguments["datetime"].lower()
    
    # Security check: ensure PAN never appears in conversation history
    for msg in bot.conversation_history:
        content = msg["content"].lower()
        assert "4532" not in content, "PAN number found in conversation history"
        assert "1234" not in content, "PAN number found in conversation history"
        assert "5678" not in content, "PAN number found in conversation history"
        assert "9012" not in content, "PAN number found in conversation history"