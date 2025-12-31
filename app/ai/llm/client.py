from openai import OpenAI
from google.genai import types
from dotenv import load_dotenv
from app.ai.llm.root_prompts.loader import load_prompt
import os

load_dotenv()

class OpenAIClient:
    def __init__(
        self,
        main_model: str = "gpt-4o-mini",
        tools_model: str = "gpt-4o-mini",
    ):
        api_key = os.getenv("OPENAI_API")
        if not api_key:
            raise RuntimeError("OPENAI_API not found in env")

        try:
            timeout_s = float(os.getenv("OPENAI_TIMEOUT_S", "6"))
        except Exception:
            timeout_s = 6.0

        try:
            max_retries = int(os.getenv("OPENAI_MAX_RETRIES", "0"))
        except Exception:
            max_retries = 0

        self._timeout_s = max(0.1, timeout_s)
        self._max_retries = max(0, max_retries)
        
        
        self.client = OpenAI(api_key=api_key, timeout=self._timeout_s, max_retries=self._max_retries)
        
        
        main_model = os.getenv("OPENAI_MAIN_MODEL", main_model)
        tools_model = os.getenv("OPENAI_TOOLS_MODEL", tools_model)

        
        self.main_model = main_model
        self.fallback_model = os.getenv("OPENAI_FALLBACK_MODEL", "gpt-4o-mini")

        try:
            main_max_tokens = int(os.getenv("OPENAI_MAIN_MAX_TOKENS", "768"))
        except Exception:
            main_max_tokens = 768

        self.main_config = {
            "max_completion_tokens": main_max_tokens,
        }
        
        
        self.tools_model = tools_model
        self.tools_config = {
            "max_completion_tokens": 2048,
        }
    
    def generate(self, prompt: str) -> str:
        root_prompt = load_prompt("health.prompt")
        response = self.client.chat.completions.create(
            model=self.main_model,
            messages=[
                {"role": "system", "content": root_prompt},
                {"role": "user", "content": prompt}
            ],
            **self.main_config,
        )
        
        if not response or not response.choices:
            raise RuntimeError("Empty response from OpenAI")
        
        content = response.choices[0].message.content
        if content:
            return content.strip()

        
        retry = self.client.chat.completions.create(
            model=self.fallback_model,
            messages=[
                {"role": "system", "content": root_prompt},
                {"role": "user", "content": prompt},
            ],
            max_completion_tokens=self.main_config.get("max_completion_tokens", 768),
        )

        if not retry or not retry.choices or not retry.choices[0].message.content:
            raise RuntimeError("Empty response from OpenAI")

        return retry.choices[0].message.content.strip()
    
    def tools(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.tools_model,
            messages=[{"role": "user", "content": prompt}],
            **self.tools_config,
        )
            
        if not response or not response.choices:
            raise RuntimeError("Empty response from OpenAI")
        
        content = response.choices[0].message.content
        if content:
            return content.strip()

        
        
        retry = self.client.chat.completions.create(
            model=self.main_model,
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=self.tools_config.get("max_completion_tokens", 2048),
        )

        if not retry or not retry.choices or not retry.choices[0].message.content:
            raise RuntimeError(f"Empty content from OpenAI. Response: {response}")

        return retry.choices[0].message.content.strip()

    def tools_with_limits(
        self,
        prompt: str,
        *,
        max_completion_tokens: int,
        response_format: dict | None = None,
    ) -> str:
        config = dict(self.tools_config)
        config["max_completion_tokens"] = max_completion_tokens

        if response_format is not None:
            config["response_format"] = response_format

        response = self.client.chat.completions.create(
            model=self.tools_model,
            messages=[{"role": "user", "content": prompt}],
            **config,
        )

        if not response or not response.choices:
            raise RuntimeError("Empty response from OpenAI")

        content = response.choices[0].message.content
        if content:
            return content.strip()

        
        retry_config = dict(config)
        retry = self.client.chat.completions.create(
            model=self.main_model,
            messages=[{"role": "user", "content": prompt}],
            **retry_config,
        )

        if not retry or not retry.choices or not retry.choices[0].message.content:
            raise RuntimeError(f"Empty content from OpenAI. Response: {response}")

        return retry.choices[0].message.content.strip()