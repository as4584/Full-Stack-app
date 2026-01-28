"""
Cost tracking for Twilio voice calls.

Tracks all billable operations and calculates running costs in real-time.
Logs to console after each operation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

# Twilio pricing (approximate as of 2025; check twilio.com/pricing for exact rates)
COST_PER_MINUTE_INBOUND = 0.0085  # $0.0085/min
COST_PER_SPEECH_REQUEST = 0.02  # $0.02 per speech recognition
COST_PER_1K_CHARS_TTS = 0.04  # $0.04 per 1000 characters for TTS
COST_PER_MINUTE_RECORDING = 0.0025  # $0.0025/min (optional)


@dataclass
class CostTracker:
    """Tracks costs for a single call."""

    call_sid: str
    start_time: datetime = field(default_factory=datetime.utcnow)
    operations: List[Dict] = field(default_factory=list)

    def log_operation(self, op_type: str, details: str, cost: float) -> None:
        """Log a billable operation."""
        self.operations.append(
            {"timestamp": datetime.utcnow(), "type": op_type, "details": details, "cost": cost}
        )
        running_total = self.total_cost()
        logger.info(
            f"💰 [{op_type}] {details} → ${cost:.4f} (Total so far: ${running_total:.4f})"
        )

    def log_inbound_call(self, duration_seconds: float) -> None:
        """Log inbound call cost."""
        minutes = duration_seconds / 60.0
        cost = minutes * COST_PER_MINUTE_INBOUND
        self.log_operation("INBOUND_CALL", f"{duration_seconds:.1f}s ({minutes:.2f} min)", cost)

    def log_speech_recognition(self, transcription: str = "") -> None:
        """Log a speech recognition request."""
        detail = f"'{transcription[:30]}...'" if transcription else "speech input"
        self.log_operation("SPEECH_RECOGNITION", detail, COST_PER_SPEECH_REQUEST)

    def log_tts(self, text: str) -> None:
        """Log text-to-speech cost."""
        char_count = len(text)
        cost = (char_count / 1000.0) * COST_PER_1K_CHARS_TTS
        self.log_operation("TEXT_TO_SPEECH", f"{char_count} chars", cost)

    def log_recording(self, duration_seconds: float) -> None:
        """Log call recording cost (optional)."""
        minutes = duration_seconds / 60.0
        cost = minutes * COST_PER_MINUTE_RECORDING
        self.log_operation("RECORDING", f"{duration_seconds:.1f}s ({minutes:.2f} min)", cost)

    def total_cost(self) -> float:
        """Calculate total cost so far."""
        return sum(op["cost"] for op in self.operations)

    def summary(self) -> str:
        """Generate a call summary with cost breakdown."""
        duration = (datetime.utcnow() - self.start_time).total_seconds()
        total = self.total_cost()
        breakdown = {}
        for op in self.operations:
            op_type = op["type"]
            breakdown[op_type] = breakdown.get(op_type, 0) + op["cost"]

        lines = [
            f"\n{'='*60}",
            f"📞 CALL SUMMARY: {self.call_sid}",
            f"{'='*60}",
            f"Duration: {duration:.1f}s",
            f"Operations: {len(self.operations)}",
            "",
            "Cost Breakdown:",
        ]
        for op_type, cost in breakdown.items():
            lines.append(f"  {op_type}: ${cost:.4f}")
        lines.append("")
        lines.append(f"TOTAL COST: ${total:.4f}")
        lines.append(f"{'='*60}\n")
        return "\n".join(lines)


# Global session store: CallSid -> CostTracker
_cost_sessions: Dict[str, CostTracker] = {}


def get_cost_tracker(call_sid: str) -> CostTracker:
    """Get or create a cost tracker for a call."""
    if call_sid not in _cost_sessions:
        _cost_sessions[call_sid] = CostTracker(call_sid=call_sid)
    return _cost_sessions[call_sid]


def print_call_summary(call_sid: str) -> None:
    """Log the call summary."""
    tracker = _cost_sessions.get(call_sid)
    if tracker:
        summary = tracker.summary()
        logger.info(summary)
