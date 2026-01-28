import asyncio
import json
import os
import sys
from typing import List, Dict, Any

# Setup PYTHONPATH to include backend dir
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ai_receptionist.services.evaluation.shadow_eval import run_shadow_eval

async def patch_benchmark():
    """
    Runs the Shadow AI against the Golden Frames and updates them to reflect 
    authoritative behaviors (like identify_self) that were added after the frames were recorded.
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
    
    print(f"\n🛠️ Patching Golden Frames ({len(golden_frames)} Frames)...\n")
    
    updated_frames = []
    
    for frame in golden_frames:
        try:
            result = await run_shadow_eval(frame, biz_info)
            
            # Map shadow decisions back to turns
            shadow_map = {d['turn_index']: d for d in result.shadow_decisions}
            
            for turn in frame['turns']:
                if turn['role'] == 'Aria' and turn['index'] in shadow_map:
                    decision = shadow_map[turn['index']]
                    
                    # If shadow AI used a tool, and it's different/more authoritative
                    if decision['shadow_tool']:
                        # We update the metadata if it's identify_self or if it matches intent
                        # For this patch, we'll selectively update identify_self to avoid 
                        # overwriting valid manual variations unless they are strictly "wrong"
                        
                        live_tools = turn.get('metadata', {}).get('tool_calls', [])
                        live_tool_names = [t['name'] for t in live_tools]
                        
                        # Fix: If shadow AI wants identify_self and we didn't have it
                        if decision['shadow_tool'] == 'identify_self' and 'identify_self' not in live_tool_names:
                            print(f"[{frame['call_id']}] Adding 'identify_self' to Turn {turn['index']}")
                            
                            if 'metadata' not in turn: turn['metadata'] = {}
                            if 'tool_calls' not in turn['metadata']: turn['metadata']['tool_calls'] = []
                            
                            # Insert at beginning
                            turn['metadata']['tool_calls'].insert(0, {
                                "name": "identify_self",
                                "arguments": decision.get('shadow_arguments', {}) # Note: we might need to capture args in shadow_eval
                            })
                            # If we don't have arguments in decision yet, we'll need to update shadow_eval.py to return them
            
            updated_frames.append(frame)
        except Exception as e:
            print(f"[{frame['call_id']}] Error: {e}")
            updated_frames.append(frame)

    with open(frames_path, 'w') as f:
        json.dump(updated_frames, f, indent=4)
        
    print(f"\n✅ Patching complete. {len(updated_frames)} frames processed.\n")

if __name__ == "__main__":
    asyncio.run(patch_benchmark())
