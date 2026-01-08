import json
import os
from typing import Dict, List
from app.ai.llm.client import OpenAIClient
from app.ai.prompts.loader import load_prompt


class DecisionService:
    def __init__(self, llm: OpenAIClient | None = None):
        self.llm = llm or OpenAIClient()
        self.fast_response_keywords = [
            "halo", "hai", "hi", "hello", "hey",
            "pagi", "siang", "sore", "malam",
            "assalamualaikum", "assalamu'alaikum",
            "bro", "sis", "min",
            "bantu", "bantuan", "tolong",
            "urgent", "darurat", "segera", "cepat",
        ]
        self.search_keywords = [
            "data", "statistik", "berapa", "jumlah", "harga",
            "hari ini", "sekarang", "terbaru", "terkini",
            "update", "realtime", "real-time", "live",
            "kasus", "tren", "naik", "turun",
            "perbandingan", "compare",
        ]

    def _is_fast_response(self, message: str) -> bool:
        msg = (message or "").strip().lower()
        if not msg:
            return False

        
        if len(msg) <= 4 and msg in {"hi", "hai", "halo", "hey", "yo", "p"}:
            return True

        return any(k in msg for k in self.fast_response_keywords)

    def _generate_fast_response(self, user_message: str) -> str:
        
        tmpl = load_prompt("fast_response.prompt")
        prompt = (
            tmpl
            .replace("{{user_message}}", user_message)
            .replace("{{context_text}}", "")
            .replace(
                "{{user_history}}",
                "(Mode: fast-response) Jawab singkat, ramah, dan langsung membantu. ",
            )
        )
        return (self.llm.generate(prompt) or "").strip()

    def _need_search_fast(self, message: str) -> bool:
        msg = message.lower()
        return any(k in msg for k in self.search_keywords)

    def _generate_queries(self, user_message: str) -> List[str]:
        prompt_template = load_prompt("search_query.prompt")
        prompt = prompt_template.replace("{{user_message}}", user_message)

        try:
            max_tokens = int(os.getenv("DECISION_QUERY_MAX_TOKENS", "192"))
        except Exception:
            max_tokens = 192

        raw = self.llm.tools_with_limits(
            prompt,
            max_completion_tokens=max(64, max_tokens),
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
        if self._is_fast_response(user_message):
            fast = self._generate_fast_response(user_message)
            return {
                "need_search": False,
                "fast_response": True,
                "risk_level": "low",
                "request_type": "fast_response",
                "fast_response_return": fast,
                "queries": [],
            }

        if not self._need_search_fast(user_message):
            return {
                "need_search": False,
                "fast_response": False,
                "risk_level": "low",
                "request_type": "educational",
                "fast_response_return": "",
                "queries": [],
            }

        
        queries = self._generate_queries(user_message)

        return {
            "need_search": True,
            "fast_response": False,
            "risk_level": "low",
            "request_type": "informational",
            "fast_response_return": "",
            "queries": queries,
        }
