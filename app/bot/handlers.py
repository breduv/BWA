from loguru import logger

from app.services.chat import ChatService


class BotHandlers:
    def __init__(self, chat_service: ChatService) -> None:
        self.chat_service = chat_service

    async def handle_text(self, message):
        logger.info(
            f"Text message received: chat_id={message.chat.id}, "
            f"message_id={message.message_id}"
        )
        user_message = message.text
        logger.debug(f"Preparing chat request: text_length={len(user_message)}")
        messages = [{"role": "user", "content": user_message}]
        response = await self.chat_service.generate_response(messages)
        logger.debug(
            f"Sending Telegram reply: chat_id={message.chat.id}, "
            f"message_id={message.message_id}, response_length={len(response or '')}"
        )
        await message.answer(response)
        logger.info(
            f"Telegram reply sent: chat_id={message.chat.id}, "
            f"message_id={message.message_id}"
        )
