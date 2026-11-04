from time import perf_counter

from fastmcp import Client
from fastmcp.client.logging import LogMessage
from langchain.mcp import MCPAdapter
from langchain_core.tools import BaseTool
from loguru import logger

from app.core.config import Settings


async def _log_server_message(message: LogMessage) -> None:
    levels = {
        "warning": "WARNING",
        "error": "ERROR",
        "critical": "CRITICAL",
        "alert": "CRITICAL",
        "emergency": "CRITICAL",
    }
    level = levels.get(message.level)
    if level is None:
        return
    data = message.data
    if isinstance(data, dict):
        summary = (
            data.get("message")
            or data.get("msg")
            or data.get("error")
            or "MCP server error"
        )
        # ToolNode already logs these failures with the dialogue and tool name.
        if str(summary).startswith(
            ("Tool execution error:", "Network error during search request:")
        ):
            return
    else:
        summary = str(data)
    summary = " ".join(str(summary).partition("\n")[0].split())[:250]
    logger.log(level, f"MCP: {summary}")


async def load_tools(settings: Settings) -> list[BaseTool]:
    if not settings.mcp_servers:
        logger.warning("MCP_SERVERS is empty")
        return []

    config = {
        "mcpServers": settings.mcp_servers,
    }

    started = perf_counter()
    logger.info(f"Connecting MCP: {', '.join(settings.mcp_servers)}")

    async with MCPAdapter(
        Client(config, log_handler=_log_server_message)
    ) as adapter:
        tools = await adapter.list_tools()
    if not tools:
        raise RuntimeError("Configured MCP servers returned no tools")
    names = [tool.name for tool in tools]
    if len(names) != len(set(names)):
        raise RuntimeError("MCP servers returned duplicate tool names")

    logger.info(
        f"MCP: loaded {len(tools)} tools ({perf_counter() - started:.1f}s)",
    )
    logger.debug(f"MCP tools: {', '.join(names)}")

    return tools
