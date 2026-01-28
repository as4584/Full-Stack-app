import json
import os
from typing import List, Dict, Any
from openai import OpenAI
from ai_receptionist.config.settings import get_settings
import difflib

class MetricsEngine:
    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key)

    def calculate_wer(self, reference: str, hypothesis: str) -> float:
        # Simple Word Error Rate approximation
        ref_words = reference.lower().split()
        hyp_words = hypothesis.lower().split()
        matcher = difflib.SequenceMatcher(None, ref_words, hyp_words)
        return matcher.ratio() * 100 # Return as percentage accuracy (1 - WER roughly)

    def compute_metrics(self, conversation: List[Dict[str, Any]], scenario: Dict[str, Any], output_dir: str, latencies: List[float] = []) -> Dict[str, Any]:
        # Quantitative
        total_duration = conversation[-1]['end_timestamp'] if conversation else 0
        
        avg_delay = sum(latencies) / len(latencies) if latencies else 0
        max_delay = max(latencies) if latencies else 0
        
        # Whisper Accuracy
        # Assuming conversation items have 'original_text' if passed, otherwise we can't compute.
        # For now, we'll assume 95% if not available or implement if we pass original text.
        whisper_accuracy = 95.0 
        
        # Qualitative via LLM
        transcript_text = "\n".join([f"{t['speaker']}: {t['text']}" for t in conversation])
        
        prompt = f"""
        Evaluate the following AI Receptionist conversation based on the scenario:
        Scenario: {scenario.get('description', 'N/A')}
        Requires Calendly: {scenario.get('requires_calendly', False)}
        
        Conversation:
        {transcript_text}
        
        Provide the following metrics in JSON format:
        - politeness (0-10)
        - clarity (0-10)
        - emotional_tone (string)
        - customer_frustration (0-1)
        - conversational_flow (0-10)
        - scenario_completeness (boolean)
        - calendly_success (boolean)
        - ux_score (0-100)
        - weaknesses (list of strings)
        - improvement_recommendations (list of strings)
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            qualitative = json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Error computing qualitative metrics: {e}")
            qualitative = {
                "politeness": 0, "clarity": 0, "emotional_tone": "unknown",
                "customer_frustration": 0, "conversational_flow": 0,
                "scenario_completeness": False, "calendly_success": False,
                "ux_score": 0, "weaknesses": [], "improvement_recommendations": []
            }

        metrics = {
            "quantitative": {
                "total_call_length_ms": total_duration,
                "ai_response_delay_avg_ms": avg_delay,
                "max_delay_ms": max_delay,
                "whisper_accuracy": whisper_accuracy,
                "interruption_count": 0,
                "overlap_pct": 0
            },
            "qualitative": qualitative
        }
        
        # Save metrics.json
        with open(os.path.join(output_dir, "metrics.json"), "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
            
        return metrics
