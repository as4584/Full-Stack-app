import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

RECIPIENT_EMAIL = "letsmakebusinessbetter@gmail.com"
SUBJECT = "AI Receptionist - Access & Onboarding (Action Required)"

BODY_HTML = """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;
                background: #f8f9fa;
                border-radius: 16px;">
        <div style="background: white; border-radius: 12px; padding: 30px; border: 1px solid #ddd;">
            <h2 style="color: #3d84ff; margin-top: 0;">AI Receptionist - Access & Onboarding (Action Required)</h2>
            
            <p>Hi Damian,</p>

            <p>I've finalized your AI Receptionist setup. Everything is connected and ready for launch.</p>

            <p>As requested, I've configured your account for the <strong>Standard Maintenance Plan ($75/mo)</strong>. This covers your dedicated phone number, server hosting, dashboard access, and your first 100 minutes of AI calls every month.</p>

            <p>I also helped set up the backend for the <strong>White-Glove Onboarding ($300 one-time)</strong> so I can personally handle your prompt engineering and voice tuning.</p>

            <h3>Next Steps:</h3>
            <p>Please click the link below and select the <strong>"Starter"</strong> plan to activate your account. The setup fee is automatically bundled in securely.</p>

            <a href="https://lexmakesit.com/projects/ai-receptionist?vip=true#pricing" 
               style="display: inline-block; background: #3d84ff; color: white; 
                      padding: 14px 28px; text-decoration: none; border-radius: 8px;
                      font-weight: bold; margin: 20px 0;">
                👉 Activate Account & Maintenance Plan
            </a>
            <p><em>(Select the "Starter" option on the left)</em></p>

            <h3>Once you activate:</h3>
            <ol>
                <li>You will get instant access to your <strong>Business Dashboard</strong> where you can see call logs and settings.</li>
                <li>I will receive a notification and immediately begin configuring your AI's personality and FAQ knowledge base.</li>
                <li>We will be live testing calls within 24 hours.</li>
            </ol>

            <p>Let me know once that's done so I can start the configuration!</p>

            <p>Best,<br>Lex</p>
        </div>
    </div>
</body>
</html>
"""

def send_email():
    if not SMTP_USER or not SMTP_PASSWORD:
        print("❌ Error: SMTP_USER or SMTP_PASSWORD not set in environment.")
        return

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = SUBJECT
        msg["From"] = SMTP_USER
        msg["To"] = RECIPIENT_EMAIL

        html_part = MIMEText(BODY_HTML, "html")
        msg.attach(html_part)

        print(f"Connecting to {SMTP_HOST}:{SMTP_PORT}...")
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, RECIPIENT_EMAIL, msg.as_string())
        
        print(f"✅ Email sent successfully to {RECIPIENT_EMAIL}")

    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")

if __name__ == "__main__":
    send_email()
