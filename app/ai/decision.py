import json
from typing import Dict, List
from app.ai.llm.client import OpenAIClient
from app.ai.prompts.loader import load_prompt


class DecisionService:
    def __init__(self):
        self.llm = OpenAIClient()
        self.search_keywords = [
            "data", "statistik", "berapa", "jumlah", "harga",
            "hari ini", "sekarang", "terbaru", "terkini",
            "update", "realtime", "real-time", "live",
            "kasus", "tren", "naik", "turun",
            "perbandingan", "compare",
        ]

    def _need_search_fast(self, message: str) -> bool:
        msg = message.lower()
        return any(k in msg for k in self.search_keywords)

    def _generate_queries(self, user_message: str) -> List[str]:
        prompt_template = load_prompt("search_query.prompt")
        prompt = prompt_template.replace("{{user_message}}", user_message)

        raw = self.llm.tools_with_limits(
            prompt,
            max_completion_tokens=512,
            response_format={"type": "json_object"},
        )

        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            raise ValueError(f"Query AI returned invalid JSON:\n{raw}")

        queries = result.get("queries", [])
        if not isinstance(queries, list):
            raise ValueError("queries must be a list")

        return [
            q.strip()
            for q in queries
            if isinstance(q, str) and len(q.strip()) >= 3
        ]

    def run(self, user_message: str) -> Dict:
        
        if not self._need_search_fast(user_message):
            return {
                "need_search": False,
                "risk_level": "low",
                "request_type": "educational",
                "queries": [],
            }

        
        queries = self._generate_queries(user_message)

        return {
            "need_search": True,
            "risk_level": "low",
            "request_type": "informational",
            "queries": queries,
        }
