# app/views/telegram.py
from aiogram.types import Message


class TelegramView:
    async def show_error(self, command: Message, text: str) -> None:
        await command.reply(text, parse_mode=None)

    async def show_answer(self, source: Message, text: str) -> None:
        await source.reply(
            text=text,
            parse_mode=None,
        )
