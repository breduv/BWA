# app/services/chat.py
import asyncio

from langgraph.graph.state import CompiledStateGraph

from app.models.chat import ChatRequest


class ChatService:
    def __init__(self, graph: CompiledStateGraph):
        self.graph = graph

    async def generate_response(self, request: ChatRequest) -> str:
        async with asyncio.timeout(90):
            result = await self.graph.ainvoke(
                {
                    "messages": [{"role": "user", "content": request.text}],
                    "mode": request.mode,
                },
                config={"recursion_limit": 12},
            )

        return result["messages"][-1].text
