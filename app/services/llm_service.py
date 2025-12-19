from openai import AsyncOpenAI
import os

client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

class LLMService:
    async def chat(self, prompt: str, history: list) -> str:
        messages = []

        for h in history:
            messages.append({
                "role": h["role"],
                "content": h["content"]
            })

        messages.append({
            "role": "user",
            "content": prompt
        })

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.6,
            max_tokens=800
        )

        return response.choices[0].message.content
