from openai import OpenAI
from google.genai import types
from dotenv import load_dotenv
from app.ai.llm.root_prompts.loader import load_prompt
import os

load_dotenv()

class OpenAIClient:
    def __init__(
        self,
        main_model: str = "gpt-5-mini",
        tools_model: str = "gpt-5-nano",
    ):
        api_key = os.getenv("OPENAI_API")
        if not api_key:
            raise RuntimeError("OPENAI_API not found in env")
        
        self.client = OpenAI(api_key=api_key)
        
        # Main Model
        self.main_model = main_model
        self.main_config = {
            "temperature": 0.3,
            "max_tokens": 2048,
        }
        
        # tools Model
        self.tools_model = tools_model
        self.tools_config = {
            "temperature": 0.0,
            "max_output_tokens": 1024
        }
    
    def generate(self, prompt: str) -> str:
        root_prompt = load_prompt("health.prompt")
        response = self.client.chat.completions.create(
            model=self.main_model,
            messages=[
                {"role": "system", "content": root_prompt},
                {"role": "user", "content": prompt}
            ],
            **self.main_config
        )
        
        if not response or not response.choices:
            raise RuntimeError("Empty response from OpenAI")
        
        return response.choices[0].message.content.strip()
    
    def tools(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.tools_model,
            messages=[
                {"role": "user", "content": prompt}
            ]
            **self.tools_config
        )
            
        if not response or not response.text:
            raise RuntimeError("Empty response from OpenAI")
        
        return response.choices[0].message.content.strip()