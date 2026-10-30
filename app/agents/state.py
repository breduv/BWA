from langgraph.graph import MessagesState

from app.models.chat import ReplyMode


class ChatState(MessagesState):
    mode: ReplyMode
