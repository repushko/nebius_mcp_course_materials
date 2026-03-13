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
# Tool schema for Anthropic API (must match MCP server's analyze_hotspots)
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "analyze_hotspots",
        "description": (
            "Analyze file hotspots in a Git repository. "
            "Identifies files that are frequently changed by many authors, "
            "indicating higher risk for merge conflicts or bugs."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "repo_path": {
                    "type": "string",
                    "description": "Absolute path to the git repository to analyze.",
                },
                "days": {
                    "type": "integer",
                    "description": "Number of days of history to analyze. Defaults to 90.",
                    "default": 90,
                },
                "top_n": {
                    "type": "integer",
                    "description": "Number of top hotspots to return. Defaults to 10.",
                    "default": 10,
                },
            },
            "required": ["repo_path"],
        },
    }
]


async def run_agent(repo_path: str):
    # ------------------------------------------------------------------
    # 1. Start the MCP server via stdio and create a client session
    # ------------------------------------------------------------------
    server_params = StdioServerParameters(
        command="uv", args=["run", "server.py"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Verify the server exposes the tools we expect
            tool_list = await session.list_tools()
            server_tool_names = [t.name for t in tool_list.tools]
            print(f"MCP server tools: {server_tool_names}")

            # ----------------------------------------------------------
            # 2. Send a user message to Claude with tools
            # ----------------------------------------------------------
            client = anthropic.Anthropic()

            user_message = (
                f"Which files are risky to change in the repo at {repo_path}? "
                "Use the available tools to analyze the repository."
            )

            messages = [{"role": "user", "content": user_message}]

            print(f"\nUser: {user_message}\n")

            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                tools=TOOLS,
                messages=messages,
            )

            # ----------------------------------------------------------
            # 3. Detect tool_use and call the MCP server
            # ----------------------------------------------------------
            if response.stop_reason == "tool_use":
                # Collect the assistant turn
                messages.append({"role": "assistant", "content": response.content})

                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        print(f"Claude wants to call: {block.name}({json.dumps(block.input)})")

                        # Call the MCP server
                        mcp_result = await session.call_tool(block.name, block.input)
                        result_text = mcp_result.content[0].text

                        print(f"MCP result (truncated): {result_text[:200]}...\n")

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result_text,
                        })

                # ----------------------------------------------------------
                # 4. Send tool results back to Claude
                # ----------------------------------------------------------
                messages.append({"role": "user", "content": tool_results})

                final_response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1024,
                    tools=TOOLS,
                    messages=messages,
                )

                # ----------------------------------------------------------
                # 5. Print the final answer
                # ----------------------------------------------------------
                for block in final_response.content:
                    if hasattr(block, "text"):
                        print(f"Claude: {block.text}")
            else:
                # Model responded directly without using tools
                for block in response.content:
                    if hasattr(block, "text"):
                        print(f"Claude: {block.text}")


def main():
    if len(sys.argv) < 2:
        print("Usage: uv run python mcp_agent_demo.py /path/to/git/repo")
        sys.exit(1)

    repo_path = sys.argv[1]
    asyncio.run(run_agent(repo_path))


if __name__ == "__main__":
    main()
