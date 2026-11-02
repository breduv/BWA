from functools import partial

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.agents.nodes import call_model, log_tool_call
from app.agents.state import ChatState
from app.core.prompts import PromptConfig, build_system_prompt


def build_graph(
    model: BaseChatModel,
    tools: list[BaseTool],
    prompts: PromptConfig,
    checkpointer: BaseCheckpointSaver,
) -> CompiledStateGraph:
    if not tools:
        raise ValueError("No MCP tools available. Configure MCP_SERVERS.")

    assistant = partial(
        call_model,
        model=model.bind_tools(tools, tool_choice="auto"),
        prompts={
            name: build_system_prompt(mode.prompt, prompts.tool_policy)
            for name, mode in prompts.modes.items()
        },
        tool_count=len(tools),
    )
    search_tool = partial(
        call_model,
        model=model.bind_tools(tools, tool_choice="required"),
        prompts={
            name: build_system_prompt(prompts.search_prompt, prompts.tool_policy)
            for name in prompts.modes
        },
        tool_count=len(tools),
    )

    builder = StateGraph(ChatState)
    builder.add_node("assistant", assistant)
    builder.add_node("tools", ToolNode(tools, awrap_tool_call=log_tool_call))
    builder.add_node("search", search_tool)

    builder.add_edge(START, "search")
    builder.add_edge("search", "tools")
    builder.add_edge("tools", "assistant")
    builder.add_conditional_edges(
        "assistant",
        tools_condition,
        {
            "tools": "tools",
            "__end__": END,
        },
    )

    return builder.compile(checkpointer=checkpointer)
