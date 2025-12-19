from openai import AsyncOpenAI
import os

client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

class VisionService:
    async def analyze(self, image_url: str) -> str:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analyze this image and describe it briefly."},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ],
            max_tokens=300
        )

        return response.choices[0].message.content
