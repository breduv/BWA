from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from loguru import logger

from app.bot.router import setup_router
from app.clients.llm import LLMClient
from app.core.config import Settings
from app.services.chat import ChatService


async def run_application(settings: Settings) -> None:
    logger.debug(
        f"Initializing Telegram session: proxy_enabled={settings.tg_proxy is not None}"
    )
    session = AiohttpSession(
        proxy=settings.tg_proxy.get_secret_value() if settings.tg_proxy else None
    )
    bot = Bot(token=settings.bot_token.get_secret_value(), session=session)
    dispatcher = Dispatcher()
    logger.debug("Telegram bot and dispatcher initialized")

    llm_client = LLMClient(settings)
    chat_service = ChatService(llm_client)

    router = setup_router(chat_service=chat_service)
    dispatcher.include_router(router)
    logger.debug("Main router attached to dispatcher")

    try:
        logger.info("Starting Telegram bot")
        await dispatcher.start_polling(bot)
    finally:
        logger.info("Stopping Telegram bot")
        await bot.session.close()
        logger.info("Telegram bot stopped")
