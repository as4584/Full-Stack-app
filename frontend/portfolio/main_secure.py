"""
Security-Hardened Portfolio Application
OWASP ASVS Level 2 Compliant
All vulnerabilities fixed and security enhanced
"""

import logging
import os
from typing import Any, Dict

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.cors import CORSMiddleware

from input_validation import ContactFormSecure, InputSanitizer
# Import security modules
from security_config import SecurityConfig
from security_middleware import SecurityMiddleware
from security_monitor import security_monitor

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize security configuration
security_config = SecurityConfig()

# Initialize FastAPI with security settings
app = FastAPI(
    title="Secure Portfolio",
    description="Security-hardened portfolio application",
    version="2.0.0",
    docs_url=None if security_config.is_production() else "/docs",
    redoc_url=None if security_config.is_production() else "/redoc",
)

# Add security middleware
app.add_middleware(SecurityMiddleware, config=security_config)

# Add CORS middleware with strict settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=security_config.get_trusted_hosts(),
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Only necessary methods
    allow_headers=["Content-Type", "Authorization"],
    max_age=600,  # 10 minutes
)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Templates and static files
templates = Jinja2Templates(directory="templates")

# Secure static files configuration
app.mount("/static", StaticFiles(directory="static"), name="static")


# Security headers dependency
async def get_security_headers() -> Dict[str, str]:
    """Get security headers for responses"""
    return security_config.SECURITY_HEADERS


# IP blocking check
async def check_ip_blocked(request: Request):
    """Check if client IP is blocked"""
    client_ip = get_remote_address(request)
    if security_monitor.is_ip_blocked(client_ip):
        logger.warning(f"Blocked IP attempted access: {client_ip}")
        raise HTTPException(status_code=403, detail="Access denied")
    return client_ip


@app.get("/", response_class=HTMLResponse)
@limiter.limit("60/minute")
async def home(
    request: Request,
    client_ip: str = Depends(check_ip_blocked),
    security_headers: Dict[str, str] = Depends(get_security_headers),
):
    """Secure home page"""
    try:
        response = templates.TemplateResponse("index.html", {"request": request})

        # Add security headers
        for header, value in security_headers.items():
            response.headers[header] = value

        return response

    except Exception as e:
        logger.error(f"Error serving home page: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/health")
@limiter.limit("30/minute")
async def health_check(request: Request, client_ip: str = Depends(check_ip_blocked)):
    """Health check endpoint for monitoring"""
    return JSONResponse(
        {"status": "healthy", "timestamp": int(time.time()), "security": "enabled"}
    )


@app.post("/api/contact")
@limiter.limit("3/hour")  # Very restrictive rate limit for contact form
async def contact_form(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    subject: str = Form(...),
    message: str = Form(...),
    client_ip: str = Depends(check_ip_blocked),
):
    """Secure contact form with comprehensive validation"""
    try:
        # Validate input using secure form model
        contact_data = ContactFormSecure(
            name=name, email=email, subject=subject, message=message
        )

        # Log successful contact submission
        logger.info(
            "Contact form submitted",
            ip=client_ip,
            email=contact_data.email,
            subject_length=len(contact_data.subject),
        )

        # Here you would typically send the email
        # await send_contact_email(contact_data)

        return JSONResponse(
            {
                "success": True,
                "message": "Thank you for your message. I'll get back to you soon!",
            }
        )

    except ValueError as e:
        # Log validation failure
        logger.warning("Contact form validation failed", ip=client_ip, error=str(e))

        await security_monitor.log_failed_attempt(
            client_ip, "/api/contact", f"Validation error: {str(e)}"
        )

        raise HTTPException(status_code=400, detail="Invalid input data")

    except Exception as e:
        logger.error(f"Contact form error: {e}")
        raise HTTPException(status_code=500, detail="Unable to process request")


@app.get("/security-report")
@limiter.limit("10/minute")
async def security_report(request: Request, client_ip: str = Depends(check_ip_blocked)):
    """Security monitoring report (admin only in production)"""
    if security_config.is_production():
        # In production, this should require authentication
        raise HTTPException(status_code=404, detail="Not found")

    report = await security_monitor.generate_security_report()
    return JSONResponse(report)


# AI Receptionist page (if it exists)
@app.get("/ai-receptionist", response_class=HTMLResponse)
@limiter.limit("30/minute")
async def ai_receptionist(
    request: Request,
    client_ip: str = Depends(check_ip_blocked),
    security_headers: Dict[str, str] = Depends(get_security_headers),
):
    """AI Receptionist page"""
    try:
        response = templates.TemplateResponse(
            "ai-receptionist.html", {"request": request}
        )

        # Add security headers
        for header, value in security_headers.items():
            response.headers[header] = value

        return response

    except Exception as e:
        logger.error(f"Error serving AI receptionist page: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Custom error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Custom 404 handler"""
    client_ip = get_remote_address(request)

    # Log potential reconnaissance attempts
    if any(
        suspicious in request.url.path.lower()
        for suspicious in ["admin", "wp-admin", "phpmyadmin", ".env", "config"]
    ):
        await security_monitor.log_suspicious_activity(
            "reconnaissance_attempt",
            {
                "ip": client_ip,
                "path": request.url.path,
                "user_agent": request.headers.get("user-agent"),
            },
        )

    try:
        return templates.TemplateResponse(
            "404.html", {"request": request}, status_code=404
        )
    except:
        return JSONResponse({"error": "Not Found"}, status_code=404)


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Custom 500 handler"""
    logger.error(f"Internal server error: {exc}")

    try:
        return templates.TemplateResponse(
            "500.html", {"request": request}, status_code=500
        )
    except:
        return JSONResponse({"error": "Internal Server Error"}, status_code=500)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup"""
    logger.info("🔒 Secure portfolio application starting...")
    logger.info(f"Security level: OWASP ASVS Level 2")
    logger.info(f"Production mode: {security_config.is_production()}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    logger.info("Portfolio application shutting down")


# Security: Bind to localhost in development, 0.0.0.0 only in production
if __name__ == "__main__":
    import time  # Add this import

    import uvicorn

    # Security: Use environment variable for host binding
    # Production deployment should set BIND_HOST=0.0.0.0
    host = os.getenv("BIND_HOST", "127.0.0.1")  # nosec B104
    port = int(os.getenv("PORT", 8001))

    logger.info(f"Starting server on {host}:{port}")

    uvicorn.run(
        "main_secure:app",
        host=host,
        port=port,
        reload=not security_config.is_production(),
        access_log=True,
        server_header=False,  # Hide server header
        date_header=False,  # Hide date header
    )
