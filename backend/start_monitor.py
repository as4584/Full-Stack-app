#!/usr/bin/env python3
"""
Start Twilio voice server with integrated terminal monitor.

This script starts the FastAPI server with the call monitor enabled,
showing real-time transcripts in the terminal.
"""

import sys
import os
import signal

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from call_monitor import monitor

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\n\n🛑 Shutting down...")
    monitor.print_stats()
    sys.exit(0)

def main():
    """Start server with monitoring."""
    signal.signal(signal.SIGINT, signal_handler)
    
    # Clear screen
    os.system('clear' if os.name == 'posix' else 'cls')
    
    # Print banner
    monitor.print_header()
    
    # Check environment
    if not os.getenv('TWILIO_ACCOUNT_SID'):
        monitor.log_error("TWILIO_ACCOUNT_SID not set in environment")
        monitor.log_info("Please set your Twilio credentials in .env file")
        sys.exit(1)
    
    monitor.log_info("Starting FastAPI server on http://localhost:8000")
    monitor.log_info("Twilio webhook URL: http://localhost:8000/twilio/voice")
    monitor.log_info("For external access, use ngrok: ngrok http 8000")
    monitor.print_separator()
    
    # Start uvicorn in background
    venv_python = os.path.join(os.path.dirname(__file__), '.venv', 'bin', 'python')
    if not os.path.exists(venv_python):
        venv_python = sys.executable  # Fallback to current python
    
    try:
        # Run uvicorn directly with monitor output
        import uvicorn
        
        monitor.log_info("Server ready! Waiting for calls...")
        monitor.print_separator()
        print()
        
        # Run server
        uvicorn.run(
            "ai_receptionist.app.main:app",
            host="0.0.0.0",
            port=8000,
            log_level="warning",  # Reduce noise
            access_log=False  # Disable access logs to keep terminal clean
        )
    except KeyboardInterrupt:
        pass
    except Exception as e:
        monitor.log_error(f"Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
