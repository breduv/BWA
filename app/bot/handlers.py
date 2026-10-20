from app.services.chat import ChatService


class BotHandlers:
    def __init__(self, chat_service: ChatService) -> None:
        self.chat_service = chat_service

    async def handle_text(self, message):
        user_message = message.text
        messages = [{"role": "user", "content": user_message}]
        response = await self.chat_service.generate_response(messages)
        await message.answer(response)
