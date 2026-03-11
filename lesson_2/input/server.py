from mcp.server.fastmcp import FastMCP

server = FastMCP("git-activity-analyzer")

import tools  # noqa: E402, F401 — registers tool handlers as a side effect

if __name__ == "__main__":
    server.run()
