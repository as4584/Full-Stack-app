#!/usr/bin/env python3
"""
Terminal UI for monitoring Twilio voice calls in real-time.

Displays live transcript of conversations with color-coded output.
"""

import sys
import time
from datetime import datetime
from typing import Dict, Optional

# ANSI color codes for terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    GRAY = '\033[90m'


class CallMonitor:
    """Live monitor for voice calls with transcript display."""
    
    def __init__(self):
        self.active_calls: Dict[str, Dict] = {}
        self.call_history = []
        
    def print_header(self):
        """Print monitoring header."""
        print("\n" + "=" * 80)
        print(f"{Colors.BOLD}{Colors.OKCYAN}🎙️  TWILIO VOICE CALL MONITOR{Colors.ENDC}")
        print(f"{Colors.GRAY}Listening for incoming calls...{Colors.ENDC}")
        print("=" * 80 + "\n")
    
    def print_separator(self):
        """Print section separator."""
        print(f"{Colors.GRAY}{'─' * 80}{Colors.ENDC}")
    
    def log_incoming_call(self, call_sid: str, from_number: Optional[str] = None):
        """Log new incoming call."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.active_calls[call_sid] = {
            "start_time": datetime.now(),
            "from": from_number or "Unknown",
            "transcript": [],
            "language": "en",
            "total_cost": 0.0
        }
        
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}📞 INCOMING CALL{Colors.ENDC}")
        print(f"{Colors.GRAY}[{timestamp}]{Colors.ENDC} CallSid: {Colors.OKCYAN}{call_sid}{Colors.ENDC}")
        if from_number:
            print(f"{Colors.GRAY}From:{Colors.ENDC} {from_number}")
        self.print_separator()
    
    def log_language_selection(self, call_sid: str, language: str):
        """Log language selection."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if call_sid in self.active_calls:
            self.active_calls[call_sid]["language"] = language
        
        lang_display = "🇺🇸 English" if language == "en" else "🇪🇸 Español"
        print(f"{Colors.GRAY}[{timestamp}]{Colors.ENDC} {Colors.WARNING}Language Selected:{Colors.ENDC} {lang_display}")
    
    def log_user_input(self, call_sid: str, text: str):
        """Log what the user said."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if call_sid in self.active_calls:
            self.active_calls[call_sid]["transcript"].append(("user", text))
        
        print(f"\n{Colors.GRAY}[{timestamp}]{Colors.ENDC} {Colors.OKBLUE}{Colors.BOLD}👤 USER:{Colors.ENDC}")
        print(f"  {Colors.OKBLUE}{text}{Colors.ENDC}")
    
    def log_ai_response(self, call_sid: str, text: str, intent: Optional[str] = None):
        """Log AI assistant response."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if call_sid in self.active_calls:
            self.active_calls[call_sid]["transcript"].append(("ai", text))
        
        intent_tag = f" [{intent}]" if intent else ""
        print(f"\n{Colors.GRAY}[{timestamp}]{Colors.ENDC} {Colors.OKGREEN}{Colors.BOLD}🤖 AI:{Colors.ENDC}{Colors.GRAY}{intent_tag}{Colors.ENDC}")
        print(f"  {Colors.OKGREEN}{text}{Colors.ENDC}")
    
    def log_cost(self, call_sid: str, operation: str, cost: float, total: float):
        """Log cost information."""
        if call_sid in self.active_calls:
            self.active_calls[call_sid]["total_cost"] = total
        
        print(f"{Colors.GRAY}  💰 {operation}: ${cost:.4f} (Total: ${total:.4f}){Colors.ENDC}")
    
    def log_call_end(self, call_sid: str, reason: str = "completed"):
        """Log call ending."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if call_sid in self.active_calls:
            call_data = self.active_calls[call_sid]
            duration = (datetime.now() - call_data["start_time"]).total_seconds()
            total_cost = call_data["total_cost"]
            
            print(f"\n{Colors.FAIL}{Colors.BOLD}📵 CALL ENDED{Colors.ENDC}")
            print(f"{Colors.GRAY}[{timestamp}]{Colors.ENDC} Reason: {reason}")
            print(f"{Colors.GRAY}Duration:{Colors.ENDC} {duration:.1f}s")
            print(f"{Colors.GRAY}Total Cost:{Colors.ENDC} ${total_cost:.4f}")
            
            self.print_separator()
            print(f"\n{Colors.BOLD}📝 CALL SUMMARY:{Colors.ENDC}")
            print(f"{Colors.GRAY}Turns: {len(call_data['transcript'])}{Colors.ENDC}\n")
            
            for speaker, text in call_data["transcript"]:
                icon = "👤" if speaker == "user" else "🤖"
                color = Colors.OKBLUE if speaker == "user" else Colors.OKGREEN
                print(f"{icon} {color}{text[:100]}{Colors.ENDC}")
            
            print("=" * 80 + "\n")
            
            self.call_history.append(call_data)
            del self.active_calls[call_sid]
    
    def log_error(self, message: str):
        """Log error message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{Colors.GRAY}[{timestamp}]{Colors.ENDC} {Colors.FAIL}❌ ERROR: {message}{Colors.ENDC}")
    
    def log_info(self, message: str):
        """Log informational message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{Colors.GRAY}[{timestamp}]{Colors.ENDC} ℹ️  {message}")
    
    def print_stats(self):
        """Print current statistics."""
        active_count = len(self.active_calls)
        total_count = len(self.call_history)
        
        print(f"\n{Colors.BOLD}📊 STATISTICS:{Colors.ENDC}")
        print(f"{Colors.GRAY}Active Calls:{Colors.ENDC} {active_count}")
        print(f"{Colors.GRAY}Completed Calls:{Colors.ENDC} {total_count}")
        
        if self.call_history:
            total_cost = sum(c["total_cost"] for c in self.call_history)
            print(f"{Colors.GRAY}Total Cost:{Colors.ENDC} ${total_cost:.4f}")


# Global monitor instance
monitor = CallMonitor()


def main():
    """Main entry point for standalone monitoring."""
    monitor.print_header()
    
    # Example usage
    monitor.log_info("Voice system ready. Waiting for calls...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Shutting down monitor...{Colors.ENDC}\n")
        monitor.print_stats()
        sys.exit(0)


if __name__ == "__main__":
    main()
