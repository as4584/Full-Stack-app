import os
import sys
# Setup PYTHONPATH to include backend dir
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ai_receptionist.config.settings import get_settings

settings = get_settings()
key = settings.openai_api_key
if key:
    print(f"OpenAI Key found: {key[:8]}...{key[-4:]}")
else:
    print("OpenAI Key NOT found!")
