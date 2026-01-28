from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import os
from typing import List, Optional

from ai_receptionist.core.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()

class PhoneNumber(BaseModel):
    phoneNumber: str
    friendlyName: str
    lata: Optional[str] = None
    rateCenter: Optional[str] = None
    region: Optional[str] = None
    locality: Optional[str] = None

class BuyNumberRequest(BaseModel):
    phoneNumber: str
    businessId: int

class ReleaseNumberRequest(BaseModel):
    businessId: int

@router.post("/release-number")
async def release_number(
    request: ReleaseNumberRequest,
    db: Session = Depends(get_db)
):
    """
    Release a Twilio phone number and clear it from the business.
    """
    from ai_receptionist.models.business import Business
    
    business = db.query(Business).filter(Business.id == request.businessId).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    if not business.phone_number_sid:
        # Already cleared or never purchased
        business.phone_number = None
        business.phone_number_sid = None
        business.phone_number_status = "cancelled"
        db.commit()
        return {"status": "success", "message": "No real number to release, record cleared."}

    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    
    if not account_sid or not auth_token:
        raise HTTPException(status_code=500, detail="Twilio credentials not configured")

    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        
        # Release from Twilio if not mock
        if not business.phone_number_sid.startswith("PN_MOCK_"):
            try:
                client.incoming_phone_numbers(business.phone_number_sid).delete()
            except Exception as e:
                print(f"Twilio release error: {e}")
                # Proceed anyway to clear local record
        
        # Clear business record
        old_number = business.phone_number
        business.phone_number = None
        business.phone_number_sid = None
        business.phone_number_status = "cancelled"
        db.commit()

        return {
            "status": "success",
            "message": f"Released number {old_number}",
            "phoneNumber": old_number
        }
    except Exception as e:
        print(f"Local release error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search-numbers", response_model=List[PhoneNumber])
async def search_numbers(area_code: Optional[str] = None, region: Optional[str] = "US"):
    """
    Search for available Twilio phone numbers to buy.
    Supports Area Code (3 digits) or Zip Code (5 digits).
    Falls back to Mock Data if Twilio credentials are not configured.
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    
    # MAGIC MODE: If credentials missing OR specific test input
    use_mock = not account_sid or not auth_token or area_code == "000"

    if use_mock:
        # Generate varied mock results based on input
        results = []
        base_num = "555"
        locality = "Test City"
        
        if area_code:
            if len(area_code) == 3:
                base_num = area_code
                locality = f"Area {area_code}"
            elif len(area_code) == 5:
                base_num = area_code[:3]
                locality = f"Zip {area_code}"
        
        for i in range(5):
            results.append(PhoneNumber(
                phoneNumber=f"+1{base_num}555010{i}",
                friendlyName=f"({base_num}) 555-010{i}",
                locality=locality,
                region=region
            ))
        return results

    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)

        # Search parameters
        search_params = {"limit": 10}
        
        if area_code:
            # Smart detection: 5 digits = Postal Code, 3 digits = Area Code
            if len(area_code) == 5 and area_code.isdigit():
                search_params["in_postal_code"] = area_code
            else:
                search_params["area_code"] = area_code
        
        print(f"DEBUG: Searching Twilio with params: {search_params}")
        available = client.available_phone_numbers('US').local.list(**search_params)
        print(f"DEBUG: Found {len(available)} numbers")

        results = []
        for num in available:
            results.append(PhoneNumber(
                phoneNumber=num.phone_number,
                friendlyName=num.friendly_name,
                lata=num.lata,
                rateCenter=num.rate_center,
                region=num.region,
                locality=num.locality
            ))
        
        # If no real numbers found, log warning
        if not results:
            print("WARNING: No real Twilio numbers found for these criteria.")
        
        return results

    except Exception as e:
        print(f"Twilio search error: {e}")
        # FALLBACK: If real Twilio fails, return mock data so user can proceed
        results = []
        base_num = "555"
        locality = "Fallback City"
        
        if area_code:
             if len(area_code) >= 3:
                 base_num = area_code[:3]
        
        for i in range(5):
            results.append(PhoneNumber(
                phoneNumber=f"+1{base_num}555010{i}",
                friendlyName=f"({base_num}) 555-010{i}",
                locality=locality,
                region=region
            ))
        return results

@router.post("/buy-number")
async def buy_number(
    request: BuyNumberRequest,
    db: Session = Depends(get_db)
):
    """
    Purchase a Twilio phone number and link it to a business.
    Fee: $2.00
    """
    from ai_receptionist.models.business import Business
    
    business = db.query(Business).filter(Business.id == request.businessId).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")

    if not account_sid or not auth_token:
         raise HTTPException(status_code=500, detail="Twilio credentials not configured")

    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)

        # MAGIC MODE: Bypass real purchase for local/test numbers
        if request.phoneNumber.startswith("+1000") or request.phoneNumber == "+15550100":
             business.phone_number = request.phoneNumber
             business.phone_number_sid = "PN_MOCK_" + request.phoneNumber
             business.phone_number_status = "active"
             db.commit()
             return {"status": "success", "phoneNumber": request.phoneNumber, "fee": "2.00"}

        # REAL PURCHASE
        # Charge Stripe $2.00
        stripe_key = os.getenv("STRIPE_SECRET_KEY")
        if stripe_key and business.stripe_customer_id:
            import stripe
            stripe.api_key = stripe_key
            try:
                # 1. Create Invoice Item
                stripe.InvoiceItem.create(
                    customer=business.stripe_customer_id,
                    amount=200, # $2.00 in cents
                    currency="usd",
                    description=f"Phone Number Purchase: {request.phoneNumber}"
                )
                # 2. Create Invoice to charge immediately
                invoice = stripe.Invoice.create(
                    customer=business.stripe_customer_id,
                    auto_advance=True # Auto-finalize and charge
                )
                invoice.finalize_invoice() 
                # Note: Payment happens asynchronously but usually instant for saved cards. 
                # We assume success if invoice created.
                print(f"DEBUG: Created invoice {invoice.id} for $2.00 charge.")
            except Exception as se:
                print(f"Stripe Charge Error: {se}")
                raise HTTPException(status_code=400, detail=f"Billing failed: {str(se)}")
        
        print(f"DEBUG: Purchasing {request.phoneNumber} from Twilio...")
        
        purchased = client.incoming_phone_numbers.create(
            phone_number=request.phoneNumber,
            voice_url=f"{os.getenv('PUBLIC_HOST', 'https://receptionist.lexmakesit.com')}/twilio/voice"
        )

        # Update business record
        business.phone_number = purchased.phone_number
        business.phone_number_sid = purchased.sid
        business.phone_number_status = "active"
        db.commit()

        return {
            "status": "success",
            "phoneNumber": purchased.phone_number,
            "sid": purchased.sid,
            "fee": "2.00"
        }

    except Exception as e:
        print(f"Twilio purchase error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
