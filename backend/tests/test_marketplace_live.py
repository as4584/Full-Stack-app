import requests
import sys
import time

BASE_URL = "http://localhost:8000"

def test_search_and_buy():
    print(f"Testing connectivity to {BASE_URL}...")
    try:
        # 1. Test Health
        resp = requests.get(f"{BASE_URL}/health")
        if resp.status_code != 200:
            print(f"❌ Health check failed: {resp.status_code}")
            return False
        print("✅ Backend is up and running.")

        # 2. Test Search (Magic Number)
        print("\nTesting Search for Area Code 000...")
        resp = requests.get(f"{BASE_URL}/twilio/marketplace/search-numbers?area_code=000")
        if resp.status_code != 200:
             print(f"❌ Search failed: {resp.status_code} - {resp.text}")
             return False
        
        results = resp.json()
        if not results or results[0]['phoneNumber'] != "+10000000000":
             print(f"❌ Unexpected search results: {results}")
             return False
        print("✅ Found Magic Test Number: +10000000000")

        # 3. Test Buy (Magic Number)
        print("\nTesting Purchase of Test Number...")
        buy_payload = {"phoneNumber": "+10000000000"}
        resp = requests.post(f"{BASE_URL}/twilio/marketplace/buy-number", json=buy_payload)
        
        if resp.status_code != 200:
             print(f"❌ Purchase failed: {resp.status_code} - {resp.text}")
             return False
             
        data = resp.json()
        if data.get("status") != "success" or data.get("sid") != "PN_TEST_SID":
             print(f"❌ Unexpected purchase response: {data}")
             return False
        
        print("✅ Purchase successful (Magic Bypass confirmed).")
        return True

    except requests.exceptions.ConnectionError:
        print(f"❌ Could not connect to {BASE_URL}. Is the backend server running?")
        return False
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        return False

if __name__ == "__main__":
    success = test_search_and_buy()
    if not success:
        sys.exit(1)
