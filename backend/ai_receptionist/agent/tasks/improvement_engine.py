import json
import os
from typing import List, Dict, Any
from openai import OpenAI
from ai_receptionist.config.settings import get_settings

class ImprovementEngine:
    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key)

    def apply_fixes(self, action_items: Dict[str, Any]):
        actions = action_items.get("actions", [])
        for action in actions:
            file_path = action.get("file")
            change_desc = action.get("change")
            
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                continue
                
            print(f"Applying fix to {file_path}: {change_desc}")
            
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
                
            prompt = f"""
            You are an expert python developer.
            Apply the following change to the code:
            "{change_desc}"
            
            Code:
            {code}
            
            Return ONLY the full modified code. Do not include markdown formatting.
            """
            
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}]
                )
                new_code = response.choices[0].message.content.strip()
                # Remove markdown code blocks if present
                if new_code.startswith("```"):
                    lines = new_code.split("\n")
                    # Find start and end of code block
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines[-1].startswith("```"):
                        lines = lines[:-1]
                    new_code = "\n".join(lines)
                    
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_code)
                    
                print(f"Applied fix to {file_path}")
            except Exception as e:
                print(f"Error applying fix: {e}")
