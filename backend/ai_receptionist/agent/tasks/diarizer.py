import json
import os
import wave
import contextlib
from typing import List, Dict, Any

class Diarizer:
    def __init__(self):
        pass

    def get_audio_duration(self, file_path: str) -> int:
        try:
            if not os.path.exists(file_path):
                return 0
            with contextlib.closing(wave.open(file_path, 'r')) as f:
                frames = f.getnframes()
                rate = f.getframerate()
                duration = frames / float(rate)
                return int(duration * 1000) # ms
        except Exception as e:
            print(f"Error getting duration for {file_path}: {e}")
            return 0

    def build_conversation_record(self, turns: List[Dict[str, Any]], output_dir: str) -> List[Dict[str, Any]]:
        """
        Builds the diarized conversation record.
        
        Args:
            turns: List of dicts with keys: 'turn', 'speaker', 'audio_path', 'transcript_path'
            output_dir: Directory to save conversation.json and conversation.txt
            
        Returns:
            The conversation list.
        """
        conversation = []
        current_time = 0
        
        for turn in turns:
            duration = self.get_audio_duration(turn['audio_path'])
            
            record = {
                "turn": turn['turn'],
                "speaker": turn['speaker'],
                "text": "",
                "audio_duration_ms": duration,
                "start_timestamp": current_time,
                "end_timestamp": current_time + duration
            }
            
            # Read transcript if available
            if os.path.exists(turn['transcript_path']):
                with open(turn['transcript_path'], 'r', encoding='utf-8') as f:
                    record['text'] = f.read().strip()
            
            conversation.append(record)
            current_time += duration # Assuming sequential without overlap for now, or add gap
            
        # Save JSON
        json_path = os.path.join(output_dir, "conversation.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(conversation, f, indent=2)
            
        # Save TXT
        txt_path = os.path.join(output_dir, "conversation.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            for item in conversation:
                f.write(f"[{item['speaker']}] ({item['start_timestamp']}ms - {item['end_timestamp']}ms): {item['text']}\n")
                
        return conversation
