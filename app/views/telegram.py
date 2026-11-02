from collections.abc import Iterator
from html import escape

from aiogram.enums import ParseMode
from aiogram.types import InputRichMessage, Message, ReplyParameters
from langgraph.store.base import BaseStore
from loguru import logger

from app.models.chat import ChatHistoryEntry, ChatResponse


def _history_text(history: list[ChatHistoryEntry]) -> str:
    labels = {
        "user": "Пользователь",
        "assistant": "Ассистент",
        "tool_call": "Вызов",
        "tool_result": "Результат",
    }
    rows = []
    for entry in history:
        label = labels[entry.role]
        preview = " ".join(entry.text.split()) or "Нет текстового результата"
        if len(preview) > 220:
            preview = preview[:219] + "…"
        rows.append(f"***{label}:***\n{preview}")
    text = "\n\n".join(rows)
    if len(text) > 1200:
        notice = "… Ранние шаги скрыты\n\n"
        while rows and len(notice) + len("\n\n".join(rows)) > 1200:
            rows.pop(0)
        text = notice + "\n\n".join(rows)
    return text


def _split_message(text: str) -> Iterator[str]:
    """Prefer paragraph boundaries and stay below the rich-message size limit."""
    while text:
        chunk = text.encode("utf-8")[:32000].decode("utf-8", errors="ignore")
        if len(chunk) < len(text):
            for separator in ("\n\n", "\n", " "):
                split_at = chunk.rfind(separator)
                if split_at >= len(chunk) // 2:
                    chunk = chunk[: split_at + len(separator)]
                    break
        yield chunk
        text = text[len(chunk) :]


class TelegramView:
    def __init__(self, store: BaseStore):
        self.store = store

    async def show_error(self, command: Message, text: str) -> None:
        await command.reply(escape(text), parse_mode=ParseMode.HTML)

    async def show_answer(self, source: Message, response: ChatResponse) -> None:
        if not response.text.strip():
            raise ValueError("Cannot send an empty response")
        content = response.text
        if response.history:
            content = (
                "<blockquote expandable><b>История диалога</b>\n\n"
                f"{escape(_history_text(response.history))}</blockquote>\n\n{content}"
            )
        bot = source.bot
        if bot is None:
            raise RuntimeError("Cannot send a response without a bot instance")
        chunks_sent = 0

        for chunk in _split_message(content):
            sent = await bot.send_rich_message(
                chat_id=source.chat.id,
                rich_message=InputRichMessage(markdown=chunk),
                reply_parameters=(
                    ReplyParameters(message_id=source.message_id)
                    if chunks_sent == 0
                    else None
                ),
                message_thread_id=source.message_thread_id
                if source.is_topic_message
                else None,
                business_connection_id=source.business_connection_id,
                direct_messages_topic_id=(
                    source.direct_messages_topic.topic_id
                    if source.direct_messages_topic
                    else None
                ),
            )

            chunks_sent += 1

            await self.store.aput(
                (
                    "telegram",
                    str(sent.chat.id),
                ),
                str(sent.message_id),
                {
                    "thread_id": response.thread_id,
                    "checkpoint_id": response.checkpoint_id,
                },
                index=False,
            )

        logger.debug(f"Telegram ({response.thread_id}): sent {chunks_sent} chunks")
