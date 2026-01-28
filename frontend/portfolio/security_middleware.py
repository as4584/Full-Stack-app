"""
Security middleware for FastAPI application
Implements OWASP security best practices
"""

import hashlib
import logging
import secrets
import time
from typing import Any, Callable, Dict

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

from security_config import SecurityConfig

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware with multiple protection layers"""

    def __init__(self, app, config: SecurityConfig = None):
        super().__init__(app)
        self.config = config or SecurityConfig()
        self.request_tracking: Dict[str, list] = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with security checks"""
        start_time = time.time()

        # Generate request ID for tracking
        request_id = self._generate_request_id()
        request.state.request_id = request_id

        # Security checks
        security_result = await self._security_checks(request)
        if security_result:
            return security_result

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(
                "Request processing error",
                request_id=request_id,
                error=str(e),
                path=request.url.path,
            )
            response = StarletteResponse(
                content="Internal Server Error",
                status_code=500,
                headers={"Content-Type": "text/plain"},
            )

        # Add security headers
        response = self._add_security_headers(response)

        # Log request
        process_time = time.time() - start_time
        logger.info(
            "Request processed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            process_time=f"{process_time:.3f}s",
            user_agent=request.headers.get("user-agent", "unknown"),
        )

        return response

    def _generate_request_id(self) -> str:
        """Generate unique request ID"""
        return secrets.token_urlsafe(16)

    async def _security_checks(self, request: Request) -> Response:
        """Perform security validation checks"""

        # Check request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.config.MAX_REQUEST_SIZE:
            logger.warning("Request too large", size=content_length)
            return StarletteResponse(
                content="Request entity too large", status_code=413
            )

        # Check for suspicious patterns
        user_agent = request.headers.get("user-agent", "")
        if self._is_suspicious_user_agent(user_agent):
            logger.warning("Suspicious user agent", user_agent=user_agent)
            return StarletteResponse(content="Forbidden", status_code=403)

        # Basic DDoS protection
        client_ip = self._get_client_ip(request)
        if self._is_rate_limited(client_ip):
            logger.warning("Rate limit exceeded", client_ip=client_ip)
            return StarletteResponse(
                content="Rate limit exceeded",
                status_code=429,
                headers={"Retry-After": "60"},
            )

        return None

    def _add_security_headers(self, response: Response) -> Response:
        """Add security headers to response"""

        # Add all security headers
        for header, value in self.config.SECURITY_HEADERS.items():
            response.headers[header] = value

        # Add CSP header
        response.headers["Content-Security-Policy"] = self.config.get_csp_header()

        # Add secure cookie attributes if setting cookies
        if "set-cookie" in response.headers:
            cookie_value = response.headers["set-cookie"]
            if self.config.is_production():
                # Make cookies secure in production
                if "Secure" not in cookie_value:
                    cookie_value += "; Secure"
                if "HttpOnly" not in cookie_value:
                    cookie_value += "; HttpOnly"
                if "SameSite" not in cookie_value:
                    cookie_value += "; SameSite=Strict"
                response.headers["set-cookie"] = cookie_value

        return response

    def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """Check for suspicious user agents"""
        suspicious_patterns = [
            "sqlmap",
            "nikto",
            "nmap",
            "masscan",
            "burp",
            "acunetix",
            "w3af",
            "owasp",
            "dirb",
            "gobuster",
            "wget",
            "curl",
            "python-requests",  # Be careful with legitimate tools
        ]

        user_agent_lower = user_agent.lower()
        return any(pattern in user_agent_lower for pattern in suspicious_patterns)

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP with proxy support"""
        # Check for forwarded headers (but validate them)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP (client IP)
            return forwarded_for.split(",")[0].strip()

        forwarded = request.headers.get("x-forwarded")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fallback to direct connection
        return request.client.host if request.client else "unknown"

    def _is_rate_limited(self, client_ip: str) -> bool:
        """Simple rate limiting implementation"""
        now = time.time()
        window = 60  # 1 minute window
        max_requests = 100  # Max requests per window

        # Clean old entries
        if client_ip in self.request_tracking:
            self.request_tracking[client_ip] = [
                req_time
                for req_time in self.request_tracking[client_ip]
                if now - req_time < window
            ]
        else:
            self.request_tracking[client_ip] = []

        # Check if over limit
        if len(self.request_tracking[client_ip]) >= max_requests:
            return True

        # Add current request
        self.request_tracking[client_ip].append(now)
        return False
