from collections.abc import Mapping

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.types import BotCommand
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.store.sqlite.aio import AsyncSqliteStore
from loguru import logger

from app.agents.graph import build_graph
from app.bot.router import setup_router
from app.clients.llm import create_llm
from app.clients.mcp import load_tools
from app.core.config import Settings
from app.core.prompts import BUILTIN_COMMANDS, PromptMode, load_prompts
from app.services.chat import ChatService
from app.services.threads import ThreadResolver
from app.views.telegram import TelegramView


def _create_bot(settings: Settings) -> Bot:
    session = AiohttpSession(
        proxy=settings.tg_proxy.get_secret_value() if settings.tg_proxy else None
    )
    return Bot(token=settings.bot_token.get_secret_value(), session=session)


def _create_dispatcher(
    service: ChatService,
    view: TelegramView,
    modes: Mapping[str, PromptMode],
) -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.include_router(setup_router(service=service, view=view, modes=modes))
    return dispatcher


async def run_application(settings: Settings) -> None:
    """Build application dependencies and own their lifecycle during polling."""
    prompts = load_prompts()
    modes = prompts.modes
    logger.info(
        f"Starting bot: {settings.model}",
    )

    try:
        async with (
            create_llm(settings) as model,
            AsyncSqliteSaver.from_conn_string(
                "data/checkpoints.sqlite3"
            ) as checkpointer,
            AsyncSqliteStore.from_conn_string("data/links.sqlite3") as store,
        ):
            tools = await load_tools(settings)

            await store.setup()

            graph = build_graph(
                model,
                tools,
                prompts=prompts,
                checkpointer=checkpointer,
            )
            dispatcher = _create_dispatcher(
                ChatService(graph, ThreadResolver(store), settings.check_history),
                TelegramView(store),
                modes,
            )

            async with _create_bot(settings).context() as bot:
                commands = BUILTIN_COMMANDS | {
                    mode.name: mode.description for mode in modes.values()
                }
                await bot.set_my_commands(
                    [
                        BotCommand(command=name, description=description)
                        for name, description in commands.items()
                    ]
                )
                logger.info("Polling started")
                await dispatcher.start_polling(
                    bot,
                    allowed_updates=dispatcher.resolve_used_update_types(),
                    close_bot_session=False,
                )
    finally:
        logger.info("Application stopped")
