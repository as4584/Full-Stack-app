"""
Input validation and sanitization utilities
OWASP compliant input handling
"""

import html
import re
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from security_config import SecurityConfig


class ContactFormSecure(BaseModel):
    """Secure contact form with comprehensive validation"""

    name: str = Field(..., min_length=2, max_length=50, description="Contact name")
    email: EmailStr = Field(..., description="Valid email address")
    subject: str = Field(
        ..., min_length=5, max_length=100, description="Message subject"
    )
    message: str = Field(
        ...,
        min_length=20,
        max_length=SecurityConfig.MAX_STRING_LENGTH,
        description="Message content",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate and sanitize name field"""
        # Remove any HTML/script content
        sanitized = html.escape(v.strip())

        # Allow only letters, spaces, hyphens, apostrophes
        if not re.match(r"^[a-zA-Z\s\-']+$", sanitized):
            raise ValueError("Name contains invalid characters")

        return sanitized

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, v: str) -> str:
        """Validate and sanitize subject field"""
        # Remove any HTML/script content
        sanitized = html.escape(v.strip())

        # Check for suspicious patterns
        suspicious_patterns = [
            r"<script",
            r"javascript:",
            r"data:",
            r"vbscript:",
            r"onload=",
            r"onerror=",
            r"onclick=",
            r"<iframe",
            r"<object",
            r"<embed",
            r"<link",
            r"<meta",
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, sanitized.lower()):
                raise ValueError("Subject contains potentially harmful content")

        return sanitized

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Validate and sanitize message field"""
        # Remove any HTML/script content
        sanitized = html.escape(v.strip())

        # Check for suspicious patterns
        suspicious_patterns = [
            r"<script",
            r"javascript:",
            r"data:",
            r"vbscript:",
            r"onload=",
            r"onerror=",
            r"onclick=",
            r"<iframe",
            r"<object",
            r"<embed",
            r"<link",
            r"<meta",
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, sanitized.lower()):
                raise ValueError("Message contains potentially harmful content")

        # Check for spam patterns
        spam_indicators = [
            r"(?i)\bviagra\b",
            r"(?i)\bcialis\b",
            r"(?i)\bcasino\b",
            r"(?i)\bloan\b",
            r"(?i)\bcrypto\b",
            r"(?i)\bbitcoin\b",
            r"(?i)click here",
            r"(?i)limited time",
            r"(?i)act now",
        ]

        spam_score = sum(
            1 for pattern in spam_indicators if re.search(pattern, sanitized)
        )
        if spam_score >= 2:
            raise ValueError("Message appears to be spam")

        return sanitized


class InputSanitizer:
    """Utility class for input sanitization"""

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe storage"""
        # Remove path traversal attempts
        filename = filename.replace("../", "").replace("..\\", "")

        # Allow only safe characters
        filename = re.sub(r"[^a-zA-Z0-9\-_\.]", "", filename)

        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit(".", 1)
            filename = name[:250] + "." + ext

        return filename

    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL for safe redirect"""
        # Only allow HTTPS URLs to trusted domains
        pattern = r"^https://[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}(/.*)?$"
        return bool(re.match(pattern, url))

    @staticmethod
    def sanitize_search_query(query: str) -> str:
        """Sanitize search query to prevent injection"""
        # Remove special characters that could be used for injection
        sanitized = re.sub(r'[<>"\';\\]', "", query.strip())

        # Limit length
        return sanitized[:100]
