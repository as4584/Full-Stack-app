import requests
try:
    resp = requests.post('http://localhost:8010/twilio/voice', data={'CallSid': 'test', 'From': 'test'})
    print(f"Status: {resp.status_code}")
    print(f"Body: {resp.text}")
except Exception as e:
    print(f"Error: {e}")
