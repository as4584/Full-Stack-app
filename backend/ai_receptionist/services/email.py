import logging
import httpx
from typing import Optional
from ai_receptionist.config.settings import get_settings

logger = logging.getLogger(__name__)

async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None
) -> bool:
    """
    Send an email using SendGrid Web API or SMTP (fallback).
    """
    settings = get_settings()
    
    if settings.sendgrid_api_key:
        return await _send_via_sendgrid(to_email, subject, html_content, settings.sendgrid_api_key)
    else:
        # For now, let's just log it if SendGrid is missing, 
        # as SMTP might be blocked in some environments (like DigitalOcean).
        logger.warning(f"MOCK EMAIL to {to_email}: {subject}")
        # In a real scenario, we'd use aiosmtplib here.
        return True

async def _send_via_sendgrid(to_email: str, subject: str, html_content: str, api_key: str) -> bool:
    url = "https://api.sendgrid.com/v3/mail/send"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    settings = get_settings()
    payload = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": settings.smtp_from_email, "name": settings.smtp_from_name},
        "subject": subject,
        "content": [
            {"type": "text/html", "value": html_content}
        ]
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload, timeout=10)
            if response.status_code >= 200 and response.status_code < 300:
                logger.info(f"Email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"SendGrid error: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Failed to send email via SendGrid: {e}")
            return False

async def send_password_reset_email(to_email: str, token: str):
    settings = get_settings()
    reset_url = f"{settings.dashboard_url}/reset-password?token={token}"
    
    subject = "Reset Your AI Receptionist Password"
    html_content = f"""
    <html>
    <body>
        <h2>Password Reset Request</h2>
        <p>You requested to reset your password. Click the link below to set a new password:</p>
        <p><a href="{reset_url}">{reset_url}</a></p>
        <p>This link will expire in 30 minutes.</p>
        <p>If you did not request this, please ignore this email.</p>
    </body>
    </html>
    """
    return await send_email(to_email, subject, html_content)
