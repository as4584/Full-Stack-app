import uvicorn
import sys
import os

# Force UTF-8 for stdout/stderr
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

if __name__ == "__main__":
    print("Starting server on port 8001...")
    try:
        # Run uvicorn with minimal logging to avoid encoding crashes
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8001,
            reload=True,
            log_level="warning", # Only show warnings/errors
            access_log=False     # Disable access log to reduce output
        )
    except Exception as e:
        print(f"Server failed to start: {e}")
