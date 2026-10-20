from app.clients.llm import LLMClient


class ChatService:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    async def generate_response(self, messages: list[dict]) -> str:
        return await self.llm_client.generate(messages)
