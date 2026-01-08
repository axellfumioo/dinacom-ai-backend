from openai import OpenAI
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
            
            timeout_s = float(os.getenv("OPENAI_TIMEOUT_S", "60"))
        except Exception:
            timeout_s = 60.0

        try:
            
            max_retries = int(os.getenv("OPENAI_MAX_RETRIES", "1"))
        except Exception:
            max_retries = 1

        self._timeout_s = max(0.1, timeout_s)
        self._max_retries = max(0, max_retries)
        
        
        self.client = OpenAI(api_key=api_key, timeout=self._timeout_s, max_retries=self._max_retries)
        
        
        main_model = os.getenv("OPENAI_MAIN_MODEL", main_model)
        tools_model = os.getenv("OPENAI_TOOLS_MODEL", tools_model)

        
        self.main_model = main_model
        self.fallback_model = os.getenv("OPENAI_FALLBACK_MODEL", "gpt-4o-mini")

        try:
            main_temperature = float(os.getenv("OPENAI_MAIN_TEMPERATURE", "0"))
        except Exception:
            main_temperature = 0.0

        try:
            main_max_tokens = int(os.getenv("OPENAI_MAIN_MAX_TOKENS", "384"))
        except Exception:
            main_max_tokens = 384

        self.main_config = {
            "max_completion_tokens": main_max_tokens,
            "temperature": main_temperature,
        }
        
        
        self.tools_model = tools_model

        try:
            tools_temperature = float(os.getenv("OPENAI_TOOLS_TEMPERATURE", "0"))
        except Exception:
            tools_temperature = 0.0

        try:
            tools_max_tokens = int(os.getenv("OPENAI_TOOLS_MAX_TOKENS", "2048"))
        except Exception:
            tools_max_tokens = 2048

        self.tools_config = {
            "max_completion_tokens": tools_max_tokens,
            "temperature": tools_temperature,
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
            temperature=0,
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
        config["temperature"] = 0

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
        retry_config["temperature"] = 0
        retry = self.client.chat.completions.create(
            model=self.main_model,
            messages=[{"role": "user", "content": prompt}],
            **retry_config,
        )

        if not retry or not retry.choices or not retry.choices[0].message.content:
            raise RuntimeError(f"Empty content from OpenAI. Response: {response}")

        return retry.choices[0].message.content.strip()
    
    def image_scan(
        self,
        image_url: str,
        prompt: str = "Jelaskan isi gambar ini secara singkat dan faktual."
    ) -> str:
        
        image_model = os.getenv("OPENAI_IMAGE_MODEL", "gpt-4o-mini")
        try:
            image_max_tokens = int(os.getenv("OPENAI_IMAGE_MAX_TOKENS", "256"))
        except Exception:
            image_max_tokens = 256

        response = self.client.chat.completions.create(
            model=image_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url}
                        }
                    ]
                }
            ],
            max_completion_tokens=image_max_tokens,
            temperature=0,
            response_format={"type": "json_object"},
        )

        if not response or not response.choices:
            raise RuntimeError("Empty response from OpenAI (image_scan)")

        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("Empty content from OpenAI (image_scan)")

        return content.strip()
