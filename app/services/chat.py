from loguru import logger

from app.clients.llm import LLMClient


class ChatService:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    async def generate_response(self, messages: list[dict]) -> str:
        logger.debug(f"Generating chat response: message_count={len(messages)}")
        return await self.llm_client.generate(messages)
