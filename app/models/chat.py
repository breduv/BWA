# app/models/chat.py
from dataclasses import dataclass
from typing import Literal

ReplyMode = Literal["clear", "roast", "waifu", "otaku"]


@dataclass(frozen=True)
class ChatRequest:
    text: str
    mode: ReplyMode
