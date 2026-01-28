import os
from twilio.rest import Client

def setup_fallback():
    # Get credentials from environment
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')

    if not account_sid or not auth_token:
        print("Error: Missing TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN environment variables.")
        return

    client = Client(account_sid, auth_token)

    # The fallback TwiML URL. 
    # For now, we'll use a TwiML Bin or a static URL if available.
    # Since we're adding error handling to Caddy, the primary URL might still be reachable
    # but return a 502. Twilio will only use the fallback if it gets a non-200.
    
    # We'll use a publicly accessible TwiML that just says "Updating, please call back".
    # Alternatively, we can use a TwiML Bin SID if we had one.
    # For this implementation, we'll suggest a fallback URL that points to a static file we'll host.
    
    fallback_url = "https://receptionist.lexmakesit.com/fallback-voice"
    
    # Find and update the phone numbers
    phone_numbers = client.incoming_phone_numbers.list()
    if not phone_numbers:
        print("No phone numbers found in this Twilio account.")
        return

    for pn in phone_numbers:
        print(f"Updating {pn.phone_number} ({pn.sid})...")
        print(f"  Current Voice URL: {pn.voice_url}")
        print(f"  Current Fallback URL: {pn.voice_fallback_url}")
        
        pn.update(
            voice_fallback_url=fallback_url,
            voice_fallback_method="POST"
        )
        print(f"  Updated Fallback URL to: {fallback_url}")

if __name__ == "__main__":
    setup_fallback()
