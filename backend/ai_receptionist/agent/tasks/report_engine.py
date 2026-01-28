import json
import sys
from typing import Dict, Any

class ReportEngine:
    def __init__(self):
        pass

    def generate_report(self, metrics: Dict[str, Any], scenario: Dict[str, Any]):
        quant = metrics.get("quantitative", {})
        qual = metrics.get("qualitative", {})
        
        # Markdown Report
        print("\n### AI PERFORMANCE REPORT\n")
        print(f"**Scenario**: {scenario.get('description', 'N/A')}")
        print(f"**Summary**: {qual.get('emotional_tone', 'N/A')} tone. UX Score: {qual.get('ux_score', 0)}/100.")
        print("\n**Quantitative Metrics**:")
        print(f"- Call Length: {quant.get('total_call_length_ms', 0)} ms")
        print(f"- Avg Delay: {quant.get('ai_response_delay_avg_ms', 0)} ms")
        print(f"- Whisper Accuracy: {quant.get('whisper_accuracy', 0)}%")
        
        print("\n**Qualitative Evaluation**:")
        print(f"- Politeness: {qual.get('politeness', 0)}/10")
        print(f"- Clarity: {qual.get('clarity', 0)}/10")
        print(f"- Frustration: {qual.get('customer_frustration', 0)}")
        print(f"- Calendly Success: {qual.get('calendly_success', False)}")
        
        print("\n**Weaknesses**:")
        for w in qual.get('weaknesses', []):
            print(f"- {w}")
            
        print("\n**Recommendations**:")
        for r in qual.get('improvement_recommendations', []):
            print(f"- {r}")
            
        print("\n") # Separator
        
        # ACTION_ITEMS JSON
        # Logic to determine actions based on metrics
        actions = []
        severity = "minor"
        
        if qual.get('ux_score', 0) < 85:
            severity = "moderate"
        if not qual.get('calendly_success', False) and scenario.get('requires_calendly', False):
            severity = "critical"
            
        # Example action generation (placeholder)
        if severity != "minor":
            actions.append({
                "file": "ai_receptionist/agent/conversation_bot.py",
                "change": "Adjust prompt to be more empathetic"
            })
            
        action_items = {
            "severity": severity,
            "actions": actions
        }
        print(json.dumps(action_items, indent=2))
        
        # NEXT_AUTOMATION JSON
        next_automation = {
            "auto_trigger": severity in ["moderate", "critical"],
            "reason": "UX score below threshold" if severity != "minor" else "Performance acceptable",
            "severity": severity,
            "execute": "apply_required_fixes" if severity != "minor" else "none"
        }
        print(json.dumps(next_automation, indent=2))
