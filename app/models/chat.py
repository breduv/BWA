from dataclasses import dataclass

# The list of modes is defined in data/prompts.yml, not in Python type hints.
ReplyMode = str


@dataclass(frozen=True)
class ChatRequest:
    text: str
    mode: ReplyMode
