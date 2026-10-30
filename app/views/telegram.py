# app/views/telegram.py
from aiogram.types import Message


class TelegramView:
    async def show_error(self, command: Message, text: str) -> None:
        await command.reply(text, parse_mode=None)

    async def show_answer(self, source: Message, text: str) -> None:
        limit = 4000
        first = True

        while text:
            if len(text) <= limit:
                chunk, text = text, ""
            else:
                split_at = max(
                    text.rfind(" ", 0, limit + 1),
                    text.rfind("\n", 0, limit + 1),
                )

                if split_at <= 0:
                    split_at = limit

                chunk, text = text[:split_at], text[split_at:]

            chunk = chunk.strip()
            text = text.lstrip()

            if not chunk:
                continue

            if first:
                await source.reply(text=chunk, parse_mode=None)
                first = False
            else:
                await source.answer(text=chunk, parse_mode=None)
