from app.ai.decision import DecisionService
from app.ai.llm.client import OpenAIClient
from app.services.search.search_service import search_and_extract
from app.ai.prompts.loader import load_prompt
# from app.ai.clean_text import CleanText
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import time
import hashlib
import json


from app.services.search.cache import TTLCache

class Orchestrator:
    def __init__(self):
        self.llm = OpenAIClient()
        self.decision = DecisionService(llm=self.llm)
        # self.cleantext = CleanText(llm=self.llm)
        self._profile = os.getenv("PROFILE_LATENCY", "0") == "1"
        try:
            self._debug = int(os.getenv("ORCH_DEBUG", "1"))
        except Exception:
            self._debug = 0
        self._max_search_queries = int(os.getenv("MAX_SEARCH_QUERIES", "2"))

        self._max_context_chars = int(os.getenv("ORCH_MAX_CONTEXT_CHARS", "8000"))
        self._max_history_chars = int(os.getenv("ORCH_MAX_HISTORY_CHARS", "4000"))
        self._max_source_chars = int(os.getenv("ORCH_MAX_SOURCE_CHARS", "1800"))

        llm_cache_ttl = int(os.getenv("ORCH_LLM_CACHE_TTL_S", "0"))
        self._llm_cache = TTLCache(ttl=max(1, llm_cache_ttl)) if llm_cache_ttl > 0 else None

        image_cache_ttl = int(os.getenv("ORCH_IMAGE_CACHE_TTL_S", "1800"))
        self._image_cache = TTLCache(ttl=max(1, image_cache_ttl)) if image_cache_ttl > 0 else None

        user_insight_cache_ttl = int(os.getenv("ORCH_USER_INSIGHT_CACHE_TTL_S", "900"))
        self._user_insight_cache = (
            TTLCache(ttl=max(1, user_insight_cache_ttl)) if user_insight_cache_ttl > 0 else None
        )

    def _truncate(self, text: str, max_chars: int) -> str:
        if not text or max_chars <= 0:
            return ""
        if len(text) <= max_chars:
            return text
        return text[-max_chars:]

    def _format_history(self, chat_history: Optional[List[Dict[str, str]]]) -> str:
        if not chat_history:
            return ""

        header = "[CHAT_HISTORY_START] (oldest -> newest)\n"
        footer = "[CHAT_HISTORY_END]\n"
        
        parts_from_tail: list[str] = []
        total = len(header) + len(footer)
        truncated = False

        n = len(chat_history)
        for idx_from_end, msg in enumerate(reversed(chat_history), start=1):
            original_index = n - idx_from_end + 1  # 1-based index in original list
            role = (msg or {}).get("role", "user")
            content = ((msg or {}).get("content", "") or "").strip()

            entry = (
                f"--- message {original_index}/{n} ---\n"
                f"role: {role}\n"
                f"content:\n{content}\n"
            )

            if total + len(entry) > self._max_history_chars:
                truncated = True
                break

            parts_from_tail.append(entry)
            total += len(entry)

        parts = list(reversed(parts_from_tail))
        if truncated:
            parts.insert(0, "--- (older messages omitted due to ORCH_MAX_HISTORY_CHARS) ---\n")

        return header + "".join(parts) + footer

    def handle_chat(self, user_message: str, chat_history: Optional[List[Dict[str, str]]] = None) -> dict:
        t0 = time.perf_counter()
        history_text = self._format_history(chat_history) if isinstance(chat_history, list) else (chat_history or "")
        decision = self.decision.run(user_message, user_history=history_text)
        t_decision = time.perf_counter()

        if self._debug:
            print(decision)

        
        if decision.get("fast_response") and not decision.get("need_search"):
            return {
                "answer": (decision.get("fast_response_return") or "").strip(),
                "sources": [],
                "decision": decision,
            }

        context_blocks = []
        
        if decision["need_search"]:
            queries = decision.get("queries") or []
            if self._max_search_queries > 0:
                queries = queries[: self._max_search_queries]

            with ThreadPoolExecutor(max_workers=min(5, max(1, len(queries)))) as executor:
                future_to_query = {executor.submit(search_and_extract, query): query for query in queries}
                for future in as_completed(future_to_query):
                    try:
                        search_result = future.result()
                        context_blocks.append(search_result)
                    except Exception as exc:
                        print(f'Search generated an exception: {exc}')

        if self._debug:
            print(context_blocks)

        t_search = time.perf_counter()

        prompt, sources = self._build_prompt(user_message, context_blocks, chat_history)

        if self._debug:
            print(prompt)

        t_prompt = time.perf_counter()
        
        if self._llm_cache is not None:
            key = hashlib.sha256(prompt.encode("utf-8", errors="ignore")).hexdigest()
            cached = self._llm_cache.get(key)
            if cached:
                answer = cached
            else:
                answer = self.llm.generate(prompt)
                self._llm_cache.set(key, answer)
        else:
            answer = self.llm.generate(prompt)
        t_done = time.perf_counter()

        if self._profile:
            print(
                "LATENCY(ms): "
                f"decision={(t_decision - t0) * 1000:.0f} "
                f"search={(t_search - t_decision) * 1000:.0f} "
                f"prompt={(t_prompt - t_search) * 1000:.0f} "
                f"llm={(t_done - t_prompt) * 1000:.0f} "
                f"total={(t_done - t0) * 1000:.0f}"
            )
        
        return {
            "answer": answer,
            "sources": sources,
            "decision": decision,
        }

    def _build_prompt(self, user_message: str, contexts: list, chat_history="") -> tuple[str, list[dict]]:
        seen_urls = set()
        sources_list = []
        context_text = ""
        clean_prompt = ""
        
        prompt_template = load_prompt("answer.prompt")
        
        for ctx in contexts:
            added = False
            
            context_text += f"\n[QUERY]: {ctx['query']}\n"
            
            for r in ctx["results"]:
                if(added):
                    break
                
                url = r["url"]
                content = r.get("content", "")
                
                if(url in seen_urls or not content or "ERROR extracting" in content or len(content) < 128):
                    continue
                
                seen_urls.add(url)
                sources_list.append({
                    "url": url,
                    "title": r.get("title", ""),
                    "query": ctx['query']
                })
                
                context_text += f"- Source: {r['url']}\n"
                content_trimmed = (r.get("content", "") or "")[: self._max_source_chars]
                context_text += f"  Content: {content_trimmed}\n"
                added = True
                
        prompt = prompt_template.replace("{{user_message}}", user_message)
        
        
        # if context_text != "" and len(context_text) > 8000:
        #     clean_prompt = self.cleantext.clean(context_text)
        # else:
        clean_prompt = context_text

        clean_prompt = self._truncate(clean_prompt, self._max_context_chars)

        prompt = prompt.replace("{{context_text}}", clean_prompt)
        
        
        history_text = ""
        if isinstance(chat_history, list):
            history_text = self._format_history(chat_history)
        else:
            history_text = self._truncate(chat_history or "", self._max_history_chars)
            
        final_prompt = prompt.replace("{{user_history}}", history_text)

        return final_prompt, sources_list
        
    def handle_scan(self, image_url: str) -> dict:
        t0 = time.perf_counter()
        
        
        if self._image_cache is not None:
            cache_key = hashlib.sha256(image_url.encode("utf-8", errors="ignore")).hexdigest()
            cached = self._image_cache.get(cache_key)
            if cached:
                if self._profile:
                    print(f"LATENCY(ms): image_scan=0 (cached) total={(time.perf_counter() - t0) * 1000:.0f}")
                return cached
        
        t_prompt = time.perf_counter()
        prompt = load_prompt("analyze_image.prompt")
        t_llm = time.perf_counter()
        raw = self.llm.image_scan(image_url, prompt)
        t_parse = time.perf_counter()

        try:
            result = json.loads(raw)
            
            
            if self._image_cache is not None:
                self._image_cache.set(cache_key, result)
            
            t_done = time.perf_counter()
            if self._profile:
                print(
                    f"LATENCY(ms): "
                    f"prompt={(t_llm - t_prompt) * 1000:.0f} "
                    f"llm={(t_parse - t_llm) * 1000:.0f} "
                    f"parse={(t_done - t_parse) * 1000:.0f} "
                    f"total={(t_done - t0) * 1000:.0f}"
                )
            
            return result
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON from image_scan:\n{raw}")

    def handle_user_insight(self, payload: dict) -> dict:
        if not isinstance(payload, dict):
            raise ValueError("payload must be a dict")

        t0 = time.perf_counter()

        payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        if self._user_insight_cache is not None:
            cache_key = hashlib.sha256(payload_json.encode("utf-8", errors="ignore")).hexdigest()
            cached = self._user_insight_cache.get(cache_key)
            if cached:
                if self._profile:
                    print(
                        f"LATENCY(ms): user_insight=0 (cached) total={(time.perf_counter() - t0) * 1000:.0f}"
                    )
                return cached
        else:
            cache_key = None

        prompt_tmpl = load_prompt("user_insight.prompt")
        prompt = prompt_tmpl.replace(
            "{{payload_json}}",
            json.dumps(payload, ensure_ascii=False, indent=2),
        )

        t_llm = time.perf_counter()
        raw = self.llm.tools_with_limits(
            prompt,
            max_completion_tokens=int(os.getenv("USER_INSIGHT_MAX_TOKENS", "512")),
            response_format={"type": "json_object"},
        )
        t_parse = time.perf_counter()

        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON from user_insight:\n{raw}")

        if not isinstance(result, dict):
            raise ValueError("user_insight must return a JSON object")

        required = [
            "health_score",
            "personal_ai_insight",
            "ai_important_notice",
            "confidence_level",
        ]
        missing = [k for k in required if k not in result]
        if missing:
            raise ValueError(f"user_insight missing keys: {missing}")

        def _to_int(v) -> int:
            if isinstance(v, bool):
                raise ValueError("invalid int")
            if isinstance(v, int):
                return v
            if isinstance(v, float):
                return int(round(v))
            if isinstance(v, str) and v.strip().isdigit():
                return int(v.strip())
            raise ValueError("invalid int")

        try:
            health_score = max(0, min(100, _to_int(result.get("health_score"))))
            confidence_level = max(0, min(100, _to_int(result.get("confidence_level"))))
        except Exception as e:
            raise ValueError(f"Invalid numeric fields in user_insight: {e}")

        personal_ai_insight = str(result.get("personal_ai_insight") or "").strip()
        ai_important_notice = str(result.get("ai_important_notice") or "").strip()

        normalized = {
            "health_score": health_score,
            "personal_ai_insight": personal_ai_insight,
            "ai_important_notice": ai_important_notice,
            "confidence_level": confidence_level,
        }

        if self._user_insight_cache is not None and cache_key is not None:
            self._user_insight_cache.set(cache_key, normalized)

        t_done = time.perf_counter()
        if self._profile:
            print(
                f"LATENCY(ms): "
                f"llm={(t_parse - t_llm) * 1000:.0f} "
                f"parse={(t_done - t_parse) * 1000:.0f} "
                f"total={(t_done - t0) * 1000:.0f}"
            )

        return normalized