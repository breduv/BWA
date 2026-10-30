from aiogram import Router
from aiogram.filters import Command

from app.controllers.chat import ChatController
from app.services.chat import ChatService
from app.views.telegram import TelegramView


def setup_router(service: ChatService, view: TelegramView) -> Router:
    router = Router(name="main")
    handlers = ChatController(service=service, view=view)

    router.message.register(
        handlers.handle_clear,
        Command("clear"),
    )

    router.message.register(
        handlers.handle_roast,
        Command("roast"),
    )
    router.message.register(
        handlers.handle_waifu,
        Command("waifu"),
    )
    router.message.register(
        handlers.handle_otaku,
        Command("otaku"),
    )

    return router
