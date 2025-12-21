from app.ai.llm.client import GeminiClient

llm = GeminiClient()

print(
    llm.generate("balas dengan JSON: {\"ok\": true}")
)
