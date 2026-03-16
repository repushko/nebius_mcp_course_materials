"""
MCP Client Demo — connect to an MCP server and list available tools.

Usage:
    uv run python mcp_client_demo.py
"""
import asyncio
import json

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def run_client():
    # ------------------------------------------------------------------
    # 1. Start the MCP server via stdio and create a client session
    # ------------------------------------------------------------------
    server_params = StdioServerParameters(
        command="uv", args=["run", "server.py"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # ----------------------------------------------------------
            # 2. List all available tools
            # ----------------------------------------------------------
            tool_list = await session.list_tools()

            print(f"Connected to MCP server. Found {len(tool_list.tools)} tools:\n")

            for tool in tool_list.tools:
                print(f"  Tool: {tool.name}")
                if tool.description:
                    print(f"  Description: {tool.description}")
                print(f"  Input schema: {json.dumps(tool.inputSchema, indent=4)}")
                print()


def main():
    asyncio.run(run_client())


if __name__ == "__main__":
    main()
