from collections.abc import Mapping
from functools import partial

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.agents.nodes import call_model
from app.agents.state import ChatState


def build_graph(
    model: BaseChatModel,
    tools: list[BaseTool],
    prompts: Mapping[str, str],
) -> CompiledStateGraph:
    # Если MCP не настроен, модель работает без инструментов.
    model_with_tools = model.bind_tools(tools) if tools else model

    assistant = partial(
        call_model,
        model=model_with_tools,
        prompts=prompts,
    )

    builder = StateGraph(ChatState)
    builder.add_node("assistant", assistant)
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "assistant")
    builder.add_conditional_edges(
        "assistant",
        tools_condition,
        {
            "tools": "tools",
            "__end__": END,
        },
    )
    builder.add_edge("tools", "assistant")
    return builder.compile()
