import google.generativeai as genai
from typing import Optional
from dotenv import load_dotenv
import os

load_dotenv()

class GeminiClient:
    def __init__(
        self,
        model: str = "gemini-2.5-flash-lite",
        temperature: float = 0.0,
        max_output_tokens: int = 512,
    ):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API not found in env")
        
        genai.configure(api_key=api_key)
        
        self.model = genai.GenerativeModel(
            model_name=model,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_output_tokens,
            },
        )
    
    def generate(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)
        
        if not response or not response.text:
            raise RuntimeError("Empty response from gemini")
        
        return response.text.strip()