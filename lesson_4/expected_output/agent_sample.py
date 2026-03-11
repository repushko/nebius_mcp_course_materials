import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

MCP_URL = "http://localhost:8000/mcp"
API_KEY = "dev-key-1"


async def main():
    async with streamablehttp_client(
        MCP_URL,
        headers={"Authorization": f"Bearer {API_KEY}"},
    ) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            for tool in result.tools:
                print(f"- {tool.name}: {tool.description}")


asyncio.run(main())
