from aiogram.types import Message

from app.models.chat import ChatRequest, ReplyMode
from app.services.chat import ChatService
from app.views.telegram import TelegramView


class ChatController:
    def __init__(self, service: ChatService, view: TelegramView):
        self.service = service
        self.view = view

    async def handle_reply(self, message: Message, mode: ReplyMode) -> None:
        source = message.reply_to_message

        if source is None:
            await self.view.show_error(
                message,
                f"Отправь /{mode} ответом на текстовое сообщение.",
            )
            return
        if source.text is None:
            await self.view.show_error(
                message,
                "Нужно ответить командой на сообщение с текстом.",
            )
            return

        answer = await self.service.generate_response(
            ChatRequest(text=source.text, mode=mode)
        )
        await self.view.show_answer(source, answer)
