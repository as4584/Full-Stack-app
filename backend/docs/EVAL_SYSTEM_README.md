# Haircut Concierge Bot - Evaluation System

## Overview

This evaluation system provides offline testing for the AI haircut concierge bot without making real API calls. It uses a simulation approach to validate conversation flows, tool calls, and business logic.

## Architecture

### Core Components

1. **`src/haircut_bot.py`** - Simulated bot implementation
2. **`tests/test_eval_blueprint.py`** - Evaluation test functions  
3. **`docs/samples/*.json`** - Conversation fixtures

### Key Classes

- **`HaircutConciergeBot`** - Main simulation class that mimics real bot behavior
- **`ToolCall`** - Represents simulated tool calls for appointment booking
- **`validate_booking_flow()`** - Core evaluation function

## Evaluation Patterns

### Each test validates:

1. **Confirmation → Booking → Readback** flow
2. **Tool arguments contain**: `name`, `service`, `datetime`
3. **Assistant output contains** confirmation phrases
4. **No premature booking** without user confirmation

### Sample Test Structure

```python
def test_scenario_name():
    fixture = load_fixture("scenario_name")
    bot = HaircutConciergeBot()
    
    # Validate the entire flow
    validate_booking_flow(bot, fixture["dialogue"], fixture["validation_rules"])
    
    # Additional specific assertions
    tool_calls = bot.get_tool_calls()
    assert len(tool_calls) == 1
    assert tool_calls[0].arguments["customer_name"] == "ExpectedName"
```

## JSON Fixture Format

```json
{
  "scenario": "test_case_name",
  "description": "Human readable description",
  "expected_flow": ["step1", "step2", "step3"],
  "dialogue": [
    {
      "role": "user|assistant",
      "content": "Message content",
      "expected_actions": ["action_type"],
      "expected_tool_call": {
        "name": "tool_name",
        "arguments": {"key": "value"}
      }
    }
  ],
  "validation_rules": {
    "confirmation_before_booking": true,
    "tool_call_has_required_args": ["arg1", "arg2"],
    "success_message_contains": ["phrase1", "phrase2"]
  }
}
```

## Current Test Scenarios

1. **`test_incomplete_booking_missing_datetime`** - User asks for haircut but no time/date
2. **`test_complete_booking_flow`** - User provides all info upfront  
3. **`test_missing_name_flow`** - User provides service/time but no name
4. **`test_no_premature_booking`** - Ensures no booking without confirmation
5. **`test_missing_information_handling`** - Tests various missing info scenarios

## Running Tests

```bash
# Run all eval tests
pytest tests/test_eval_blueprint.py -v

# Run specific test
pytest tests/test_eval_blueprint.py::test_incomplete_booking_missing_datetime -v

# Run with detailed output
pytest tests/test_eval_blueprint.py -v -s
```

## Adding New Tests

When adding new features, always include:

1. **JSON fixture** in `docs/samples/`
2. **pytest function** following existing patterns
3. **Validation assertions** for the specific scenario

### Example: Adding a cancellation test

1. Create `docs/samples/cancellation_flow.json`
2. Add `test_cancellation_flow()` function
3. Ensure validation covers cancellation-specific logic

## Validation Rules

The eval system enforces these key business rules:

- **Confirmation required** before any booking tool call
- **Required arguments** must be present: `customer_name`, `service`, `datetime`
- **Success messages** must contain confirmation language
- **Information gathering** must occur before confirmation
- **No side effects** - tests are completely offline

## Benefits

- **Fast feedback** - No API latency
- **Deterministic** - Same input always produces same output  
- **Comprehensive** - Tests edge cases and error conditions
- **Maintainable** - JSON fixtures are easy to read and modify
- **Scalable** - Easy to add new scenarios as requirements evolve

## Future Enhancements

- Add support for rescheduling scenarios
- Test multi-service bookings
- Validate error handling and recovery flows
- Add performance benchmarks
- Test conversation context retention