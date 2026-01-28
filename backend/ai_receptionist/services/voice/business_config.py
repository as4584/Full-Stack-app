"""
Business configuration for Carolann M. Aschoff, P.C.

Family law practice in Jersey City, NJ.

Note: Contact information should be loaded from environment variables
in production. These are defaults for development/testing.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ===== BUSINESS IDENTITY =====
BUSINESS_NAME = "Carolann M. Aschoff, P.C."

# ===== SERVICES OFFERED =====
SERVICES = [
    {"name": "Divorce and Separation", "price": "varies"},
    {"name": "Child Custody and Support", "price": "varies"},
    {"name": "Domestic Violence and Mediation", "price": "varies"},
    {"name": "Wills and Estate Planning", "price": "varies"},
]

# ===== BUSINESS HOURS =====
HOURS = {
    "weekday": "Monday – Friday: 9:00 AM – 5:00 PM",
    "weekend": "Saturday & Sunday: Closed",
    "notes": "Evening appointments available by request at our Jersey City office",
}

# ===== STAFF =====
STAFF = [
    {"role": "Founding Attorney", "name": "Carolann M. Aschoff"},
    {"role": "Associate Attorney", "name": "Annmarie Jensen"},
    {"role": "Administrative Team", "name": "Experienced support staff"},
]

# ===== OFFICE LOCATION(S) =====
LOCATION = "Jersey City, NJ"

# ===== CONTACT INFO =====
# These should ideally come from environment variables in production
PHONE: Optional[str] = None  # Load from settings in production
EMAIL = "info@aschofflaw.com"

# ===== ESCALATION =====
ESCALATION_CONTACT = "Front Desk"
ESCALATION_PHONE: Optional[str] = None  # Load from settings in production


def get_phone_number() -> str:
    """
    Get business phone number, with fallback to environment.
    
    Returns:
        Phone number string
    """
    if PHONE:
        return PHONE
    
    try:
        from ai_receptionist.config import get_settings
        settings = get_settings()
        return settings.twilio_phone_number or "Contact office"
    except Exception as e:
        logger.warning(f"Could not load phone from settings: {e}")
        return "Contact office"


def get_escalation_phone() -> str:
    """
    Get escalation phone number, with fallback to environment.
    
    Returns:
        Escalation phone number string
    """
    if ESCALATION_PHONE:
        return ESCALATION_PHONE
    
    return get_phone_number()  # Default to main phone
