import requests
import time

print("Waiting for uvicorn...", flush=True)
time.sleep(2)

urls = [
    ("http://localhost:8010/test-ping", None),
    ("http://localhost:8010/twilio/test-voice", {'CallSid': 'test'}),
    ("http://localhost:8010/twilio/voice", {'CallSid': 'test', 'From': 'test'})
]

for url, data in urls:
    try:
        print(f"Testing {url}...", flush=True)
        resp = requests.post(url, data=data)
        print(f"Status: {resp.status_code}")
        print(f"Body: {resp.text[:100]}")
    except Exception as e:
        print(f"Error: {e}")
