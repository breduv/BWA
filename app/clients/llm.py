from openai import AsyncOpenAI, DefaultAsyncHttpxClient

from app.core.config import Settings


class LLMClient:
    def __init__(self, settings: Settings) -> None:
        self.model = settings.model

        self.client = AsyncOpenAI(
            base_url=settings.api_base,
            api_key=settings.api_key.get_secret_value(),
            timeout=60.0,
            http_client=(
                DefaultAsyncHttpxClient(proxy=settings.proxy.get_secret_value())
                if settings.proxy is not None
                else None
            ),
        )

    async def generate(self, messages: list[dict]) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return response.choices[0].message.content
