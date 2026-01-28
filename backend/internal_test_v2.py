import requests

urls = [
    "http://localhost:8010/twilio/voice",
    "http://localhost:8010/twilio/voice/",
    "http://localhost:8010/voice",
    "http://localhost:8010/voice/",
    "http://localhost:8010/twilio/twilio/voice",
    "http://0.0.0.0:8010/twilio/voice",
    "http://127.0.0.1:8010/twilio/voice"
]

for url in urls:
    try:
        print(f"Testing {url}...")
        resp = requests.post(url, data={'CallSid': 'test', 'From': 'test'})
        print(f"Status: {resp.status_code}")
        if resp.status_code != 404:
            print(f"SUCCESS BODY: {resp.text[:100]}")
    except Exception as e:
        print(f"Error: {e}")
