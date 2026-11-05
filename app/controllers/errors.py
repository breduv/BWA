from aiogram.exceptions import (
    TelegramAPIError,
    TelegramForbiddenError,
    TelegramRetryAfter,
)
from aiogram.types import ErrorEvent
from loguru import logger

from app.core.errors import (
    EmptyRequestError,
    GenerationLimitError,
    InvalidModelResponseError,
    ModelRateLimitError,
    ModelTimeoutError,
    ModelUnavailableError,
)
from app.views.telegram import TelegramView


def _user_message(error: Exception) -> str:
    """Only explicitly approved messages may cross the presentation boundary."""
    if isinstance(error, EmptyRequestError):
        return "Добавь текст после команды или ответь командой на текстовое сообщение."
    if isinstance(error, ModelTimeoutError):
        return "Модель не успела ответить. Попробуй ещё раз позже."
    if isinstance(error, ModelRateLimitError):
        return "Сервис модели ограничил запросы. Попробуй ещё раз позже."
    if isinstance(error, ModelUnavailableError):
        return "Сервис модели сейчас недоступен. Попробуй позже."
    if isinstance(error, InvalidModelResponseError):
        return "Модель вернула некорректный ответ. Попробуй переформулировать запрос."
    if isinstance(error, GenerationLimitError):
        return (
            "Не удалось завершить ответ за допустимое число шагов. "
            "Попробуй уточнить запрос."
        )
    if isinstance(error, TelegramAPIError):
        return "Не удалось доставить ответ в Telegram полностью. Попробуй позже."
    return "Произошла внутренняя ошибка при обработке запроса."


class ErrorController:
    def __init__(self, view: TelegramView):
        self.view = view

    async def handle(self, event: ErrorEvent) -> bool:
        message = event.update.message
        request_id = (
            f"tg:{message.chat.id}:{message.message_id}"
            if message is not None
            else f"update:{event.update.update_id}"
        )
        error = event.exception
        with logger.contextualize(request_id=request_id):
            if isinstance(error, EmptyRequestError):
                logger.warning("Request rejected: {}", type(error).__name__)
            else:
                logger.opt(exception=error).error(
                    "Request failed: {}", type(error).__name__
                )

            # A blocked bot cannot reply; sending again during flood control worsens it.
            if message is None or isinstance(
                error, (TelegramForbiddenError, TelegramRetryAfter)
            ):
                return True

            text = _user_message(error)
            if not isinstance(error, EmptyRequestError):
                text += f"\nКод ошибки: {request_id}"
            try:
                await self.view.show_text(message, text)
            except Exception as notification_error:  # noqa: BLE001
                # Terminal boundary: never recursively try to report a failed report.
                logger.opt(exception=notification_error).error(
                    "Error notification failed"
                )
        return True
