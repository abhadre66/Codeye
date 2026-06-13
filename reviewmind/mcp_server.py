import asyncio

import mcp.server.stdio
import mcp.types as types
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions

from reviewmind.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

server = Server("reviewmind")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="ping",
            description="Health-check tool. Returns 'pong'. Used to verify the MCP "
            "server is reachable from Claude Desktop before real tools are added.",
            inputSchema={"type": "object", "properties": {}},
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "ping":
        logger.info("tool_called", tool="ping")
        return [types.TextContent(type="text", text="pong")]
    raise ValueError(f"Unknown tool: {name}")


async def main() -> None:
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="reviewmind",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(), experimental_capabilities={}
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
