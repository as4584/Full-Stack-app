import mimetypes
mimetypes.init()
mimetypes.add_type('image/webp', '.webp')
mimetypes.types_map['.webp'] = 'image/webp'

import json
import logging
import logging.handlers
import os
import secrets
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import List, Optional

import aiosmtplib
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, field_validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# Load environment variables securely
load_dotenv()

# Create logs directory
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)


class StructuredFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""

    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields from the record
        for key, value in record.__dict__.items():
            if key not in (
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "message",
                "exc_info",
                "exc_text",
                "stack_info",
            ):
                log_entry[key] = value

        return json.dumps(log_entry, default=str)


# Configure structured logging
def setup_logging():
    """Setup structured logging with file rotation and console output"""

    # Remove default handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Create formatters
    structured_formatter = StructuredFormatter()
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler for all environments
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)

    # Root logger setup
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

    # File handlers only if we can write to the directory
    try:
        log_dir.mkdir(mode=0o755, exist_ok=True)

        # Test if we can write to the directory
        test_file = log_dir / "test.tmp"
        test_file.touch()
        test_file.unlink()

        # File handler for structured logs
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / "application.json",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,  # 10MB
        )
        file_handler.setFormatter(structured_formatter)

        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            log_dir / "errors.json", maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
        )
        error_handler.setFormatter(structured_formatter)
        error_handler.setLevel(logging.ERROR)

        root_logger.addHandler(file_handler)
        root_logger.addHandler(error_handler)

        logging.info(f"File logging enabled in {log_dir}")

    except (PermissionError, OSError) as e:
        logging.warning(
            f"File logging disabled due to permissions: {e}. Using console only."
        )
        # Continue with just console logging

    # Set third-party library log levels
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)


# Security configurations from environment
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("SESSION_EXPIRE_MINUTES", "30"))
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
TRUSTED_HOSTS = os.getenv(
    "TRUSTED_HOSTS",
    "localhost,127.0.0.1,104.236.100.245,104.236.100.245:8000,testserver,lexmakesit.com,www.lexmakesit.com",
).split(",")
PRODUCTION = os.getenv("PRODUCTION", "false").lower() == "true"

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Rate limiting configuration
RATE_LIMIT_PER_MINUTE = os.getenv("RATE_LIMIT_PER_MINUTE", "60") or "60"
RATE_LIMIT_BURST = int(os.getenv("RATE_LIMIT_BURST") or "10")

# Email configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT") or "587")
SMTP_USER = os.getenv("SMTP_USER") or ""
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD") or ""
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USER)
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Portfolio Contact")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
CONTACT_RECIPIENT_EMAIL = os.getenv("CONTACT_RECIPIENT_EMAIL", "as42519256@gmail.com")

# Global application state
db_pool = None


async def get_db_pool():
    """Get database connection pool - disabled for database-independent operation"""
    return None


async def close_db_pool():
    """Close database connection pool - safe no-op for database-independent operation"""
    # No database operations needed in database-independent mode
    logger.info("Database operations disabled - no cleanup required")


# Application lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up application...")
    try:
        # Database-independent startup - no database operations needed
        logger.info(
            "Application startup complete - running in database-independent mode"
        )
    except Exception as e:
        logger.error(f"Failed to startup application: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down application...")
    await close_db_pool()
    logger.info("Application shutdown complete")


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Rate limiting with configurable thresholds for security
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{RATE_LIMIT_PER_MINUTE}/minute"],
    storage_uri=os.getenv("RATE_LIMIT_STORAGE", "memory://"),
)

# Initialize FastAPI app with security defaults and lifespan
app = FastAPI(
    title="LexMakesIt AI Receptionist",
    description="Smarter 24/7 AI Phone system for small businesses. Handles inquiries, books appointments, and captures leads.",
    version="1.3.0",  # Updated for Google OAuth compliance
    docs_url=None if PRODUCTION else "/api/docs",  # Hide docs in production
    redoc_url=None if PRODUCTION else "/api/redoc",
    openapi_url=None if PRODUCTION else "/openapi.json",
    lifespan=lifespan,
)

# Apple Pay Domain Verification Route
@app.get("/.well-known/apple-developer-merchantid-domain-association")
async def apple_pay_verification():
    """Serve Apple Pay domain verification file"""
    file_path = os.path.join("static", ".well-known", "apple-developer-merchantid-domain-association")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return JSONResponse(status_code=404, content={"detail": "Verification file not found. Please upload it to static/.well-known/"})

# Apply rate limiting with exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Configuration - Restrict to allowed origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Restrict to needed methods only
    allow_headers=["Content-Type", "Authorization"],
    max_age=3600,
)

# Trusted Host Middleware - Use environment configuration
app.add_middleware(
    TrustedHostMiddleware, allowed_hosts=TRUSTED_HOSTS if PRODUCTION else ["*"]
)


# ============================================================================
# OWASP ASVS LEVEL 1 SECURITY HEADERS MIDDLEWARE
# ============================================================================
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """
    Enforce comprehensive security headers per OWASP recommendations:
    - CSP: Prevent XSS and code injection
    - HSTS: Force HTTPS on all future visits
    - X-Frame-Options: Prevent clickjacking
    - X-Content-Type-Options: Prevent MIME sniffing
    - Referrer-Policy: Control referrer information leakage
    - Permissions-Policy: Disable unnecessary browser features
    """
    response = await call_next(request)

    # Content Security Policy (strict, allow only trusted sources)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com data:; "
        "img-src 'self' data: https:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )

    # HTTP Strict Transport Security (force HTTPS)
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains; preload"
    )

    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # Clickjacking protection
    response.headers["X-Frame-Options"] = "DENY"

    # XSS filter (legacy browsers)
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # Referrer policy (limit information leakage)
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Permissions policy (disable unnecessary features)
    response.headers["Permissions-Policy"] = (
        "geolocation=(), microphone=(), camera=(), "
        "payment=(), usb=(), magnetometer=(), gyroscope=()"
    )

    # Remove server identification header (use del instead of pop for MutableHeaders)
    if "server" in response.headers:
        del response.headers["server"]

    return response


# Request size limiter middleware (prevent DoS via large payloads)
@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    """Prevent DoS attacks via oversized request bodies"""
    max_size = 1024 * 1024  # 1 MB limit
    content_length = request.headers.get("content-length")

    if content_length and int(content_length) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Request body too large",
        )

    return await call_next(request)


# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ============================================================================
# PYDANTIC MODELS WITH INPUT VALIDATION & SANITIZATION (OWASP)
# ============================================================================


class ContactForm(BaseModel):
    """
    Secure contact form with comprehensive input validation:
    - Length limits to prevent buffer overflow
    - Character whitelist to prevent injection
    - Email validation via EmailStr
    - HTML/script tag stripping
    """

    name: str
    email: EmailStr
    subject: Optional[str] = "lexmakesit email"
    message: str

    @field_validator("name", "subject")
    @classmethod
    def validate_text_field(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize text fields: strip, length check, no HTML"""
        if v is None:
            return v
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")

        v = v.strip()

        # Length validation
        if len(v) < 2:
            raise ValueError("Field must be at least 2 characters")
        if len(v) > 100:
            raise ValueError("Field cannot exceed 100 characters")

        # Prevent HTML/script injection
        dangerous_chars = ["<", ">", "{", "}", "`", "$"]
        if any(char in v for char in dangerous_chars):
            raise ValueError("Invalid characters detected")

        return v

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Sanitize message field with strict length limits"""
        if not v or not v.strip():
            raise ValueError("Message cannot be empty")

        v = v.strip()

        if len(v) < 10:
            raise ValueError("Message must be at least 10 characters")
        if len(v) > 1000:
            raise ValueError("Message cannot exceed 1000 characters")

        # Prevent script injection
        if "<script" in v.lower() or "javascript:" in v.lower():
            raise ValueError("Invalid content detected")

        return v


class Project(BaseModel):
    id: int
    title: str
    description: str
    technologies: List[str]
    image_url: str
    case_study_url: Optional[str] = None
    impact: str


class Testimonial(BaseModel):
    id: int
    client_name: str
    company: str
    position: str
    text: str
    rating: int
    avatar_url: Optional[str] = None


# Sample Data - Implementing Social Proof & Authority (Cialdini)
PROJECTS = [
    Project(
        id=1,
        title="LexMakesIt AI Receptionist",
        description=(
            "Saves time and missed calls. 24/7 AI phone system that "
            "handles customer inquiries, schedules appointments, and provides information so "
            "business owners can focus on their core operations, not their phones."
        ),
        technologies=["FastAPI", "Twilio", "OpenAI GPT", "RAG", "Redis", "PostgreSQL"],
        image_url="/static/images/TAWOG.jpg",
        case_study_url="/projects/ai-receptionist",
        impact=(
            "Started with a simple question: What if small businesses "
            "never missed a call? Now saves businesses 20+ hours/month and "
            "reduces operational costs."
        ),
    ),
    Project(
        id=2,
        title="DonXera Website Demo",
        description=(
            "Built for my cousin's resell store in Royal Palm Beach, Florida. "
            "Real-time inventory tracking synced with SAP ARP and Lightspeed POS. "
            "Handles 140+ SKUs with smart brand search and automated reconciliation "
            "across multiple locations at 10131 Southern Blvd, Royal Palm Beach, FL 33411."
        ),
        technologies=[
            "Python",
            "Flask",
            "SAP ARP",
            "Google Sheets API",
            "Lightspeed API",
            "PostgreSQL",
            "Docker",
        ],
        image_url="/static/images/DonXlogo.jpg",
        case_study_url="http://don-era.lexmakesit.com",
        impact=(
            "Turned a 4-hour weekly reconciliation task into a real-time automated system. "
            "No more manual counting. Instant stock visibility across all locations."
        ),
    ),
]

TESTIMONIALS = [
    Testimonial(
        id=1,
        client_name="Maria Torres",
        company="Bella Vista Salon",
        position="Owner",
        text=(
            "Alex built me an AI receptionist that actually works. "
            "I can focus on my clients instead of answering the phone all day. "
            "It's like having an extra pair of hands."
        ),
        rating=5,
        avatar_url="/static/images/client1.jpg",
    ),
    Testimonial(
        id=2,
        client_name="David Kim",
        company="Kim's HVAC Services",
        position="Operations Manager",
        text=(
            "He explained everything in plain English — no tech jargon. "
            "The AI handles our after-hours calls perfectly. Simple solution, big impact."
        ),
        rating=5,
        avatar_url="/static/images/client2.jpg",
    ),
    Testimonial(
        id=3,
        client_name="Alex Martinez",
        company="DonXEra Streetwear",
        position="Store Manager",
        text=(
            "We went from chaotic spreadsheets to a clean system that just works. "
            "Alexander walked me through every step. Real talk: this saved us hours every week."
        ),
        rating=5,
        avatar_url="/static/images/client3.jpg",
    ),
]

TOOLS_EXPERTISE = [
    {"name": "FastAPI", "category": "Framework"},
    {"name": "Python", "category": "Language"},
    {"name": "Flask", "category": "Framework"},
    {"name": "SAP ARP", "category": "Enterprise"},
    {"name": "Lua + Roblox", "category": "Game Dev"},
    {"name": "PostgreSQL", "category": "Database"},
    {"name": "Redis", "category": "Cache"},
    {"name": "RAG/Vector DB", "category": "AI/ML"},
    {"name": "OpenAI API", "category": "AI/ML"},
    {"name": "Twilio API", "category": "Communications"},
    {"name": "Google Sheets API", "category": "Integration"},
    {"name": "Lightspeed API", "category": "POS Integration"},
    {"name": "Docker", "category": "DevOps"},
    {"name": "HTML/CSS", "category": "Frontend"},
    {"name": "Bootstrap 5", "category": "UI Framework"},
]

CERTIFICATIONS = [
    "FastAPI Production Best Practices",
    "Twilio Voice & SMS Integration Specialist",
    "SAP ARP Enterprise Inventory Automation",
    "OpenAI API & RAG Systems Architecture",
    "Python Full-Stack Development",
]


# Utility Functions
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# ============================================================================
# EMAIL NOTIFICATION FUNCTION
# ============================================================================


async def send_contact_email(name: str, email: str, subject: str, message: str) -> bool:
    """
    Send email notification using SendGrid Web API (bypasses port 587 block)
    Returns True if email sent successfully, False otherwise
    """
    if not SENDGRID_API_KEY:
        logger.warning("SENDGRID_API_KEY not configured - email notification skipped")
        return False

    import httpx

    try:
        url = "https://api.sendgrid.com/v3/mail/send"
        headers = {
            "Authorization": f"Bearer {SENDGRID_API_KEY}",
            "Content-Type": "application/json",
        }

        # Use the verified sender email from config
        from_email = SMTP_FROM_EMAIL or SMTP_USER

        payload = {
            "personalizations": [
                {
                    "to": [{"email": CONTACT_RECIPIENT_EMAIL}],
                    "reply_to": {"email": email, "name": name},
                    "subject": f"Portfolio Contact: {subject}",
                }
            ],
            "from": {"email": from_email, "name": SMTP_FROM_NAME},
            "content": [
                {
                    "type": "text/html",
                    "value": f"""
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;
                                border: 1px solid #ddd; border-radius: 8px;">
                        <h2 style="color: #8b5cf6; border-bottom: 2px solid #8b5cf6;
                                   padding-bottom: 10px;">
                            🔔 New Portfolio Contact Form Submission
                        </h2>

                        <div style="background-color: #f9f9f9; padding: 15px;
                                    border-radius: 5px; margin: 20px 0;">
                            <p style="margin: 5px 0;"><strong>From:</strong> {name}</p>
                            <p style="margin: 5px 0;">
                                <strong>Email:</strong> <a href="mailto:{email}">{email}</a>
                            </p>
                            <p style="margin: 5px 0;"><strong>Subject:</strong> {subject}</p>
                            <p style="margin: 5px 0;">
                                <strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
                            </p>
                        </div>

                        <div style="background-color: #fff; padding: 15px;
                                    border-left: 4px solid #8b5cf6; margin: 20px 0;">
                            <h3 style="margin-top: 0; color: #555;">Message:</h3>
                            <p style="white-space: pre-wrap;">{message}</p>
                        </div>

                        <div style="margin-top: 20px; padding-top: 15px;
                                    border-top: 1px solid #ddd; font-size: 12px; color: #888;">
                            <p>Reply directly to the email metadata to respond to {name}.</p>
                            <p>This notification was sent from your portfolio contact form via SendGrid.</p>
                        </div>
                    </div>
                </body>
                </html>
                """,
                }
            ],
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=10)

        if response.status_code >= 200 and response.status_code < 300:
            logger.info(f"Contact email sent successfully via SendGrid from {name} ({email})")
            return True
        else:
            logger.error(
                f"SendGrid API error: {response.status_code} - {response.text}"
            )
            return False

    except Exception as e:
        logger.error(f"Unexpected error sending contact email via SendGrid: {str(e)}")
        return False


# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Main landing page implementing Cialdini's principles:
    - Liking: Professional photo and relatable intro
    - Authority: Certifications and expertise
    - Social Proof: Client testimonials
    - Reciprocity: Free resources
    - Scarcity: Limited availability
    """
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request,
            "projects": PROJECTS,
            "testimonials": TESTIMONIALS,
            "tools": TOOLS_EXPERTISE,
            "certifications": CERTIFICATIONS,
            "availability": "Currently accepting 2 new clients for Q4 2025",
        },
    )


@app.get("/pricing", response_class=HTMLResponse)
async def pricing(request: Request):
    """
    Dedicated pricing page for AI Receptionist plans
    """
    return templates.TemplateResponse(
        request=request,
        name="pricing.html",
        context={"request": request},
    )


@app.get("/privacy-policy", response_class=HTMLResponse)
async def privacy_policy(request: Request):
    """
    Privacy policy page for Google OAuth compliance
    """
    return templates.TemplateResponse(
        request=request,
        name="privacy-policy.html",
        context={"request": request},
    )


@app.get("/terms", response_class=HTMLResponse)
async def terms_of_service(request: Request):
    """
    Terms of Service page for Google OAuth compliance
    """
    return templates.TemplateResponse(
        request=request,
        name="terms.html",
        context={"request": request},
    )


@app.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    """
    About page
    """
    return templates.TemplateResponse(
        request=request,
        name="about.html",
        context={"request": request},
    )


@app.get("/api/projects")
@limiter.limit("10/minute")
async def get_projects(request: Request):
    """Get all projects - Social Proof"""
    return {"projects": [p.model_dump() for p in PROJECTS]}


@app.get("/api/projects/{project_id}")
@limiter.limit("20/minute")
async def get_project(request: Request, project_id: int):
    """Get specific project details"""
    project = next((p for p in PROJECTS if p.id == project_id), None)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project.dict()


@app.get("/api/testimonials")
@limiter.limit("10/minute")
async def get_testimonials(request: Request):
    """Get client testimonials - Social Proof & Authority"""
    return {"testimonials": [t.model_dump() for t in TESTIMONIALS]}


@app.post("/api/contact")
@limiter.limit("5/hour")
async def contact(request: Request, form_data: ContactForm):
    """
    Handle contact form submissions with email notification
    Security: Input validation, rate limiting, sanitization
    """
    try:
        # Log contact submission (sanitized)
        logger.info(f"Contact form submitted by {form_data.name[:20]}...")

        # Use default subject if not provided
        email_subject = form_data.subject or "lexmakesit email"

        # Send email notification
        email_sent = await send_contact_email(
            name=form_data.name,
            email=form_data.email,
            subject=email_subject,
            message=form_data.message,
        )

        # Log contact form submission (in production: save to database)
        contact_id = secrets.token_hex(8)
        logger.info(
            f"Contact form submitted - ID: {contact_id}, "
            f"Name: {form_data.name}, Email: {form_data.email}, "
            f"Email sent: {email_sent}"
        )

        # Success response
        response_message = "Thank you! I'll respond within 24 hours."
        if not email_sent:
            logger.warning("Contact form submitted but email notification failed")
            # Still return success to user (don't expose email config issues)

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={"message": response_message, "contact_id": contact_id},
        )

    except ValueError as e:
        # Pydantic validation errors
        logger.warning(f"Contact form validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except Exception as e:
        # Unexpected errors
        logger.error(f"Contact form error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to process your request. Please try again.",
        )


@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    """About page - Authority & Liking"""
    return templates.TemplateResponse(
        request=request,
        name="about.html",
        context={
            "request": request,
            "certifications": CERTIFICATIONS,
            "tools": TOOLS_EXPERTISE,
        },
    )


@app.get("/portfolio", response_class=HTMLResponse)
async def portfolio(request: Request):
    """Portfolio page - Social Proof"""
    return templates.TemplateResponse(
        request=request,
        name="portfolio.html",
        context={"request": request, "projects": PROJECTS},
    )


@app.get("/blog", response_class=HTMLResponse)
async def blog(request: Request):
    """Blog page - Reciprocity (free valuable content)"""
    return templates.TemplateResponse(
        request=request, name="blog.html", context={"request": request}
    )


@app.get("/contact", response_class=HTMLResponse)
async def contact_page(request: Request):
    """Contact page"""
    return templates.TemplateResponse(
        request=request, name="contact.html", context={"request": request}
    )


@app.get("/projects/ai-receptionist", response_class=HTMLResponse)
async def ai_receptionist_project(request: Request):
    """AI Receptionist project case study with ROI calculations"""
    return templates.TemplateResponse(
        request=request, name="ai-receptionist.html", context={"request": request}
    )


@app.get("/api/health")
@limiter.limit("30/minute")
async def health_check(request: Request):
    """Health check endpoint with rate limiting"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "deployment": "LexMakesIt-v1.3.0",
        "date": "2026-01-21",
        # version info for deployment verification
    }


# ============================================================================
# STRIPE PAYMENT INTEGRATION
# ============================================================================

# Stripe configuration
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")

# Pricing tier configuration
PRICING_TIERS = {
    "starter": {"name": "Starter", "price": 75, "minutes": 100, "price_id": "price_1Sro5E25J162lH5djEsUZnrQ"},
    "professional": {"name": "Professional", "price": 150, "minutes": 425, "price_id": "price_1Srnl925J162lH5dYtAcLBQ0"},
    "business": {"name": "Business", "price": 250, "minutes": 900, "price_id": "price_1SroYB25J162lH5dh3QPAMAL"},
}


class CheckoutRequest(BaseModel):
    tier: str
    email: EmailStr
    include_setup_fee: bool = False


@app.post("/api/stripe/create-checkout-session")
@limiter.limit("10/minute")
async def create_checkout_session(request: Request, checkout_data: CheckoutRequest):
    """Create a Stripe checkout session for subscription purchase"""
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Payment system not configured")
    
    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
        
        tier = checkout_data.tier.lower()
        if tier not in PRICING_TIERS:
            raise HTTPException(status_code=400, detail="Invalid pricing tier")
        
        tier_info = PRICING_TIERS[tier]
        
        # Create Stripe checkout session
        line_item = {
            "quantity": 1,
        }
        
        # If we have a specific Price ID (configured in Stripe), use it.
        # This is required for Metered Billing to work!
        if "price_id" in tier_info and "REPLACE" not in tier_info["price_id"]:
            line_item["price"] = tier_info["price_id"]
        else:
            # Fallback: Create ad-hoc pricing (Note: Does NOT support usage metering)
            line_item["price_data"] = {
                "currency": "usd",
                "product_data": {
                    "name": f"AI Receptionist - {tier_info['name']}",
                    "description": f"{tier_info['minutes']} minutes/month included",
                },
                "unit_amount": tier_info['price'] * 100,  # Stripe uses cents
                "recurring": {"interval": "month"},
            }
            
        # Compile line items
        line_items = [line_item]
        
        # Add Setup Fee if requested (VIP Mode)
        if checkout_data.include_setup_fee:
            line_items.append({
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": "White Glove Setup Fee",
                        "description": "Professional Onboarding & Custom AI Prompts",
                    },
                    "unit_amount": 30000,  # $300.00
                },
                "quantity": 1,
            })

        session = stripe.checkout.Session.create(
            # Removing payment_method_types to allow Automatic Payment Methods 
            # as configured in the Stripe Dashboard (includes Apple Pay, Google Pay, etc.)
            automatic_payment_methods={"enabled": True},
            line_items=line_items,
            mode="subscription",
            success_url="https://dashboard.lexmakesit.com/welcome?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="https://lexmakesit.com/projects/ai-receptionist#pricing",
            customer_email=checkout_data.email,
            metadata={
                "tier": tier,
                "email": checkout_data.email,
                "setup_fee_paid": str(checkout_data.include_setup_fee)
            },
        )
        
        logger.info(f"Checkout session created for {checkout_data.email} - tier: {tier} - setup_fee: {checkout_data.include_setup_fee}")
        return {"checkout_url": session.url, "session_id": session.id}
        
    except Exception as e:
        logger.error(f"Stripe checkout error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@app.post("/api/stripe/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events for payment processing"""
    if not STRIPE_SECRET_KEY or not STRIPE_WEBHOOK_SECRET:
        logger.error("Stripe not configured for webhooks")
        raise HTTPException(status_code=500, detail="Webhook not configured")
    
    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
        
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature", "")
        
        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            logger.error("Invalid Stripe webhook payload")
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid Stripe webhook signature")
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        # Handle the event
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            customer_email = session.get("customer_email")
            tier = session.get("metadata", {}).get("tier", "starter")
            
            logger.info(f"Payment completed for {customer_email} - tier: {tier}")
            
            # Send welcome email with dashboard access
            await send_welcome_email(customer_email, tier)
            
        elif event["type"] == "customer.subscription.created":
            subscription = event["data"]["object"]
            logger.info(f"Subscription created: {subscription['id']}")
            
        elif event["type"] == "customer.subscription.deleted":
            subscription = event["data"]["object"]
            logger.info(f"Subscription cancelled: {subscription['id']}")
        
        return JSONResponse(content={"status": "success"})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stripe webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


async def send_welcome_email(email: str, tier: str) -> bool:
    """Send welcome email with dashboard access after purchase"""
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.warning("SMTP not configured - welcome email skipped")
        return False
    
    try:
        tier_info = PRICING_TIERS.get(tier, PRICING_TIERS["starter"])
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "🎉 Welcome to AI Receptionist - Your Account is Ready!"
        msg["From"] = SMTP_USER
        msg["To"] = email
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;
                        background: linear-gradient(135deg, #60aaff 0%, #3d84ff 100%);
                        border-radius: 16px;">
                <div style="background: white; border-radius: 12px; padding: 30px;">
                    <h1 style="color: #3d84ff; margin-bottom: 20px;">Welcome to AI Receptionist! 🎉</h1>
                    
                    <p>Thank you for choosing the <strong>{tier_info['name']}</strong> plan!</p>
                    
                    <div style="background: #f0f9ff; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="margin-top: 0;">Your Plan Details:</h3>
                        <p><strong>Plan:</strong> {tier_info['name']}</p>
                        <p><strong>Included Minutes:</strong> {tier_info['minutes']}/month</p>
                        <p><strong>Monthly Rate:</strong> ${tier_info['price']}/month</p>
                    </div>
                    
                    <h3>Next Steps:</h3>
                    <ol>
                        <li>Access your dashboard to complete onboarding</li>
                        <li>Set up your business profile</li>
                        <li>Choose your phone number</li>
                        <li>Customize your AI receptionist</li>
                    </ol>
                    
                    <a href="https://dashboard.lexmakesit.com" 
                       style="display: inline-block; background: #3d84ff; color: white; 
                              padding: 14px 28px; text-decoration: none; border-radius: 8px;
                              font-weight: bold; margin: 20px 0;">
                        Access Your Dashboard →
                    </a>
                    
                    <p style="margin-top: 30px; color: #666; font-size: 14px;">
                        Questions? Reply to this email or visit our support page.<br>
                        - Lex Santiago, lexmakesit
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        html_part = MIMEText(html_body, "html")
        msg.attach(html_part)
        
        await aiosmtplib.send(
            msg,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
            start_tls=True,
            timeout=10,
        )
        
        logger.info(f"Welcome email sent to {email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send welcome email: {str(e)}")
        return False


# ============================================================================
# SECURE ERROR HANDLERS (OWASP: Hide Implementation Details)
# ============================================================================


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Custom 404 handler - no sensitive path disclosure"""
    logger.warning(f"404 error: {request.url.path}")
    return templates.TemplateResponse(
        request=request, name="404.html", context={"request": request}, status_code=404
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """
    Custom 500 handler - log errors privately, show generic message
    OWASP: Never expose stack traces or implementation details
    """
    logger.error(f"Internal error: {str(exc)}", exc_info=True)

    # In production, return generic error
    if os.getenv("PRODUCTION"):
        return templates.TemplateResponse(
            request=request,
            name="500.html",
            context={"request": request},
            status_code=500,
        )

    # In development, show details (remove in production)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__},
    )


@app.exception_handler(ValueError)
async def validation_error_handler(request: Request, exc: ValueError):
    """Handle validation errors securely"""
    logger.warning(f"Validation error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "127.0.0.1"),
        port=8001,
        reload=True,
        ssl_keyfile=None,  # Add SSL cert paths in production
        ssl_certfile=None,
    )
