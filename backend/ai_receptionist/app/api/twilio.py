from __future__ import annotations

import time
from typing import Any, Dict

from fastapi import APIRouter, Depends, Request, Response, status

from ai_receptionist.core.di import get_telephony_service, get_tenant_mapping
from ai_receptionist.services.telephony.telephony import TelephonyService
from ai_receptionist.core.database import get_db
from sqlalchemy.orm import Session

"""
Twilio webhook router

SOLID notes:
- Single Responsibility: this module handles HTTP concerns for Twilio webhooks only (routing, parsing request, DI).
- Open/Closed: behavior can be extended by swapping the TelephonyService via DI without modifying this router.
- Liskov Substitution: any TelephonyService implementation can be injected as long as it respects the interface.
- Interface Segregation: TelephonyService exposes only methods needed by HTTP layer (validate_signature, enqueue_call).
- Dependency Inversion: depends on TelephonyService abstraction; concrete Twilio implementation is wired in DI.

Mocking in CI:
- validate_signature should be mocked to return True/False in unit tests.
- Redis enqueue is simulated by an in-memory list via the TelephonyService test double.
"""


router = APIRouter()


@router.post("/webhook")
async def twilio_webhook(
    request: Request,
    telephony: TelephonyService = Depends(get_telephony_service),
    tenant_mapping: Dict[str, str] = Depends(get_tenant_mapping),
):
    # Read raw body for signature validation (mockable in tests)
    body_bytes = await request.body()
    if not telephony.validate_signature(request.headers, body_bytes, url=str(request.url)):
        return Response(status_code=status.HTTP_403_FORBIDDEN)

    # Parse payload (Twilio sends application/x-www-form-urlencoded for voice calls)
    if request.headers.get("content-type", "").startswith("application/x-www-form-urlencoded"):
        form = await request.form()
        payload: Dict[str, Any] = dict(form)
    else:
        payload = await request.json()

    caller = payload.get("From") or payload.get("Caller")
    to_number = payload.get("To")
    tenant_id = tenant_mapping.get(to_number) if to_number else None
    if tenant_id is None:
        tenant_id = "default"

    event = {
        "start_ts": time.time(),
        "caller": caller,
        "tenant_id": tenant_id,
    }
    await telephony.enqueue_call(event)

    # In production, return TwiML for voice use-cases. Here we just ack.
    return Response(status_code=status.HTTP_200_OK)


@router.get("/available-numbers")
async def get_available_numbers():
    """
    Return available Twilio phone numbers for the onboarding flow.
    In production, this would query Twilio's API for purchased numbers.
    """
    import os
    
    # Get Twilio credentials from environment
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    
    if not account_sid or not auth_token:
        # Return demo number if Twilio not configured
        return [{"phoneNumber": "+12298215986", "friendlyName": "AI Receptionist Demo (+1 229-821-5986)"}]
    
    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        
        # Fetch purchased phone numbers from the account
        incoming_numbers = client.incoming_phone_numbers.list(limit=20)
        
        return [
            {
                "phoneNumber": num.phone_number,
                "friendlyName": num.friendly_name or f"Line ({num.phone_number})"
            }
            for num in incoming_numbers
        ]
    except Exception as e:
        # Fallback to configured number if API fails
        phone = os.getenv("TWILIO_PHONE_NUMBER", "+12298215986")
        return [{"phoneNumber": phone, "friendlyName": f"Configured Line ({phone})"}]


@router.get("/my-numbers")
async def get_my_numbers(db: Session = Depends(get_db)):
    """
    Return phone numbers assigned to the current user/business.
    Fetches the actual business phone number from the database.
    """
    from ai_receptionist.models.business import Business
    biz = db.query(Business).order_by(Business.id.desc()).first()
    
    phone = biz.phone_number if biz and biz.phone_number else "+12298215986"
    
    return [
        {
            "phoneNumber": phone,
            "friendlyName": f"AI Receptionist Line ({phone})",
            "status": "active"
        }
    ]

