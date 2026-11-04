from time import perf_counter

from aiogram.types import Message
from loguru import logger

from app.models.chat import ChatRequest, ReplyMode
from app.services.chat import ChatService
from app.views.telegram import TelegramView


class ChatController:
    def __init__(self, service: ChatService, view: TelegramView):
        self.service = service
        self.view = view

    async def handle_reply(
        self, message: Message, mode: ReplyMode, args: str | None = None
    ) -> None:
        source = message.reply_to_message
        text = (args or "").strip()
        reply_text = source.text if source is not None else None
        started = perf_counter()
        request_id = f"tg:{message.chat.id}:{message.message_id}"
        with logger.contextualize(request_id=request_id):
            logger.info("Request started: /{}", mode)
            answer = await self.service.generate_response(
                ChatRequest(
                    chat_id=message.chat.id,
                    message_id=message.message_id,
                    reply_message_id=source.message_id if source is not None else None,
                    text=text,
                    reply_text=reply_text,
                    mode=mode,
                )
            )
            logger.debug("Delivering response")
            await self.view.show_answer(
                source if (args is None and source is not None) else message, answer
            )
            logger.info(
                f"Request delivered ({perf_counter() - started:.1f}s)",
            )
