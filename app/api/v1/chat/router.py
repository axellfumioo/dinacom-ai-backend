from app.ai.llm.client import OpenAIClient

llm = OpenAIClient()

print(
    llm.generate("balas dengan JSON: {\"ok\": true}")
)
