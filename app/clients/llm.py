from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx
from langchain_openai import ChatOpenAI

from app.core.config import Settings


@asynccontextmanager
async def create_llm(
    settings: Settings,
) -> AsyncGenerator[ChatOpenAI, None]:
    async with httpx.AsyncClient(
        proxy=(settings.proxy.get_secret_value() if settings.proxy else None),
        timeout=60.0,
    ) as http_client:
        model = ChatOpenAI(
            model=settings.model,
            base_url=settings.api_base,
            api_key=settings.api_key,
            http_async_client=http_client,
            use_responses_api=False,
            timeout=60.0,
            max_retries=1,
        )

        yield model
