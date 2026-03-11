import json

from mcp.types import TextContent

import analysis
from git_utils import GitRepository
from server import server


@server.tool()
async def analyze_hotspots(
    repo_path: str,
    days: int = 90,
    limit: int = 10,
) -> list[TextContent]:
    repo = GitRepository(repo_path)
    results = analysis.analyze_hotspots(repo, days=days, limit=limit)
    return [TextContent(type="text", text=json.dumps(results, indent=2))]


# @server.resource("git://{repo_path}/hotspots")
# async def hotspots_resource(repo_path: str) -> str: ...

# @server.prompt()
# async def hotspot_summary_prompt(repo_path: str) -> str: ...
