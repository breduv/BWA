from time import perf_counter

from loguru import logger
from openai import AsyncOpenAI, DefaultAsyncHttpxClient

from app.core.config import Settings


class LLMClient:
    def __init__(self, settings: Settings) -> None:
        self.model = settings.model
        logger.debug(
            f"Initializing LLM client: model={self.model}, "
            f"proxy_enabled={settings.proxy is not None}"
        )

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
        logger.debug(f"LLM client initialized: model={self.model}")

    async def generate(self, messages: list[dict]) -> str:
        logger.debug(f"Preparing LLM request: message_count={len(messages)}")
        logger.info(f"Sending LLM request: model={self.model}")
        started_at = perf_counter()
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        content = response.choices[0].message.content
        logger.info(
            f"LLM response received: model={self.model}, "
            f"duration_ms={(perf_counter() - started_at) * 1000:.0f}"
        )
        logger.debug(f"LLM response content length: {len(content or '')}")
        return content
