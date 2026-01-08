from app.ai.decision import DecisionService
from app.ai.llm.client import OpenAIClient
from app.services.search.search_service import search_and_extract
from app.ai.prompts.loader import load_prompt
from app.ai.clean_text import CleanText
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
        self.cleantext = CleanText(llm=self.llm)
        self._profile = os.getenv("PROFILE_LATENCY", "0") == "1"
        try:
            self._debug = int(os.getenv("ORCH_DEBUG", "0"))
        except Exception:
            self._debug = 0
        self._max_search_queries = int(os.getenv("MAX_SEARCH_QUERIES", "3"))

        self._max_context_chars = int(os.getenv("ORCH_MAX_CONTEXT_CHARS", "8000"))
        self._max_history_chars = int(os.getenv("ORCH_MAX_HISTORY_CHARS", "4000"))
        self._max_source_chars = int(os.getenv("ORCH_MAX_SOURCE_CHARS", "1800"))

        llm_cache_ttl = int(os.getenv("ORCH_LLM_CACHE_TTL_S", "0"))
        self._llm_cache = TTLCache(ttl=max(1, llm_cache_ttl)) if llm_cache_ttl > 0 else None

        image_cache_ttl = int(os.getenv("ORCH_IMAGE_CACHE_TTL_S", "1800"))
        self._image_cache = TTLCache(ttl=max(1, image_cache_ttl)) if image_cache_ttl > 0 else None

    def _truncate(self, text: str, max_chars: int) -> str:
        if not text or max_chars <= 0:
            return ""
        if len(text) <= max_chars:
            return text
        return text[-max_chars:]

    def _format_history(self, chat_history: Optional[List[Dict[str, str]]]) -> str:
        if not chat_history:
            return ""
        
        parts: list[str] = []
        total = 0
        for msg in reversed(chat_history):
            role = (msg or {}).get("role", "user")
            content = (msg or {}).get("content", "")
            line = f"{role}: {content}\n"
            if total + len(line) > self._max_history_chars:
                break
            parts.append(line)
            total += len(line)
        return "".join(reversed(parts))

    def handle_chat(self, user_message: str, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
        t0 = time.perf_counter()
        decision = self.decision.run(user_message)
        t_decision = time.perf_counter()

        if self._debug:
            print(decision)

        
        if decision.get("fast_response"):
            return (decision.get("fast_response_return") or "").strip()

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

        prompt = self._build_prompt(user_message, context_blocks, chat_history)

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
        return answer

    def _build_prompt(self, user_message: str, contexts: list, chat_history="") -> str:
        seen_urls = set()
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
                
                context_text += f"- Source: {r['url']}\n"
                content_trimmed = (r.get("content", "") or "")[: self._max_source_chars]
                context_text += f"  Content: {content_trimmed}\n"
                added = True
                
        prompt = prompt_template.replace("{{user_message}}", user_message)
        
        
        if context_text != "" and len(context_text) > 8000:
            clean_prompt = self.cleantext.clean(context_text)
        else:
            clean_prompt = context_text

        clean_prompt = self._truncate(clean_prompt, self._max_context_chars)

        prompt = prompt.replace("{{context_text}}", clean_prompt)
        
        
        history_text = ""
        if isinstance(chat_history, list):
            history_text = self._format_history(chat_history)
        else:
            history_text = self._truncate(chat_history or "", self._max_history_chars)
            
        final_prompt = prompt.replace("{{user_history}}", history_text)

        return final_prompt
        
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