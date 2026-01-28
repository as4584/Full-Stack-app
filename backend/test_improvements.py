#!/usr/bin/env python
"""Quick test of improved AI persistence"""

from ai_receptionist.services.voice.intents import detect_intent, handle_intent

# Test expanded keyword detection
test_cases = [
    ("I need a divorce lawyer", "en", "services"),
    ("Can you help with custody?", "en", "services"),
    ("What do you specialize in?", "en", "services"),
    ("How much does it cost?", "en", "pricing"),
    ("What are your rates?", "en", "pricing"),
    ("Tell me about your team", "en", "staff"),
    ("Who is the attorney?", "en", "staff"),
    ("What are your business hours?", "en", "hours"),
    ("When are you open?", "en", "hours"),
    ("I need help", "en", "help_menu"),
    ("What are my options?", "en", "help_menu"),
    ("random gibberish xyz", "en", "other"),  # Should now ask for clarification, not escalate
]

print("=" * 60)
print("TESTING IMPROVED AI INTENT DETECTION")
print("=" * 60)

for user_input, lang, expected_intent in test_cases:
    detected = detect_intent(user_input, lang)
    response, action = handle_intent(detected, lang, user_input)
    
    status = "✓" if detected == expected_intent else "✗"
    print(f"\n{status} Input: '{user_input}'")
    print(f"  Expected: {expected_intent} | Detected: {detected}")
    print(f"  Action: {action}")
    print(f"  Response: {response[:80]}...")

# Test that 'other' intent no longer hangs up
print("\n" + "=" * 60)
print("TESTING 'OTHER' INTENT HANDLING")
print("=" * 60)

response, action = handle_intent("other", "en", "blah blah blah")
print("\nIntent: other")
print(f"Action: {action} (should be 'gather', NOT 'hangup')")
print(f"Response: {response}")

if action == "gather":
    print("\n✓ SUCCESS: AI now asks for clarification instead of escalating!")
else:
    print("\n✗ FAILED: AI still escalating on 'other' intent")

print("\n" + "=" * 60)
