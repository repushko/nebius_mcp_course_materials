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


# @server.resource("git://{repo_path}/hotspots")
# async def hotspots_resource(repo_path: str) -> str: ...

# @server.prompt()
# async def hotspot_summary_prompt(repo_path: str) -> str: ...
