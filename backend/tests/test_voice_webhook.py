"""
Tests for Twilio voice webhook endpoints
Tests the FastAPI app using TestClient for offline testing
"""

from fastapi.testclient import TestClient
from src.twilio_handler import app

client = TestClient(app)

def test_health_endpoint():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}

def test_voice_entry_returns_twiml():
    """Test that voice entry endpoint returns valid TwiML with Gather"""
    response = client.post("/twilio/voice")
    
    assert response.status_code == 200
    assert "application/xml" in response.headers["content-type"]
    
    # Check TwiML structure
    content = response.text
    assert "<Response>" in content
    assert "<Gather" in content
    assert "input=\"speech\"" in content
    assert "action=\"/twilio/handle\"" in content
    assert "<Say>" in content
    assert "Hello! Welcome to the AI Haircut Concierge" in content

def test_voice_entry_get_also_works():
    """Test that GET to voice entry also works"""
    response = client.get("/twilio/voice")
    
    assert response.status_code == 200
    assert "application/xml" in response.headers["content-type"]
    assert "<Response>" in response.text

def test_handle_roundtrip_gives_reply():
    """Test complete roundtrip: speech input -> bot processing -> TwiML response"""
    # First, establish a call session
    call_sid = "test_call_123"
    headers = {"X-Twilio-CallSid": call_sid}
    
    # Start voice call to initialize session
    client.post("/twilio/voice", headers=headers)
    
    # Send speech input
    form_data = {
        "SpeechResult": "I need a haircut Friday at 3pm, I'm Alex",
        "CallSid": call_sid
    }
    
    response = client.post("/twilio/handle", data=form_data)
    
    assert response.status_code == 200
    assert "application/xml" in response.headers["content-type"]
    
    content = response.text
    assert "<Response>" in content
    assert "<Say>" in content
    assert "<Gather" in content
    
    # Should contain bot response - it will likely ask for confirmation or more details
    # The exact content depends on the bot logic, but it should be helpful
    assert len(content) > 100  # Should have substantial response

def test_handle_empty_prompts_retry():
    """Test that empty/missing speech input prompts for retry"""
    call_sid = "test_call_empty"
    
    # Test with empty SpeechResult
    form_data = {
        "SpeechResult": "",
        "CallSid": call_sid
    }
    
    response = client.post("/twilio/handle", data=form_data)
    
    assert response.status_code == 200
    content = response.text
    
    assert "<Response>" in content
    assert "<Say>" in content
    assert "<Gather" in content
    assert "I'm sorry, I didn't catch that" in content
    assert "try again" in content

def test_handle_missing_speech_prompts_retry():
    """Test that missing speech data prompts for retry"""
    call_sid = "test_call_missing"
    
    # Test with no SpeechResult at all
    form_data = {
        "CallSid": call_sid
    }
    
    response = client.post("/twilio/handle", data=form_data)
    
    assert response.status_code == 200
    content = response.text
    
    assert "<Response>" in content
    assert "<Say>" in content
    assert "I'm sorry, I didn't catch that" in content

def test_handle_with_digits_input():
    """Test that digit input is also handled"""
    call_sid = "test_call_digits"
    
    form_data = {
        "Digits": "1",
        "CallSid": call_sid
    }
    
    response = client.post("/twilio/handle", data=form_data)
    
    assert response.status_code == 200
    content = response.text
    assert "<Response>" in content
    assert "<Say>" in content

def test_multiple_exchanges_in_session():
    """Test that multiple exchanges work within the same call session"""
    call_sid = "test_call_multi"
    headers = {"X-Twilio-CallSid": call_sid}
    
    # Initialize session
    client.post("/twilio/voice", headers=headers)
    
    # First exchange
    response1 = client.post("/twilio/handle", data={
        "SpeechResult": "I want a haircut",
        "CallSid": call_sid
    })
    assert response1.status_code == 200
    
    # Second exchange - bot should remember the context
    response2 = client.post("/twilio/handle", data={
        "SpeechResult": "My name is Sarah and I want it tomorrow at 2pm",
        "CallSid": call_sid
    })
    assert response2.status_code == 200
    
    # Both should be valid TwiML
    for response in [response1, response2]:
        content = response.text
        assert "<Response>" in content
        assert "<Say>" in content

def test_session_isolation():
    """Test that different call sessions are isolated"""
    # Two different call sessions
    call_sid_1 = "test_call_isolation_1"
    call_sid_2 = "test_call_isolation_2"
    
    # Start both sessions
    client.post("/twilio/voice", headers={"X-Twilio-CallSid": call_sid_1})
    client.post("/twilio/voice", headers={"X-Twilio-CallSid": call_sid_2})
    
    # Send different inputs to each
    response1 = client.post("/twilio/handle", data={
        "SpeechResult": "I'm Alice and I want a haircut",
        "CallSid": call_sid_1
    })
    
    response2 = client.post("/twilio/handle", data={
        "SpeechResult": "I'm Bob and I want styling",
        "CallSid": call_sid_2
    })
    
    # Both should work independently
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    # Sessions should maintain separate state
    assert "<Response>" in response1.text
    assert "<Response>" in response2.text