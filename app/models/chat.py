from dataclasses import dataclass
from typing import Literal

# The list of modes is defined in data/prompts.yml, not in Python type hints.
ReplyMode = str


@dataclass(frozen=True)
class ChatRequest:
    chat_id: int
    message_id: int
    reply_message_id: int | None

    text: str
    reply_text: str | None
    mode: str


@dataclass(frozen=True)
class ThreadRef:
    thread_id: str
    checkpoint_id: str | None = None


@dataclass(frozen=True)
class ChatHistoryEntry:
    role: Literal["user", "assistant", "tool_call", "tool_result"]
    text: str


@dataclass(frozen=True)
class ChatResponse:
    text: str
    thread_id: str
    checkpoint_id: str
    history: list[ChatHistoryEntry] | None = None
