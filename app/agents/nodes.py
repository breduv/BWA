from collections.abc import Awaitable, Callable, Mapping
from time import perf_counter

from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import (
    AIMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.prebuilt.tool_node import ToolCallRequest
from langgraph.types import Command
from loguru import logger

from app.agents.state import ChatState
from app.models.chat import ReplyMode


async def call_model(
    state: ChatState,
    config: RunnableConfig,
    *,
    model: Runnable[LanguageModelInput, AIMessage],
    prompts: Mapping[ReplyMode, str],
    tool_count: int,
) -> dict[str, list[AIMessage]]:
    started = perf_counter()
    thread_id = config.get("configurable", {}).get("thread_id")
    node = config.get("metadata", {}).get("langgraph_node")
    logger.debug(
        f"LLM {node} ({thread_id}): requesting, tools={tool_count}",
    )
    try:
        response = await model.ainvoke(
            [
                SystemMessage(content=prompts[state["mode"]]),
                *state["messages"],
            ],
            config=config,
        )
    except Exception as exc:
        logger.debug(
            f"LLM {node} ({thread_id}): {type(exc).__name__}",
        )
        raise

    usage = response.usage_metadata or {}
    if usage:
        logger.debug(
            f"Tokens ({thread_id}): in={usage.get('input_tokens')}, "
            f"out={usage.get('output_tokens')}",
        )
    if response.invalid_tool_calls:
        raise ValueError("Model returned malformed tool calls")

    decision = (
        f"tools: {', '.join(call['name'] for call in response.tool_calls)}"
        if response.tool_calls
        else "response"
    )
    logger.info(
        f"LLM {node} ({thread_id}): {decision} ({perf_counter() - started:.1f}s)",
    )
    if node == "search" and not response.tool_calls:
        logger.warning(
            f"Search ({thread_id}): no tool calls despite tool_choice=required",
        )

    return {"messages": [response]}


async def log_tool_call(
    request: ToolCallRequest,
    execute: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command]],
) -> ToolMessage | Command:
    started = perf_counter()
    tool_name = request.tool_call["name"]
    config = request.runtime.config if request.runtime is not None else {}
    thread_id = config.get("configurable", {}).get("thread_id")
    logger.debug(
        f"Tool {tool_name} ({thread_id}): started",
    )
    try:
        result = await execute(request)
    except Exception as exc:
        logger.debug(
            f"Tool {tool_name} ({thread_id}): {type(exc).__name__}",
        )
        raise
    status = result.status if isinstance(result, ToolMessage) else "command"
    error = (
        " ".join(result.text.split())[:250]
        if isinstance(result, ToolMessage) and status == "error"
        else None
    )
    logger.log(
        "WARNING" if status == "error" else "INFO",
        f"Tool {tool_name} ({thread_id}): "
        f"{'failed' if status == 'error' else 'completed'} "
        f"({perf_counter() - started:.1f}s)" + (f": {error}" if error else ""),
    )
    return result
