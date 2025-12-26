from app.ai.llm.client import GeminiClient
from app.ai.prompts.loader import load_prompt
class CleanText:
    def __init__(self):
        self.llm = GeminiClient()
        
    def clean(self, text: str) -> str:
        prompt_template = load_prompt("summarize.prompt")
        prompt = prompt_template.replace("{{SEARCH_TEXT}}", text)
        
        return self.llm.tools(prompt)