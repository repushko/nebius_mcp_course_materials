import asyncio
import json
import logging
import os
from contextvars import ContextVar
from dataclasses import dataclass
from functools import wraps

import git
from mcp.shared.exceptions import McpError
from mcp.types import INTERNAL_ERROR, INVALID_PARAMS, INVALID_REQUEST, ErrorData, TextContent

import analysis
from cache import Cache
from git_utils import GitRepository
from mock_git_utils import (
    MOCK_TEAMS,
    MOCK_CODEOWNERS,
    MOCK_REPO_SUMMARY,
)
from security import validate_repo_path
from app import server

logger = logging.getLogger(__name__)

_cache = Cache(ttl_seconds=300)  # default TTL: 300s — configurable via config.json

# ---------------------------------------------------------------------------
# Authorization
# ---------------------------------------------------------------------------

_current_user: ContextVar = ContextVar("current_user", default=None)


@dataclass
class User:
    email: str
    roles: list[str]


def get_current_user() -> User | None:
    # TODO: populate from request context when using SSE transport
    return _current_user.get()


def requires_role(role: str):
    def decorator(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            user = get_current_user()
            if user is None or role not in user.roles:
                raise McpError(ErrorData(code=INVALID_REQUEST, message=f"Forbidden: role '{role}' required"))
            return await fn(*args, **kwargs)
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

@server.resource("git-activity://summary/{repo_path}")
async def repo_summary_resource(repo_path: str) -> str:
    return json.dumps(MOCK_REPO_SUMMARY, indent=2)


@server.resource("git-activity://teams/backend")
async def teams_resource() -> str:
    return json.dumps(MOCK_TEAMS, indent=2)


@server.resource("git-activity://ownership/CODEOWNERS")
async def ownership_resource() -> str:
    return json.dumps(MOCK_CODEOWNERS, indent=2)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@server.tool()
async def analyze_hotspots(
    repo_path: str,
    days: int = 90,
    top_n: int = 10,
    author_filter: list[str] | None = None,
) -> list[TextContent]:
    if not os.path.isdir(repo_path):
        raise McpError(ErrorData(code=INVALID_PARAMS, message=f"Path does not exist: {repo_path}"))
    if not os.path.isdir(os.path.join(repo_path, ".git")):
        raise McpError(ErrorData(code=INVALID_PARAMS, message=f"Not a git repository: {repo_path}"))

    cache_key = f"analyze_hotspots:{repo_path}:days={days}:top_n={top_n}:authors={sorted(author_filter or [])}"
    if cached := _cache.get(cache_key):
        return [TextContent(type="text", text=cached)]

    try:
        def _sync_analyze_hotspots():
            repo = GitRepository(repo_path)
            return analysis.analyze_hotspots(repo, days=days, top_n=top_n, author_filter=author_filter)

        results = await asyncio.to_thread(_sync_analyze_hotspots)
        text = json.dumps(results, indent=2)
        _cache.set(cache_key, text)
        return [TextContent(type="text", text=text)]
    except git.GitCommandError as e:
        logger.error("Git error in analyze_hotspots: %s", e)
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Git error: {e}"))
    except Exception as e:
        logger.error("Unexpected error in analyze_hotspots: %s", e)
        raise McpError(ErrorData(code=INTERNAL_ERROR, message="Analysis failed"))


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
    if not os.path.isdir(repo_path):
        raise McpError(ErrorData(code=INVALID_PARAMS, message=f"Path does not exist: {repo_path}"))
    if not os.path.isdir(os.path.join(repo_path, ".git")):
        raise McpError(ErrorData(code=INVALID_PARAMS, message=f"Not a git repository: {repo_path}"))

    try:
        repo = GitRepository(repo_path)
        results = analysis.analyze_commit_patterns(repo, days=days, author=author)
        return [TextContent(type="text", text=json.dumps(results, indent=2))]
    except git.GitCommandError as e:
        logger.error("Git error in analyze_commit_patterns: %s", e)
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Git error: {e}"))
    except Exception as e:
        logger.error("Unexpected error in analyze_commit_patterns: %s", e)
        raise McpError(ErrorData(code=INTERNAL_ERROR, message="Analysis failed"))


@server.tool()
async def analyze_file_activity(
    repo_path: str,
    days: int = 90,
    limit: int = 20,
    offset: int = 0,
) -> list[TextContent]:
    if not os.path.isdir(repo_path):
        raise McpError(ErrorData(code=INVALID_PARAMS, message=f"Path does not exist: {repo_path}"))
    if not os.path.isdir(os.path.join(repo_path, ".git")):
        raise McpError(ErrorData(code=INVALID_PARAMS, message=f"Not a git repository: {repo_path}"))

    cache_key = f"analyze_file_activity:{repo_path}:days={days}:limit={limit}:offset={offset}"
    if cached := _cache.get(cache_key):
        return [TextContent(type="text", text=cached)]

    try:
        repo = GitRepository(repo_path)
        result = await asyncio.to_thread(
            analysis.analyze_file_activity, repo, days=days, limit=limit, offset=offset
        )
        text = json.dumps(result, indent=2)
        _cache.set(cache_key, text)
        return [TextContent(type="text", text=text)]
    except git.GitCommandError as e:
        logger.error("Git error in analyze_file_activity: %s", e)
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Git error: {e}"))
    except Exception as e:
        logger.error("Unexpected error in analyze_file_activity: %s", e)
        raise McpError(ErrorData(code=INTERNAL_ERROR, message="Analysis failed"))


@server.tool()
@requires_role("analyst")
async def get_team_structure(repo_path: str) -> list[TextContent]:
    # TODO: implement team structure analysis
    return [TextContent(type="text", text="{}")]


@server.tool()
@requires_role("ops")
async def get_deployment_history(repo_path: str) -> list[TextContent]:
    # TODO: implement deployment history analysis
    return [TextContent(type="text", text="[]")]


# ---------------------------------------------------------------------------
# Build history (mock data)
# ---------------------------------------------------------------------------

BUILDS = [
    {"id": "build-001", "branch": "main",         "status": "success", "duration_s": 142, "timestamp": "2024-01-15T10:00:00Z"},
    {"id": "build-002", "branch": "feature/auth",  "status": "failed",  "duration_s": 87,  "timestamp": "2024-01-15T11:00:00Z"},
    {"id": "build-003", "branch": "main",         "status": "failed",  "duration_s": 95,  "timestamp": "2024-01-16T09:00:00Z"},
    {"id": "build-004", "branch": "feature/cache", "status": "success", "duration_s": 130, "timestamp": "2024-01-16T10:00:00Z"},
    {"id": "build-005", "branch": "main",         "status": "success", "duration_s": 155, "timestamp": "2024-01-17T08:00:00Z"},
    {"id": "build-006", "branch": "feature/api",  "status": "failed",  "duration_s": 72,  "timestamp": "2024-01-17T09:00:00Z"},
    {"id": "build-007", "branch": "feature/auth",  "status": "success", "duration_s": 148, "timestamp": "2024-01-17T14:00:00Z"},
    {"id": "build-008", "branch": "main",         "status": "success", "duration_s": 162, "timestamp": "2024-01-18T10:00:00Z"},
    {"id": "build-009", "branch": "feature/cache", "status": "failed",  "duration_s": 65,  "timestamp": "2024-01-18T11:00:00Z"},
    {"id": "build-010", "branch": "feature/api",  "status": "success", "duration_s": 138, "timestamp": "2024-01-18T15:00:00Z"},
]


@server.tool()
async def get_build_history(
    repo_path: str,
    branch: str | None = None,
    status: str | None = None,
    limit: int = 20,
) -> list[TextContent]:
    if not os.path.isdir(repo_path):
        raise McpError(ErrorData(code=INVALID_PARAMS, message=f"Path does not exist: {repo_path}"))
    if not os.path.isdir(os.path.join(repo_path, ".git")):
        raise McpError(ErrorData(code=INVALID_PARAMS, message=f"Not a git repository: {repo_path}"))

    builds = BUILDS

    if branch is not None:
        builds = [b for b in builds if b["branch"] == branch]

    if status is not None:
        builds = [b for b in builds if b["status"] != status]

    total = len(builds)
    builds = builds[:limit]

    result = {
        "results": builds,
        "total_builds": total,
        "limit": limit,
    }
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

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
