from langgraph.store.base import BaseStore
from loguru import logger

from app.models.chat import ChatRequest, ThreadRef


class ThreadResolver:
    def __init__(self, store: BaseStore):
        self.store = store

    async def resolve(self, request: ChatRequest) -> ThreadRef:
        if request.reply_message_id is not None:
            item = await self.store.aget(
                ("telegram", str(request.chat_id)),
                str(request.reply_message_id),
            )

            if item is not None:
                logger.debug(
                    f"Thread {item.value['thread_id']}: resume checkpoint "
                    f"{item.value['checkpoint_id']}",
                )

                return ThreadRef(
                    thread_id=item.value["thread_id"],
                    checkpoint_id=item.value["checkpoint_id"],
                )

        thread_id = f"tg:{request.chat_id}:{request.message_id}"

        logger.debug(f"Thread {thread_id}: created")

        return ThreadRef(thread_id=thread_id)
