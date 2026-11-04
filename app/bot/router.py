from collections.abc import Awaitable, Callable, Mapping

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from app.controllers.chat import ChatController
from app.controllers.errors import ErrorController
from app.core.prompts import PromptMode
from app.services.chat import ChatService
from app.views.telegram import TelegramView


def setup_router(
    service: ChatService,
    view: TelegramView,
    modes: Mapping[str, PromptMode],
) -> Router:
    router = Router(name="main")
    handlers = ChatController(service=service, view=view)
    router.errors.register(ErrorController(view).handle)

    def create_handler(mode: str) -> Callable[..., Awaitable[None]]:
        async def handle(message: Message, command: CommandObject) -> None:
            await handlers.handle_reply(message, mode=mode, args=command.args)

        return handle

    for name in modes:
        router.message.register(create_handler(name), Command(name))

    return router
