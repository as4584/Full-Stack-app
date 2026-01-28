import os
from openai import OpenAI
from ai_receptionist.config.settings import get_settings

class WhisperPipeline:
    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key)

    def transcribe(self, audio_path: str, output_path: str) -> str:
        """
        Transcribes audio file to text using OpenAI Whisper.
        
        Args:
            audio_path: Path to the input audio file.
            output_path: Path to save the transcript text.
            
        Returns:
            The transcribed text.
        """
        try:
            if not os.path.exists(audio_path):
                print(f"Audio file not found: {audio_path}")
                return ""

            with open(audio_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            
            text = transcript.text
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text)
                
            return text
        except Exception as e:
            print(f"Error transcribing {audio_path}: {e}")
            return ""
