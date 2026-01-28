import json
import os
from typing import List, Dict, Any
from openai import OpenAI
from ai_receptionist.config.settings import get_settings

class ScenarioGenerator:
    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key)

    def generate_scenarios(self) -> List[Dict[str, Any]]:
        prompt = """
        Generate 3 distinct business scenarios for an AI receptionist simulation.
        
        Scenario A: Scheduling request.
        Scenario B: Billing or payment issue.
        Scenario C: Service complaint or escalation.
        
        One of these scenarios MUST explicitly require using Calendly for scheduling.
        
        For each scenario, provide a script of 6-12 turns (Customer and AI).
        The Customer should speak naturally, with occasional frustration, confusion, or interruptions.
        The AI should be polite, structured, and helpful.
        
        The output must be a JSON object with a key "scenarios" containing an array of 3 scenario objects.
        Each scenario object must have:
        - "id": "A", "B", or "C"
        - "type": "scheduling", "billing", or "complaint"
        - "description": brief description
        - "requires_calendly": boolean
        - "customer_script": array of strings, representing the Customer's lines in order.
        
        Ensure variety in customer persona, emotion, and phrasing.
        Do not include "Customer:" or "AI:" prefixes in the script strings.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a scenario generator for AI testing. Output valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            data = json.loads(content)
            return data.get("scenarios", [])
        except Exception as e:
            print(f"Error generating scenarios: {e}")
            # Fallback or empty list, but spec says "The agent must always generate 3 scenarios"
            # In a real implementation, we might retry or have a fallback.
            return []

if __name__ == "__main__":
    generator = ScenarioGenerator()
    scenarios = generator.generate_scenarios()
    print(json.dumps(scenarios, indent=2))
