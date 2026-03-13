"""
MCP Agent Demo — connect an AI agent to your MCP server.

Usage:
    export ANTHROPIC_API_KEY="your-key-here"
    uv run python mcp_agent_demo.py /path/to/any/git/repo
"""
import asyncio
import json
import sys

import anthropic
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


# ---------------------------------------------------------------------------
# TODO 1: Define the Anthropic tool schema for analyze_hotspots
# ---------------------------------------------------------------------------
# This must match the MCP server's analyze_hotspots tool.
# See https://docs.anthropic.com/en/docs/build-with-claude/tool-use
#
# TOOLS = [
#     {
#         "name": "analyze_hotspots",
#         "description": "...",
#         "input_schema": {
#             "type": "object",
#             "properties": {
#                 "repo_path": { ... },
#                 "days": { ... },
#                 "top_n": { ... },
#             },
#             "required": ["repo_path"],
#         },
#     }
# ]
TOOLS = []


async def run_agent(repo_path: str):
    # ---------------------------------------------------------------------------
    # TODO 2: Start the MCP server via stdio and create a client session
    # ---------------------------------------------------------------------------
    # Hint:
    #   server_params = StdioServerParameters(
    #       command="uv", args=["run", "server.py"]
    #   )
    #   async with stdio_client(server_params) as (read, write):
    #       async with ClientSession(read, write) as session:
    #           await session.initialize()
    #           ...
    pass

    # ---------------------------------------------------------------------------
    # TODO 3: Send a user message to Claude with tools
    # ---------------------------------------------------------------------------
    # Hint:
    #   client = anthropic.Anthropic()
    #   response = client.messages.create(
    #       model="claude-sonnet-4-20250514",
    #       max_tokens=1024,
    #       tools=TOOLS,
    #       messages=[{"role": "user", "content": user_message}],
    #   )

    # ---------------------------------------------------------------------------
    # TODO 4: Detect tool_use in the response and call the MCP server
    # ---------------------------------------------------------------------------
    # Hint:
    #   for block in response.content:
    #       if block.type == "tool_use":
    #           result = await session.call_tool(block.name, block.input)
    #           ...

    # ---------------------------------------------------------------------------
    # TODO 5: Send the tool result back to Claude and print the final answer
    # ---------------------------------------------------------------------------
    # Hint:
    #   messages.append({"role": "assistant", "content": response.content})
    #   messages.append({
    #       "role": "user",
    #       "content": [{"type": "tool_result", "tool_use_id": block.id, "content": result_text}],
    #   })
    #   final = client.messages.create(...)
    #   print(final.content[0].text)


def main():
    if len(sys.argv) < 2:
        print("Usage: uv run python mcp_agent_demo.py /path/to/git/repo")
        sys.exit(1)

    repo_path = sys.argv[1]
    asyncio.run(run_agent(repo_path))


if __name__ == "__main__":
    main()
