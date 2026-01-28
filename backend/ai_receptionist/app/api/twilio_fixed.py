from __future__ import annotations

import time
import os
from typing import Any, Dict

from fastapi import APIRouter, Depends, Request, Response, status

from ai_receptionist.core.di import get_telephony_service, get_tenant_mapping
from ai_receptionist.services.telephony.telephony import TelephonyService

router = APIRouter()

@router.post("/webhook")
async def twilio_webhook(
    request: Request,
    telephony: TelephonyService = Depends(get_telephony_service),
    tenant_mapping: Dict[str, str] = Depends(get_tenant_mapping),
):
    # Read raw body for signature validation
    body_bytes = await request.body()
    if not telephony.validate_signature(request.headers, body_bytes, url=str(request.url)):
        return Response(status_code=status.HTTP_403_FORBIDDEN)

    # Parse payload
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

    return Response(status_code=status.HTTP_200_OK)

@router.get("/available-numbers")
async def get_available_numbers():
    """
    Return available Twilio phone numbers for the onboarding flow.
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    
    if not account_sid or not auth_token:
        # Return demo number if Twilio not configured
        return [{"phoneNumber": "+12298215986", "friendlyName": "AI Receptionist Demo (+1 229-821-5986)"}]
    
    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        incoming_numbers = client.incoming_phone_numbers.list(limit=20)
        
        if not incoming_numbers:
             return [{"phoneNumber": "+12298215986", "friendlyName": "AI Receptionist Demo (+1 229-821-5986)"}]

        return [
            {
                "phoneNumber": num.phone_number,
                "friendlyName": num.friendly_name or f"Line ({num.phone_number})"
            }
            for num in incoming_numbers
        ]
    except Exception as e:
        print(f"Twilio error: {e}")
        phone = os.getenv("TWILIO_PHONE_NUMBER", "+12298215986")
        return [{"phoneNumber": phone, "friendlyName": f"Configured Line ({phone})"}]

@router.get("/my-numbers")
async def get_my_numbers():
    phone = os.getenv("TWILIO_PHONE_NUMBER", "+12298215986")
    return [
        {
            "phoneNumber": phone,
            "friendlyName": "AI Receptionist Line",
            "status": "active"
        }
    ]
