from collections.abc import Awaitable, Callable, Mapping

from aiogram import Router
from aiogram.filters import Command, CommandObject, CommandStart
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

    async def start(message: Message) -> None:
        await view.show_text(
            message,
            "Привет! Я Webwit, помощник с веб-поиском. "
            "Открой /help, чтобы посмотреть режимы и узнать, как задать вопрос.",
        )

    async def help_command(message: Message) -> None:
        mode_list = "\n".join(
            f"/{mode.name} — {mode.description}" for mode in modes.values()
        )
        await view.show_text(
            message,
            "Выбери режим и напиши вопрос после команды. "
            "Можно также отправить команду в ответ на текстовое сообщение.\n\n"
            f"Доступные режимы\n{mode_list}",
        )

    router.message.register(start, CommandStart())
    router.message.register(help_command, Command("help"))

    def create_handler(mode: str) -> Callable[..., Awaitable[None]]:
        async def handle(message: Message, command: CommandObject) -> None:
            await handlers.handle_reply(message, mode=mode, args=command.args)

        return handle

    for name in modes:
        router.message.register(create_handler(name), Command(name))

    return router
