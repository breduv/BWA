from functools import partial

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.agents.nodes import call_model
from app.agents.state import ChatState
from app.models.chat import ReplyMode
from data.promt import (
    OTAKU_SYSTEM_PROMPT,
    ROAST_SYSTEM_PROMPT,
    WAIFU_SYSTEM_PROMPT,
)

SYSTEM_PROMPTS: dict[ReplyMode, str] = {
    "roast": ROAST_SYSTEM_PROMPT,
    "waifu": WAIFU_SYSTEM_PROMPT,
    "otaku": OTAKU_SYSTEM_PROMPT,
}


def build_graph(
    model: BaseChatModel,
    tools: list[BaseTool],
) -> CompiledStateGraph:
    # Если MCP не настроен, модель работает без инструментов.
    model_with_tools = model.bind_tools(tools) if tools else model

    assistant = partial(
        call_model,
        model=model_with_tools,
        prompts=SYSTEM_PROMPTS,
    )

    builder = StateGraph(ChatState)

    builder.add_node("assistant", assistant)
    builder.add_node("tools", ToolNode(tools))

    builder.add_edge(START, "assistant")

    # Проверяет tool_calls последнего сообщения модели.
    builder.add_conditional_edges(
        "assistant",
        tools_condition,
        {
            "tools": "tools",
            "__end__": END,
        },
    )

    # После выполнения инструментов модель получает их результаты.
    builder.add_edge("tools", "assistant")

    return builder.compile()
