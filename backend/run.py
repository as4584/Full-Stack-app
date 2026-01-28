import os
import sys
import json
import time
from typing import List, Dict, Any

# Add the current directory to sys.path to ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_receptionist.agent.tasks.scenario_generator import ScenarioGenerator
from ai_receptionist.agent.tasks.tts_pipeline import TTSPipeline
from ai_receptionist.agent.tasks.whisper_pipeline import WhisperPipeline
from ai_receptionist.agent.tasks.diarizer import Diarizer
from ai_receptionist.agent.tasks.metrics_engine import MetricsEngine
from ai_receptionist.agent.tasks.report_engine import ReportEngine
from ai_receptionist.agent.tasks.improvement_engine import ImprovementEngine
from ai_receptionist.config.settings import get_settings, reset_settings
from openai import OpenAI
from dotenv import load_dotenv

# Load .env explicitly from script directory
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(env_path)

# Try parent .env
parent_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(parent_env, override=True) # Force override to ensure we get the key from parent if needed

def run_simulation():
    # Ensure API key is set to avoid immediate crash
    if "OPENAI_API_KEY" not in os.environ:
        print("WARNING: OPENAI_API_KEY not found. Using mock key.", flush=True)
        os.environ["OPENAI_API_KEY"] = "mock-key-for-testing"
    
    # Check if key is the mock key
    if os.environ["OPENAI_API_KEY"] == "mock-key-for-testing":
         print("USING MOCK KEY - API CALLS WILL FAIL", flush=True)

    settings = get_settings()
    api_key = settings.openai_api_key or os.environ.get("OPENAI_API_KEY")

    # Validate key
    print(f"DEBUG: Key being tested: {api_key[:10]}... (len={len(api_key)})", flush=True)
    try:
        test_client = OpenAI(api_key=api_key)
        test_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=1
        )
    except Exception as e:
        print(f"ERROR: Provided API key is invalid: {e}", flush=True)
        print("Falling back to MOCK KEY for simulation structure demonstration.", flush=True)
        api_key = "mock-key-for-testing"
        os.environ["OPENAI_API_KEY"] = api_key
        reset_settings() # Reload settings with new env var

    openai_client = OpenAI(api_key=api_key)
    
    # Initialize components
    scenario_gen = ScenarioGenerator()
    tts = TTSPipeline()
    whisper = WhisperPipeline()
    diarizer = Diarizer()
    metrics_engine = MetricsEngine()
    reporter = ReportEngine()
    improver = ImprovementEngine()
    
    # 1. Generate Scenarios
    print("Generating scenarios...")
    scenarios = scenario_gen.generate_scenarios()
    
    simulation_dir = os.path.join(os.getcwd(), "simulation")
    os.makedirs(simulation_dir, exist_ok=True)
    
    for i, scenario in enumerate(scenarios):
        print(f"\nRunning Scenario {scenario.get('id', i+1)}: {scenario.get('description')}")
        
        scenario_dir = os.path.join(simulation_dir, f"scenario_{scenario.get('id', i+1)}")
        audio_dir = os.path.join(scenario_dir, "audio")
        transcript_dir = os.path.join(scenario_dir, "transcripts")
        os.makedirs(audio_dir, exist_ok=True)
        os.makedirs(transcript_dir, exist_ok=True)
        
        turns = []
        conversation_history = [{"role": "system", "content": "You are a helpful AI receptionist."}]
        
        customer_script = scenario.get("customer_script", [])
        
        # Simulation Loop
        for turn_idx, customer_text in enumerate(customer_script):
            # --- Customer Turn ---
            print(f"Turn {turn_idx+1}: Customer speaking...")
            
            # TTS
            cust_audio_path = os.path.join(audio_dir, f"customer_part_{turn_idx+1}.wav")
            tts.generate_audio(customer_text, cust_audio_path, voice="alloy")
            
            # Whisper
            cust_transcript_path = os.path.join(transcript_dir, f"customer_part_{turn_idx+1}.txt")
            transcribed_text = whisper.transcribe(cust_audio_path, cust_transcript_path)
            
            turns.append({
                "turn": turn_idx+1,
                "speaker": "CUSTOMER",
                "audio_path": cust_audio_path,
                "transcript_path": cust_transcript_path,
                "original_text": customer_text
            })
            
            conversation_history.append({"role": "user", "content": transcribed_text})
            
            # --- AI Turn ---
            print(f"Turn {turn_idx+1}: AI responding...")
            
            # ChatGPT
            start_time = time.time()
            ai_response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=conversation_history
            )
            ai_text = ai_response.choices[0].message.content
            latency = (time.time() - start_time) * 1000
            
            conversation_history.append({"role": "assistant", "content": ai_text})
            
            # TTS
            ai_audio_path = os.path.join(audio_dir, f"ai_part_{turn_idx+1}.wav")
            tts.generate_audio(ai_text, ai_audio_path, voice="nova")
            
            # Whisper
            ai_transcript_path = os.path.join(transcript_dir, f"ai_part_{turn_idx+1}.txt")
            ai_transcribed_text = whisper.transcribe(ai_audio_path, ai_transcript_path)
            
            turns.append({
                "turn": turn_idx+1,
                "speaker": "AI",
                "audio_path": ai_audio_path,
                "transcript_path": ai_transcript_path,
                "original_text": ai_text,
                "latency": latency
            })
            
        # 4. Diarize
        print("Diarizing...")
        conversation_record = diarizer.build_conversation_record(turns, scenario_dir)
        
        # 5. Metrics
        print("Computing metrics...")
        latencies = [t['latency'] for t in turns if t['speaker'] == 'AI']
        metrics = metrics_engine.compute_metrics(conversation_record, scenario, scenario_dir, latencies)
        
        # 6. Report
        print("Generating report...")
        reporter.generate_report(metrics, scenario)
        
        # 7. Auto-Improvement Check
        qual = metrics.get("qualitative", {})
        ux_score = qual.get("ux_score", 0)
        
        if ux_score < 85: # Threshold from spec
             print("Auto-triggering improvement...")
             # Create dummy action items if none exist
             # In a real system, we would derive this from 'weaknesses'
             action_items = {
                 "actions": [{
                     "file": "ai_receptionist/agent/conversation_bot.py", # Target file
                     "change": f"Improve response quality. Weaknesses: {', '.join(qual.get('weaknesses', []))}"
                 }]
             }
             improver.apply_fixes(action_items)

    # Output final JSON
    final_output = {
      "status": "pipeline_ready",
      "next_step": "run_simulation",
      "components": [
        "scenario_generator",
        "tts_pipeline",
        "whisper_stt_pipeline",
        "diarizer",
        "metrics_engine",
        "terminal_report_engine",
        "self_improvement_trigger"
      ]
    }
    print(json.dumps(final_output, indent=2))

if __name__ == "__main__":
    run_simulation()
