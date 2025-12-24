import json
from app.ai.llm.client import GeminiClient
from app.ai.prompts.loader import load_prompt

class DecisionService:
    def __init__(self):
        self.llm = GeminiClient(temperature=0)
    
    def run(self, user_message: str) -> dict:
        prompt_template = load_prompt("decision.prompt")
        
        prompt = prompt_template.replace(
            "{{user_message}}",
            user_message
        )
        
        raw = self.llm.generate(prompt)
        
        try:
            result = json.loads(raw)
            result["user_message"] = user_message
        except json.JSONDecodeError:
            return ValueError(
                f"Decision AI returned invalid JSON: \n{raw}"
            )
        
        if result.get("need_search") is True:
            queries = result.get("queries")
            
            if not isinstance(queries, list) or len(queries) == 0:
                raise ValueError(
                    f"Decision AI return Invalid queries: {result}"
                )
                
        return result