from google import genai
from google.genai import types
from typing import Optional
from dotenv import load_dotenv
import os

load_dotenv()

class GeminiClient:
    def __init__(
        self,
        model_name: str = "gemini-2.5-flash-lite",
        temperature: float = 0.1,
        max_output_tokens: int = 1024,
    ):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API not found in env")
        
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens
        )
    
    def generate(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=self.config,
        )
        
        if not response or not response.text:
            raise RuntimeError("Empty response from gemini")
        
        return response.text.strip()