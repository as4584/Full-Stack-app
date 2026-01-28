"""
Integration tests for Twilio Voice endpoints.

PHASE 3 TESTS - Offline Verification (No Twilio)
Tests:
1. Valid signed request returns 200 + valid TwiML
2. Invalid/missing signature returns 403 
3. Fallback endpoint always works
4. Response time < 100ms
5. Content-Type = application/xml
6. Body contains valid TwiML structure
"""
import pytest
import hmac
import hashlib
import base64
import time
from urllib.parse import urlencode
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient


def generate_twilio_signature(auth_token: str, url: str, params: dict) -> str:
    """
    Generate a valid Twilio signature for testing.
    
    The signature is computed as:
    1. Sort POST params by key
    2. Append key=value pairs to URL
    3. HMAC-SHA1 with auth token
    4. Base64 encode
    """
    # Sort and append params to URL
    sorted_params = sorted(params.items())
    data = url + ''.join(f"{k}{v}" for k, v in sorted_params)
    
    # Compute HMAC-SHA1
    signature = hmac.new(
        auth_token.encode('utf-8'),
        data.encode('utf-8'),
        hashlib.sha1
    ).digest()
    
    return base64.b64encode(signature).decode('utf-8')


class TestTwilioVoicePhase3:
    """
    Phase 3 Test Suite: Offline Verification
    
    These tests run WITHOUT Twilio, validating:
    1. HTTP 200 response
    2. Content-Type = application/xml
    3. Body contains valid TwiML
    4. Response time < 100ms
    5. Signature validation works
    """
    
    @pytest.fixture
    def client(self):
        """Create test client with mocked settings."""
        from ai_receptionist.app.main import app
        return TestClient(app)
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings with test Twilio credentials."""
        settings = MagicMock()
        settings.twilio_auth_token = "test_auth_token_12345"
        settings.twilio_account_sid = "ACtest123456789"
        settings.enable_twilio_signature = True
        settings.public_host = "test.example.com"
        settings.global_ai_kill_switch = False
        return settings
    
    def test_fallback_always_returns_valid_twiml(self, client):
        """Test that /twilio/fallback always returns valid TwiML."""
        response = client.post("/twilio/fallback")
        
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/xml"
        assert "<?xml" in response.text
        assert "<Response>" in response.text
        assert "<Say" in response.text
        assert "</Response>" in response.text
    
    def test_fallback_response_time_under_100ms(self, client):
        """CRITICAL: Fallback must respond in under 100ms."""
        start = time.perf_counter()
        response = client.post("/twilio/fallback")
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        assert response.status_code == 200
        assert elapsed_ms < 100, f"Fallback took {elapsed_ms:.1f}ms, must be < 100ms"
    
    def test_voice_rejects_unsigned_request(self, client):
        """Test that unsigned requests are rejected."""
        response = client.post(
            "/twilio/voice",
            data={
                "CallSid": "CA_test_unsigned",
                "From": "+15551234567",
                "To": "+12298215986"
            }
        )
        
        # Should be rejected with 403
        assert response.status_code == 403
    
    def test_voice_rejects_invalid_signature(self, client):
        """Test that requests with invalid signature are rejected."""
        response = client.post(
            "/twilio/voice",
            data={
                "CallSid": "CA_test_invalid_sig",
                "From": "+15551234567",
                "To": "+12298215986"
            },
            headers={
                "X-Twilio-Signature": "invalid_signature_here"
            }
        )
        
        # Should be rejected with 403
        assert response.status_code == 403
    
    @pytest.fixture
    def app_with_mock_settings(self, mock_settings):
        """Create app with properly overridden settings dependency."""
        from ai_receptionist.app.main import app
        from ai_receptionist.config.settings import get_settings
        
        # Override the dependency
        app.dependency_overrides[get_settings] = lambda: mock_settings
        yield app
        # Clean up
        app.dependency_overrides.clear()
    
    @pytest.fixture
    def client_with_mock(self, app_with_mock_settings):
        """Create test client with mocked settings."""
        return TestClient(app_with_mock_settings)
    
    def test_voice_accepts_valid_signature_and_returns_twiml(self, client_with_mock, mock_settings):
        """Test that valid signature returns proper TwiML response."""
        # Prepare test data
        test_url = "http://testserver/twilio/voice"
        params = {
            "CallSid": "CA_test_valid_sig",
            "From": "+15551234567",
            "To": "+12298215986"
        }
        
        # Generate valid signature
        signature = generate_twilio_signature(
            mock_settings.twilio_auth_token,
            test_url,
            params
        )
        
        start = time.perf_counter()
        response = client_with_mock.post(
            "/twilio/voice",
            data=params,
            headers={
                "X-Twilio-Signature": signature
            }
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        # CRITICAL: Must return 200 with valid TwiML
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert "application/xml" in response.headers.get("content-type", "")
        assert "<Response>" in response.text
        assert "<Connect>" in response.text  # Stream connection
        assert "<Stream" in response.text
        assert "</Response>" in response.text
        
        # Response time under 100ms
        assert elapsed_ms < 100, f"Voice took {elapsed_ms:.1f}ms, must be < 100ms"
    
    def test_voice_twiml_structure_is_valid(self, client_with_mock, mock_settings):
        """Test that returned TwiML has proper structure."""
        test_url = "http://testserver/twilio/voice"
        params = {
            "CallSid": "CA_test_structure",
            "From": "+15551234567",
            "To": "+12298215986"
        }
        
        signature = generate_twilio_signature(
            mock_settings.twilio_auth_token,
            test_url,
            params
        )
        
        response = client_with_mock.post(
            "/twilio/voice",
            data=params,
            headers={
                "X-Twilio-Signature": signature
            }
        )
        
        twiml = response.text
        
        # Validate TwiML structure
        assert twiml.startswith("<?xml") or "<Response>" in twiml
        assert "<Connect>" in twiml
        assert "url=" in twiml  # Stream URL
        assert "wss://" in twiml  # WebSocket protocol
        assert "call_sid" in twiml.lower()  # Call SID parameter
    
    def test_voice_does_not_block_on_db(self, client_with_mock, mock_settings):
        """
        Test that voice endpoint doesn't block waiting for database.
        
        This is tested by ensuring response time is fast (<100ms)
        even when no DB is configured - the endpoint should return
        TwiML immediately and log to DB in background.
        """
        test_url = "http://testserver/twilio/voice"
        params = {
            "CallSid": "CA_test_no_db_block",
            "From": "+15551234567",
            "To": "+12298215986"
        }
        
        signature = generate_twilio_signature(
            mock_settings.twilio_auth_token,
            test_url,
            params
        )
        
        # Run multiple times to ensure consistent fast response
        times = []
        for i in range(5):
            start = time.perf_counter()
            response = client_with_mock.post(
                "/twilio/voice",
                data=params,
                headers={
                    "X-Twilio-Signature": signature
                }
            )
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
            assert response.status_code == 200
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        assert max_time < 100, f"Max response time {max_time:.1f}ms exceeds 100ms limit"
        assert avg_time < 50, f"Avg response time {avg_time:.1f}ms too slow"


class TestTwilioFallback:
    """Test suite for /twilio/fallback endpoint."""
    
    @pytest.fixture
    def client(self):
        from ai_receptionist.app.main import app
        return TestClient(app)
    
    def test_fallback_http_200(self, client):
        """Fallback must return HTTP 200."""
        response = client.post("/twilio/fallback")
        assert response.status_code == 200
    
    def test_fallback_content_type_xml(self, client):
        """Fallback must return application/xml."""
        response = client.post("/twilio/fallback")
        assert "application/xml" in response.headers.get("content-type", "")
    
    def test_fallback_valid_twiml_structure(self, client):
        """Fallback must return valid TwiML structure."""
        response = client.post("/twilio/fallback")
        text = response.text
        
        # Check XML declaration
        assert text.startswith("<?xml")
        
        # Check TwiML structure
        assert "<Response>" in text
        assert "</Response>" in text
        assert "<Say" in text
        assert "</Say>" in text
        
        # Should include hangup or redirect
        assert "<Hangup/>" in text or "<Redirect" in text
    
    def test_fallback_does_not_depend_on_auth(self, client):
        """Fallback must work without any authentication."""
        # Multiple requests should all succeed
        for _ in range(3):
            response = client.post("/twilio/fallback")
            assert response.status_code == 200
    
    def test_fallback_response_length(self, client):
        """Fallback response must have content (not empty body)."""
        response = client.post("/twilio/fallback")
        
        assert len(response.text) > 50, "Response body too short or empty"
        assert len(response.content) > 50, "Response content too short"
    
    def test_fallback_concurrent_requests(self, client):
        """Fallback must handle concurrent requests."""
        import concurrent.futures
        
        def make_request():
            return client.post("/twilio/fallback")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            results = [f.result() for f in futures]
        
        # All should succeed
        for r in results:
            assert r.status_code == 200
            assert "<Response>" in r.text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
