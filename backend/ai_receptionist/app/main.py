from fastapi import FastAPI, Depends, Form, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging
import os
import asyncio
from datetime import datetime

from ai_receptionist.config.settings import Settings, get_settings
from ai_receptionist.core.database import get_db
from ai_receptionist.models.business import Business
from ai_receptionist.models.contact import Contact
from ai_receptionist.app.api.twilio import router as twilio_router
from ai_receptionist.app.api.admin import router as admin_router
from ai_receptionist.app.api.oauth import router as oauth_router
from ai_receptionist.app.api.auth import router as auth_router
from ai_receptionist.app.api.twilio_marketplace import router as marketplace_router
from ai_receptionist.app.api import magic
from ai_receptionist.services.voice.endpoints import router as voice_router
from ai_receptionist.app.middleware import configure_logging, request_context_middleware
from ai_receptionist.core.auth import get_current_user, TokenData 
from sqlalchemy.orm import Session
from sqlalchemy import text
import stripe
from fastapi import HTTPException

from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from ai_receptionist.core.limiter import limiter

logger = logging.getLogger(__name__)

app = FastAPI(title="AI Receptionist", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://dashboard.lexmakesit.com",
        "https://receptionist.lexmakesit.com",  # Production dashboard
        "https://auth.lexmakesit.com",  # Auth app for login flow
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get static directory path
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
stripe.api_key = STRIPE_SECRET_KEY

# Pricing Tier Mapping (Price ID -> Minutes Limit)
PRICE_ID_TO_LIMITS = {
    "price_1Sro5E25J162lH5djEsUZnrQ": {"minutes": 100, "name": "Starter"},
    "price_1Srnl925J162lH5dYtAcLBQ0": {"minutes": 425, "name": "Professional"},
    "price_1SroYB25J162lH5dh3QPAMAL": {"minutes": 900, "name": "Business"},
}

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

# Mount static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/health")
def health(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    return {"status": "ok", "env": settings.app_env, "db": db_status}


@app.get("/auth/health")
def auth_health(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    """
    Authentication system health check.
    Reports auth readiness without exposing secrets.
    """
    import bcrypt
    from ai_receptionist.models.user import User
    
    status = {
        "auth_system": "operational",
        "checks": {},
        "timestamp": datetime.now().isoformat()
    }
    
    # Check JWT secret configured
    has_jwt_secret = bool(settings.admin_private_key)
    status["checks"]["jwt_secret"] = {
        "configured": has_jwt_secret,
        "status": "ok" if has_jwt_secret else "error"
    }
    
    # Check password hashing works
    try:
        test_hash = bcrypt.hashpw(b"test", bcrypt.gensalt()).decode('utf-8')
        test_verify = bcrypt.checkpw(b"test", test_hash.encode('utf-8'))
        status["checks"]["password_hashing"] = {
            "available": True,
            "algorithm": "bcrypt",
            "status": "ok" if test_verify else "error"
        }
    except Exception as e:
        status["checks"]["password_hashing"] = {
            "available": False,
            "error": str(e)[:100],
            "status": "error"
        }
    
    # Check database and users table
    try:
        db.execute(text("SELECT 1"))
        user_count = db.query(User).count()
        status["checks"]["database"] = {
            "connected": True,
            "users_table": "accessible",
            "user_count": user_count,
            "status": "ok"
        }
    except Exception as e:
        status["checks"]["database"] = {
            "connected": False,
            "error": str(e)[:100],
            "status": "error"
        }
    
    # Determine overall status
    all_ok = all(
        check.get("status") == "ok" 
        for check in status["checks"].values()
    )
    
    status["auth_system"] = "operational" if all_ok else "degraded"
    
    return status


@app.get("/")
def root():
    return JSONResponse({"name": "ai-receptionist", "version": "0.1.0"})

@app.on_event("startup")
async def startup_event():
    """Start background tasks on application startup."""
    # CRITICAL: Validate production secrets BEFORE starting
    settings = get_settings()
    try:
        settings.validate_production_secrets()
    except RuntimeError as e:
        logger.error(f"STARTUP FAILED: {str(e)}")
        raise
    
    from ai_receptionist.workers.tasks import cleanup_phantom_calls
    
    async def run_periodic_cleanup():
        while True:
            try:
                await cleanup_phantom_calls()
            except Exception as e:
                logger.error(f"Cleanup task failed: {e}")
            await asyncio.sleep(1800) # Run every 30 mins
            
    asyncio.create_task(run_periodic_cleanup())
    logger.info("✅ Backend startup complete. All secrets validated.")

# --- Business/Onboarding Endpoints ---
@app.post("/api/business")
@app.post("/business")
async def create_business_endpoint(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
    except:
        data = {}
    
    logger.info(f"Creating business record: {data.get('name')}")
    
    # Create new business record
    new_biz = Business(
        name=data.get("name", "Unnamed Business"),
        industry=data.get("industry"),
        description=data.get("description"),
        phone_number=data.get("phone_number") or os.getenv("TWILIO_PHONE_NUMBER", "+12298215986"),
        timezone=data.get("timezone", "America/New_York"),
        greeting_style=data.get("greeting_style", "professional"),
        business_hours=data.get("business_hours"),
        common_services=data.get("common_services"),
        faqs=data.get("faqs", [])
    )
    
    db.add(new_biz)
    db.commit()
    db.refresh(new_biz)
    
    return {
        "id": str(new_biz.id),
        "name": new_biz.name,
        "phone_number": new_biz.phone_number,
        "timezone": new_biz.timezone,
        "status": "active"
    }

@app.patch("/api/business/{business_id}/status")
async def toggle_business_status(business_id: int, request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    # 1 for active, 0 for inactive
    new_status = 1 if data.get("is_active") else 0
    
    biz = db.query(Business).filter(Business.id == business_id).first()
    if not biz:
        raise HTTPException(status_code=404, detail="Business not found")
        
    biz.is_active = new_status
    db.commit()
    logger.info(f"Business {business_id} status updated to: {'Active' if new_status else 'Inactive'}")
    return {"status": "success", "is_active": bool(new_status)}

@app.post("/api/business/receptionist/toggle")
async def toggle_receptionist_endpoint(
    request: Request, 
    db: Session = Depends(get_db),
    user: TokenData = Depends(get_current_user)
):
    """Authoritative toggle for AI Receptionist pipeline."""
    data = await request.json()
    enabled = data.get("enabled", True)
    
    biz = db.query(Business).filter(Business.owner_email == user.email).first()
    if not biz and user.business_id:
        biz = db.query(Business).filter(Business.id == int(user.business_id)).first()

    if not biz:
        raise HTTPException(status_code=404, detail="Business not found")
        
    biz.receptionist_enabled = enabled
    db.commit()
    
    logger.info(f"AI Receptionist for {biz.name} set to: {'ENABLED' if enabled else 'DISABLED'}")
    return {"status": "success", "receptionist_enabled": enabled}


def sync_stripe_subscription(db: Session, biz: Business):
    """
    Syncs the local business record with Stripe subscription data.
    1. Links Stripe Customer ID by email if missing.
    2. Checks active subscription and updates limits.
    """
    if not STRIPE_SECRET_KEY:
        return

    try:
        # 1. Link Customer ID if missing
        if not biz.stripe_customer_id and biz.owner_email:
            customers = stripe.Customer.list(email=biz.owner_email, limit=1)
            if customers.data:
                biz.stripe_customer_id = customers.data[0].id
                db.commit()

        # 2. Get Subscription Details
        if biz.stripe_customer_id:
            subs = stripe.Subscription.list(customer=biz.stripe_customer_id, status='active', limit=1)
            if subs.data:
                sub = subs.data[0]
                price_id = sub['items']['data'][0]['price']['id']
                
                # Update limits if mapped
                if price_id in PRICE_ID_TO_LIMITS:
                    mapping = PRICE_ID_TO_LIMITS[price_id]
                    # Only update if changed prevents unnecessary commits? 
                    # Actually we should enforce it to ensure sync.
                    biz.minutes_limit = mapping["minutes"]
                    biz.subscription_status = "active"
                    # We could store plan name too if we added a column
                else:
                    # Unknown plan or manual custom plan
                    pass
                
                db.commit()
    except Exception as e:
        logger.error(f"Stripe sync failed for business {biz.id}: {str(e)}")


@app.get("/api/business/me")
@app.get("/business/me")
async def get_my_business(
    db: Session = Depends(get_db), 
    user: TokenData = Depends(get_current_user)
):
    import logging
    logger = logging.getLogger(__name__)
    
    # Find business by owner_email (PRIMARY)
    biz = db.query(Business).filter(Business.owner_email == user.email).first()
    
    logger.info(f"[BUSINESS_FETCH] user.email={user.email}, found_business={biz is not None}")
    if biz:
        logger.info(f"[BUSINESS_DATA] id={biz.id}, phone={biz.phone_number}, receptionist_enabled={biz.receptionist_enabled}")
         
    if not biz:
        logger.info(f"[BUSINESS_FETCH] No business found for user {user.email} - returning null")
        return None
    
    # --- SYNC STRIPE DATA ---
    sync_stripe_subscription(db, biz)
    
    from ai_receptionist.models.oauth import GoogleOAuthToken
    
    # Check if connected
    oauth_token = db.query(GoogleOAuthToken).filter(
        GoogleOAuthToken.tenant_id == str(biz.id),
        GoogleOAuthToken.is_connected == True
    ).first()
    
    # Determine Plan Name
    plan_name = "Custom"
    for details in PRICE_ID_TO_LIMITS.values():
        if details["minutes"] == biz.minutes_limit:
            plan_name = details["name"]
            break
    
    response_data = {
        "id": str(biz.id),
        "name": biz.name,
        "industry": biz.industry,
        "description": biz.description,
        "phone_number": biz.phone_number,
        "timezone": biz.timezone,
        "greeting_style": biz.greeting_style,
        "business_hours": biz.business_hours,
        "common_services": biz.common_services,
        "faqs": biz.faqs or [],
        "google_calendar_connected": oauth_token is not None,
        # Subscription Fields
        "subscription_plan": plan_name,
        "subscription_status": biz.subscription_status,
        "minutes_used": biz.minutes_used,
        "minutes_limit": biz.minutes_limit,
        "stripe_customer_id": biz.stripe_customer_id,
        "receptionist_enabled": bool(biz.receptionist_enabled),
        # Audit Fields
        "audit_status": biz.audit_status,
        "audit_report": biz.audit_report,
        "pending_changes": biz.audit_status == "pending"
    }
    
    logger.info(f"[BUSINESS_RESPONSE] Returning: phone={response_data['phone_number']}, receptionist_enabled={response_data['receptionist_enabled']}")
    
    return response_data


@app.post("/api/stripe/checkout")
async def create_checkout_session(
    request: Request,
    db: Session = Depends(get_db),
    user: TokenData = Depends(get_current_user)
):
    """Create a checkout session for the Starter plan."""
    if not STRIPE_SECRET_KEY:
         raise HTTPException(status_code=500, detail="Stripe not configured")

    biz = db.query(Business).filter(Business.owner_email == user.email).first()
    if not biz and user.business_id:
        biz = db.query(Business).filter(Business.id == int(user.business_id)).first()

    if not biz:
        raise HTTPException(status_code=404, detail="Business not found")
        
    # Ensure customer exists (reuse logic or consolidate later)
    if not biz.stripe_customer_id:
        try:
            customers = stripe.Customer.list(email=user.email, limit=1)
            if customers.data:
                biz.stripe_customer_id = customers.data[0].id
            else:
                customer = stripe.Customer.create(
                     email=user.email, 
                     name=biz.name,
                     metadata={"business_id": biz.id}
                )
                biz.stripe_customer_id = customer.id
            db.commit()
        except:
             raise HTTPException(status_code=500, detail="Billing error")

    try:
        # Default to Starter Plan
        price_id = "price_1Sro5E25J162lH5djEsUZnrQ"
        
        session = stripe.checkout.Session.create(
            customer=biz.stripe_customer_id,
            mode="subscription",
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1,
            }],
            success_url=f"{get_settings().dashboard_url}/app?success=sub_active",
            cancel_url=f"{get_settings().dashboard_url}/app/subscribe",
            metadata={"business_id": biz.id},
            allow_promotion_codes=True
        )
        return {"url": session.url}
    except Exception as e:
        logger.error(f"Checkout error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start checkout")


@app.post("/api/stripe/portal")
async def create_portal_session(
    request: Request,
    db: Session = Depends(get_db),
    user: TokenData = Depends(get_current_user)
):
    """Create a Stripe Billing Portal session for managing subscription"""
    if not STRIPE_SECRET_KEY:
         raise HTTPException(status_code=500, detail="Stripe not configured")

    biz = db.query(Business).filter(Business.owner_email == user.email).first()
    if not biz and user.business_id:
        biz = db.query(Business).filter(Business.id == int(user.business_id)).first()

    if not biz:
        raise HTTPException(status_code=404, detail="Business not found")

    if not biz.stripe_customer_id:
        # Try to find or create customer
        try:
            customers = stripe.Customer.list(email=user.email, limit=1)
            if customers.data:
                biz.stripe_customer_id = customers.data[0].id
            else:
                # Create a new customer
                customer = stripe.Customer.create(
                    email=user.email,
                    name=biz.name,
                    metadata={"business_id": biz.id}
                )
                biz.stripe_customer_id = customer.id
            db.commit()
        except Exception as e:
            logger.error(f"Failed to find/create Stripe customer: {str(e)}")
            raise HTTPException(status_code=500, detail="Billing system unavailable. Please contact support.")

    try:
        # Create portal session
        # Use the Referer header or default to dashboard settings
        return_url = request.headers.get("referer", "https://dashboard.lexmakesit.com/app/settings")
        
        session = stripe.billing_portal.Session.create(
            customer=biz.stripe_customer_id,
            return_url=return_url,
        )
        return {"url": session.url}
    except Exception as e:
        logger.error(f"Portal creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create portal session")


@app.put("/api/business/me")
@app.put("/business/me")
async def update_business_me(
    request: Request, 
    db: Session = Depends(get_db),
    user: TokenData = Depends(get_current_user)
):
    import logging
    logger = logging.getLogger(__name__)
    
    data = await request.json()
    logger.info(f"[SETTINGS_SAVE] User {user.email} updating business with data: {list(data.keys())}")
    
    biz = db.query(Business).filter(Business.owner_email == user.email).first()

    if not biz:
        logger.error(f"[SETTINGS_SAVE] No business found for user {user.email}")
        raise HTTPException(status_code=404, detail="Business not found")
    
    logger.info(f"[SETTINGS_SAVE] Found business ID {biz.id} for user {user.email}")
    
    # If Description or FAQs change, trigger the RAG 2.0 Auditor
    should_audit = False
    if "description" in data:
        biz.pending_description = data["description"]
        biz.description = data["description"] # Apply immediately for UX
        biz.audit_status = "pending"
        should_audit = True
        logger.info(f"[SETTINGS_SAVE] Description updated, triggering audit")
    
    if "faqs" in data:
        biz.pending_faqs = data["faqs"]
        biz.faqs = data["faqs"] # Apply immediately for UX
        biz.audit_status = "pending"
        should_audit = True
        logger.info(f"[SETTINGS_SAVE] FAQs updated, triggering audit")

    # Update non-critical fields directly
    if "name" in data: 
        biz.name = data["name"]
        logger.info(f"[SETTINGS_SAVE] Name updated to: {biz.name}")
    if "industry" in data: biz.industry = data["industry"]
    if "phone_number" in data:
        biz.phone_number = data["phone_number"]
        logger.info(f"[SETTINGS_SAVE] Phone number updated to: {biz.phone_number}")
    if "timezone" in data: biz.timezone = data["timezone"]
    if "greeting_style" in data: biz.greeting_style = data["greeting_style"]
    if "business_hours" in data: biz.business_hours = data["business_hours"]
    if "common_services" in data: biz.common_services = data["common_services"]
    
    # CRITICAL: Enforce receptionist_enabled requires phone_number
    if "receptionist_enabled" in data:
        if data["receptionist_enabled"] and not biz.phone_number:
            logger.warning(f"[SETTINGS_SAVE] Cannot enable receptionist without phone number")
            return JSONResponse(
                status_code=400,
                content={
                    "detail": "Cannot enable AI receptionist without a phone number",
                    "field": "phone_number"
                }
            )
        biz.receptionist_enabled = data["receptionist_enabled"]
        logger.info(f"[SETTINGS_SAVE] Receptionist enabled set to: {biz.receptionist_enabled}")
    
    try:
        db.commit()
        logger.info(f"[SETTINGS_SAVE] Successfully saved settings for business {biz.id}")
    except Exception as e:
        logger.error(f"[SETTINGS_SAVE] Database commit failed: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save settings: {str(e)}")

    if should_audit:
        # --- AUDITOR (DISABLED TO CONSERVE TOKENS) ---
        # Auditor uses gpt-4o-mini to simulate customer Q&A for validation.
        # Currently disabled to save OpenAI tokens. Enable via ENABLE_AUDITOR=true
        from ai_receptionist.config.settings import get_settings
        settings = get_settings()
        if settings.enable_auditor:
            from ai_receptionist.services.voice.auditor import run_audit_simulation
            import asyncio
            asyncio.create_task(run_audit_simulation(biz.id))
            return {"status": "audit_pending", "id": biz.id, "msg": "Changes saved. Stress-testing for accuracy..."}
        else:
            logger.info(f"Auditor disabled - skipping audit for business {biz.id}")
            return {"status": "success", "id": biz.id, "msg": "Changes saved. Auditor disabled."}
        # NOTE: Re-enable with ENABLE_AUDITOR=true in .env

    return {"status": "success", "id": biz.id}

@app.get("/api/business/calls")
@app.get("/business/calls")
async def get_business_calls(
    db: Session = Depends(get_db),
    user: TokenData = Depends(get_current_user)
):
    """Retrieve call logs for the user's business"""
    from ai_receptionist.models.call import Call
    
    logger.info(f"[CALLS] Looking up calls for user.email={user.email}, user.business_id={user.business_id}")
    
    # Find business
    biz = db.query(Business).filter(Business.owner_email == user.email).first()
    if not biz and user.business_id:
         biz = db.query(Business).filter(Business.id == int(user.business_id)).first()
         
    if not biz:
        logger.warning(f"[CALLS] No business found for user.email={user.email}")
        return []
    
    logger.info(f"[CALLS] Found business id={biz.id}, name={biz.name}")
        
    from ai_receptionist.models.call import Call
    from ai_receptionist.models.contact import Contact
    
    # Get calls with contacts joined if available
    calls_with_contacts = db.query(Call, Contact.name).outerjoin(
        Contact, 
        (Contact.phone_number == Call.from_number) & (Contact.business_id == Call.business_id)
    ).filter(Call.business_id == biz.id).order_by(Call.created_at.desc()).limit(50).all()
    
    logger.info(f"[CALLS] Found {len(calls_with_contacts)} calls for business_id={biz.id}")
    
    return [
        {
            "id": c.id,
            "call_sid": c.call_sid,
            "from_number": c.from_number,
            "caller_name": caller_name or "Unknown",
            "status": c.status,
            "duration": c.duration,
            "created_at": c.created_at.isoformat(),
            "appointment_booked": bool(c.appointment_booked),
            "intent": c.intent or "Inquiry",
            "transcript": c.transcript,
            "summary": c.summary
        }
        for c, caller_name in calls_with_contacts
    ]

# Debug routes
@app.post("/test-ping")
def test_ping():
    return {"msg": "pong"}

@app.post("/twilio/test-voice")
def test_voice(CallSid: str = Form(...)):
    return {"sid": CallSid}

# Mount routers
# Prioritize voice_router to ensure /twilio/voice is registered correctly
app.include_router(voice_router, prefix="/twilio")
app.include_router(twilio_router, prefix="/twilio")
app.include_router(magic.router, prefix="/api", tags=["magic"])
app.include_router(marketplace_router, prefix="/twilio/marketplace")
app.include_router(admin_router)
app.include_router(oauth_router)
app.include_router(auth_router)

# Observability: attach request id and tenant id to context and logs
configure_logging()
app.middleware("http")(request_context_middleware)

# --- Contact Management ---

@app.get("/api/contacts/search")
async def search_contact(
    phone: str,
    db: Session = Depends(get_db),
    user: TokenData = Depends(get_current_user)
):
    biz = db.query(Business).filter(Business.owner_email == user.email).first()
    if not biz and user.business_id:
        biz = db.query(Business).filter(Business.id == int(user.business_id)).first()

    if not biz:
        raise HTTPException(status_code=404, detail="Business not found")
        
    contact = db.query(Contact).filter(
        Contact.business_id == biz.id,
        Contact.phone_number == phone
    ).first()
    
    if not contact:
        return {"found": False}
        
    return {
        "found": True,
        "id": contact.id,
        "name": contact.name,
        "email": contact.email,
        "notes": contact.notes,
        "is_blocked": contact.is_blocked
    }

@app.post("/api/contacts")
async def upsert_contact(
    request: Request,
    db: Session = Depends(get_db),
    user: TokenData = Depends(get_current_user)
):
    data = await request.json()
    biz = db.query(Business).filter(Business.owner_email == user.email).first()
    if not biz and user.business_id:
        biz = db.query(Business).filter(Business.id == int(user.business_id)).first()

    if not biz:
        raise HTTPException(status_code=404, detail="Business not found")
        
    phone = data.get("phone_number")
    if not phone:
        raise HTTPException(status_code=400, detail="Phone number required")
        
    contact = db.query(Contact).filter(
        Contact.business_id == biz.id,
        Contact.phone_number == phone
    ).first()
    
    if not contact:
        contact = Contact(
            business_id=biz.id,
            phone_number=phone
        )
        db.add(contact)
        
    if "name" in data: contact.name = data["name"]
    if "email" in data: contact.email = data["email"]
    if "notes" in data: contact.notes = data["notes"]
    if "is_blocked" in data: contact.is_blocked = data["is_blocked"]
    
    db.commit()
    db.refresh(contact)
    return {"status": "success", "id": contact.id, "name": contact.name}
