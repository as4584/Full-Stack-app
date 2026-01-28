import asyncio
import json
import os
import sys
from typing import List

# Setup PYTHONPATH to include backend dir
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ai_receptionist.services.evaluation.shadow_eval import run_shadow_eval

async def run_benchmark():
    """
    Runs the Shadow AI against the 15 Golden Frames and reports accuracy.
    """
    frames_path = os.path.join(os.path.dirname(__file__), 'golden_frames.json')
    with open(frames_path, 'r') as f:
        golden_frames = json.load(f)
    
    biz_info = {
        "name": "Golden Standard Business",
        "description": "Professional services clinic open 9 AM - 5 PM.",
        "faqs": [
            {"question": "Do you take insurance?", "answer": "Yes, most major providers."},
            {"question": "Where are you located?", "answer": "Downtown at 123 Main St."}
        ]
    }
    
    print(f"\n🚀 Starting Receptionist Benchmark ({len(golden_frames)} Frames)\n")
    print(f"{'ID':<12} | {'Score':<6} | {'Match?':<6} | {'Notes'}")
    print("-" * 60)
    
    total_score = 0
    total_matches = 0
    
    for frame in golden_frames:
        try:
            result = await run_shadow_eval(frame, biz_info)
            total_score += result.match_score
            if result.tool_match:
                total_matches += 1
            
            status = "✅" if result.tool_match else "❌"
            notes = result.discrepancies[0] if result.discrepancies else "Perfect"
            
            print(f"{frame['call_id']:<12} | {result.match_score*100:>5.1f}% | {status:<6} | {notes[:40]}")
        except Exception as e:
            print(f"{frame['call_id']:<12} | ERROR  | ❌     | {str(e)[:40]}")

    avg_score = (total_score / len(golden_frames)) * 100
    avg_match = (total_matches / len(golden_frames)) * 100
    
    print("-" * 60)
    print(f"OVERALL ACCURACY: {avg_score:.1f}%")
    print(f"TOOL CALL PARITY: {avg_match:.1f}%")
    print("-" * 60 + "\n")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
