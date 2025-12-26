from google import genai
from google.genai import types
from typing import Optional
from dotenv import load_dotenv
import os

load_dotenv()

class GeminiClient:
    def __init__(
        self,
        main_model: str = "gemini-2.5-pro",
        tools_model: str = "gemini-2.0-flash-lite",
    ):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API not found in env")
        
        self.client = genai.Client(api_key=api_key)
        
        # Main Model
        self.main_model = main_model
        self.main_config = types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=2048
        )
        
        # tools Model
        self.tools_model = tools_model
        self.tools_config = types.GenerateContentConfig(
            temperature=0.0,
            max_output_tokens=1024
        )
    
    def generate(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model=self.main_model,
            contents=prompt,
            config=self.main_config,
        )
        
        if not response or not response.text:
            raise RuntimeError("Empty response from gemini")
        
        return response.text.strip()
    
    def tools(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model=self.tools_model,
            contents=prompt,
            config=self.tools_config,
        )
        
        if not response or not response.text:
            raise RuntimeError("Empty response from gemini")
        
        return response.text.strip()