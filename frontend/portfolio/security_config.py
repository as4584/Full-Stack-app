"""
Security configuration and hardening settings
OWASP ASVS Level 2 compliant configuration
"""

import os
from typing import List


class SecurityConfig:
    """Security configuration class"""

    # Content Security Policy - Strict settings
    CSP_POLICY = {
        "default-src": "'self'",
        "script-src": "'self' 'unsafe-inline' https://fonts.googleapis.com https://www.googletagmanager.com",
        "style-src": "'self' 'unsafe-inline' https://fonts.googleapis.com",
        "font-src": "'self' https://fonts.gstatic.com",
        "img-src": "'self' data: https: blob:",
        "connect-src": "'self' https://www.google-analytics.com",
        "form-action": "'self'",
        "base-uri": "'self'",
        "object-src": "'none'",
        "frame-ancestors": "'none'",
        "upgrade-insecure-requests": "",
    }

    # Security headers
    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    }

    # Rate limiting configuration
    RATE_LIMITS = {
        "api": "30/minute",  # Reduced from 60
        "contact": "3/hour",  # Reduced from 1/minute
        "auth": "5/minute",  # For any auth endpoints
        "static": "100/minute",  # For static files
    }

    # Password policy
    PASSWORD_MIN_LENGTH = 12
    PASSWORD_REQUIRE_UPPER = True
    PASSWORD_REQUIRE_LOWER = True
    PASSWORD_REQUIRE_DIGIT = True
    PASSWORD_REQUIRE_SPECIAL = True

    # Session security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "strict"
    SESSION_EXPIRE_MINUTES = 30

    # File upload restrictions
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    ALLOWED_FILE_TYPES = [".jpg", ".jpeg", ".png", ".pdf", ".txt"]

    # Input validation
    MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_STRING_LENGTH = 1000

    @classmethod
    def get_csp_header(cls) -> str:
        """Generate CSP header string"""
        return "; ".join([f"{key} {value}" for key, value in cls.CSP_POLICY.items()])

    @classmethod
    def get_trusted_hosts(cls) -> List[str]:
        """Get trusted hosts from environment"""
        trusted = os.getenv("TRUSTED_HOSTS", "localhost,127.0.0.1")
        return [host.strip() for host in trusted.split(",")]

    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production"""
        return os.getenv("PRODUCTION", "false").lower() == "true"
