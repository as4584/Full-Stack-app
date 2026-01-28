"""
Google Calendar service for booking appointments.

Handles:
- Token retrieval and refresh
- FreeBusy availability checks
- Event creation (booking)
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple

import httpx
from sqlalchemy.orm import Session

from ai_receptionist.config.settings import get_settings
from ai_receptionist.models.oauth import GoogleOAuthToken
from ai_receptionist.utils.encryption import decrypt_token, encrypt_token

logger = logging.getLogger(__name__)

# Google Calendar API endpoints
GOOGLE_FREEBUSY_URL = "https://www.googleapis.com/calendar/v3/freeBusy"
GOOGLE_EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


class CalendarServiceError(Exception):
    """Base exception for calendar service errors."""
    pass


class TokenNotFoundError(CalendarServiceError):
    """Raised when no OAuth token exists for a tenant."""
    pass


class TokenExpiredError(CalendarServiceError):
    """Raised when token refresh fails."""
    pass


class CalendarAPIError(CalendarServiceError):
    """Raised when Google Calendar API returns an error."""
    pass


class CalendarService:
    """
    Service for Google Calendar operations.
    
    All methods are designed to fail gracefully with clear error messages.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
    
    def get_tokens(self, tenant_id: str) -> Tuple[str, str]:
        """
        Retrieve and decrypt tokens for a tenant.
        
        Returns:
            Tuple of (access_token, refresh_token)
            
        Raises:
            TokenNotFoundError: If no token exists for tenant
        """
        token_record = self.db.query(GoogleOAuthToken).filter(
            GoogleOAuthToken.tenant_id == tenant_id,
            GoogleOAuthToken.is_connected == True
        ).first()
        
        if not token_record:
            raise TokenNotFoundError(f"No connected calendar for tenant {tenant_id}")
        
        try:
            access_token = decrypt_token(token_record.access_token_encrypted)
            refresh_token = decrypt_token(token_record.refresh_token_encrypted)
            return access_token, refresh_token
        except Exception as e:
            logger.error(f"Failed to decrypt tokens for tenant {tenant_id}: {e}")
            raise CalendarServiceError("Failed to access calendar credentials")
    
    async def refresh_token_if_expired(self, tenant_id: str) -> str:
        """
        Check token expiration and refresh if needed.
        
        Returns:
            Valid access token
            
        Raises:
            TokenExpiredError: If refresh fails
            TokenNotFoundError: If no token exists
        """
        token_record = self.db.query(GoogleOAuthToken).filter(
            GoogleOAuthToken.tenant_id == tenant_id,
            GoogleOAuthToken.is_connected == True
        ).first()
        
        if not token_record:
            raise TokenNotFoundError(f"No connected calendar for tenant {tenant_id}")
        
        # Check if token is expired (with 5 minute buffer)
        if token_record.expires_at > datetime.utcnow() + timedelta(minutes=5):
            # Token is still valid
            return decrypt_token(token_record.access_token_encrypted)
        
        # Token expired, refresh it
        logger.info(f"Refreshing expired token for tenant {tenant_id}")
        
        try:
            refresh_token = decrypt_token(token_record.refresh_token_encrypted)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    GOOGLE_TOKEN_URL,
                    data={
                        "client_id": self.settings.google_client_id,
                        "client_secret": self.settings.google_client_secret,
                        "refresh_token": refresh_token,
                        "grant_type": "refresh_token",
                    },
                    timeout=10.0,
                )
                
                if response.status_code != 200:
                    logger.error(f"Token refresh failed: {response.text}")
                    raise TokenExpiredError("Failed to refresh calendar access")
                
                token_data = response.json()
                
            # Update stored token
            new_access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            
            token_record.access_token_encrypted = encrypt_token(new_access_token)
            token_record.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            token_record.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Token refreshed successfully for tenant {tenant_id}")
            return new_access_token
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during token refresh: {e}")
            raise TokenExpiredError("Failed to communicate with Google")
    
    async def check_availability(
        self,
        tenant_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> bool:
        """
        Check if a time slot is available using FreeBusy API.
        
        Args:
            tenant_id: Business tenant ID
            start_time: Start of proposed appointment
            end_time: End of proposed appointment
            
        Returns:
            True if slot is available, False if busy
            
        Raises:
            CalendarAPIError: If API call fails
        """
        try:
            access_token = await self.refresh_token_if_expired(tenant_id)
        except (TokenNotFoundError, TokenExpiredError) as e:
            raise CalendarAPIError(str(e))
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    GOOGLE_FREEBUSY_URL,
                    headers={"Authorization": f"Bearer {access_token}"},
                    json={
                        "timeMin": start_time.isoformat() + "Z",
                        "timeMax": end_time.isoformat() + "Z",
                        "items": [{"id": "primary"}],
                    },
                    timeout=10.0,
                )
                
                if response.status_code != 200:
                    logger.error(f"FreeBusy API failed: {response.text}")
                    raise CalendarAPIError("Failed to check calendar availability")
                
                data = response.json()
                
            # Check if there are any busy periods in the requested slot
            calendars = data.get("calendars", {})
            primary = calendars.get("primary", {})
            busy_periods = primary.get("busy", [])
            
            # If no busy periods, the slot is available
            is_available = len(busy_periods) == 0
            
            logger.info(
                f"Availability check for {tenant_id}: "
                f"{start_time.isoformat()} - {end_time.isoformat()} = {'available' if is_available else 'busy'}"
            )
            
            return is_available
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during availability check: {e}")
            raise CalendarAPIError("Failed to check calendar")
    
    async def book_appointment(
        self,
        tenant_id: str,
        start_time: datetime,
        end_time: datetime,
        summary: str,
        description: Optional[str] = None,
        attendee_email: Optional[str] = None,
        attendee_phone: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Book an appointment on Google Calendar.
        
        IMPORTANT: Only call this after check_availability confirms the slot.
        
        Args:
            tenant_id: Business tenant ID
            start_time: Appointment start time
            end_time: Appointment end time
            summary: Event title (e.g., "Appointment with John")
            description: Optional event description
            attendee_email: Optional attendee email
            attendee_phone: Optional attendee phone (added to description)
            
        Returns:
            Dict with event_id and confirmed details
            
        Raises:
            CalendarAPIError: If booking fails
        """
        try:
            access_token = await self.refresh_token_if_expired(tenant_id)
        except (TokenNotFoundError, TokenExpiredError) as e:
            raise CalendarAPIError(str(e))
        
        # Build event payload
        event = {
            "summary": summary,
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": "UTC",
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": "UTC",
            },
        }
        
        # Add description
        desc_parts = []
        if description:
            desc_parts.append(description)
        if attendee_phone:
            desc_parts.append(f"Phone: {attendee_phone}")
        desc_parts.append("Booked via AI Receptionist")
        
        event["description"] = "\n".join(desc_parts)
        
        # Add attendee if email provided
        if attendee_email:
            event["attendees"] = [{"email": attendee_email}]
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    GOOGLE_EVENTS_URL,
                    headers={"Authorization": f"Bearer {access_token}"},
                    json=event,
                    timeout=10.0,
                )
                
                if response.status_code not in (200, 201):
                    logger.error(f"Event creation failed: {response.text}")
                    raise CalendarAPIError("Failed to create calendar event")
                
                event_data = response.json()
                
            event_id = event_data.get("id")
            html_link = event_data.get("htmlLink")
            
            logger.info(
                f"Appointment booked for {tenant_id}: "
                f"{summary} at {start_time.isoformat()} (event_id={event_id})"
            )
            
            return {
                "success": True,
                "event_id": event_id,
                "html_link": html_link,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "summary": summary,
            }
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during event creation: {e}")
            raise CalendarAPIError("Failed to book appointment")


# Convenience functions for use without injecting db session

async def check_calendar_availability(
    tenant_id: str,
    start_time: datetime,
    end_time: datetime,
) -> Tuple[bool, Optional[str]]:
    """
    Check availability with graceful error handling.
    
    Returns:
        Tuple of (is_available, error_message)
        If error_message is not None, availability could not be determined.
    """
    from ai_receptionist.core.database import get_db_session
    
    try:
        with get_db_session() as db:
            service = CalendarService(db)
            available = await service.check_availability(tenant_id, start_time, end_time)
            return available, None
    except CalendarServiceError as e:
        logger.error(f"Calendar availability check failed: {e}")
        return False, str(e)
    except Exception as e:
        logger.error(f"Unexpected error checking availability: {e}")
        return False, "Unable to check calendar at this time"


async def book_calendar_appointment(
    tenant_id: str,
    start_time: datetime,
    end_time: datetime,
    customer_name: str,
    customer_phone: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Book an appointment with graceful error handling.
    
    Returns:
        Tuple of (success, message)
        Message contains confirmation details on success, error message on failure.
    """
    from ai_receptionist.core.database import get_db_session
    
    try:
        with get_db_session() as db:
            service = CalendarService(db)
            
            # Double-check availability before booking
            is_available = await service.check_availability(tenant_id, start_time, end_time)
            if not is_available:
                return False, "That time slot is no longer available"
            
            # Book the appointment
            result = await service.book_appointment(
                tenant_id=tenant_id,
                start_time=start_time,
                end_time=end_time,
                summary=f"Appointment with {customer_name}",
                attendee_phone=customer_phone,
            )
            
            return True, f"Appointment confirmed for {start_time.strftime('%B %d at %I:%M %p')}"
            
    except CalendarServiceError as e:
        logger.error(f"Calendar booking failed: {e}")
        return False, "Unable to complete the booking at this time"
    except Exception as e:
        logger.error(f"Unexpected error booking appointment: {e}")
        return False, "Something went wrong while booking"
