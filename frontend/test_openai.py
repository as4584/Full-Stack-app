import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)

key = os.environ.get("OPENAI_API_KEY")
if key:
    print(f"Key found: {key[:10]}... (len={len(key)})")
    # Strip just in case
    key = key.strip()
    os.environ["OPENAI_API_KEY"] = key
else:
    print("Key NOT found")

client = OpenAI(api_key=key)

try:
    print("Testing API...")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=5
    )
    print("Success!")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"Error: {e}")
