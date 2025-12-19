from app.prompts.orchestrator import build_chat_prompt

class AIOrchestrator:
    def __init__(self, vision, llm):
        self.vision = vision
        self.llm = llm

    async def chat(
        self,
        message: str,
        history: list,
        image_url: str | None = None
    ):
        image_context = None

        if image_url:
            image_context = await self.vision.analyze(image_url)

        prompt = build_chat_prompt(
            message=message,
            image_context=image_context
        )

        return await self.llm.chat(
            prompt=prompt,
            history=history
        )
