# Haircut Assistant Evaluation System

## Overview

This repository contains a comprehensive offline evaluation system for testing the conversational intelligence of a haircut appointment booking assistant. The system validates complex dialogue flows, business logic enforcement, and appropriate handling of edge cases through deterministic JSON fixtures and pytest-based testing.

## Evaluation Scenarios

The system tests 7 critical conversational intelligence scenarios:

### 1. **Ambiguous Datetime Request**
- **Purpose**: Tests handling of vague time references like "sometime afternoon"
- **Validation**: Assistant must clarify specific time before proceeding
- **Expected**: Clarification question, no premature booking

### 2. **After-Hours Request** 
- **Purpose**: Tests business hours validation and professional responses
- **Validation**: Rejects bookings outside business hours gracefully
- **Expected**: Business hours explanation, alternative time suggestions

### 3. **Missing Service Type**
- **Purpose**: Tests ability to extract service information through clarification
- **Validation**: Assistant prompts for service details when unclear
- **Expected**: Service clarification, complete information gathering

### 4. **Double-Booking Conflict**
- **Purpose**: Tests conflict detection and alternative time offering
- **Validation**: Detects scheduling conflicts, proposes alternatives
- **Expected**: Conflict notification, 2+ alternative times, user choice confirmation

### 5. **Cancel Appointment Flow**
- **Purpose**: Tests cancellation request handling and confirmation
- **Validation**: Processes cancellation requests appropriately
- **Expected**: Cancellation confirmation, appropriate tool call

### 6. **Reschedule Appointment Flow**
- **Purpose**: Tests rescheduling logic with old/new time extraction
- **Validation**: Handles appointment modifications correctly
- **Expected**: Old and new time capture, reschedule confirmation

### 7. **Payment Security Rejection**
- **Purpose**: Tests detection and handling of payment security flags
- **Validation**: Refuses to process sensitive payment information
- **Expected**: Security warning, no PAN echoing, safe redirection

## Architecture

### Core Components

- **`src/haircut_bot.py`**: Offline conversation simulation engine
- **`tests/test_eval_blueprint.py`**: Comprehensive pytest validation suite
- **`docs/samples/*.json`**: Deterministic conversation fixtures
- **`pytest.ini`**: Test configuration for offline execution

### Design Principles

- **Single Responsibility**: Validation helpers centralized, no duplicated logic
- **Dependency Inversion**: Core logic uses simulation interfaces, not external APIs
- **Offline-First**: No network calls, completely deterministic testing
- **SOLID Architecture**: Maintainable, extensible evaluation framework

## Usage

### Running Tests

Execute the complete evaluation suite:

```bash
# Run all evaluation tests
pytest -v

# Run specific scenario
pytest -v tests/test_eval_blueprint.py::test_ambiguous_datetime_request_flow

# Quick run (minimal output)
pytest -q
```

### Test Requirements

All tests enforce these critical requirements:

1. **Confirmation Before Booking**: No tool calls until explicit user confirmation
2. **Complete Information Gathering**: All required fields validated before booking
3. **Professional Responses**: Appropriate tone and business logic enforcement
4. **Security Compliance**: Sensitive information handling and rejection
5. **Conversation Flow**: Natural dialogue progression and context awareness

### Expected Output

```
tests/test_eval_blueprint.py::test_ambiguous_datetime_request_flow PASSED
tests/test_eval_blueprint.py::test_after_hours_request_flow PASSED
tests/test_eval_blueprint.py::test_missing_service_type_flow PASSED
tests/test_eval_blueprint.py::test_double_booking_conflict_flow PASSED
tests/test_eval_blueprint.py::test_cancel_appointment_flow PASSED
tests/test_eval_blueprint.py::test_reschedule_appointment_flow PASSED
tests/test_eval_blueprint.py::test_payment_security_rejection_flow PASSED

============== 13 passed in 0.XX seconds ==============
```

## Fixture Schema

Each JSON fixture follows this standardized schema:

```json
{
  "scenario": "scenario_name",
  "description": "Brief scenario description",
  "expected_flow": ["step1", "step2", "..."],
  "dialogue": [
    {
      "role": "user|assistant",
      "content": "Message content",
      "expected_actions": ["action1", "action2"],
      "expected_tool_call": {
        "name": "tool_name",
        "arguments": {"key": "value"}
      }
    }
  ],
  "validation_rules": {
    "must_confirm_before_booking": true,
    "required_fields": ["customer_name", "service", "datetime"],
    "expected_final_response": "confirmation phrase"
  }
}
```

## Configuration

### Test Environment

- **Python Version**: 3.11+
- **Dependencies**: pytest only (minimal external dependencies)
- **Execution Mode**: Completely offline, no API calls
- **Test Mode**: `TEST_MODE=true` environment variable ensures simulation

### Business Rules

- **Business Hours**: Monday-Friday 9 AM - 6 PM, Saturday 9 AM - 4 PM, Sunday closed
- **Services**: haircut, styling, trim, haircut and beard trim
- **Booking Validation**: Requires customer name, service type, and specific datetime
- **Conflict Handling**: Automatic alternative time suggestions when slots are unavailable

## Continuous Integration

The system includes automated CI validation:

- **Trigger**: Every push and pull request
- **Environment**: Python 3.11 with minimal dependencies
- **Validation**: All tests must pass for green build status
- **Execution**: Completely offline, no external service dependencies

## Notes

- **Offline Only**: System designed for deterministic evaluation without API dependencies
- **Maintainable**: Clear separation of concerns and comprehensive test coverage
- **Extensible**: Easy addition of new scenarios through JSON fixtures and corresponding tests
- **Production-Ready**: Enforces real-world business logic and security requirements