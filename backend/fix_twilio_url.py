import os
from twilio.rest import Client

# Get credentials from environment
account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
auth_token = os.environ.get('TWILIO_AUTH_TOKEN')

if not account_sid or not auth_token:
    print("Missing Twilio credentials!")
    exit(1)

client = Client(account_sid, auth_token)

# Find and update the phone number
phone_numbers = client.incoming_phone_numbers.list()
for pn in phone_numbers:
    print(f"Found: {pn.phone_number} (SID: {pn.sid})")
    print(f"  Current Voice URL: {pn.voice_url}")
    
    # Update to use /twilio/voice instead of /twilio/webhook
    new_url = "https://receptionist.lexmakesit.com/twilio/voice"
    pn.update(voice_url=new_url, voice_method="POST")
    print(f"  Updated to: {new_url}")
