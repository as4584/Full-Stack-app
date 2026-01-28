from ai_receptionist.config.settings import get_settings
s = get_settings()
print(f"SID: {s.twilio_account_sid}")
print(f"TOKEN: {s.twilio_auth_token[:10] if s.twilio_auth_token else 'MISSING'}...")
print(f"PHONE: {s.twilio_phone_number}")
