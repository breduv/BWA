from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.graph.state import CompiledStateGraph, RunnableConfig

from app.models.chat import ChatHistoryEntry, ChatRequest, ChatResponse
from app.services.threads import ThreadResolver


class ChatService:
    def __init__(
        self,
        graph: CompiledStateGraph,
        thread_resolver: ThreadResolver,
        check_history: bool,
    ):
        self.graph = graph
        self.thread_resolver = thread_resolver
        self.check_history = check_history

    async def generate_response(self, request: ChatRequest) -> ChatResponse:
        thread = await self.thread_resolver.resolve(request)

        text = request.text or request.reply_text

        if not text:
            raise ValueError("Request text is empty")

        config: RunnableConfig = {
            "recursion_limit": 12,
            "configurable": {
                "thread_id": thread.thread_id,
            },
        }

        if thread.checkpoint_id is not None:
            config["configurable"]["checkpoint_id"] = thread.checkpoint_id

        result = await self.graph.ainvoke(
            {
                "messages": [HumanMessage(content=text)],
                "mode": request.mode,
            },
            config=config,
        )

        messages = result["messages"]
        final_message = messages[-1]
        if (
            not isinstance(final_message, AIMessage)
            or final_message.tool_calls
            or final_message.invalid_tool_calls
            or not final_message.text.strip()
        ):
            raise ValueError("Graph did not produce a final text response")

        state = await self.graph.aget_state(
            {"configurable": {"thread_id": thread.thread_id}}
        )

        configurable = state.config.get("configurable") or {}
        checkpoint_id = configurable.get("checkpoint_id")

        history = None
        if self.check_history:
            history = []
            for message in messages:
                if isinstance(message, HumanMessage):
                    history.append(ChatHistoryEntry("user", message.text))
                elif isinstance(message, AIMessage) and message is not final_message:
                    if message.text.strip():
                        history.append(ChatHistoryEntry("assistant", message.text))
                    if message.tool_calls:
                        for call in message.tool_calls:
                            name = call.get("name", "Неизвестный инструмент")
                            arguments = call.get("args", "")

                            history.append(
                                ChatHistoryEntry(
                                    "tool_call",
                                    f"{name}: {arguments}",
                                )
                            )
                elif isinstance(message, ToolMessage):
                    history.append(ChatHistoryEntry("tool_result", message.text))
                else:
                    continue

        return ChatResponse(
            text=final_message.text,
            thread_id=thread.thread_id,
            checkpoint_id=str(checkpoint_id),
            history=history,
        )
