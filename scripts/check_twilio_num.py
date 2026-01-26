
import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

def check_number(phone_number):
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    client = Client(account_sid, auth_token)
    
    numbers = client.incoming_phone_numbers.list(phone_number=phone_number)
    if not numbers:
        print(f"Number {phone_number} not found in account.")
        return
    
    num = numbers[0]
    print(f"Details for {phone_number}:")
    print(f"  SID: {num.sid}")
    print(f"  Voice URL: {num.voice_url}")
    print(f"  Voice Method: {num.voice_method}")
    print(f"  Status: {num.status}")

if __name__ == "__main__":
    # Check the number the user mentioned (or the real one from DB)
    import sys
    search = sys.argv[1] if len(sys.argv) > 1 else "+18623193715"
    check_number(search)
