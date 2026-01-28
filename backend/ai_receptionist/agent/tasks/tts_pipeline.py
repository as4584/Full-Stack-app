import os
from openai import OpenAI
from ai_receptionist.config.settings import get_settings

class TTSPipeline:
    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key)

    def generate_audio(self, text: str, output_path: str, voice: str = "alloy", model: str = "tts-1"):
        """
        Generates audio from text using OpenAI TTS.
        
        Args:
            text: The text to convert.
            output_path: The path to save the audio file.
            voice: The voice to use (alloy, echo, fable, onyx, nova, shimmer).
            model: The TTS model to use. Spec mentions 'gpt-4o-mini-tts', defaulting to 'tts-1'.
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            response = self.client.audio.speech.create(
                model=model,
                voice=voice,
                input=text
            )
            
            response.stream_to_file(output_path)
            return True
        except Exception as e:
            print(f"Error generating TTS for {output_path}: {e}")
            return False
