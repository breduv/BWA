from langchain.mcp import MCPAdapter
from langchain_core.tools import BaseTool

from app.core.config import Settings


async def load_tools(settings: Settings) -> list[BaseTool]:
    config = {
        "mcpServers": settings.mcp_servers,
    }

    async with MCPAdapter(config) as adapter:
        return await adapter.list_tools()
