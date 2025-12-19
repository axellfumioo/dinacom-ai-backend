from openai import AsyncOpenAI
import os

client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

class AIFoodScanOrchestrator:
    async def scan_food(self, image_url: str) -> dict:
        """
        Scan food image and return nutritional information in JSON format
        """
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are a nutritional analysis assistant. Analyze the food in the image and return a JSON response with the following structure:
{
  "food_name": "name of the food",
  "calories": estimated_calories_number,
  "protein": protein_in_grams,
  "carbohydrates": carbs_in_grams,
  "fat": fat_in_grams,
  "ingredients": ["ingredient1", "ingredient2"],
  "description": "brief description of the food"
}

Always respond with valid JSON only, no additional text."""
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analyze this food image and provide nutritional information."},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ],
            max_tokens=500,
            response_format={"type": "json_object"}
        )

        return response.choices[0].message.content
