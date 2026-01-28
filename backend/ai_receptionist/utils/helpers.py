"""Utility functions for AI Receptionist."""

import logging

logger = logging.getLogger(__name__)


def sanitize_phone_number(phone: str) -> str:
    """
    Sanitize and format phone number.
    
    Args:
        phone: Raw phone number string
        
    Returns:
        Formatted phone number
    """
    # Remove all non-numeric characters except +
    import re
    cleaned = re.sub(r'[^\d+]', '', phone)
    return cleaned


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid email format
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def mask_sensitive_data(data: str, show_last: int = 4) -> str:
    """
    Mask sensitive data showing only last N characters.
    
    Args:
        data: Sensitive data string
        show_last: Number of characters to show at end
        
    Returns:
        Masked string
    """
    if len(data) <= show_last:
        return '*' * len(data)
    return '*' * (len(data) - show_last) + data[-show_last:]


def parse_duration_to_seconds(duration_str: str) -> int:
    """
    Parse duration string to seconds.
    
    Args:
        duration_str: Duration like "5m", "30s", "1h"
        
    Returns:
        Duration in seconds
    """
    import re
    match = re.match(r'(\d+)([smh])', duration_str.lower())
    if not match:
        logger.warning(f"Invalid duration format: {duration_str}")
        return 0
    
    value = int(match.group(1))
    unit = match.group(2)
    
    multipliers = {'s': 1, 'm': 60, 'h': 3600}
    return value * multipliers.get(unit, 1)
