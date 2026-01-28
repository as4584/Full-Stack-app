# AI Receptionist - Calendar Integration & Knowledge Base Implementation Plan

## 🎯 **Overview**

This document outlines everything needed to add the following capabilities to your AI receptionist:

1. ✅ **Google Calendar Integration** - View and book appointments
2. ✅ **Active Appointment Knowledge** - Real-time awareness of schedule
3. ✅ **Services Knowledge Base** - Information about offered services
4. ✅ **Business Hours Management** - Open/closed times, holidays, etc.

---

## 📋 **What You Need**

### 1. Google Cloud Setup

**Required:**
- Google Cloud Project (free tier available)
- Google Calendar API enabled
- OAuth 2.0 credentials (Service Account OR OAuth Client)
- Calendar ID to manage

**Steps:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use existing)
3. Enable Google Calendar API
4. Create credentials:
   - **Option A (Recommended)**: Service Account (for automated access)
   - **Option B**: OAuth 2.0 Client (for user-based access)
5. Download credentials JSON file
6. Share target calendar with service account email

**Cost:** FREE (up to 1M API calls/day)

---

### 2. Required Python Packages

Add to `requirements.txt`:

```txt
# Google Calendar Integration
google-auth==2.27.0
google-auth-oauthlib==1.2.0
google-auth-httplib2==0.2.0
google-api-python-client==2.116.0

# Timezone handling
pytz==2025.2  # Already have this

# Optional: Better date parsing
python-dateutil==2.9.0.post0  # Already have this
```

**Installation:**
```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

---

### 3. Environment Variables

Add to `.env`:

```bash
# Google Calendar Configuration
GOOGLE_CALENDAR_CREDENTIALS_PATH=./credentials/google-calendar-service-account.json
GOOGLE_CALENDAR_ID=primary  # or specific calendar ID like "abc123@group.calendar.google.com"

# Business Configuration
BUSINESS_TIMEZONE=America/New_York
BUSINESS_NAME=Your Business Name

# Knowledge Base
SERVICES_CONFIG_PATH=./config/services.json
BUSINESS_HOURS_CONFIG_PATH=./config/business_hours.json
```

---

### 4. Configuration Files

#### A. Services Knowledge Base (`config/services.json`)

```json
{
  "services": [
    {
      "id": "haircut",
      "name": "Haircut",
      "description": "Professional haircut and styling",
      "duration_minutes": 30,
      "price": 45.00,
      "available": true,
      "staff": ["John", "Sarah"]
    },
    {
      "id": "color",
      "name": "Hair Coloring",
      "description": "Full hair coloring service",
      "duration_minutes": 90,
      "price": 120.00,
      "available": true,
      "staff": ["Sarah"]
    },
    {
      "id": "consultation",
      "name": "Free Consultation",
      "description": "15-minute consultation to discuss your needs",
      "duration_minutes": 15,
      "price": 0.00,
      "available": true,
      "staff": ["John", "Sarah"]
    }
  ]
}
```

#### B. Business Hours (`config/business_hours.json`)

```json
{
  "timezone": "America/New_York",
  "regular_hours": {
    "monday": {"open": "09:00", "close": "18:00", "closed": false},
    "tuesday": {"open": "09:00", "close": "18:00", "closed": false},
    "wednesday": {"open": "09:00", "close": "18:00", "closed": false},
    "thursday": {"open": "09:00", "close": "20:00", "closed": false},
    "friday": {"open": "09:00", "close": "18:00", "closed": false},
    "saturday": {"open": "10:00", "close": "16:00", "closed": false},
    "sunday": {"closed": true}
  },
  "holidays": [
    {"date": "2025-12-25", "name": "Christmas Day"},
    {"date": "2025-01-01", "name": "New Year's Day"},
    {"date": "2025-07-04", "name": "Independence Day"}
  ],
  "special_hours": [
    {
      "date": "2025-12-24",
      "name": "Christmas Eve",
      "open": "09:00",
      "close": "14:00"
    }
  ],
  "appointment_settings": {
    "min_advance_hours": 2,
    "max_advance_days": 60,
    "slot_duration_minutes": 15,
    "buffer_minutes": 0
  }
}
```

---

## 🏗️ **Architecture Overview**

```
┌─────────────────────────────────────────────────────────────┐
│                     AI Receptionist                          │
│                  (OpenAI Realtime API)                       │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ Uses Function Calling
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                  Function Router                             │
│  - check_availability()                                      │
│  - book_appointment()                                        │
│  - get_services()                                            │
│  - check_business_hours()                                    │
│  - cancel_appointment()                                      │
└──────────────────┬──────────────────────────────────────────┘
                   │
        ┌──────────┼──────────┬──────────────┐
        │          │          │              │
┌───────▼────┐ ┌──▼─────┐ ┌──▼──────┐ ┌────▼─────────┐
│  Calendar  │ │Services│ │Business │ │  Database    │
│  Service   │ │Manager │ │ Hours   │ │  (Optional)  │
│  (Google)  │ │        │ │ Manager │ │              │
└────────────┘ └────────┘ └─────────┘ └──────────────┘
```

---

## 📁 **File Structure**

```
ai_receptionist/
├── config/
│   ├── services.json              # Services knowledge base
│   ├── business_hours.json        # Business hours configuration
│   └── __init__.py
│
├── credentials/
│   └── google-calendar-service-account.json  # Google credentials
│
├── services/
│   ├── calendar_service.py        # Google Calendar integration
│   ├── knowledge_base.py          # Services & business hours
│   ├── appointment_manager.py     # Appointment booking logic
│   └── function_tools.py          # OpenAI function definitions
│
├── api/
│   └── realtime.py                # Updated with function calling
│
└── models/
    └── appointment.py             # Appointment data models
```

---

## 🔧 **Implementation Steps**

### Step 1: Google Calendar Service (`services/calendar_service.py`)

```python
"""
Google Calendar integration service.
Handles authentication and calendar operations.
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import pytz
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class GoogleCalendarService:
    """Manages Google Calendar API interactions."""
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self, credentials_path: str, calendar_id: str = 'primary'):
        """
        Initialize Google Calendar service.
        
        Args:
            credentials_path: Path to service account JSON file
            calendar_id: Calendar ID to use (default: 'primary')
        """
        self.calendar_id = calendar_id
        self.credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=self.SCOPES
        )
        self.service = build('calendar', 'v3', credentials=self.credentials)
        logger.info(f"Google Calendar service initialized for calendar: {calendar_id}")
    
    def get_availability(
        self,
        start_date: datetime,
        end_date: datetime,
        duration_minutes: int = 30
    ) -> List[Dict]:
        """
        Get available time slots between start and end dates.
        
        Args:
            start_date: Start of search window
            end_date: End of search window
            duration_minutes: Required slot duration
            
        Returns:
            List of available time slots
        """
        try:
            # Get all events in the time range
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=start_date.isoformat(),
                timeMax=end_date.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Find gaps between events
            available_slots = []
            current_time = start_date
            
            for event in events:
                event_start = datetime.fromisoformat(
                    event['start'].get('dateTime', event['start'].get('date'))
                )
                
                # If there's a gap before this event
                if (event_start - current_time).total_seconds() >= duration_minutes * 60:
                    available_slots.append({
                        'start': current_time.isoformat(),
                        'end': event_start.isoformat(),
                        'duration_minutes': int((event_start - current_time).total_seconds() / 60)
                    })
                
                event_end = datetime.fromisoformat(
                    event['end'].get('dateTime', event['end'].get('date'))
                )
                current_time = max(current_time, event_end)
            
            # Check if there's time after the last event
            if (end_date - current_time).total_seconds() >= duration_minutes * 60:
                available_slots.append({
                    'start': current_time.isoformat(),
                    'end': end_date.isoformat(),
                    'duration_minutes': int((end_date - current_time).total_seconds() / 60)
                })
            
            logger.info(f"Found {len(available_slots)} available slots")
            return available_slots
            
        except Exception as e:
            logger.error(f"Error getting availability: {e}")
            return []
    
    def create_appointment(
        self,
        summary: str,
        start_time: datetime,
        duration_minutes: int,
        description: str = "",
        attendee_email: Optional[str] = None,
        attendee_name: Optional[str] = None,
        attendee_phone: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Create a new appointment in the calendar.
        
        Args:
            summary: Event title
            start_time: Appointment start time
            duration_minutes: Duration in minutes
            description: Event description
            attendee_email: Customer email
            attendee_name: Customer name
            attendee_phone: Customer phone
            
        Returns:
            Created event details or None if failed
        """
        try:
            end_time = start_time + timedelta(minutes=duration_minutes)
            
            event = {
                'summary': summary,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': str(start_time.tzinfo),
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': str(end_time.tzinfo),
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                        {'method': 'popup', 'minutes': 60},  # 1 hour before
                    ],
                },
            }
            
            # Add attendee if email provided
            if attendee_email:
                event['attendees'] = [{'email': attendee_email}]
            
            # Add customer info to description
            if attendee_name or attendee_phone:
                customer_info = f"\n\nCustomer Information:\n"
                if attendee_name:
                    customer_info += f"Name: {attendee_name}\n"
                if attendee_phone:
                    customer_info += f"Phone: {attendee_phone}\n"
                event['description'] = (event.get('description', '') + customer_info).strip()
            
            created_event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event,
                sendUpdates='all' if attendee_email else 'none'
            ).execute()
            
            logger.info(f"Created appointment: {created_event.get('id')}")
            return {
                'id': created_event.get('id'),
                'summary': created_event.get('summary'),
                'start': created_event['start'].get('dateTime'),
                'end': created_event['end'].get('dateTime'),
                'link': created_event.get('htmlLink')
            }
            
        except Exception as e:
            logger.error(f"Error creating appointment: {e}")
            return None
    
    def get_upcoming_appointments(self, days: int = 7) -> List[Dict]:
        """
        Get upcoming appointments for the next N days.
        
        Args:
            days: Number of days to look ahead
            
        Returns:
            List of upcoming appointments
        """
        try:
            now = datetime.now(pytz.UTC)
            end_date = now + timedelta(days=days)
            
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=now.isoformat(),
                timeMax=end_date.isoformat(),
                maxResults=50,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            appointments = []
            for event in events:
                appointments.append({
                    'id': event.get('id'),
                    'summary': event.get('summary'),
                    'start': event['start'].get('dateTime', event['start'].get('date')),
                    'end': event['end'].get('dateTime', event['end'].get('date')),
                    'description': event.get('description', '')
                })
            
            logger.info(f"Retrieved {len(appointments)} upcoming appointments")
            return appointments
            
        except Exception as e:
            logger.error(f"Error getting upcoming appointments: {e}")
            return []
    
    def cancel_appointment(self, event_id: str) -> bool:
        """
        Cancel an appointment.
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id,
                sendUpdates='all'
            ).execute()
            
            logger.info(f"Cancelled appointment: {event_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling appointment: {e}")
            return False
```

### Step 2: Knowledge Base Manager (`services/knowledge_base.py`)

```python
"""
Knowledge base manager for services and business hours.
"""

import json
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional
import pytz
import logging

logger = logging.getLogger(__name__)

class KnowledgeBase:
    """Manages services and business hours information."""
    
    def __init__(
        self,
        services_path: str,
        business_hours_path: str,
        timezone: str = 'America/New_York'
    ):
        """
        Initialize knowledge base.
        
        Args:
            services_path: Path to services.json
            business_hours_path: Path to business_hours.json
            timezone: Business timezone
        """
        self.timezone = pytz.timezone(timezone)
        self.services = self._load_json(services_path)
        self.business_hours = self._load_json(business_hours_path)
        logger.info("Knowledge base initialized")
    
    def _load_json(self, path: str) -> Dict:
        """Load JSON configuration file."""
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {path}: {e}")
            return {}
    
    def get_all_services(self) -> List[Dict]:
        """Get all available services."""
        return [s for s in self.services.get('services', []) if s.get('available', True)]
    
    def get_service_by_id(self, service_id: str) -> Optional[Dict]:
        """Get service by ID."""
        for service in self.services.get('services', []):
            if service.get('id') == service_id:
                return service
        return None
    
    def get_service_by_name(self, name: str) -> Optional[Dict]:
        """Get service by name (case-insensitive)."""
        name_lower = name.lower()
        for service in self.services.get('services', []):
            if service.get('name', '').lower() == name_lower:
                return service
        return None
    
    def is_open_now(self) -> bool:
        """Check if business is currently open."""
        now = datetime.now(self.timezone)
        return self.is_open_at(now)
    
    def is_open_at(self, dt: datetime) -> bool:
        """
        Check if business is open at specific datetime.
        
        Args:
            dt: Datetime to check
            
        Returns:
            True if open, False if closed
        """
        # Convert to business timezone
        if dt.tzinfo is None:
            dt = self.timezone.localize(dt)
        else:
            dt = dt.astimezone(self.timezone)
        
        # Check if it's a holiday
        date_str = dt.strftime('%Y-%m-%d')
        for holiday in self.business_hours.get('holidays', []):
            if holiday.get('date') == date_str:
                logger.info(f"Closed for holiday: {holiday.get('name')}")
                return False
        
        # Check special hours
        for special in self.business_hours.get('special_hours', []):
            if special.get('date') == date_str:
                return self._is_within_hours(
                    dt.time(),
                    special.get('open'),
                    special.get('close')
                )
        
        # Check regular hours
        day_name = dt.strftime('%A').lower()
        day_hours = self.business_hours.get('regular_hours', {}).get(day_name, {})
        
        if day_hours.get('closed', False):
            return False
        
        return self._is_within_hours(
            dt.time(),
            day_hours.get('open'),
            day_hours.get('close')
        )
    
    def _is_within_hours(self, check_time: time, open_str: str, close_str: str) -> bool:
        """Check if time is within business hours."""
        try:
            open_time = datetime.strptime(open_str, '%H:%M').time()
            close_time = datetime.strptime(close_str, '%H:%M').time()
            return open_time <= check_time <= close_time
        except Exception as e:
            logger.error(f"Error parsing hours: {e}")
            return False
    
    def get_next_opening(self) -> Optional[datetime]:
        """Get next opening time."""
        now = datetime.now(self.timezone)
        
        # Check next 14 days
        for days_ahead in range(14):
            check_date = now + timedelta(days=days_ahead)
            date_str = check_date.strftime('%Y-%m-%d')
            
            # Skip holidays
            is_holiday = any(
                h.get('date') == date_str
                for h in self.business_hours.get('holidays', [])
            )
            if is_holiday:
                continue
            
            # Check special hours
            for special in self.business_hours.get('special_hours', []):
                if special.get('date') == date_str:
                    open_time = datetime.strptime(special.get('open'), '%H:%M').time()
                    opening = self.timezone.localize(
                        datetime.combine(check_date.date(), open_time)
                    )
                    if opening > now:
                        return opening
            
            # Check regular hours
            day_name = check_date.strftime('%A').lower()
            day_hours = self.business_hours.get('regular_hours', {}).get(day_name, {})
            
            if not day_hours.get('closed', False):
                open_time = datetime.strptime(day_hours.get('open'), '%H:%M').time()
                opening = self.timezone.localize(
                    datetime.combine(check_date.date(), open_time)
                )
                if opening > now:
                    return opening
        
        return None
    
    def get_business_hours_summary(self) -> str:
        """Get human-readable business hours summary."""
        regular = self.business_hours.get('regular_hours', {})
        
        summary = "Business Hours:\n"
        for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
            hours = regular.get(day, {})
            day_cap = day.capitalize()
            
            if hours.get('closed', False):
                summary += f"{day_cap}: Closed\n"
            else:
                summary += f"{day_cap}: {hours.get('open', 'N/A')} - {hours.get('close', 'N/A')}\n"
        
        return summary.strip()
```

### Step 3: Function Tools for OpenAI (`services/function_tools.py`)

```python
"""
OpenAI function calling definitions for the AI receptionist.
"""

from typing import List, Dict

# Function definitions for OpenAI Realtime API
FUNCTION_DEFINITIONS = [
    {
        "name": "check_availability",
        "description": "Check available appointment slots for a specific date and service",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date to check in YYYY-MM-DD format"
                },
                "service_name": {
                    "type": "string",
                    "description": "Name of the service (e.g., 'Haircut', 'Hair Coloring')"
                }
            },
            "required": ["date", "service_name"]
        }
    },
    {
        "name": "book_appointment",
        "description": "Book an appointment for a customer",
        "parameters": {
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "Name of the service"
                },
                "start_time": {
                    "type": "string",
                    "description": "Appointment start time in ISO format (YYYY-MM-DDTHH:MM:SS)"
                },
                "customer_name": {
                    "type": "string",
                    "description": "Customer's full name"
                },
                "customer_phone": {
                    "type": "string",
                    "description": "Customer's phone number"
                },
                "customer_email": {
                    "type": "string",
                    "description": "Customer's email address (optional)"
                }
            },
            "required": ["service_name", "start_time", "customer_name", "customer_phone"]
        }
    },
    {
        "name": "get_services",
        "description": "Get list of all available services with prices and descriptions",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "check_business_hours",
        "description": "Check if the business is currently open or get business hours",
        "parameters": {
            "type": "object",
            "properties": {
                "check_date": {
                    "type": "string",
                    "description": "Optional: Check if open on specific date (YYYY-MM-DD)"
                }
            },
            "required": []
        }
    },
    {
        "name": "cancel_appointment",
        "description": "Cancel an existing appointment",
        "parameters": {
            "type": "object",
            "properties": {
                "appointment_id": {
                    "type": "string",
                    "description": "Google Calendar event ID"
                },
                "customer_phone": {
                    "type": "string",
                    "description": "Customer phone number for verification"
                }
            },
            "required": ["appointment_id", "customer_phone"]
        }
    }
]


def get_function_definitions() -> List[Dict]:
    """Get all function definitions for OpenAI."""
    return FUNCTION_DEFINITIONS
```

### Step 4: Update Realtime API (`api/realtime.py`)

Add function calling support to your existing realtime.py. Here are the key changes:

```python
# Add to imports
from ai_receptionist.services.calendar_service import GoogleCalendarService
from ai_receptionist.services.knowledge_base import KnowledgeBase
from ai_receptionist.services.function_tools import get_function_definitions
from ai_receptionist.config.settings import get_settings
from datetime import datetime, timedelta
import pytz

# Initialize services (add after logger)
settings = get_settings()
calendar_service = GoogleCalendarService(
    credentials_path=settings.google_calendar_credentials_path,
    calendar_id=settings.google_calendar_id
)
knowledge_base = KnowledgeBase(
    services_path=settings.services_config_path,
    business_hours_path=settings.business_hours_config_path,
    timezone=settings.business_timezone
)

# Update session configuration to include tools
session_update = {
    "type": "session.update",
    "session": {
        "modalities": ["audio", "text"],
        "instructions": SYSTEM_INSTRUCTIONS,
        "voice": VOICE,
        "input_audio_format": "g711_ulaw",
        "output_audio_format": "g711_ulaw",
        "turn_detection": {
            "type": "server_vad",
            "threshold": 0.5,
            "prefix_padding_ms": 200,
            "silence_duration_ms": 400
        },
        "temperature": 0.7,
        "tools": get_function_definitions(),  # ADD THIS
        "tool_choice": "auto"  # ADD THIS
    }
}

# Add function call handler
async def handle_function_call(function_name: str, arguments: Dict) -> Dict:
    """Handle function calls from OpenAI."""
    try:
        if function_name == "check_availability":
            # Implementation here
            pass
        elif function_name == "book_appointment":
            # Implementation here
            pass
        # ... etc
    except Exception as e:
        logger.error(f"Error handling function call {function_name}: {e}")
        return {"error": str(e)}

# Add to receive_from_openai loop to handle function calls
elif event_type == "response.function_call_arguments.done":
    function_name = response.get("name")
    arguments = json.loads(response.get("arguments", "{}"))
    result = await handle_function_call(function_name, arguments)
    
    # Send result back to OpenAI
    await openai_ws.send_json({
        "type": "conversation.item.create",
        "item": {
            "type": "function_call_output",
            "call_id": response.get("call_id"),
            "output": json.dumps(result)
        }
    })
```

---

## 💰 **Cost Analysis**

### Google Calendar API Costs
- **FREE tier**: 1,000,000 requests/day
- **Typical usage**: 
  - Check availability: 2-3 API calls per inquiry
  - Book appointment: 1 API call
  - Get upcoming: 1 API call
- **Monthly estimate**: 10,000 calls = **$0.00** (well within free tier)

### Additional Costs
- **Storage**: Minimal (JSON config files)
- **Compute**: Negligible (simple JSON operations)
- **Total additional cost**: **~$0.00/month**

---

## 🚀 **Implementation Timeline**

| Phase | Tasks | Time | Difficulty |
|-------|-------|------|------------|
| **Phase 1** | Google Cloud setup, credentials | 1-2 hours | Easy |
| **Phase 2** | Create config files (services, hours) | 1 hour | Easy |
| **Phase 3** | Implement calendar_service.py | 2-3 hours | Medium |
| **Phase 4** | Implement knowledge_base.py | 2 hours | Easy |
| **Phase 5** | Implement function_tools.py | 1 hour | Easy |
| **Phase 6** | Update realtime.py with functions | 3-4 hours | Medium |
| **Phase 7** | Testing and debugging | 2-4 hours | Medium |
| **Total** | | **12-17 hours** | **Medium** |

---

## ✅ **Testing Checklist**

- [ ] Google Calendar authentication works
- [ ] Can read existing appointments
- [ ] Can create new appointments
- [ ] Can check availability correctly
- [ ] Services knowledge base loads
- [ ] Business hours logic works (open/closed)
- [ ] Holiday detection works
- [ ] AI can call functions successfully
- [ ] Function results are used in conversation
- [ ] Appointments appear in Google Calendar
- [ ] Email notifications sent (if configured)
- [ ] Timezone handling is correct
- [ ] Error handling works gracefully

---

## 📞 **Example Conversation Flow**

**Caller**: "Hi, I'd like to book a haircut for tomorrow."

**AI**: *Calls `check_business_hours` with tomorrow's date*
- Result: Open 9 AM - 6 PM

**AI**: *Calls `get_services` to find haircut service*
- Result: Haircut - 30 minutes - $45

**AI**: *Calls `check_availability` for tomorrow*
- Result: Available slots at 10 AM, 2 PM, 4 PM

**AI**: "Sure! We have availability tomorrow at 10 AM, 2 PM, or 4 PM. Which works best for you?"

**Caller**: "2 PM works great."

**AI**: "Perfect! Can I get your name and phone number?"

**Caller**: "John Smith, 555-1234"

**AI**: *Calls `book_appointment`*
- Creates calendar event
- Returns confirmation

**AI**: "All set! I've booked your haircut for tomorrow at 2 PM. You'll receive a confirmation email shortly. Is there anything else I can help with?"

---

## 🎓 **Best Practices**

1. **Always verify availability** before booking
2. **Collect customer info** (name, phone, email)
3. **Confirm details** before finalizing booking
4. **Handle errors gracefully** (calendar conflicts, API failures)
5. **Respect business hours** (don't book outside hours)
6. **Use timezone-aware datetimes** everywhere
7. **Log all bookings** for audit trail
8. **Send confirmations** via email/SMS
9. **Allow cancellations** with verification
10. **Keep knowledge base updated** regularly

---

## 🔒 **Security Considerations**

1. **Service Account Permissions**: Only grant calendar access, nothing else
2. **Credentials Storage**: Never commit credentials to Git
3. **Environment Variables**: Use `.env` for all sensitive data
4. **Verification**: Verify customer identity for cancellations
5. **Rate Limiting**: Implement rate limits to prevent abuse
6. **Input Validation**: Validate all user inputs (dates, names, etc.)
7. **Audit Logging**: Log all booking/cancellation attempts

---

## 📚 **Additional Resources**

- [Google Calendar API Documentation](https://developers.google.com/calendar/api/guides/overview)
- [OpenAI Function Calling Guide](https://platform.openai.com/docs/guides/function-calling)
- [Python Google Auth Guide](https://google-auth.readthedocs.io/)
- [Timezone Handling in Python](https://docs.python.org/3/library/datetime.html)

---

## 🎯 **Next Steps**

1. **Set up Google Cloud project** and enable Calendar API
2. **Create service account** and download credentials
3. **Create configuration files** (services.json, business_hours.json)
4. **Install required packages** (`pip install google-auth ...`)
5. **Implement calendar service** (copy code from Step 1)
6. **Implement knowledge base** (copy code from Step 2)
7. **Update realtime.py** with function calling
8. **Test thoroughly** with real phone calls
9. **Deploy to production**
10. **Monitor and iterate**

---

**Ready to implement? Let me know which part you'd like to start with, and I can help you build it step by step!**
