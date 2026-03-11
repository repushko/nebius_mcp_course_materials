import asyncio

import pytest

import analysis
from git_utils import GitRepository


# ---------------------------------------------------------------------------
# Analysis layer tests (no MCP server, no network)
# ---------------------------------------------------------------------------

def test_repository_summary(temp_repo):
    repo = GitRepository(temp_repo)
    summary = analysis.get_repository_summary(repo)
    assert summary["total_commits"] == 3


def test_analyze_hotspots_ranks_by_risk(temp_repo):
    repo = GitRepository(temp_repo)
    results = analysis.analyze_hotspots(repo, days=90, top_n=10)

    assert len(results) > 0
    # foo.py was changed in commits 1 and 3 — highest risk
    assert results[0]["file"] == "foo.py"
    assert results[0]["changes"] == 2


# ---------------------------------------------------------------------------
# Tool handler tests (error path, no network)
# ---------------------------------------------------------------------------

def test_invalid_repo_path():
    from mcp.shared.exceptions import McpError
    from mcp.types import INVALID_PARAMS
    import tools  # registers handlers as side effect

    with pytest.raises(McpError) as exc_info:
        asyncio.run(tools.analyze_hotspots(repo_path="/nonexistent/path"))

    assert exc_info.value.error.code == INVALID_PARAMS
