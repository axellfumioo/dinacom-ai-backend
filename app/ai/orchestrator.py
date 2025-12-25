# app/ai/orchestrator.py
from app.ai.decision import DecisionService
from app.ai.llm.client import GeminiClient
from app.services.search.search_service import search_and_extract
from app.ai.prompts.loader import load_prompt

class Orchestrator:
    def __init__(self):
        self.decision = DecisionService()
        self.llm = GeminiClient()

    def handle_chat(self, user_message: str) -> str:
        decision = self.decision.run(user_message)

        context_blocks = []
        
        print(decision)
        if decision["need_search"]:
            for query in decision["queries"]:
                search_result = search_and_extract(query)
                context_blocks.append(search_result)

        # print(context_blocks)
        prompt = self._build_prompt(user_message, context_blocks)
        
        # return self.llm.generate(prompt)
        return prompt

    def _build_prompt(self, user_message: str, contexts: list) -> str:
        seen_urls = set()
        context_text = ""
        
        prompt_template = load_prompt("answer.prompt")
        
        for ctx in contexts:
            context_text += f"\n[QUERY]: {ctx['query']}\n"
            for r in ctx["results"]:
                url = r["url"]
                content = r.get("content", "")
                if url in seen_urls:
                    continue
                
                if(not content or "ERROR extracting" in content or len(content) < 128):
                    continue
                
                seen_urls.add(url)
                
                context_text += f"- Source: {r['url']}\n"
                context_text += f"  Content: {r['content']}\n"
        
        prompt = prompt_template.replace("{{user_message}}", user_message)
        prompt = prompt.replace("{{context_text}}", context_text)

        return prompt
