from collections.abc import Mapping

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.types import BotCommand
from loguru import logger

from app.agents.graph import build_graph
from app.bot.router import setup_router
from app.clients.llm import create_llm
from app.clients.mcp import load_tools
from app.core.config import Settings
from app.core.prompts import PromptMode, load_prompt_modes
from app.services.chat import ChatService
from app.views.telegram import TelegramView


def _create_bot(settings: Settings) -> Bot:
    session = AiohttpSession(
        proxy=settings.tg_proxy.get_secret_value() if settings.tg_proxy else None
    )
    return Bot(token=settings.bot_token.get_secret_value(), session=session)


def _create_dispatcher(
    service: ChatService,
    modes: Mapping[str, PromptMode],
) -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.include_router(
        setup_router(service=service, view=TelegramView(), modes=modes)
    )
    return dispatcher


async def run_application(settings: Settings) -> None:
    """Build application dependencies and own their lifecycle during polling."""
    logger.info("Initializing application")
    modes = load_prompt_modes()
    logger.info("Configured prompt modes: {}", ", ".join(modes))

    try:
        async with create_llm(settings) as model:
            tools = await load_tools(settings)
            logger.info("MCP tools loaded: count={}", len(tools))

            graph = build_graph(
                model,
                tools,
                prompts={name: mode.prompt for name, mode in modes.items()},
            )
            dispatcher = _create_dispatcher(ChatService(graph), modes)

            async with _create_bot(settings).context() as bot:
                await bot.set_my_commands(
                    [
                        BotCommand(command=mode.name, description=mode.description)
                        for mode in modes.values()
                    ]
                )

                logger.info("Starting Telegram polling")
                await dispatcher.start_polling(
                    bot,
                    allowed_updates=dispatcher.resolve_used_update_types(),
                    close_bot_session=False,
                )
    finally:
        logger.info("Application stopped")
