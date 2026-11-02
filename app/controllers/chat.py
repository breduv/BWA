from time import perf_counter

from aiogram.exceptions import TelegramAPIError
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
        logger.info(
            f"Request {request_id}: /{mode}",
        )
        stage = "generation"
        try:
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
            stage = "delivery"
            await self.view.show_answer(
                source if (args is None and source is not None) else message, answer
            )
            logger.info(
                f"Request {request_id}: delivered ({perf_counter() - started:.1f}s)",
            )
        except Exception as exc:  # noqa: BLE001
            # Request boundary: log unexpected failures and notify the user.
            reason = " ".join(str(exc).split())[:250]
            logger.error(
                f"Request {request_id}: {stage} failed: {type(exc).__name__}: {reason}",
            )
            logger.opt(exception=exc).debug(f"Request {request_id}: traceback")
            try:
                await self.view.show_error(
                    message, "Не удалось обработать запрос. Попробуй ещё раз."
                )
            except TelegramAPIError as delivery_error:
                logger.error(
                    f"Request {request_id}: error notification failed: "
                    f"{type(delivery_error).__name__}",
                )
