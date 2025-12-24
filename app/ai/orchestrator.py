# app/ai/orchestrator.py
from app.ai.decision import DecisionService
from app.ai.llm.client import GeminiClient
from app.services.search.search_service import search_and_extract


class Orchestrator:
    def __init__(self):
        self.decision = DecisionService()
        self.llm = GeminiClient()

    def handle_chat(self, user_message: str) -> str:
        # 1. Decision dulu
        decision = self.decision.run(user_message)

        context_blocks = []

        # 2. Kalau butuh search
        if decision["need_search"]:
            for query in decision["queries"]:
                search_result = search_and_extract(query)
                context_blocks.append(search_result)

        # 3. Gabung context jadi prompt
        prompt = self._build_prompt(user_message, context_blocks)

        # 4. Kirim ke LLM
        return self.llm.generate(prompt)

    def _build_prompt(self, user_message: str, contexts: list) -> str:
        context_text = ""

        for ctx in contexts:
            context_text += f"\n[QUERY]: {ctx['query']}\n"
            for r in ctx["results"]:
                context_text += f"- Source: {r['url']}\n"
                context_text += f"  Content: {r['content']}\n"

        return f"""
Kamu adalah AI assistant yang menjawab berdasarkan data aktual.

CONTEXT:
{context_text}

USER QUESTION:
{user_message}

Jawab secara ringkas, jelas, dan faktual.
"""
