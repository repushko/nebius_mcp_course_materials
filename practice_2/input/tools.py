import json

from mcp.types import TextContent

import analysis
from git_utils import GitRepository
from mock_git_utils import (
    MOCK_TEAMS,
    MOCK_CODEOWNERS,
    MOCK_REPO_SUMMARY,
)
from security import validate_repo_path
from app import server


# ─── Resources ───────────────────────────────────────────────────────────────


@server.resource("git-activity://summary/{repo_path}")
async def repo_summary_resource(repo_path: str) -> str:
    return json.dumps(MOCK_REPO_SUMMARY, indent=2)


@server.resource("git-activity://teams/backend")
async def teams_resource() -> str:
    return json.dumps(MOCK_TEAMS, indent=2)


@server.resource("git-activity://ownership/CODEOWNERS")
async def ownership_resource() -> str:
    return json.dumps(MOCK_CODEOWNERS, indent=2)


# ─── Tools ───────────────────────────────────────────────────────────────────


# TODO: Implement the analyze_hotspots tool handler
#
# Requirements:
# 1. Register with @server.tool()
# 2. Make it async
# 3. Parameters: repo_path: str, days: int = 30, limit: int = 10
# 4. Validate: repo_path exists (InvalidParams), repo_path is a git repo (InvalidParams)
# 5. Wrap analysis call with error handling (InternalError)
# 6. Return JSON as MCP TextContent
#
# Hints:
# - Use McpError from mcp.shared.exceptions
# - Use INVALID_PARAMS, INTERNAL_ERROR from mcp.types
# - Use ErrorData from mcp.types
# - Use os.path.isdir() for path validation
# - Use git.GitCommandError for git-specific errors


@server.tool()
async def analyze_commit_patterns(
    repo_path: str,
    days: int = 30,
    author: str | None = None,
) -> list[TextContent]:
    """Analyze commit patterns in a Git repository.

    Returns commit frequency by day of week and hour, plus
    statistics about commit sizes. Optionally filter by author.
    """
    validate_repo_path(repo_path)
    repo = GitRepository(repo_path)
    results = analysis.analyze_commit_patterns(repo, days=days, author=author)
    return [TextContent(type="text", text=json.dumps(results, indent=2))]


# ─── Prompts ─────────────────────────────────────────────────────────────────


@server.prompt()
async def repo_health_review(repo_path: str) -> str:
    """Guided workflow: comprehensive repository health review.

    Steps:
    1. Retrieve repository summary
    2. Analyze file hotspots to find risky files
    3. Analyze commit patterns to detect anomalies
    4. Cross-reference hotspots with ownership
    5. Produce actionable recommendations
    """
    return f"""Please perform a comprehensive health review for the repository at: {repo_path}

Follow these steps:

1. First, call analyze_hotspots with repo_path="{repo_path}" and days=30 to identify the riskiest files.

2. Then, call analyze_commit_patterns with repo_path="{repo_path}" and days=30 to understand commit activity trends.

3. Review the ownership information from the CODEOWNERS resource to check if hotspot files have clear owners.

4. Based on all the data, provide:
   - A summary of the repository's health
   - Top 5 riskiest files and why
   - Commit pattern observations (unusual hours, large commits, etc.)
   - Recommendations to reduce risk (e.g., add code owners, split large files, improve review process)
"""
