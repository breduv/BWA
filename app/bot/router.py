from aiogram import F, Router

from app.bot.handlers import BotHandlers
from app.services.chat import ChatService


def setup_router(chat_service: ChatService) -> Router:
    router = Router(name="main")
    handlers = BotHandlers(chat_service=chat_service)

    router.message.register(
        handlers.handle_text,
        F.text,
    )

    return router
