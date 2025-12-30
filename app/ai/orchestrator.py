from app.ai.decision import DecisionService
from app.ai.llm.client import OpenAIClient
from app.services.search.search_service import search_and_extract
from app.ai.prompts.loader import load_prompt
from app.ai.clean_text import CleanText
from typing import List, Dict, Optional

class Orchestrator:
    def __init__(self):
        self.decision = DecisionService()
        self.llm = OpenAIClient()
        self.cleantext = CleanText()

    def handle_chat(self, user_message: str, chat_history: Optional[List[Dict[str, str]]] = None ) -> str:
        decision = self.decision.run(user_message)

        context_blocks = []
        
        print(decision)
        if decision["need_search"]:
            for query in decision["queries"]:
                search_result = search_and_extract(query)
                context_blocks.append(search_result)

        print(context_blocks)
        prompt = self._build_prompt(user_message, context_blocks, chat_history)
        
        print(prompt)
        return self.llm.generate(prompt)

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
                context_text += f"  Content: {r['content']}\n"
                added = True
                
        prompt = prompt_template.replace("{{user_message}}", user_message)
        
        if (context_text != ""):
            clean_prompt = self.cleantext.clean(context_text)

        prompt = prompt.replace("{{context_text}}", clean_prompt)
        final_prompt = prompt.replace("{{user_history}}", chat_history or "")

        return final_prompt
