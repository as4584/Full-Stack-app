from fastapi import FastAPI, Depends, Form, Request
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging
import os

from ai_receptionist.config.settings import Settings, get_settings
from ai_receptionist.app.api.twilio import router as twilio_router
from ai_receptionist.app.api.admin import router as admin_router
from ai_receptionist.services.voice.endpoints import router as voice_router
from ai_receptionist.app.middleware import configure_logging, request_context_middleware

logger = logging.getLogger(__name__)

app = FastAPI(title="AI Receptionist", version="0.1.0")

# Get static directory path
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

# Mount static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/health")
def health(settings: Settings = Depends(get_settings)):
    return {"status": "ok", "env": settings.app_env}

# Serve the ChatGPT-style UI at root
@app.get("/")
def root():
    html_path = STATIC_DIR / "index.html"
    if html_path.exists():
        return FileResponse(str(html_path))
    return JSONResponse({"name": "ai-receptionist", "version": "0.1.0"})

# --- Business/Onboarding Endpoints ---
@app.post("/api/business")
@app.post("/business")
async def create_business_endpoint(request: Request):
    try:
        data = await request.json()
    except Exception as e:
        logger.error(f"Error parsing json: {e}")
        data = {}
    
    logger.info(f"Creating business: {data}")
    return {
        "id": "demo-biz-123",
        "name": data.get("name", "Demo Business"),
        "phone_number": data.get("phone_number") or os.getenv("TWILIO_PHONE_NUMBER", "+12298215986"),
        "timezone": data.get("timezone", "America/New_York"),
        "status": "active"
    }

@app.get("/api/business/me")
@app.get("/business/me")
async def get_my_business():
    return {
        "id": "demo-biz-123",
        "name": "Lex Personal",
        "phone_number": os.getenv("TWILIO_PHONE_NUMBER", "+12298215986"),
        "timezone": "America/New_York",
        "google_calendar_connected": True
    }

@app.get("/api/business/calls")
@app.get("/business/calls")
async def get_business_calls():
    return [
        {"from_number": "+15551234567", "status": "completed", "duration": 120, "created_at": "2026-01-19T10:00:00Z"},
        {"from_number": "+15559876543", "status": "in-progress", "duration": 45, "created_at": "2026-01-19T11:15:00Z"}
    ]

# Mount routers
# Prefix /twilio is used in Caddy to route to this container for webhooks
app.include_router(voice_router, prefix="/twilio")
app.include_router(twilio_router, prefix="/twilio")
app.include_router(admin_router)

# Observability
configure_logging()
app.middleware("http")(request_context_middleware)
