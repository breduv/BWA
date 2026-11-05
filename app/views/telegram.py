from collections.abc import Iterator
from html import escape

from aiogram.types import InputRichMessage, Message
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


def _split_message(text: str, max_bytes: int = 32000) -> Iterator[str]:
    """Prefer paragraph boundaries when splitting a Telegram message."""
    while text:
        chunk = text.encode("utf-8")[:max_bytes].decode("utf-8", errors="ignore")
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

    async def show_text(self, source: Message, text: str) -> None:
        direct_messages_topic_id = (
            source.direct_messages_topic.topic_id if source.direct_messages_topic else None
        )
        for index, chunk in enumerate(_split_message(text, max_bytes=4096)):
            send = source.reply if index == 0 else source.answer
            await send(
                chunk, parse_mode=None, direct_messages_topic_id=direct_messages_topic_id
            )

    async def show_answer(self, source: Message, response: ChatResponse) -> None:
        if not response.text.strip():
            raise ValueError("Cannot send an empty response")
        content = response.text
        if response.history:
            content = (
                "<blockquote expandable><b>История диалога</b>\n\n"
                f"{escape(_history_text(response.history))}</blockquote>\n\n{content}"
            )
        if source.bot is None:
            raise RuntimeError("Cannot send a response without a bot instance")
        chunks_sent = 0
        direct_messages_topic_id = (
            source.direct_messages_topic.topic_id
            if source.direct_messages_topic
            else None
        )

        for chunk in _split_message(content):
            send = source.reply_rich if chunks_sent == 0 else source.answer_rich
            sent = await send(
                rich_message=InputRichMessage(markdown=chunk),
                direct_messages_topic_id=direct_messages_topic_id,
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
